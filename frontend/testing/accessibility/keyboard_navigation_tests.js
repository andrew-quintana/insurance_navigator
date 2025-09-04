/**
 * Keyboard Navigation Testing
 * 
 * This module provides automated testing for keyboard navigation accessibility,
 * including tab order, focus management, and keyboard shortcuts validation.
 */

class KeyboardNavigationTester {
    constructor() {
        this.results = {
            tabOrder: { score: 0, issues: [], recommendations: [] },
            focusManagement: { score: 0, issues: [], recommendations: [] },
            keyboardShortcuts: { score: 0, issues: [], recommendations: [] },
            skipLinks: { score: 0, issues: [], recommendations: [] },
            overall: { score: 0, status: 'unknown' }
        };
        
        this.focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            'details summary',
            '[contenteditable="true"]'
        ].join(', ');
    }

    /**
     * Run comprehensive keyboard navigation testing
     */
    async runComprehensiveTesting() {
        console.log('⌨️ Starting keyboard navigation testing...');
        
        try {
            // Run all keyboard navigation tests
            await this.testTabOrder();
            await this.testFocusManagement();
            await this.testKeyboardShortcuts();
            await this.testSkipLinks();
            
            // Calculate overall score
            this.calculateOverallScore();
            
            // Generate report
            this.generateReport();
            
            return this.results;
        } catch (error) {
            console.error('❌ Keyboard navigation testing failed:', error);
            throw error;
        }
    }

    /**
     * Test tab order and focusable elements
     */
    async testTabOrder() {
        console.log('🔄 Testing tab order...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Get all focusable elements
            const focusableElements = document.querySelectorAll(this.focusableSelectors);
            
            if (focusableElements.length === 0) {
                score -= 0.5;
                issues.push('No focusable elements found on the page');
                recommendations.push('Add interactive elements that can be focused with keyboard');
                this.results.tabOrder = { score, issues, recommendations };
                return;
            }
            
            // Test tab order
            const tabOrder = this.getTabOrder(focusableElements);
            const hasLogicalOrder = this.validateTabOrder(tabOrder);
            
            if (!hasLogicalOrder) {
                score -= 0.3;
                issues.push('Tab order may not be logical or intuitive');
                recommendations.push('Review and fix tab order for better keyboard navigation');
            }
            
            // Test for elements with positive tabindex
            const positiveTabIndexElements = document.querySelectorAll('[tabindex]:not([tabindex="0"]):not([tabindex="-1"])');
            if (positiveTabIndexElements.length > 0) {
                score -= 0.2;
                issues.push(`${positiveTabIndexElements.length} elements with positive tabindex found`);
                recommendations.push('Avoid positive tabindex values as they can disrupt natural tab order');
            }
            
            // Test for elements that should be focusable but aren't
            const buttons = document.querySelectorAll('button:not([disabled])');
            const inputs = document.querySelectorAll('input:not([disabled]), select:not([disabled]), textarea:not([disabled])');
            const links = document.querySelectorAll('a[href]');
            
            const totalInteractiveElements = buttons.length + inputs.length + links.length;
            const focusableRatio = focusableElements.length / Math.max(totalInteractiveElements, 1);
            
            if (focusableRatio < 0.8) {
                score -= 0.2;
                issues.push('Some interactive elements may not be keyboard accessible');
                recommendations.push('Ensure all interactive elements are keyboard accessible');
            }
            
        } catch (error) {
            console.error('Tab order test failed:', error);
            score = 0;
            issues.push('Tab order test failed due to technical error');
        }
        
        this.results.tabOrder = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Test focus management
     */
    async testFocusManagement() {
        console.log('🎯 Testing focus management...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Test for focus traps in modals
            const modals = document.querySelectorAll('[role="dialog"], .modal, [data-modal]');
            
            for (const modal of modals) {
                const hasFocusTrap = modal.querySelector('[data-focus-trap]') ||
                                   modal.querySelector('.focus-trap') ||
                                   modal.hasAttribute('data-focus-trap');
                
                if (!hasFocusTrap) {
                    score -= 0.2;
                    issues.push('Modal without focus trap found');
                    recommendations.push('Implement focus traps for modal dialogs');
                }
            }
            
            // Test for focus restoration
            const hasFocusRestoration = document.querySelector('[data-focus-restore]') ||
                                      document.querySelector('.focus-restore');
            
            if (!hasFocusRestoration && modals.length > 0) {
                score -= 0.1;
                recommendations.push('Implement focus restoration when closing modals');
            }
            
            // Test for visible focus indicators
            const focusableElements = document.querySelectorAll(this.focusableSelectors);
            let elementsWithoutFocusIndicator = 0;
            
            for (const element of focusableElements) {
                const styles = window.getComputedStyle(element, ':focus');
                const outline = styles.outline;
                const outlineWidth = styles.outlineWidth;
                const boxShadow = styles.boxShadow;
                
                if (outline === 'none' && outlineWidth === '0px' && !boxShadow.includes('inset')) {
                    elementsWithoutFocusIndicator++;
                }
            }
            
            if (elementsWithoutFocusIndicator > 0) {
                score -= 0.2 * (elementsWithoutFocusIndicator / focusableElements.length);
                issues.push(`${elementsWithoutFocusIndicator} elements without visible focus indicators`);
                recommendations.push('Add visible focus indicators to all focusable elements');
            }
            
            // Test for focus management in dynamic content
            const dynamicContent = document.querySelectorAll('[data-dynamic], .dynamic-content');
            if (dynamicContent.length > 0) {
                score -= 0.1;
                recommendations.push('Ensure focus management for dynamic content updates');
            }
            
        } catch (error) {
            console.error('Focus management test failed:', error);
            score = 0;
            issues.push('Focus management test failed due to technical error');
        }
        
        this.results.focusManagement = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Test keyboard shortcuts
     */
    async testKeyboardShortcuts() {
        console.log('⌨️ Testing keyboard shortcuts...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Test for common keyboard shortcuts
            const hasKeyboardShortcuts = document.querySelector('[data-shortcut]') ||
                                       document.querySelector('[title*="shortcut"]') ||
                                       document.querySelector('[aria-keyshortcuts]');
            
            if (!hasKeyboardShortcuts) {
                score -= 0.1;
                recommendations.push('Consider implementing keyboard shortcuts for power users');
            }
            
            // Test for escape key handling
            const hasEscapeHandling = document.querySelector('[data-escape-handler]') ||
                                    document.querySelector('.escape-handler');
            
            if (!hasEscapeHandling) {
                score -= 0.1;
                recommendations.push('Implement escape key handling for modals and dropdowns');
            }
            
            // Test for arrow key navigation
            const hasArrowNavigation = document.querySelector('[data-arrow-navigation]') ||
                                     document.querySelector('.arrow-navigation');
            
            if (!hasArrowNavigation) {
                score -= 0.1;
                recommendations.push('Consider implementing arrow key navigation for lists and menus');
            }
            
            // Test for enter and space key handling
            const interactiveElements = document.querySelectorAll('button, [role="button"], [tabindex]');
            let elementsWithoutKeyboardHandling = 0;
            
            for (const element of interactiveElements) {
                const hasKeyboardHandler = element.hasAttribute('data-keyboard-handler') ||
                                         element.classList.contains('keyboard-handler') ||
                                         element.onkeydown !== null;
                
                if (!hasKeyboardHandler) {
                    elementsWithoutKeyboardHandling++;
                }
            }
            
            if (elementsWithoutKeyboardHandling > 0) {
                score -= 0.1 * (elementsWithoutKeyboardHandling / interactiveElements.length);
                recommendations.push('Ensure all interactive elements respond to keyboard events');
            }
            
        } catch (error) {
            console.error('Keyboard shortcuts test failed:', error);
            score = 0;
            issues.push('Keyboard shortcuts test failed due to technical error');
        }
        
        this.results.keyboardShortcuts = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Test skip links
     */
    async testSkipLinks() {
        console.log('⏭️ Testing skip links...');
        
        let score = 1.0;
        const issues = [];
        const recommendations = [];
        
        try {
            // Test for skip links
            const skipLinks = document.querySelectorAll('a[href*="#"], a[href*="skip"], .skip-link');
            
            if (skipLinks.length === 0) {
                score -= 0.3;
                issues.push('No skip links found');
                recommendations.push('Implement skip links for keyboard users to bypass navigation');
            } else {
                // Test if skip links work
                let workingSkipLinks = 0;
                
                for (const link of skipLinks) {
                    const href = link.getAttribute('href');
                    if (href) {
                        if (href.startsWith('#')) {
                            const target = document.querySelector(href);
                            if (target) {
                                workingSkipLinks++;
                            }
                        } else if (href.includes('skip')) {
                            workingSkipLinks++;
                        }
                    }
                }
                
                if (workingSkipLinks < skipLinks.length) {
                    score -= 0.2;
                    issues.push(`${skipLinks.length - workingSkipLinks} skip links may not work properly`);
                    recommendations.push('Fix skip links to ensure they work correctly');
                }
            }
            
            // Test for main content landmark
            const mainContent = document.querySelector('main, [role="main"], #main, .main-content');
            if (!mainContent) {
                score -= 0.2;
                issues.push('No main content landmark found');
                recommendations.push('Add main content landmark for skip link targeting');
            }
            
            // Test for navigation landmark
            const navigation = document.querySelector('nav, [role="navigation"], #nav, .navigation');
            if (!navigation) {
                score -= 0.1;
                recommendations.push('Add navigation landmark for better skip link structure');
            }
            
        } catch (error) {
            console.error('Skip links test failed:', error);
            score = 0;
            issues.push('Skip links test failed due to technical error');
        }
        
        this.results.skipLinks = {
            score: Math.max(0, score),
            issues,
            recommendations
        };
    }

    /**
     * Get tab order of focusable elements
     */
    getTabOrder(elements) {
        const tabOrder = [];
        
        for (const element of elements) {
            const tabIndex = element.getAttribute('tabindex');
            const index = tabIndex ? parseInt(tabIndex) : 0;
            
            tabOrder.push({
                element,
                tabIndex: index,
                rect: element.getBoundingClientRect()
            });
        }
        
        // Sort by tabindex, then by position
        return tabOrder.sort((a, b) => {
            if (a.tabIndex !== b.tabIndex) {
                return a.tabIndex - b.tabIndex;
            }
            
            // If tabindex is the same, sort by position (top to bottom, left to right)
            if (Math.abs(a.rect.top - b.rect.top) > 10) {
                return a.rect.top - b.rect.top;
            }
            return a.rect.left - b.rect.left;
        });
    }

    /**
     * Validate tab order is logical
     */
    validateTabOrder(tabOrder) {
        if (tabOrder.length <= 1) return true;
        
        // Check if elements are in a logical reading order
        for (let i = 1; i < tabOrder.length; i++) {
            const prev = tabOrder[i - 1];
            const current = tabOrder[i];
            
            // Check if current element is significantly to the left of previous element
            // (which would be illogical in most cases)
            if (current.rect.left < prev.rect.left - 50 && 
                Math.abs(current.rect.top - prev.rect.top) < 50) {
                return false;
            }
        }
        
        return true;
    }

    /**
     * Calculate overall keyboard navigation score
     */
    calculateOverallScore() {
        const scores = [
            this.results.tabOrder.score,
            this.results.focusManagement.score,
            this.results.keyboardShortcuts.score,
            this.results.skipLinks.score
        ];
        
        this.results.overall.score = scores.reduce((sum, score) => sum + score, 0) / scores.length;
        this.results.overall.status = this.results.overall.score >= 0.8 ? 'pass' : 'fail';
    }

    /**
     * Generate keyboard navigation report
     */
    generateReport() {
        console.log('\n⌨️ Keyboard Navigation Report');
        console.log('==============================');
        console.log(`Overall Score: ${(this.results.overall.score * 100).toFixed(1)}%`);
        console.log(`Status: ${this.results.overall.status.toUpperCase()}`);
        
        console.log('\n📋 Detailed Results:');
        console.log(`Tab Order: ${(this.results.tabOrder.score * 100).toFixed(1)}%`);
        console.log(`Focus Management: ${(this.results.focusManagement.score * 100).toFixed(1)}%`);
        console.log(`Keyboard Shortcuts: ${(this.results.keyboardShortcuts.score * 100).toFixed(1)}%`);
        console.log(`Skip Links: ${(this.results.skipLinks.score * 100).toFixed(1)}%`);
        
        // Print issues and recommendations
        const allIssues = [
            ...this.results.tabOrder.issues,
            ...this.results.focusManagement.issues,
            ...this.results.keyboardShortcuts.issues,
            ...this.results.skipLinks.issues
        ];
        
        const allRecommendations = [
            ...this.results.tabOrder.recommendations,
            ...this.results.focusManagement.recommendations,
            ...this.results.keyboardShortcuts.recommendations,
            ...this.results.skipLinks.recommendations
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
            testType: 'Keyboard Navigation',
            results: this.results,
            summary: {
                overallScore: this.results.overall.score,
                status: this.results.overall.status,
                totalIssues: [
                    ...this.results.tabOrder.issues,
                    ...this.results.focusManagement.issues,
                    ...this.results.keyboardShortcuts.issues,
                    ...this.results.skipLinks.issues
                ].length,
                totalRecommendations: [
                    ...this.results.tabOrder.recommendations,
                    ...this.results.focusManagement.recommendations,
                    ...this.results.keyboardShortcuts.recommendations,
                    ...this.results.skipLinks.recommendations
                ].length
            }
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KeyboardNavigationTester;
}

// Auto-run if in browser environment
if (typeof window !== 'undefined') {
    window.KeyboardNavigationTester = KeyboardNavigationTester;
    
    // Auto-run on page load if requested
    if (window.location.search.includes('run-keyboard-tests')) {
        document.addEventListener('DOMContentLoaded', async () => {
            const tester = new KeyboardNavigationTester();
            await tester.runComprehensiveTesting();
        });
    }
}
