/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - API Client
   v0.1.0 - Handles all communication with MitmProxy FastAPI backend
   
   Endpoints (from OpenAPI spec):
   - POST /proxy/process-request
   - POST /proxy/process-response
   - GET  /proxy/get-proxy-stats
   - POST /proxy/reset-proxy-stats
   - GET  /info/health
   ═══════════════════════════════════════════════════════════════════════════════ */

/**
 * API Client for MitmProxy Service
 */
class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl || '';
        this.defaultTimeout = 30000;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Core HTTP Methods
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Make a POST request to the API
     * @param {string} endpoint - API endpoint path
     * @param {object} data - Request body data
     * @param {object} options - Additional fetch options
     * @returns {Promise<object>} Response data
     */
    async post(endpoint, data, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const timeout = options.timeout || this.defaultTimeout;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                body: JSON.stringify(data),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new ApiError(
                    errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
                    response.status,
                    errorData
                );
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new ApiError('Request timed out', 408);
            }

            if (error instanceof ApiError) {
                throw error;
            }

            throw new ApiError(
                error.message || 'Network error',
                0,
                { originalError: error }
            );
        }
    }

    /**
     * Make a GET request to the API
     * @param {string} endpoint - API endpoint path
     * @param {object} options - Additional fetch options
     * @returns {Promise<object>} Response data
     */
    async get(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const timeout = options.timeout || this.defaultTimeout;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: options.headers || {},
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new ApiError(
                    `HTTP ${response.status}: ${response.statusText}`,
                    response.status
                );
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            return await response.text();
        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new ApiError('Request timed out', 408);
            }

            if (error instanceof ApiError) {
                throw error;
            }

            throw new ApiError(error.message || 'Network error', 0);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // MitmProxy API Methods
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Process a request through MitmProxy
     * This simulates what happens when a browser request hits the proxy
     * 
     * @param {object} requestData - Request data matching Schema__Proxy__Request_Data__BaseModel
     * @param {string} requestData.method - HTTP method (GET, POST, etc.)
     * @param {string} requestData.host - Target host
     * @param {string} requestData.path - Request path
     * @param {object} requestData.headers - Request headers (including cookies)
     * @param {object} requestData.stats - Optional stats object
     * @param {string} requestData.version - Optional version string
     * @returns {Promise<object>} Proxy response (may include cached response or action: continue)
     */
    async processRequest(requestData) {
        return this.post('/proxy/process-request', requestData);
    }

    /**
     * Process a response through MitmProxy
     * This simulates what happens when an upstream response is received
     * 
     * @param {object} responseData - Response data matching Schema__Proxy__Response_Data__BaseModel
     * @param {object} responseData.request - Original request object
     * @param {object} responseData.response - Upstream response object
     * @param {object} responseData.stats - Optional stats object
     * @param {string} responseData.version - Optional version string
     * @returns {Promise<object>} Transformed response
     */
    async processResponse(responseData) {
        return this.post('/proxy/process-response', responseData);
    }

    /**
     * Get proxy statistics
     * @returns {Promise<object>} Stats object
     */
    async getProxyStats() {
        return this.get('/proxy/get-proxy-stats');
    }

    /**
     * Reset proxy statistics
     * @returns {Promise<object>} Reset confirmation
     */
    async resetProxyStats() {
        return this.post('/proxy/reset-proxy-stats', {});
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Health & Info
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Check API health status
     * @returns {Promise<boolean>}
     */
    async checkHealth() {
        try {
            await this.get('/info/health', { timeout: 5000 });
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Get server info
     * @returns {Promise<object>}
     */
    async getServerInfo() {
        return this.get('/info/server');
    }

    /**
     * Get service version
     * @returns {Promise<object>}
     */
    async getVersion() {
        return this.get('/info/version');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Helper Methods for Building Payloads
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Build a request payload from URL and options
     * @param {string} url - Full URL
     * @param {string} mode - Transformation mode (cache, xxx, xxx-negative, etc.)
     * @param {object} extraHeaders - Additional headers
     * @returns {object} Request payload for processRequest()
     */
    buildRequestPayload(url, mode, extraHeaders = {}) {
        const parsed = Helpers.parseUrl(url);
        if (!parsed) {
            throw new ApiError('Invalid URL', 400);
        }

        return {
            method: 'GET',
            host: parsed.host,
            path: parsed.path || '/',
            headers: {
                'cookie': `mitm-mode=${mode}`,
                'user-agent': 'MitmProxy-Simulator/0.1.0',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                ...extraHeaders
            },
            stats: {
                simulator: true,
                timestamp: Date.now()
            }
        };
    }

    /**
     * Build a response payload from request and upstream response
     * @param {string} url - Original URL
     * @param {string} mode - Transformation mode
     * @param {string} upstreamHtml - HTML content from upstream (simulated)
     * @param {object} upstreamHeaders - Upstream response headers
     * @returns {object} Response payload for processResponse()
     */
    buildResponsePayload(url, mode, upstreamHtml, upstreamHeaders = {}) {
        const parsed = Helpers.parseUrl(url);
        if (!parsed) {
            throw new ApiError('Invalid URL', 400);
        }

        return {
            request: {
                method: 'GET',
                host: parsed.host,
                path: parsed.path || '/',
                headers: {
                    'cookie': `mitm-mode=${mode}`
                }
            },
            response: {
                status_code: 200,
                content_type: 'text/html; charset=utf-8',
                body: upstreamHtml,
                headers: {
                    'content-type': 'text/html; charset=utf-8',
                    'content-length': String(new Blob([upstreamHtml]).size),
                    ...upstreamHeaders
                }
            },
            stats: {
                simulator: true,
                timestamp: Date.now()
            }
        };
    }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
    constructor(message, statusCode = 0, data = null) {
        super(message);
        this.name = 'ApiError';
        this.statusCode = statusCode;
        this.data = data;
    }
}

// Export singleton instance
const apiClient = new ApiClient();

// Also export class for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, ApiError, apiClient };
}

if (typeof window !== 'undefined') {
    window.ApiClient = ApiClient;
    window.ApiError = ApiError;
    window.apiClient = apiClient;
}
