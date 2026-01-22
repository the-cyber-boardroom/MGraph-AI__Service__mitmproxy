/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Syntax Highlighting
   v0.1.1 - Simple JSON and HTML syntax highlighting
   ═══════════════════════════════════════════════════════════════════════════════ */

const SyntaxHighlight = {
    
    /**
     * Highlight JSON string
     * @param {string} json - JSON string or object
     * @returns {string} HTML with syntax highlighting spans
     */
    json(json) {
        if (typeof json === 'object') {
            try {
                json = JSON.stringify(json, null, 2);
            } catch {
                return this.escapeHtml(String(json));
            }
        }
        
        if (typeof json !== 'string') {
            return this.escapeHtml(String(json));
        }
        
        // Escape HTML first
        let escaped = this.escapeHtml(json);
        
        // Apply highlighting patterns
        return escaped
            // Strings (must be before other patterns)
            .replace(/"([^"\\]*(\\.[^"\\]*)*)"/g, '<span class="sh-string">"$1"</span>')
            // Property keys
            .replace(/<span class="sh-string">"([^"]+)"<\/span>(\s*:)/g, '<span class="sh-key">"$1"</span>$2')
            // Numbers
            .replace(/\b(-?\d+\.?\d*)\b/g, '<span class="sh-number">$1</span>')
            // Booleans and null
            .replace(/\b(true|false|null)\b/g, '<span class="sh-boolean">$1</span>');
    },
    
    /**
     * Highlight HTML string
     * @param {string} html - HTML string
     * @returns {string} HTML with syntax highlighting spans
     */
    html(html) {
        if (typeof html !== 'string') {
            return this.escapeHtml(String(html));
        }
        
        // Escape HTML first
        let escaped = this.escapeHtml(html);
        
        // Apply highlighting patterns
        return escaped
            // Comments
            .replace(/(&lt;!--[\s\S]*?--&gt;)/g, '<span class="sh-comment">$1</span>')
            // DOCTYPE
            .replace(/(&lt;!DOCTYPE[^&]*&gt;)/gi, '<span class="sh-doctype">$1</span>')
            // Tags
            .replace(/(&lt;\/?)([\w-]+)/g, '$1<span class="sh-tag">$2</span>')
            // Attributes
            .replace(/(\s)([\w-]+)(=)(&quot;|&#39;)([^&]*?)(\4)/g, 
                '$1<span class="sh-attr">$2</span>$3<span class="sh-string">$4$5$6</span>')
            // Closing brackets
            .replace(/(\/?&gt;)/g, '<span class="sh-bracket">$1</span>')
            // Opening brackets
            .replace(/(&lt;)/g, '<span class="sh-bracket">$1</span>');
    },
    
    /**
     * Auto-detect and highlight
     * @param {string} text - Text to highlight
     * @returns {string} Highlighted HTML
     */
    auto(text) {
        if (!text || typeof text !== 'string') {
            return this.escapeHtml(String(text || ''));
        }
        
        const trimmed = text.trim();
        
        // Detect JSON
        if ((trimmed.startsWith('{') && trimmed.endsWith('}')) ||
            (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
            try {
                JSON.parse(trimmed);
                return this.json(text);
            } catch {
                // Not valid JSON, fall through
            }
        }
        
        // Detect HTML
        if (trimmed.startsWith('<') && (trimmed.includes('</') || trimmed.includes('/>'))) {
            return this.html(text);
        }
        
        // Plain text
        return this.escapeHtml(text);
    },
    
    /**
     * Escape HTML entities
     * @param {string} text
     * @returns {string}
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Freeze
Object.freeze(SyntaxHighlight);

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SyntaxHighlight;
}
if (typeof window !== 'undefined') {
    window.SyntaxHighlight = SyntaxHighlight;
}
