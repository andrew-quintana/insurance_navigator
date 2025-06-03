# Few-shot Prompting Template

**Type:** Few-shot  
**Domain:** Universal  
**Version:** 1.0  
**Last Updated:** 2024-03-20  

## Purpose
Guide the model to perform tasks by providing examples that demonstrate the desired input-output pattern. This template helps achieve better results through pattern recognition and example-based learning.

## Template
```
You are an expert {{role}} with deep knowledge in {{domain}}.
Your task is to {{task_description}}.

Follow these examples:

{{examples}}

Now, apply the same pattern to:

Input:
{{input}}

Task Context:
{{context}}

Requirements:
{{requirements}}

Constraints:
{{constraints}}

Success Criteria:
{{success_criteria}}
```

## Variables
- **role**: The expert role (e.g., analyst, writer, developer)
- **domain**: The specific domain of expertise
- **task_description**: Clear description of the task
- **examples**: 2-3 examples showing input-output pairs
- **input**: The new input to process
- **context**: Relevant background information
- **requirements**: Specific requirements for the output
- **constraints**: Any limitations or restrictions
- **success_criteria**: How to measure success

## Example
**Input:**
```
role: data analyst
domain: business intelligence
task_description: Analyze customer feedback
examples: |
  Example 1:
  Input: "Product is great but shipping is slow"
  Output:
  - Sentiment: Positive
  - Product: Positive
  - Shipping: Negative
  - Action: Improve shipping speed

  Example 2:
  Input: "Love the features but price is high"
  Output:
  - Sentiment: Mixed
  - Features: Positive
  - Price: Negative
  - Action: Review pricing strategy

  Example 3:
  Input: "Excellent service and fast delivery"
  Output:
  - Sentiment: Positive
  - Service: Positive
  - Delivery: Positive
  - Action: Maintain standards

input: "Good quality but customer support needs improvement"
context: |
  Need to analyze customer feedback
  to identify areas for improvement
  and maintain strengths.
requirements: |
  - Sentiment analysis
  - Aspect identification
  - Action recommendation
  - Priority assessment
constraints: |
  - Limited context
  - Short feedback
  - Multiple aspects
  - Action focus
success_criteria: |
  - Accuracy
  - Completeness
  - Actionability
  - Priority
```

