/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Main Orchestrator Component
   v0.1.0 - Coordinates flow execution and component communication
   
   Flow Sequence:
   1. User configures URL, mode, sample HTML
   2. User clicks Execute
   3. Orchestrator emits flow-started
   4. Stage: Request - Build request payload
   5. Stage: Cache - Call /proxy/process-request
   6. Stage: Upstream - Simulate upstream response (use sample HTML)
   7. Stage: Response - Call /proxy/process-response
   8. Orchestrator emits flow-completed
   
   Events Emitted:
   - flow-started: { config }
   - stage-completed: { stage, status, input, output, timing, error }
   - flow-completed: { success, totalTiming, message }
   ═══════════════════════════════════════════════════════════════════════════════ */

class MitmproxySimulator extends BaseComponent {
    constructor() {
        super();
        this.isExecuting = false;
        this.flowStartTime = null;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        this.configComponent = this.$('simulator-config');
        this.pipelineComponent = this.$('pipeline-status');
        this.detailsComponent = this.$('details-panel');
    }

    setupEventListeners() {
        // Listen for execute request from config panel
        this.addTrackedListener(this.shadowRoot, 'execute-requested', this.handleExecuteRequested);
        
        // Listen for reset request
        this.addTrackedListener(this.shadowRoot, 'reset-requested', this.handleResetRequested);
    }

