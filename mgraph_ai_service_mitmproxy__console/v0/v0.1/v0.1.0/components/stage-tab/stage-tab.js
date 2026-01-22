/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Stage Tab Component
   v0.1.0 - Individual pipeline stage details with side-by-side input/output
   
   Features:
   - Displays stage status, timing, and data
   - Side-by-side input/output panels
   - Tabs for headers, body, preview
   - Listens for stage-completed events (filtered by stage name)
   ═══════════════════════════════════════════════════════════════════════════════ */

class StageTab extends BaseComponent {
    constructor() {
        super();
        this.stageName = '';
        this.stageData = null;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        // Header elements
        this.stageIconEl = this.$('#stage-icon');
        this.stageNameEl = this.$('#stage-name');
        this.stageStatusEl = this.$('#stage-status');
        this.stageTimingEl = this.$('#stage-timing');
        
        // Content
        this.contentEl = this.$('.stage-tab-content');
        this.emptyEl = this.$('#stage-empty');
        
        // Input panel
        this.inputHeadersCode = this.$('#input-headers-code');
        this.inputBodyCode = this.$('#input-body-code');
        
        // Output panel
        this.outputHeadersCode = this.$('#output-headers-code');
        this.outputBodyCode = this.$('#output-body-code');
        this.previewFrame = this.$('#preview-frame');
        
        // Panel views
        this.inputViews = {
            headers: this.$('#input-headers'),
            body: this.$('#input-body')
        };
        this.outputViews = {
            headers: this.$('#output-headers'),
            body: this.$('#output-body'),
            preview: this.$('#output-preview')
        };
    }

    setupEventListeners() {
        // Tab switching for input panel
        const inputTabs = this.$('.input-panel .panel-tabs');
        if (inputTabs) {
            this.addTrackedListener(inputTabs, 'click', (e) => {
                const btn = e.target.closest('.panel-tab-btn');
                if (btn) this.switchInputView(btn.dataset.view);
            });
        }
        
        // Tab switching for output panel
        const outputTabs = this.$('.output-panel .panel-tabs');
        if (outputTabs) {
            this.addTrackedListener(outputTabs, 'click', (e) => {
                const btn = e.target.closest('.panel-tab-btn');
                if (btn) this.switchOutputView(btn.dataset.view);
            });
        }
        
        // Listen for stage-completed events (global)
        this.addTrackedListener(document, 'stage-completed', this.handleStageCompleted);
        
        // Listen for flow-started to reset
        this.addTrackedListener(document, 'flow-started', this.handleFlowStarted);
    }

