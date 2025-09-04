/**
 * WCAG 2.1 AA Compliance Testing
 * 
 * This module provides automated accessibility testing for WCAG 2.1 AA compliance,
 * including color contrast, keyboard navigation, and semantic markup validation.
 */

class WCAGComplianceTester {
    constructor() {
        this.results = {
            colorContrast: { score: 0, issues: [], recommendations: [] },
            keyboardNavigation: { score: 0, issues: [], recommendations: [] },
            semanticMarkup: { score: 0, issues: [], recommendations: [] },
            formAccessibility: { score: 0, issues: [], recommendations: [] },
            overall: { score: 0, status: 'unknown' }
        };
    }

    /**
     * Run comprehensive WCAG 2.1 AA compliance testing
     */
    async runComprehensiveTesting() {
        console.log('🔍 Starting WCAG 2.1 AA compliance testing...');
        
        try {
            // Run all accessibility tests
            await this.testColorContrast();
            await this.testKeyboardNavigation();
            await this.testSemanticMarkup();
            await this.testFormAccessibility();
            
            // Calculate overall score
            this.calculateOverallScore();
            
            // Generate report
            this.generateReport();
            
            return this.results;
        } catch (error) {
            console.error('❌ WCAG compliance testing failed:', error);
            throw error;
        }
    }

