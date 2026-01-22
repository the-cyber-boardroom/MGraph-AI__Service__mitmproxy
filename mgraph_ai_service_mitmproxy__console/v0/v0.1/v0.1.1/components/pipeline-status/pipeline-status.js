/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Pipeline Status Component
   v0.1.0 - Visual pipeline with stage status boxes
   
   Listens for:
   - flow-started: Resets all stages
   - stage-completed: Updates corresponding stage box
   - flow-completed: Shows summary
   ═══════════════════════════════════════════════════════════════════════════════ */

class PipelineStatus extends BaseComponent {
    constructor() {
        super();
        this.stages = ['request', 'cache', 'upstream', 'response'];
        this.stageData = {};
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        // Stage elements
        this.stageElements = {};
        for (const stage of this.stages) {
            this.stageElements[stage] = {
                container: this.$(`.pipeline-stage[data-stage="${stage}"]`),
                status: this.$(`#${stage}-status`),
                timing: this.$(`#${stage}-timing`)
            };
        }
        
        // Summary
        this.summaryEl = this.$('#pipeline-summary');
        this.summaryTextEl = this.$('.summary-text');
    }

    setupEventListeners() {
        // Listen for flow events
        this.addTrackedListener(document, 'flow-started', this.handleFlowStarted);
        this.addTrackedListener(document, 'stage-completed', this.handleStageCompleted);
        this.addTrackedListener(document, 'flow-completed', this.handleFlowCompleted);
        
        // Click on stage to select it in details panel
        const stageContainers = this.$$('.pipeline-stage');
        stageContainers.forEach(el => {
            this.addTrackedListener(el, 'click', () => {
                this.emit('stage-selected', { stage: el.dataset.stage });
            });
        });
    }

    onReady() {
        this.reset();
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Event Handlers
    // ═══════════════════════════════════════════════════════════════════════════

    handleFlowStarted(event) {
        this.reset();
        this.setSummary('Executing flow...', '');
    }

    handleStageCompleted(event) {
        const { stage, status, timing, error } = event.detail;
        
        if (!this.stages.includes(stage)) return;
        
        this.stageData[stage] = event.detail;
        this.updateStage(stage, status, timing);
        
        if (error) {
            this.setSummary(`Error in ${stage}: ${error}`, 'error');
        }
    }

    handleFlowCompleted(event) {
        const { totalTiming, success, message } = event.detail;
        
        if (success) {
            this.setSummary(
                `Flow completed in ${this.formatTiming(totalTiming)}`,
                'success'
            );
        } else {
            this.setSummary(message || 'Flow completed with errors', 'error');
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Reset all stages to idle
     */
    reset() {
        this.stageData = {};
        for (const stage of this.stages) {
            this.updateStage(stage, 'idle', null);
        }
        this.setSummary('Ready to execute', '');
    }

    /**
     * Update a specific stage
     * @param {string} stage - Stage name
     * @param {string} status - Status (idle, running, complete, hit, miss, error, simulated, skipped)
     * @param {number|null} timing - Timing in ms
     */
    updateStage(stage, status, timing = null) {
        const els = this.stageElements[stage];
        if (!els) return;
        
        // Update container data attribute for CSS styling
        if (els.container) {
            els.container.dataset.status = status;
        }
        
        // Update status text
        if (els.status) {
            els.status.textContent = status;
        }
        
        // Update timing
        if (els.timing) {
            els.timing.textContent = this.formatTiming(timing);
        }
    }

    /**
     * Set summary message
     * @param {string} text - Summary text
     * @param {string} type - Type ('', 'success', 'error')
     */
    setSummary(text, type = '') {
        if (this.summaryTextEl) {
            this.summaryTextEl.textContent = text;
            this.summaryTextEl.className = 'summary-text ' + type;
        }
    }

    /**
     * Get stage data
     * @param {string} stage - Stage name
     * @returns {object|null}
     */
    getStageData(stage) {
        return this.stageData[stage] || null;
    }

    /**
     * Get all stage data
     * @returns {object}
     */
    getAllStageData() {
        return { ...this.stageData };
    }

    /**
     * Mark a stage as running
     * @param {string} stage
     */
    setStageRunning(stage) {
        this.updateStage(stage, 'running', null);
    }

    /**
     * Mark a stage as skipped
     * @param {string} stage
     */
    setStageSkipped(stage) {
        this.updateStage(stage, 'skipped', null);
    }
}

customElements.define('pipeline-status', PipelineStatus);
