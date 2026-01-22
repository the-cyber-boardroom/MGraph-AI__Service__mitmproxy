/* ═══════════════════════════════════════════════════════════════════════════════
   MitmProxy Simulator - Sample HTML Documents
   v0.1.0 - Pre-configured HTML samples for upstream simulation
   
   These samples represent what an upstream server would return.
   They're designed to test different transformation modes:
   - article-page: General content with mixed sentiment
   - simple-page: Minimal content for quick testing
   - negative-content: Heavy negative sentiment for xxx-negative testing
   - mixed-sentiment: Balanced positive/negative for sentiment analysis
   - table-data: Structured data for hash testing
   ═══════════════════════════════════════════════════════════════════════════════ */

const SampleHtml = {
    
    /**
     * Article Page - General news article with mixed content
     * Size: ~2KB | Good for: cache, xxx, xxx-random
     */
    'article-page': {
        name: 'Article Page (2KB)',
        description: 'News article with mixed sentiment - headlines, paragraphs, footer',
        html: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tech Trends 2026 - XYZ News</title>
</head>
<body>
    <header>
        <nav>
            <a href="/">XYZ News</a>
            <a href="/tech">Technology</a>
            <a href="/business">Business</a>
        </nav>
    </header>
    <main>
        <article>
            <h1>Tech Trends 2026: AI Continues to Transform Industries</h1>
            <p class="meta">Published: January 21, 2026 | Author: Jane Smith</p>
            
            <p>Artificial intelligence continues to reshape industries worldwide, 
            bringing both exciting opportunities and significant challenges to 
            businesses of all sizes.</p>
            
            <h2>Positive Developments</h2>
            <p>Companies report unprecedented productivity gains, with automation 
            handling routine tasks efficiently. Customer satisfaction scores have 
            improved dramatically across sectors adopting AI solutions.</p>
            
            <h2>Concerns Remain</h2>
            <p>Critics argue that regulation is lagging behind innovation. 
            Job displacement worries persist, and some experts warn of potential 
            risks from rapidly advancing AI capabilities.</p>
            
            <h2>Looking Ahead</h2>
            <p>Despite challenges, optimists point to the tremendous potential 
            for AI to solve pressing global problems, from climate change to 
            healthcare accessibility.</p>
        </article>
    </main>
    <footer>
        <p>&copy; 2026 XYZ Corp. All rights reserved.</p>
    </footer>
</body>
</html>`
    },

    /**
     * Simple Page - Minimal content for quick tests
     * Size: ~500B | Good for: quick cache testing, basic xxx
     */
    'simple-page': {
        name: 'Simple Page (500B)',
        description: 'Minimal page for quick testing - just heading and paragraph',
        html: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Welcome - XYZ Corp</title>
</head>
<body>
    <h1>Welcome to XYZ Corp</h1>
    <p>We build amazing products that help people work smarter.</p>
    <p>Contact us at <a href="mailto:hello@xyz-corp.test">hello@xyz-corp.test</a></p>
</body>
</html>`
    },

    /**
     * Negative Content - Heavy negative sentiment
     * Size: ~1.5KB | Good for: xxx-negative, xxx-negative-1/2/4, sentiment testing
     */
    'negative-content': {
        name: 'Negative Sentiment (1.5KB)',
        description: 'Market crash article - heavy negative sentiment for masking tests',
        html: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Market Crash Analysis - Financial Times</title>
</head>
<body>
    <article>
        <h1>Markets Plunge Amid Growing Economic Fears</h1>
        <p class="lead">Investors panicked as stocks tumbled dramatically in the worst 
        trading session of the decade.</p>
        
        <p>The devastating losses wiped out billions in market value, leaving 
        shareholders reeling from the catastrophic decline. Retirement accounts 
        suffered terrible damage as the selloff intensified.</p>
        
        <p>Analysts warn of worse conditions ahead, predicting continued volatility 
        and potential further crashes. The grim outlook has shattered confidence 
        among institutional investors.</p>
        
        <p>Economic indicators paint a bleak picture, with unemployment claims 
        surging and consumer spending plummeting. The situation appears dire 
        for many sectors.</p>
        
        <p>However, some contrarian investors see buying opportunities emerging 
        from the chaos, though they remain a small minority.</p>
    </article>
</body>
</html>`
    },

    /**
     * Mixed Sentiment - Balanced positive and negative
     * Size: ~2KB | Good for: xxx-hide-positive, xxx-hide-neutral, comparison testing
     */
    'mixed-sentiment': {
        name: 'Mixed Sentiment (2KB)',
        description: 'Product review with balanced positive/negative - good for sentiment analysis',
        html: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Product Review: SmartWidget Pro - Tech Reviews</title>
</head>
<body>
    <article class="review">
        <h1>SmartWidget Pro Review: A Mixed Bag</h1>
        <div class="rating">Rating: 3.5/5 stars</div>
        
        <section class="pros">
            <h2>What We Loved</h2>
            <p>The build quality is exceptional - this is a beautifully crafted device 
            that feels premium in every way. Performance exceeded our expectations, 
            delivering blazing fast results in every benchmark.</p>
            <p>Battery life is outstanding, lasting well over two days of heavy use. 
            The customer support team was incredibly helpful and responsive.</p>
        </section>
        
        <section class="cons">
            <h2>What Disappointed Us</h2>
            <p>The price is frustratingly high, putting this out of reach for many 
            consumers. Software bugs plagued our testing, causing annoying crashes 
            and data loss.</p>
            <p>The warranty terms are disappointingly restrictive, and repair costs 
            are outrageously expensive. Documentation is confusing and incomplete.</p>
        </section>
        
        <section class="verdict">
            <h2>The Verdict</h2>
            <p>Overall, the SmartWidget Pro is a capable device with significant 
            strengths and notable weaknesses. Whether it's worth the investment 
            depends entirely on your priorities and budget.</p>
        </section>
    </article>
</body>
</html>`
    },

    /**
     * Table Data - Structured data content
     * Size: ~1.5KB | Good for: hashes, hashes-random, abcde-by-size
     */
    'table-data': {
        name: 'Table Data (1.5KB)',
        description: 'Structured table with names and data - good for hash/ID testing',
        html: `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Q4 Sales Report - Internal</title>
</head>
<body>
    <h1>Q4 2025 Sales Report</h1>
    <p>Regional performance summary for the fourth quarter.</p>
    
    <table>
        <thead>
            <tr>
                <th>Region</th>
                <th>Manager</th>
                <th>Revenue</th>
                <th>Growth</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>North America</td>
                <td>John Smith</td>
                <td>$4.2M</td>
                <td>+15%</td>
                <td>Excellent</td>
            </tr>
            <tr>
                <td>Europe</td>
                <td>Maria Garcia</td>
                <td>$3.8M</td>
                <td>+8%</td>
                <td>Good</td>
            </tr>
            <tr>
                <td>Asia Pacific</td>
                <td>Wei Chen</td>
                <td>$5.1M</td>
                <td>+22%</td>
                <td>Outstanding</td>
            </tr>
            <tr>
                <td>Latin America</td>
                <td>Carlos Rodriguez</td>
                <td>$1.9M</td>
                <td>-3%</td>
                <td>Needs Improvement</td>
            </tr>
        </tbody>
    </table>
    
    <p class="footer">Report generated: January 21, 2026</p>
</body>
</html>`
    }
};

