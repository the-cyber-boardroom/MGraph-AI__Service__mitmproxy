/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Configuration Panel Component
   v0.1.0 - URL, mode, and sample selection with execute button
   
   Events Emitted:
   - config-changed: { url, mode, sampleHtml }
   - execute-requested: { url, mode, sampleHtml }
   - reset-requested: {}
   ═══════════════════════════════════════════════════════════════════════════════ */

class SimulatorConfig extends BaseComponent {
    constructor() {
        super();
        this.config = {
            url: 'https://news.acme-corp.test/articles/tech-trends-2026',
            mode: 'cache',
            sampleHtml: 'article-page'
        };
        this.isExecuting = false;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        this.urlInput = this.$('#url-input');
        this.urlHint = this.$('#url-hint');
        this.modeSelect = this.$('#mode-select');
        this.sampleSelect = this.$('#sample-select');
        this.executeBtn = this.$('#execute-btn');
        this.resetBtn = this.$('#reset-btn');
    }

    setupEventListeners() {
        // URL input
        this.addTrackedListener(this.urlInput, 'input', 
            Helpers.debounce(() => this.handleUrlChange(), 300)
        );
        this.addTrackedListener(this.urlInput, 'blur', () => this.validateUrl());
        
        // Mode select
        this.addTrackedListener(this.modeSelect, 'change', () => this.handleModeChange());
        
        // Sample select
        this.addTrackedListener(this.sampleSelect, 'change', () => this.handleSampleChange());
        
        // Execute button
        this.addTrackedListener(this.executeBtn, 'click', () => this.handleExecute());
        
        // Reset button
        this.addTrackedListener(this.resetBtn, 'click', () => this.handleReset());
        
        // Keyboard shortcut: Enter to execute
        this.addTrackedListener(this.urlInput, 'keydown', (e) => {
            if (e.key === 'Enter' && !this.isExecuting) {
                this.handleExecute();
            }
        });
    }

    onReady() {
        this.populateSampleOptions();
        this.syncFromInputs();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Initialization
    // ═══════════════════════════════════════════════════════════════════════════

    populateSampleOptions() {
        if (!this.sampleSelect || !window.SampleHtml) return;
        
        const options = SampleHtml.getOptions();
        this.sampleSelect.innerHTML = options.map(opt => 
            `<option value="${opt.value}">${opt.label}</option>`
        ).join('');
        
        // Set default
        this.sampleSelect.value = this.config.sampleHtml;
    }

    syncFromInputs() {
        if (this.urlInput) this.config.url = this.urlInput.value;
        if (this.modeSelect) this.config.mode = this.modeSelect.value;
        if (this.sampleSelect) this.config.sampleHtml = this.sampleSelect.value;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Handlers
    // ═══════════════════════════════════════════════════════════════════════════

    handleUrlChange() {
        this.config.url = this.urlInput.value;
        this.validateUrl();
        this.emitConfigChanged();
    }

    handleModeChange() {
        this.config.mode = this.modeSelect.value;
        this.emitConfigChanged();
    }

    handleSampleChange() {
        this.config.sampleHtml = this.sampleSelect.value;
        this.emitConfigChanged();
    }

    handleExecute() {
        if (this.isExecuting) return;
        
        // Validate before executing
        if (!this.validateUrl()) {
            this.urlInput.focus();
            return;
        }
        
        this.emit('execute-requested', { ...this.config });
    }

    handleReset() {
        this.emit('reset-requested', {});
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Validation
    // ═══════════════════════════════════════════════════════════════════════════

    validateUrl() {
        const url = this.urlInput.value.trim();
        const isValid = this.isValidUrl(url);
        
        this.urlInput.classList.toggle('invalid', !isValid);
        
        if (!url) {
            this.setUrlHint('Enter a URL to test', 'muted');
        } else if (!isValid) {
            this.setUrlHint('Invalid URL format (must be http:// or https://)', 'error');
        } else {
            const parsed = this.parseUrl(url);
            this.setUrlHint(`Host: ${parsed.host}`, 'success');
        }
        
        return isValid;
    }

    setUrlHint(text, type = 'muted') {
        if (!this.urlHint) return;
        this.urlHint.textContent = text;
        this.urlHint.className = 'url-hint ' + type;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Get current configuration
     * @returns {object} { url, mode, sampleHtml }
     */
    getConfig() {
        return { ...this.config };
    }

    /**
     * Set configuration
     * @param {object} config - { url?, mode?, sampleHtml? }
     */
    setConfig(config) {
        if (config.url !== undefined) {
            this.config.url = config.url;
            if (this.urlInput) this.urlInput.value = config.url;
        }
        if (config.mode !== undefined) {
            this.config.mode = config.mode;
            if (this.modeSelect) this.modeSelect.value = config.mode;
        }
        if (config.sampleHtml !== undefined) {
            this.config.sampleHtml = config.sampleHtml;
            if (this.sampleSelect) this.sampleSelect.value = config.sampleHtml;
        }
        this.validateUrl();
    }

    /**
     * Set executing state (disables button)
     * @param {boolean} executing
     */
    setExecuting(executing) {
        this.isExecuting = executing;
        if (this.executeBtn) {
            this.executeBtn.disabled = executing;
            this.executeBtn.classList.toggle('loading', executing);
        }
    }

    /**
     * Reset to defaults
     */
    resetToDefaults() {
        this.setConfig({
            url: 'https://news.acme-corp.test/articles/tech-trends-2026',
            mode: 'cache',
            sampleHtml: 'article-page'
        });
        this.emitConfigChanged();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Emission
    // ═══════════════════════════════════════════════════════════════════════════

    emitConfigChanged() {
        this.emit('config-changed', { ...this.config });
    }
}

customElements.define('simulator-config', SimulatorConfig);
