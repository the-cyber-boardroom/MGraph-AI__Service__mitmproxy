/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Top Navigation Component
   v0.1.0 - App header with branding and API status
   
   Features:
   - Brand with version
   - Navigation links
   - Live API health status indicator
   ═══════════════════════════════════════════════════════════════════════════════ */

class TopNav extends BaseComponent {
    constructor() {
        super();
        this.healthCheckInterval = null;
        this.healthCheckDelay = 30000; // Check every 30 seconds
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ═══════════════════════════════════════════════════════════════════════════

    bindElements() {
        this.apiStatusEl = this.$('#api-status');
        this.statusDotEl = this.$('.status-dot');
        this.statusTextEl = this.$('.status-text');
    }

    setupEventListeners() {
        // No external event listeners needed
    }

    onReady() {
        // Initial health check
        this.checkApiHealth();
        
        // Periodic health checks
        this.healthCheckInterval = setInterval(
            () => this.checkApiHealth(),
            this.healthCheckDelay
        );
    }

    cleanup() {
        super.cleanup();
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Health Check
    // ═══════════════════════════════════════════════════════════════════════════

    async checkApiHealth() {
        try {
            const isHealthy = await window.apiClient.checkHealth();
            this.updateStatus(isHealthy);
        } catch (error) {
            console.warn('[TopNav] Health check failed:', error);
            this.updateStatus(false);
        }
    }

    updateStatus(isOnline) {
        if (!this.apiStatusEl) return;

        this.apiStatusEl.classList.remove('online', 'offline');
        this.apiStatusEl.classList.add(isOnline ? 'online' : 'offline');
        
        if (this.statusTextEl) {
            this.statusTextEl.textContent = isOnline ? 'API Online' : 'API Offline';
        }

        this.emit('api-status-changed', { online: isOnline });
    }

    // ═══════════════════════════════════════════════════════════════════════════
    // Public API
    // ═══════════════════════════════════════════════════════════════════════════

    /**
     * Force a health check
     */
    async refreshStatus() {
        await this.checkApiHealth();
    }

    /**
     * Set active nav link
     * @param {string} href - Link href to mark as active
     */
    setActiveLink(href) {
        const links = this.$$('.top-nav-link');
        links.forEach(link => {
            link.classList.toggle('active', link.getAttribute('href') === href);
        });
    }
}

customElements.define('top-nav', TopNav);
