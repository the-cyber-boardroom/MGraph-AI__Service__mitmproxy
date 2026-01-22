/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Details Panel Component
   v0.1.0 - Tabbed container for stage-tab components
   
   Features:
   - Tabs to switch between stages
   - Auto-switches to stage on stage-completed event
   - Contains stage-tab components in Shadow DOM
   
   Listens for:
   - stage-completed: Updates tab status and optionally switches
   - stage-selected: Switches to selected stage
   ═══════════════════════════════════════════════════════════════════════════════ */

class DetailsPanel extends BaseComponent {
    constructor() {
        super();
        this.stages = ['request', 'cache', 'upstream', 'response'];
        this.activeStage = 'request';
        this.autoSwitch = true; // Auto-switch to stage when it completes
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        this.tabButtons = {};
        this.tabContents = {};
        
        for (const stage of this.stages) {
            this.tabButtons[stage] = this.$(`.details-tab-btn[data-stage="${stage}"]`);
            this.tabContents[stage] = this.$(`.details-tab-content[data-stage="${stage}"]`);
        }
    }

    setupEventListeners() {
        // Tab click handling
        const tabsContainer = this.$('.details-tabs');
        if (tabsContainer) {
            this.addTrackedListener(tabsContainer, 'click', (e) => {
                const btn = e.target.closest('.details-tab-btn');
                if (btn) {
                    this.switchToStage(btn.dataset.stage);
                }
            });
        }
        
        // Listen for stage events
        this.addTrackedListener(document, 'stage-completed', this.handleStageCompleted);
        this.addTrackedListener(document, 'stage-selected', this.handleStageSelected);
        this.addTrackedListener(document, 'flow-started', this.handleFlowStarted);
    }

    onReady() {
        // Ensure first tab is active
        this.switchToStage('request');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Handlers
    // ═══════════════════════════════════════════════════════════════════════════

    handleStageCompleted(event) {
        const { stage, status } = event.detail;
        
        if (!this.stages.includes(stage)) return;
        
        // Update tab status indicator
        this.updateTabStatus(stage, status);
        
        // Auto-switch to completed stage
        if (this.autoSwitch && (status === 'complete' || status === 'hit' || status === 'error')) {
            this.switchToStage(stage);
        }
    }

    handleStageSelected(event) {
        const { stage } = event.detail;
        if (this.stages.includes(stage)) {
            this.switchToStage(stage);
        }
    }

    handleFlowStarted(event) {
        // Reset all tab statuses
        for (const stage of this.stages) {
            this.updateTabStatus(stage, 'idle');
        }
        // Switch to request tab
        this.switchToStage('request');
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Switch to a specific stage tab
     * @param {string} stage - Stage name
     */
    switchToStage(stage) {
        if (!this.stages.includes(stage)) return;
        
        this.activeStage = stage;
        
        // Update tab buttons
        for (const [name, btn] of Object.entries(this.tabButtons)) {
            if (btn) {
                btn.classList.toggle('active', name === stage);
            }
        }
        
        // Update tab contents
        for (const [name, content] of Object.entries(this.tabContents)) {
            if (content) {
                content.classList.toggle('active', name === stage);
            }
        }
        
        this.emit('tab-changed', { stage });
    }

    /**
     * Update tab status indicator
     * @param {string} stage - Stage name
     * @param {string} status - Status
     */
    updateTabStatus(stage, status) {
        const btn = this.tabButtons[stage];
        if (btn) {
            btn.dataset.status = status;
        }
    }

    /**
     * Get active stage name
     * @returns {string}
     */
    getActiveStage() {
        return this.activeStage;
    }

    /**
     * Enable/disable auto-switch on stage completion
     * @param {boolean} enabled
     */
    setAutoSwitch(enabled) {
        this.autoSwitch = enabled;
    }

    /**
     * Get stage-tab component for a stage
     * @param {string} stage - Stage name
     * @returns {HTMLElement|null}
     */
    getStageTab(stage) {
        const content = this.tabContents[stage];
        if (content) {
            return content.querySelector('stage-tab');
        }
        return null;
    }
}

customElements.define('details-panel', DetailsPanel);
