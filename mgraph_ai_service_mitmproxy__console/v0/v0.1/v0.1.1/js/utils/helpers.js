/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Shared Utility Helpers
   v0.1.0 - Core utility functions
   ═══════════════════════════════════════════════════════════════════════════════ */

const Helpers = {
    
    /**
     * Escape HTML entities to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    },
    
    /**
     * Format number with K/M suffixes for display
     * @param {number} num - Number to format
     * @returns {string} Formatted string (e.g., "1.5K", "2.3M")
     */
    formatNumber(num) {
        if (num == null || isNaN(num)) return '0';
        num = Number(num);
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    },
    
    /**
     * Format bytes to human-readable string
     * @param {number} bytes - Number of bytes
     * @returns {string} Formatted string (e.g., "1.5 KB", "2.3 MB")
     */
    formatBytes(bytes) {
        if (bytes == null || isNaN(bytes)) return '0 B';
        bytes = Number(bytes);
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    },
    
    /**
     * Format milliseconds to human-readable timing
     * @param {number} ms - Milliseconds
     * @returns {string} Formatted string (e.g., "24ms", "1.5s")
     */
    formatTiming(ms) {
        if (ms == null || isNaN(ms)) return '-';
        ms = Number(ms);
        if (ms < 1000) return Math.round(ms) + 'ms';
        return (ms / 1000).toFixed(2) + 's';
    },
    
    /**
     * Validate URL format (http/https only)
     * @param {string} urlString - URL to validate
     * @returns {boolean} True if valid http/https URL
     */
    isValidUrl(urlString) {
        if (!urlString) return false;
        try {
            const url = new URL(urlString);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch {
            return false;
        }
    },
    
    /**
     * Parse URL into components
     * @param {string} urlString - URL to parse
     * @returns {object|null} Parsed URL components or null if invalid
     */
    parseUrl(urlString) {
        if (!urlString) return null;
        try {
            const url = new URL(urlString);
            return {
                scheme: url.protocol.replace(':', ''),
                host: url.hostname,
                port: url.port || (url.protocol === 'https:' ? '443' : '80'),
                path: url.pathname + url.search,
                query: url.search.replace('?', '')
            };
        } catch {
            return null;
        }
    },
    
    /**
     * Debounce a function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Wait for next animation frame
     * @returns {Promise<void>}
     */
    nextFrame() {
        return new Promise(resolve => requestAnimationFrame(resolve));
    },
    
    /**
     * Wait for specified milliseconds
     * @param {number} ms - Milliseconds to wait
     * @returns {Promise<void>}
     */
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },
    
    /**
     * Generate a simple unique ID
     * @param {string} prefix - Optional prefix
     * @returns {string} Unique ID
     */
    uniqueId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    },
    
    /**
     * Pretty print JSON with indentation
     * @param {any} obj - Object to stringify
     * @param {number} indent - Indentation spaces (default 2)
     * @returns {string} Formatted JSON string
     */
    prettyJson(obj, indent = 2) {
        try {
            return JSON.stringify(obj, null, indent);
        } catch {
            return String(obj);
        }
    }
};

// Freeze to prevent accidental modification
Object.freeze(Helpers);

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Helpers;
}
if (typeof window !== 'undefined') {
    window.Helpers = Helpers;
}
