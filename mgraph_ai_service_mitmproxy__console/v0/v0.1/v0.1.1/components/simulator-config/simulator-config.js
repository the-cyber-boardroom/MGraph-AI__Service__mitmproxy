/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Configuration Panel Component
   v0.1.1 - URL auto-sync with sample selection to prevent backend caching
   
   Events Emitted:
   - config-changed: { url, mode, sampleHtml }
   - execute-requested: { url, mode, sampleHtml }
   - reset-requested: {}
   ═══════════════════════════════════════════════════════════════════════════════ */

class SimulatorConfig extends BaseComponent {
    constructor() {
        super();
        this.config = {
            url: 'https://website-xyz.test/content/article-page',
            mode: 'cache',
            sampleHtml: 'article-page'
        };
        this.isExecuting = false;
        this.autoSyncUrl = true;
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        this.urlInput = this.$('#url-input');
        this.urlHint = this.$('#url-hint');
        this.modeSelect = this.$('#mode-select');
        this.sampleSelect = this.$('#sample-select');
        this.autoSyncCheckbox = this.$('#auto-sync-url');
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
        
        // Auto-sync checkbox
        this.addTrackedListener(this.autoSyncCheckbox, 'change', () => this.handleAutoSyncChange());
        
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
        this.validateUrl();
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
        if (this.autoSyncCheckbox) this.autoSyncUrl = this.autoSyncCheckbox.checked;
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
        
        // Auto-sync URL if enabled
        if (this.autoSyncUrl) {
            this.syncUrlToSample();
        }
        
        this.emitConfigChanged();
    }

    handleAutoSyncChange() {
        this.autoSyncUrl = this.autoSyncCheckbox.checked;
        
        // If just enabled, sync now
        if (this.autoSyncUrl) {
            this.syncUrlToSample();
        }
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
    // URL Sync
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Update URL to match selected sample (prevents backend caching issues)
     */
    syncUrlToSample() {
        const baseUrl = 'https://website-xyz.test/content/';
        const newUrl = baseUrl + this.config.sampleHtml;
        
        this.config.url = newUrl;
        if (this.urlInput) {
            this.urlInput.value = newUrl;
        }
        this.validateUrl();
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

    getConfig() {
        return { ...this.config };
    }

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

    setExecuting(executing) {
        this.isExecuting = executing;
        if (this.executeBtn) {
            this.executeBtn.disabled = executing;
            this.executeBtn.classList.toggle('loading', executing);
        }
    }

    resetToDefaults() {
        this.setConfig({
            url: 'https://website-xyz.test/content/article-page',
            mode: 'cache',
            sampleHtml: 'article-page'
        });
        if (this.autoSyncCheckbox) {
            this.autoSyncCheckbox.checked = true;
            this.autoSyncUrl = true;
        }
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