    onReady() {
        console.log('[MitmproxySimulator] Ready');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Handlers
    // ═══════════════════════════════════════════════════════════════════════════

    async handleExecuteRequested(event) {
        if (this.isExecuting) return;
        
        const config = event.detail;
        await this.executeFlow(config);
    }

    handleResetRequested(event) {
        this.reset();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Flow Execution
    // ═══════════════════════════════════════════════════════════════════════════

    async executeFlow(config) {
        const { url, mode, sampleHtml } = config;
        
        this.isExecuting = true;
        this.flowStartTime = performance.now();
        
        // Update config component state
        if (this.configComponent) {
            this.configComponent.setExecuting(true);
        }
        
        // Emit flow started
        this.emit('flow-started', { config });
        
        try {
            // ═══════════════════════════════════════════════════════════════════
            // Stage 1: Request
            // ═══════════════════════════════════════════════════════════════════
            const requestResult = await this.executeRequestStage(url, mode);
            
            // ═══════════════════════════════════════════════════════════════════
            // Stage 2: Cache
            // ═══════════════════════════════════════════════════════════════════
            const cacheResult = await this.executeCacheStage(requestResult.payload);
            
            // Check if cache hit - if so, we can skip upstream
            let upstreamResult = null;
            let responseResult = null;
            
            if (cacheResult.hit) {
                // Cache hit - skip upstream, use cached response
                this.emitStageCompleted('upstream', 'skipped', null, null, null);
                responseResult = {
                    output: cacheResult.output,
                    timing: 0
                };
                this.emitStageCompleted('response', 'hit', 
                    { source: 'cache' }, 
                    cacheResult.output, 
                    0
                );
            } else {
                // ═══════════════════════════════════════════════════════════════
                // Stage 3: Upstream (simulated)
                // ═══════════════════════════════════════════════════════════════
                upstreamResult = await this.executeUpstreamStage(sampleHtml);
                
                // ═══════════════════════════════════════════════════════════════
                // Stage 4: Response
                // ═══════════════════════════════════════════════════════════════
                responseResult = await this.executeResponseStage(
                    url, 
                    mode, 
                    upstreamResult.html
                );
            }
            
            // Flow complete
            const totalTiming = performance.now() - this.flowStartTime;
            this.emit('flow-completed', {
                success: true,
                totalTiming,
                message: 'Flow completed successfully'
            });
            
        } catch (error) {
            console.error('[MitmproxySimulator] Flow error:', error);
            
            const totalTiming = performance.now() - this.flowStartTime;
            this.emit('flow-completed', {
                success: false,
                totalTiming,
                message: error.message || 'Flow failed'
            });
            
        } finally {
            this.isExecuting = false;
            if (this.configComponent) {
                this.configComponent.setExecuting(false);
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Stage Executors
    // ═══════════════════════════════════════════════════════════════════════════

    async executeRequestStage(url, mode) {
        const startTime = performance.now();
        
        try {
            // Build request payload
            const payload = window.apiClient.buildRequestPayload(url, mode);
            const timing = performance.now() - startTime;
            
            this.emitStageCompleted('request', 'complete', 
                { url, mode }, 
                payload, 
                timing
            );
            
            return { payload, timing };
            
        } catch (error) {
            const timing = performance.now() - startTime;
            this.emitStageCompleted('request', 'error', 
                { url, mode }, 
                null, 
                timing, 
                error.message
            );
            throw error;
        }
    }

    async executeCacheStage(requestPayload) {
        const startTime = performance.now();
        
        try {
            // Call process-request API
            const response = await window.apiClient.processRequest(requestPayload);
            const timing = performance.now() - startTime;
            
            // Determine if cache hit
            // A hit means the response includes a cached response body
            const hit = response?.action !== 'continue' && response?.response?.body;
            
            this.emitStageCompleted('cache', hit ? 'hit' : 'miss',
                requestPayload,
                response,
                timing
            );
            
            return { hit, output: response, timing };
            
        } catch (error) {
            const timing = performance.now() - startTime;
            this.emitStageCompleted('cache', 'error',
                requestPayload,
                null,
                timing,
                error.message
            );
            throw error;
        }
    }

    async executeUpstreamStage(sampleKey) {
        const startTime = performance.now();
        
        try {
            // Get sample HTML (simulating upstream fetch)
            const html = window.SampleHtml.getHtml(sampleKey);
            
            if (!html) {
                throw new Error(`Sample HTML not found: ${sampleKey}`);
            }
            
            // Simulate network delay
            await Helpers.wait(50 + Math.random() * 100);
            
            const timing = performance.now() - startTime;
            
            const output = {
                status_code: 200,
                content_type: 'text/html; charset=utf-8',
                body: html,
                headers: {
                    'content-type': 'text/html; charset=utf-8',
                    'content-length': String(new Blob([html]).size),
                    'x-simulator': 'true'
                }
            };
            
            this.emitStageCompleted('upstream', 'simulated',
                { sampleKey },
                output,
                timing
            );
            
            return { html, output, timing };
            
        } catch (error) {
            const timing = performance.now() - startTime;
            this.emitStageCompleted('upstream', 'error',
                { sampleKey },
                null,
                timing,
                error.message
            );
            throw error;
        }
    }

    async executeResponseStage(url, mode, upstreamHtml) {
        const startTime = performance.now();
        
        try {
            // Build response payload
            const payload = window.apiClient.buildResponsePayload(url, mode, upstreamHtml);
            
            // Call process-response API
            const response = await window.apiClient.processResponse(payload);
            const timing = performance.now() - startTime;
            
            this.emitStageCompleted('response', 'complete',
                payload,
                response,
                timing
            );
            
            return { output: response, timing };
            
        } catch (error) {
            const timing = performance.now() - startTime;
            this.emitStageCompleted('response', 'error',
                { url, mode },
                null,
                timing,
                error.message
            );
            throw error;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Emission
    // ═══════════════════════════════════════════════════════════════════════════

    emitStageCompleted(stage, status, input, output, timing, error = null) {
        this.emit('stage-completed', {
            stage,
            status,
            input,
            output,
            timing,
            error
        });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Reset the simulator
     */
    reset() {
        this.isExecuting = false;
        this.flowStartTime = null;
        
        // Reset child components
        if (this.pipelineComponent && this.pipelineComponent.reset) {
            this.pipelineComponent.reset();
        }
        
        this.emit('flow-started', { config: null }); // Triggers reset in stage-tabs
    }

    /**
     * Execute flow with given config
     * @param {object} config - { url, mode, sampleHtml }
     */
    async execute(config) {
        await this.executeFlow(config);
    }

    /**
     * Get current execution state
     * @returns {boolean}
     */
    get executing() {
        return this.isExecuting;
    }
}

customElements.define('mitmproxy-simulator', MitmproxySimulator);
