/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Stage Tab Component
   v0.1.1 - Improved with syntax highlighting, modified_body support, input preview
   
   Features:
   - Displays stage status, timing, and data
   - Side-by-side input/output panels
   - Tabs: Payload/Response, Body, Preview (both sides)
   - Shows modified_body for output when available
   - Syntax highlighting for JSON and HTML
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
        this.contentEl = this.$('#stage-content');
        this.emptyEl = this.$('#stage-empty');
        
        // Input panel
        this.inputPayloadCode = this.$('#input-payload-code');
        this.inputBodyCode = this.$('#input-body-code');
        this.inputPreviewFrame = this.$('#input-preview-frame');
        
        // Output panel
        this.outputResponseCode = this.$('#output-response-code');
        this.outputBodyCode = this.$('#output-body-code');
        this.outputPreviewFrame = this.$('#output-preview-frame');
        
        // Panel views
        this.inputViews = {
            payload: this.$('#input-payload'),
            body: this.$('#input-body'),
            preview: this.$('#input-preview')
        };
        this.outputViews = {
            response: this.$('#output-response'),
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

    setStageData(data) {
        this.stageData = data;
        this.render();
    }

    reset() {
        this.stageData = null;
        this.updateStatus('idle');
        this.updateTiming(null);
        this.showEmpty(true);
    }

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
        
        this.stageStatusEl.classList.remove(
            'idle', 'running', 'complete', 'hit', 'miss', 'error', 'simulated'
        );
        this.stageStatusEl.classList.add(status || 'idle');
        this.stageStatusEl.textContent = status || 'idle';
    }

    updateTiming(ms) {
        if (!this.stageTimingEl) return;
        this.stageTimingEl.textContent = this.formatTiming(ms);
    }

    renderInput(input) {
        if (!input) {
            this.setCodeContent(this.inputPayloadCode, 'No input data', false);
            this.setCodeContent(this.inputBodyCode, 'No body', false);
            this.clearPreview(this.inputPreviewFrame);
            return;
        }
        
        // Full payload (syntax highlighted JSON)
        this.setCodeContent(this.inputPayloadCode, input, true);
        
        // Extract body for body view
        const body = this.extractInputBody(input);
        if (body) {
            this.setCodeContent(this.inputBodyCode, body, true);
            this.updatePreview(this.inputPreviewFrame, body);
        } else {
            this.setCodeContent(this.inputBodyCode, 'No body', false);
            this.clearPreview(this.inputPreviewFrame);
        }
    }

    renderOutput(output) {
        if (!output) {
            this.setCodeContent(this.outputResponseCode, 'No output data', false);
            this.setCodeContent(this.outputBodyCode, 'No body', false);
            this.clearPreview(this.outputPreviewFrame);
            return;
        }
        
        // Full response (excluding large body fields for readability)
        const responseWithoutBody = this.extractResponseMetadata(output);
        this.setCodeContent(this.outputResponseCode, responseWithoutBody, true);
        
        // Extract modified_body (preferred) or body for body view
        const body = this.extractOutputBody(output);
        if (body) {
            this.setCodeContent(this.outputBodyCode, body, true);
            this.updatePreview(this.outputPreviewFrame, body);
        } else {
            this.setCodeContent(this.outputBodyCode, 'No body', false);
            this.clearPreview(this.outputPreviewFrame);
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Data Extraction
    // ═══════════════════════════════════════════════════════════════════════════

    extractInputBody(input) {
        if (!input) return null;
        
        // Check various locations for body
        if (input.response?.body) return input.response.body;
        if (typeof input.body === 'string') return input.body;
        
        return null;
    }

    extractOutputBody(output) {
        if (!output) return null;
        
        // Prefer modified_body over body
        if (output.modified_body) return output.modified_body;
        if (output.response?.modified_body) return output.response.modified_body;
        if (output.response?.body) return output.response.body;
        if (typeof output.body === 'string') return output.body;
        
        return null;
    }

    extractResponseMetadata(output) {
        if (!output) return null;
        
        // Create a copy without large body fields
        const clean = JSON.parse(JSON.stringify(output));
        
        // Remove body fields but indicate their presence
        // if (clean.body) {
        //     clean.body = `[${clean.body.length} chars]`;
        // }
        // if (clean.modified_body) {
        //     clean.modified_body = `[${clean.modified_body.length} chars]`;
        // }
        // if (clean.response?.body) {
        //     clean.response.body = `[${clean.response.body.length} chars]`;
        // }
        // if (clean.response?.modified_body) {
        //     clean.response.modified_body = `[${clean.response.modified_body.length} chars]`;
        // }
        
        return clean;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Content Rendering
    // ═══════════════════════════════════════════════════════════════════════════

    setCodeContent(element, content, highlight = true) {
        if (!element) return;
        
        if (typeof content === 'object') {
            const json = JSON.stringify(content, null, 2);
            element.innerHTML = highlight 
                ? SyntaxHighlight.json(json)
                : this.escapeHtml(json);
        } else if (typeof content === 'string') {
            element.innerHTML = highlight
                ? SyntaxHighlight.auto(content)
                : this.escapeHtml(content);
        } else {
            element.textContent = String(content);
        }
    }

    updatePreview(iframe, html) {
        if (!iframe) return;
        
        // Only show preview for HTML-like content
        if (!html || typeof html !== 'string' || !html.trim().startsWith('<')) {
            this.clearPreview(iframe);
            return;
        }
        
        try {
            const doc = iframe.contentDocument;
            doc.open();
            doc.write(html);
            doc.close();
        } catch (error) {
            console.warn('[StageTab] Preview update failed:', error);
            this.clearPreview(iframe);
        }
    }

    clearPreview(iframe) {
        if (!iframe) return;
        
        try {
            const doc = iframe.contentDocument;
            doc.open();
            doc.write('<p style="color:#666;padding:20px;font-family:sans-serif;">No preview available</p>');
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