    onReady() {
        // Read stage name from attribute
        this.stageName = this.getAttribute('name') || 'unknown';
        this.updateHeader();
        this.showEmpty(true);
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Handlers
    // ═══════════════════════════════════════════════════════════════════════════

    handleStageCompleted(event) {
        const { stage, status, input, output, timing, error } = event.detail;
        
        // Only handle events for our stage
        if (stage !== this.stageName) return;
        
        this.stageData = { status, input, output, timing, error };
        this.render();
    }

    handleFlowStarted(event) {
        this.reset();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Set stage data programmatically
     * @param {object} data - { status, input, output, timing, error }
     */
    setStageData(data) {
        this.stageData = data;
        this.render();
    }

    /**
     * Reset to initial state
     */
    reset() {
        this.stageData = null;
        this.updateStatus('idle');
        this.updateTiming(null);
        this.showEmpty(true);
    }

    /**
     * Get current stage data
     * @returns {object|null}
     */
    getStageData() {
        return this.stageData;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Rendering
    // ═══════════════════════════════════════════════════════════════════════════

    render() {
        if (!this.stageData) {
            this.showEmpty(true);
            return;
        }
        
        const { status, input, output, timing, error } = this.stageData;
        
        this.updateStatus(status);
        this.updateTiming(timing);
        
        if (input || output) {
            this.showEmpty(false);
            this.renderInput(input);
            this.renderOutput(output);
        } else {
            this.showEmpty(true);
        }
    }

    updateHeader() {
        const icons = {
            request: '📤',
            cache: '💾',
            upstream: '🌐',
            response: '📥'
        };
        
        if (this.stageIconEl) {
            this.stageIconEl.textContent = icons[this.stageName] || '⏳';
        }
        if (this.stageNameEl) {
            this.stageNameEl.textContent = this.stageName;
        }
    }

    updateStatus(status) {
        if (!this.stageStatusEl) return;
        
        // Remove all status classes
        this.stageStatusEl.classList.remove(
            'idle', 'running', 'complete', 'hit', 'miss', 'error', 'simulated'
        );
        
        // Add current status class
        this.stageStatusEl.classList.add(status || 'idle');
        this.stageStatusEl.textContent = status || 'idle';
    }

    updateTiming(ms) {
        if (!this.stageTimingEl) return;
        this.stageTimingEl.textContent = this.formatTiming(ms);
    }

    renderInput(input) {
        if (!input) {
            this.inputHeadersCode.textContent = 'No input data';
            this.inputBodyCode.textContent = 'No input data';
            return;
        }
        
        // Separate headers and body
        const headers = this.extractHeaders(input);
        const body = this.extractBody(input);
        
        this.inputHeadersCode.textContent = headers 
            ? this.prettyJson(headers) 
            : 'No headers';
        this.inputBodyCode.textContent = body || 'No body';
    }

    renderOutput(output) {
        if (!output) {
            this.outputHeadersCode.textContent = 'No output data';
            this.outputBodyCode.textContent = 'No output data';
            this.clearPreview();
            return;
        }
        
        // Separate headers and body
        const headers = this.extractHeaders(output);
        const body = this.extractBody(output);
        
        this.outputHeadersCode.textContent = headers 
            ? this.prettyJson(headers) 
            : 'No headers';
        this.outputBodyCode.textContent = body || 'No body';
        
        // Update preview if body looks like HTML
        if (body && body.trim().startsWith('<')) {
            this.updatePreview(body);
        } else {
            this.clearPreview();
        }
    }

    extractHeaders(data) {
        if (!data) return null;
        
        // If data has explicit headers property
        if (data.headers) {
            return data.headers;
        }
        
        // Otherwise return everything except body
        const { body, ...rest } = data;
        return Object.keys(rest).length > 0 ? rest : null;
    }

    extractBody(data) {
        if (!data) return null;
        
        // Check for body in various locations
        if (typeof data.body === 'string') return data.body;
        if (data.response?.body) return data.response.body;
        if (typeof data === 'string') return data;
        
        return null;
    }

    updatePreview(html) {
        if (!this.previewFrame) return;
        
        try {
            const doc = this.previewFrame.contentDocument;
            doc.open();
            doc.write(html);
            doc.close();
        } catch (error) {
            console.warn('[StageTab] Preview update failed:', error);
        }
    }

    clearPreview() {
        if (!this.previewFrame) return;
        
        try {
            const doc = this.previewFrame.contentDocument;
            doc.open();
            doc.write('<p style="color:#666;padding:20px;">No preview available</p>');
            doc.close();
        } catch (error) {
            // Ignore
        }
    }

    showEmpty(show) {
        if (this.contentEl) {
            this.contentEl.classList.toggle('hidden', show);
        }
        if (this.emptyEl) {
            this.emptyEl.classList.toggle('hidden', !show);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Tab Switching
    // ═══════════════════════════════════════════════════════════════════════════

    switchInputView(viewName) {
        this.switchView('.input-panel', this.inputViews, viewName);
    }

    switchOutputView(viewName) {
        this.switchView('.output-panel', this.outputViews, viewName);
    }

    switchView(panelSelector, views, viewName) {
        const panel = this.$(panelSelector);
        if (!panel) return;
        
        // Update tab buttons
        const tabs = panel.querySelectorAll('.panel-tab-btn');
        tabs.forEach(tab => {
            tab.classList.toggle('active', tab.dataset.view === viewName);
        });
        
        // Update views
        Object.entries(views).forEach(([name, el]) => {
            if (el) el.classList.toggle('active', name === viewName);
        });
    }
}

customElements.define('stage-tab', StageTab);
