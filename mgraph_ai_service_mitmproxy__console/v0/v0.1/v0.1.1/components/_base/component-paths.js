/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Component Paths Configuration
   v0.1.0 - Configurable resource paths for components
   
   Enables:
   - Easy path overrides in v0.1.x minor versions
   - Testing with alternative resources
   - Potential CDN deployment in future
   ═══════════════════════════════════════════════════════════════════════════════ */

const ComponentPaths = {
    // Base path for all component resources
    // Override this in v0.1.x for different deployment scenarios
    basePath: '/console/v0/v0.1/v0.1.1',
    
    /**
     * Returns paths for a component's resources
     * @param {string} componentName - e.g., 'simulator-config'
     * @returns {object} Object with js, css, html paths
     */
    getComponentPaths(componentName) {
        const base = `${this.basePath}/components/${componentName}`;
        return {
            js: `${base}/${componentName}.js`,
            css: `${base}/${componentName}.css`,
            html: `${base}/${componentName}.html`
        };
    },
    
    // Shared CSS resources
    sharedCss: {
        get common() { return `${ComponentPaths.basePath}/css/common.css`; },
        get components() { return `${ComponentPaths.basePath}/css/components-shared.css`; }
    },
    
    // Utility scripts
    utils: {
        get helpers() { return `${ComponentPaths.basePath}/js/utils/helpers.js`; }
    },
    
    // Services
    services: {
        get apiClient() { return `${ComponentPaths.basePath}/js/services/api-client.js`; },
        get sampleHtml() { return `${ComponentPaths.basePath}/js/sample-html.js`; }
    },
    
    /**
     * Update base path (useful for testing or different deployments)
     * @param {string} newBasePath
     */
    setBasePath(newBasePath) {
        // Note: This is a method because the object is frozen after initial setup
        // In v0.1.x, override this via surgical patch if needed
        console.warn('[ComponentPaths] setBasePath called but object is frozen. Override in minor version.');
    }
};

// Freeze to prevent accidental modification
Object.freeze(ComponentPaths.sharedCss);
Object.freeze(ComponentPaths.utils);
Object.freeze(ComponentPaths.services);
Object.freeze(ComponentPaths);

// Export for both browser and Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComponentPaths;
}
if (typeof window !== 'undefined') {
    window.ComponentPaths = ComponentPaths;
}
