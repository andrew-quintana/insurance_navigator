import { Section } from "./types.ts";

export class MarkdownHeaderParser {
  /**
   * Parses markdown content directly to extract sections based on headers
   * This replaces the LLM-based approach to avoid context window issues
   */
  parseMarkdownToSections(markdown: string): Section[] {
    const lines = markdown.split('\n');
    const sections: Section[] = [];
    let pathCounters: number[] = [0]; // Track section numbers at each level
    
    let currentSection: Partial<Section> | null = null;
    let contentLines: string[] = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const headerMatch = line.match(/^(#{1,6})\s+(.+)$/);
      
      if (headerMatch) {
        // Save previous section if it exists
        if (currentSection) {
          sections.push({
            ...currentSection,
            content: contentLines.join('\n').trim()
          } as Section);
        }
        
        const level = headerMatch[1].length;
        const title = headerMatch[2].trim();
        
        // Update path tracking for hierarchical numbering
        this.updatePathCounters(pathCounters, level);
        const path = [...pathCounters.slice(0, level)];
        
        // Start new section
        currentSection = { 
          path, 
          title, 
          content: '' 
        };
        contentLines = [];
      } else {
        // Accumulate content for current section
        contentLines.push(line);
      }
    }
    
    // Don't forget the last section
    if (currentSection) {
      sections.push({
        ...currentSection,
        content: contentLines.join('\n').trim()
      } as Section);
    }
    
    // Filter out sections with no meaningful content
    return sections.filter(section => 
      section.content.trim().length > 0 || section.title.trim().length > 0
    );
  }
  
  /**
   * Updates path counters based on header level
   * Maintains proper hierarchical numbering like [1], [1,2], [1,2,3]
   */
  private updatePathCounters(counters: number[], level: number): void {
    // Ensure we have enough levels in our counter array
    while (counters.length < level) {
      counters.push(0);
    }
    
    // Reset all deeper levels to 0
    for (let i = level; i < counters.length; i++) {
      counters[i] = 0;
    }
    
    // Increment the counter at the current level
    counters[level - 1]++;
  }
  
  /**
   * Extracts document metadata from sections
   */
  getDocumentMetadata(sections: Section[]): {
    totalSections: number;
    maxDepth: number;
    documentTitle?: string;
  } {
    const maxDepth = Math.max(...sections.map(s => s.path.length), 0);
    const documentTitle = sections.find(s => s.path.length === 1)?.title;
    
    return {
      totalSections: sections.length,
      maxDepth,
      documentTitle
    };
  }
  
  /**
   * Validates that markdown contains proper header structure
   */
  validateMarkdownStructure(markdown: string): {
    isValid: boolean;
    hasHeaders: boolean;
    headerCount: number;
    issues: string[];
  } {
    const lines = markdown.split('\n');
    const issues: string[] = [];
    let headerCount = 0;
    let hasHeaders = false;
    
    for (const line of lines) {
      if (line.match(/^(#{1,6})\s+(.+)$/)) {
        headerCount++;
        hasHeaders = true;
      }
    }
    
    if (!hasHeaders) {
      issues.push("No headers found in markdown");
    }
    
    if (markdown.trim().length === 0) {
      issues.push("Empty markdown content");
    }
    
    return {
      isValid: issues.length === 0,
      hasHeaders,
      headerCount,
      issues
    };
  }
}