/**
 * Get sample by key
 * @param {string} key - Sample key
 * @returns {object|null} Sample object or null
 */
SampleHtml.get = function(key) {
    return this[key] || null;
};

/**
 * Get all sample keys
 * @returns {string[]} Array of sample keys
 */
SampleHtml.getKeys = function() {
    return Object.keys(this).filter(k => typeof this[k] === 'object' && this[k].html);
};

/**
 * Get samples as options for select dropdown
 * @returns {Array<{value: string, label: string}>}
 */
SampleHtml.getOptions = function() {
    return this.getKeys().map(key => ({
        value: key,
        label: this[key].name
    }));
};

/**
 * Get HTML content by key
 * @param {string} key - Sample key
 * @returns {string} HTML content or empty string
 */
SampleHtml.getHtml = function(key) {
    const sample = this.get(key);
    return sample ? sample.html : '';
};

/**
 * Get sample size in bytes
 * @param {string} key - Sample key
 * @returns {number} Size in bytes
 */
SampleHtml.getSize = function(key) {
    const html = this.getHtml(key);
    return new Blob([html]).size;
};

// Freeze to prevent modification
Object.freeze(SampleHtml);

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SampleHtml;
}
if (typeof window !== 'undefined') {
    window.SampleHtml = SampleHtml;
}