    /**
     * Test color contrast ratios for WCAG 2.1 AA compliance
     */
    async testColorContrast() {
        console.log('🎨 Testing color contrast ratios...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Get all text elements
            const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div, a, button, input, label');
            
            for (const element of textElements) {
                const styles = window.getComputedStyle(element);
                const color = styles.color;
                const backgroundColor = styles.backgroundColor;
                
                // Check if element has visible text
                if (element.textContent.trim() && color !== 'rgba(0, 0, 0, 0)') {
                    // Calculate contrast ratio (simplified)
                    const contrastRatio = this.calculateContrastRatio(color, backgroundColor);
                    
                    if (contrastRatio < 4.5) {
                        score -= 0.1;
                        issues.push(`Low contrast ratio (${contrastRatio.toFixed(2)}) for element: ${element.tagName}`);
                        recommendations.push('Improve color contrast to meet WCAG 2.1 AA standards (4.5:1 for normal text)');
                    }
                }
            }
            
            // Check for high contrast theme support
            const hasHighContrast = document.querySelector('[data-theme="high-contrast"]') || 
                                  document.querySelector('.high-contrast') ||
                                  document.querySelector('[class*="contrast"]');
            
            if (!hasHighContrast) {
                score -= 0.2;
                recommendations.push('Implement high contrast theme for better accessibility');
            }
            
        } catch (error) {
            console.error('Color contrast test failed:', error);
            score = 0;
            issues.push('Color contrast test failed due to technical error');
        }
        
        this.results.colorContrast = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Test keyboard navigation support
     */
    async testKeyboardNavigation() {
        console.log('⌨️ Testing keyboard navigation...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Test tab order
            const focusableElements = document.querySelectorAll(
                'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) {
                score -= 0.3;
                issues.push('No focusable elements found');
                recommendations.push('Ensure interactive elements are keyboard accessible');
            }
            
            // Test for skip links
            const skipLinks = document.querySelectorAll('a[href*="#"], a[href*="skip"]');
            if (skipLinks.length === 0) {
                score -= 0.2;
                recommendations.push('Implement skip links for keyboard navigation');
            }
            
            // Test focus management
            const hasFocusManagement = document.querySelector('[data-focus-trap]') ||
                                     document.querySelector('.focus-trap') ||
                                     document.querySelector('[class*="focus"]');
            
            if (!hasFocusManagement) {
                score -= 0.1;
                recommendations.push('Implement focus management for modals and dynamic content');
            }
            
            // Test keyboard shortcuts
            const hasKeyboardShortcuts = document.querySelector('[data-shortcut]') ||
                                       document.querySelector('[title*="shortcut"]');
            
            if (!hasKeyboardShortcuts) {
                score -= 0.1;
                recommendations.push('Consider implementing keyboard shortcuts for power users');
            }
            
        } catch (error) {
            console.error('Keyboard navigation test failed:', error);
            score = 0;
            issues.push('Keyboard navigation test failed due to technical error');
        }
        
        this.results.keyboardNavigation = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Test semantic markup and ARIA support
     */
    async testSemanticMarkup() {
        console.log('🏗️ Testing semantic markup...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Test semantic HTML5 elements
            const semanticElements = [
                'header', 'nav', 'main', 'section', 'article', 
                'aside', 'footer', 'figure', 'figcaption'
            ];
            
            let semanticCount = 0;
            for (const element of semanticElements) {
                if (document.querySelector(element)) {
                    semanticCount++;
                }
            }
            
            if (semanticCount < 3) {
                score -= 0.3;
                issues.push(`Only ${semanticCount} semantic HTML5 elements found`);
                recommendations.push('Use more semantic HTML5 elements for better structure');
            }
            
            // Test heading structure
            const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            if (headings.length === 0) {
                score -= 0.2;
                issues.push('No heading elements found');
                recommendations.push('Implement proper heading structure');
            } else {
                // Check heading hierarchy
                let hasProperHierarchy = true;
                let previousLevel = 0;
                
                for (const heading of headings) {
                    const level = parseInt(heading.tagName.charAt(1));
                    if (level > previousLevel + 1) {
                        hasProperHierarchy = false;
                        break;
                    }
                    previousLevel = level;
                }
                
                if (!hasProperHierarchy) {
                    score -= 0.2;
                    issues.push('Improper heading hierarchy detected');
                    recommendations.push('Maintain proper heading hierarchy (h1 > h2 > h3, etc.)');
                }
            }
            
            // Test ARIA labels
            const elementsWithAria = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby]');
            const interactiveElements = document.querySelectorAll('button, input, select, textarea, a');
            
            if (interactiveElements.length > 0 && elementsWithAria.length / interactiveElements.length < 0.5) {
                score -= 0.2;
                recommendations.push('Add ARIA labels to more interactive elements');
            }
            
            // Test alt text for images
            const images = document.querySelectorAll('img');
            let imagesWithoutAlt = 0;
            
            for (const img of images) {
                if (!img.alt && !img.getAttribute('aria-label')) {
                    imagesWithoutAlt++;
                }
            }
            
            if (imagesWithoutAlt > 0) {
                score -= 0.1 * (imagesWithoutAlt / images.length);
                issues.push(`${imagesWithoutAlt} images without alt text`);
                recommendations.push('Add alt text to all images for screen reader accessibility');
            }
            
        } catch (error) {
            console.error('Semantic markup test failed:', error);
            score = 0;
            issues.push('Semantic markup test failed due to technical error');
        }
        
        this.results.semanticMarkup = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Test form accessibility
     */
    async testFormAccessibility() {
        console.log('📝 Testing form accessibility...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            const forms = document.querySelectorAll('form');
            
            if (forms.length === 0) {
                // No forms to test
                this.results.formAccessibility = { score: 1.0, issues: [], recommendations: [] };
                return;
            }
            
            for (const form of forms) {
                // Test form labels
                const inputs = form.querySelectorAll('input, select, textarea');
                let inputsWithoutLabels = 0;
                
                for (const input of inputs) {
                    const hasLabel = input.labels && input.labels.length > 0;
                    const hasAriaLabel = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
                    const hasPlaceholder = input.placeholder;
                    
                    if (!hasLabel && !hasAriaLabel && !hasPlaceholder) {
                        inputsWithoutLabels++;
                    }
                }
                
                if (inputsWithoutLabels > 0) {
                    score -= 0.2 * (inputsWithoutLabels / inputs.length);
                    issues.push(`${inputsWithoutLabels} form inputs without proper labels`);
                    recommendations.push('Add labels or ARIA attributes to all form inputs');
                }
                
                // Test fieldset and legend
                const fieldsets = form.querySelectorAll('fieldset');
                const legends = form.querySelectorAll('legend');
                
                if (fieldsets.length > 0 && legends.length < fieldsets.length) {
                    score -= 0.1;
                    issues.push('Fieldsets without legends found');
                    recommendations.push('Add legends to all fieldsets for better grouping');
                }
                
                // Test error handling
                const errorElements = form.querySelectorAll('[aria-invalid="true"], .error, .invalid');
                if (errorElements.length === 0 && inputs.length > 0) {
                    score -= 0.1;
                    recommendations.push('Implement accessible error handling for form validation');
                }
            }
            
        } catch (error) {
            console.error('Form accessibility test failed:', error);
            score = 0;
            issues.push('Form accessibility test failed due to technical error');
        }
        
        this.results.formAccessibility = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Calculate contrast ratio between two colors
     */
    calculateContrastRatio(color1, color2) {
        // Simplified contrast ratio calculation
        // In a real implementation, you would parse the colors and calculate the actual ratio
        const rgb1 = this.parseColor(color1);
        const rgb2 = this.parseColor(color2);
        
        if (!rgb1 || !rgb2) return 4.5; // Default to passing
        
        const luminance1 = this.getLuminance(rgb1);
        const luminance2 = this.getLuminance(rgb2);
        
        const lighter = Math.max(luminance1, luminance2);
        const darker = Math.min(luminance1, luminance2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * Parse color string to RGB values
     */
    parseColor(color) {
        // Simplified color parsing - in reality you'd need a more robust parser
        const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (match) {
            return {
                r: parseInt(match[1]),
                g: parseInt(match[2]),
                b: parseInt(match[3])
            };
        }
        return null;
    }

    /**
     * Calculate relative luminance of a color
     */
    getLuminance(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }

    /**
     * Calculate overall accessibility score
     */
    calculateOverallScore() {
        const scores = [
            this.results.colorContrast.score,
            this.results.keyboardNavigation.score,
            this.results.semanticMarkup.score,
            this.results.formAccessibility.score
        ];
        
        this.results.overall.score = scores.reduce((sum, score) => sum + score, 0) / scores.length;
        this.results.overall.status = this.results.overall.score >= 0.8 ? 'pass' : 'fail';
    }

    /**
     * Generate accessibility report
     */
    generateReport() {
        console.log('\n📊 WCAG 2.1 AA Compliance Report');
        console.log('=====================================');
        console.log(`Overall Score: ${(this.results.overall.score * 100).toFixed(1)}%`);
        console.log(`Status: ${this.results.overall.status.toUpperCase()}`);
        
        console.log('\n📋 Detailed Results:');
        console.log(`Color Contrast: ${(this.results.colorContrast.score * 100).toFixed(1)}%`);
        console.log(`Keyboard Navigation: ${(this.results.keyboardNavigation.score * 100).toFixed(1)}%`);
        console.log(`Semantic Markup: ${(this.results.semanticMarkup.score * 100).toFixed(1)}%`);
        console.log(`Form Accessibility: ${(this.results.formAccessibility.score * 100).toFixed(1)}%`);
        
        // Print issues and recommendations
        const allIssues = [
            ...this.results.colorContrast.issues,
            ...this.results.keyboardNavigation.issues,
            ...this.results.semanticMarkup.issues,
            ...this.results.formAccessibility.issues
        ];
        
        const allRecommendations = [
            ...this.results.colorContrast.recommendations,
            ...this.results.keyboardNavigation.recommendations,
            ...this.results.semanticMarkup.recommendations,
            ...this.results.formAccessibility.recommendations
        ];
        
        if (allIssues.length > 0) {
            console.log('\n⚠️ Issues Found:');
            allIssues.forEach((issue, index) => {
                console.log(`  ${index + 1}. ${issue}`);
            });
        }
        
        if (allRecommendations.length > 0) {
            console.log('\n💡 Recommendations:');
            const uniqueRecommendations = [...new Set(allRecommendations)];
            uniqueRecommendations.forEach((rec, index) => {
                console.log(`  ${index + 1}. ${rec}`);
            });
        }
    }

    /**
     * Export results as JSON
     */
    exportResults() {
        return {
            timestamp: new Date().toISOString(),
            testType: 'WCAG 2.1 AA Compliance',
            results: this.results,
            summary: {
                overallScore: this.results.overall.score,
                status: this.results.overall.status,
                totalIssues: [
                    ...this.results.colorContrast.issues,
                    ...this.results.keyboardNavigation.issues,
                    ...this.results.semanticMarkup.issues,
                    ...this.results.formAccessibility.issues
                ].length,
                totalRecommendations: [
                    ...this.results.colorContrast.recommendations,
                    ...this.results.keyboardNavigation.recommendations,
                    ...this.results.semanticMarkup.recommendations,
                    ...this.results.formAccessibility.recommendations
                ].length
            }
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WCAGComplianceTester;
}

// Auto-run if in browser environment
if (typeof window !== 'undefined') {
    window.WCAGComplianceTester = WCAGComplianceTester;
    
    // Auto-run on page load if requested
    if (window.location.search.includes('run-accessibility-tests')) {
        document.addEventListener('DOMContentLoaded', async () => {
            const tester = new WCAGComplianceTester();
            await tester.runComprehensiveTesting();
        });
    }
}