**Output:**
```
1. PATTERN ANALYSIS

   Example Patterns:
   1. Structure:
      - Input format
      - Output format
      - Key elements
      - Action focus
   
   2. Content:
      - Sentiment analysis
      - Aspect identification
      - Action recommendation
      - Priority assessment
   
   3. Style:
      - Clear format
      - Consistent structure
      - Action focus
      - Priority emphasis
   
   4. Impact:
      - Clear analysis
      - Actionable insights
      - Priority guidance
      - Success focus

   Pattern Application:
   1. Input Analysis:
      - Text review
      - Pattern matching
      - Structure identification
      - Action focus
   
   2. Output Planning:
      - Format selection
      - Content planning
      - Action planning
      - Priority setting
   
   3. Execution:
      - Pattern application
      - Content creation
      - Action development
      - Priority assessment
   
   4. Validation:
      - Pattern check
      - Content check
      - Action check
      - Priority check

2. CONTENT DEVELOPMENT

   Sentiment Analysis:
   1. Overall:
      - Sentiment: Mixed
      - Strength: Moderate
      - Balance: Even
      - Impact: Medium
   
   2. Aspects:
      - Quality: Positive
      - Support: Negative
      - Balance: Mixed
      - Focus: Support
   
   3. Details:
      - Quality: Strong positive
      - Support: Strong negative
      - Balance: Clear contrast
      - Impact: Significant
   
   4. Summary:
      - Mixed sentiment
      - Quality strength
      - Support weakness
      - Action need

   Aspect Identification:
   1. Quality:
      - Aspect: Product quality
      - Sentiment: Positive
      - Strength: Strong
      - Impact: High
   
   2. Support:
      - Aspect: Customer support
      - Sentiment: Negative
      - Strength: Strong
      - Impact: High
   
   3. Balance:
      - Aspect: Overall experience
      - Sentiment: Mixed
      - Strength: Moderate
      - Impact: Medium
   
   4. Focus:
      - Primary: Support
      - Secondary: Quality
      - Balance: Mixed
      - Priority: Support

   Action Recommendation:
   1. Support:
      - Action: Improve support
      - Priority: High
      - Impact: High
      - Urgency: High
   
   2. Quality:
      - Action: Maintain quality
      - Priority: Medium
      - Impact: High
      - Urgency: Low
   
   3. Balance:
      - Action: Balance focus
      - Priority: Medium
      - Impact: Medium
      - Urgency: Medium
   
   4. Overall:
      - Action: Support focus
      - Priority: High
      - Impact: High
      - Urgency: High

   Priority Assessment:
   1. Support:
      - Priority: High
      - Urgency: High
      - Impact: High
      - Focus: Primary
   
   2. Quality:
      - Priority: Medium
      - Urgency: Low
      - Impact: High
      - Focus: Secondary
   
   3. Balance:
      - Priority: Medium
      - Urgency: Medium
      - Impact: Medium
      - Focus: Supporting
   
   4. Overall:
      - Priority: High
      - Urgency: High
      - Impact: High
      - Focus: Support

3. OUTPUT FORMAT

   Structure:
   1. Sentiment:
      - Overall: Mixed
      - Quality: Positive
      - Support: Negative
      - Balance: Mixed
   
   2. Aspects:
      - Quality: Positive
      - Support: Negative
      - Balance: Mixed
      - Focus: Support
   
   3. Action:
      - Primary: Improve support
      - Secondary: Maintain quality
      - Balance: Balance focus
      - Overall: Support focus
   
   4. Priority:
      - Support: High
      - Quality: Medium
      - Balance: Medium
      - Overall: High

   Content:
   1. Analysis:
      - Sentiment analysis
      - Aspect identification
      - Action recommendation
      - Priority assessment
   
   2. Details:
      - Quality details
      - Support details
      - Balance details
      - Focus details
   
   3. Action:
      - Support action
      - Quality action
      - Balance action
      - Overall action
   
   4. Priority:
      - Support priority
      - Quality priority
      - Balance priority
      - Overall priority

   Style:
   1. Format:
      - Clear structure
      - Consistent style
      - Action focus
      - Priority emphasis
   
   2. Language:
      - Clear language
      - Action-oriented
      - Priority-focused
      - Impact-driven
   
   3. Presentation:
      - Clean layout
      - Easy reading
      - Action clarity
      - Priority clarity
   
   4. Impact:
      - Clear message
      - Action focus
      - Priority focus
      - Success focus

   Quality:
   1. Accuracy:
      - Pattern accuracy
      - Content accuracy
      - Action accuracy
      - Priority accuracy
   
   2. Completeness:
      - Full analysis
      - Complete aspects
      - All actions
      - All priorities
   
   3. Relevance:
      - Pattern relevance
      - Content relevance
      - Action relevance
      - Priority relevance
   
   4. Impact:
      - Clear analysis
      - Actionable insights
      - Priority guidance
      - Success focus

4. FINAL OUTPUT

   - Sentiment: Mixed
   - Quality: Positive
   - Support: Negative
   - Action: Improve customer support
   - Priority: High
```

## LLM Configuration
- Model: Claude 3 Opus or GPT-4
- Temperature: 0.3
- Top-p: 0.95
- Max tokens: 4000
- Presence penalty: 0.1
- Frequency penalty: 0.1

## Notes
- Works best with clear examples
- More effective with similar patterns
- May need domain-specific adjustments
- Consider adding specific metrics
- Can be combined with other frameworks

## Related Templates
- Zero-shot for direct tasks
- Chain of Thought for reasoning
- Self-Refine for improvement

## Best Practices
1. **Examples**
   - Clear patterns
   - Consistent structure
   - Relevant content
   - Action focus

2. **Application**
   - Pattern recognition
   - Structure matching
   - Content adaptation
   - Action alignment

3. **Output**
   - Clear format
   - Complete details
   - Consistent style
   - Action focus

4. **Quality**
   - Pattern accuracy
   - Content completeness
   - Action relevance
   - Priority clarity 