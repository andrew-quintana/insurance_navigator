# Tree of Thoughts Prompting Template

**Type:** Tree of Thoughts  
**Domain:** Universal  
**Version:** 1.0  
**Last Updated:** 2024-03-20  

## Purpose
Guide the model in exploring multiple solution paths simultaneously, evaluating different approaches, and selecting the optimal solution through systematic branching and evaluation. This template helps achieve more comprehensive problem-solving by considering various perspectives and approaches.

## Template
```
You are an expert {{role}} with deep knowledge in {{domain}}.
Your task is to {{task_description}}.

Follow the Tree of Thoughts framework:

1. PROBLEM ANALYSIS
   - What are the key aspects?
   - What are the constraints?
   - What are the goals?
   - What are the criteria?

2. SOLUTION BRANCHING
   - What are possible approaches?
   - What are the alternatives?
   - What are the variations?
   - What are the combinations?

3. PATH EVALUATION
   - How to evaluate each path?
   - What are the trade-offs?
   - What are the risks?
   - What are the benefits?

4. SOLUTION SELECTION
   - How to compare paths?
   - How to optimize choice?
   - How to validate selection?
   - How to implement solution?

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
- **role**: The expert role (e.g., problem solver, strategist, analyst)
- **domain**: The specific domain of expertise
- **task_description**: Clear description of the problem
- **context**: Relevant background information
- **requirements**: Specific requirements for the solution
- **constraints**: Any limitations or restrictions
- **success_criteria**: How to measure success

## Example
**Input:**
```
role: business strategist
domain: market entry strategy
task_description: Develop a market entry strategy for a new product
context: |
  Need to enter a competitive market with
  a new innovative product targeting
  tech-savvy consumers.
requirements: |
  - Market analysis
  - Entry strategy
  - Risk assessment
  - Success metrics
constraints: |
  - Limited budget
  - Time pressure
  - Market competition
  - Resource constraints
success_criteria: |
  - Market penetration
  - Revenue growth
  - Brand awareness
  - Customer acquisition
```

**Output:**
```
1. PROBLEM ANALYSIS

   Key Aspects:
   1. Market:
      - Competition level
      - Customer needs
      - Market size
      - Growth potential
   
   2. Product:
      - Innovation level
      - Value proposition
      - Unique features
      - Market fit
   
   3. Resources:
      - Budget constraints
      - Time limitations
      - Team capabilities
      - Available tools
   
   4. Goals:
      - Market entry
      - Customer acquisition
      - Revenue generation
      - Brand building

   Constraints:
   1. Financial:
      - Limited budget
      - Resource allocation
      - Cost control
      - ROI requirements
   
   2. Time:
      - Entry deadline
      - Market timing
      - Resource availability
      - Implementation speed
   
   3. Market:
      - Competition level
      - Market saturation
      - Customer behavior
      - Regulatory requirements
   
   4. Resources:
      - Team size
      - Skill sets
      - Tools available
      - Support systems

   Goals:
   1. Market:
      - Market entry
      - Market share
      - Brand presence
      - Customer base
   
   2. Business:
      - Revenue growth
      - Profit margins
      - Market position
      - Business growth
   
   3. Brand:
      - Brand awareness
      - Brand perception
      - Brand loyalty
      - Brand value
   
   4. Customer:
      - Customer acquisition
      - Customer satisfaction
      - Customer retention
      - Customer loyalty

   Criteria:
   1. Success:
      - Market penetration
      - Revenue growth
      - Brand awareness
      - Customer acquisition
   
   2. Performance:
      - Sales targets
      - Market share
      - Customer metrics
      - Brand metrics
   
   3. Quality:
      - Product quality
      - Service quality
      - Customer experience
      - Brand experience
   
   4. Impact:
      - Market impact
      - Customer impact
      - Brand impact
      - Business impact

2. SOLUTION BRANCHING

   Possible Approaches:
   1. Direct Entry:
      - Market launch
      - Brand building
      - Customer acquisition
      - Sales focus
   
   2. Partnership:
      - Strategic alliances
      - Distribution partners
      - Technology partners
      - Market partners
   
   3. Acquisition:
      - Market acquisition
      - Brand acquisition
      - Technology acquisition
      - Customer acquisition
   
   4. Innovation:
      - Product innovation
      - Service innovation
      - Business model
      - Market approach

   Alternatives:
   1. Market Focus:
      - Niche market
      - Mass market
      - Premium market
      - Value market
   
   2. Entry Strategy:
      - Direct entry
      - Gradual entry
      - Phased entry
      - Strategic entry
   
   3. Resource Allocation:
      - Focused approach
      - Diversified approach
      - Balanced approach
      - Strategic approach
   
   4. Implementation:
      - Quick launch
      - Phased launch
      - Strategic launch
      - Controlled launch

   Variations:
   1. Product:
      - Core product
      - Enhanced product
      - Premium product
      - Value product
   
   2. Service:
      - Basic service
      - Enhanced service
      - Premium service
      - Value service
   
   3. Pricing:
      - Premium pricing
      - Value pricing
      - Competitive pricing
      - Strategic pricing
   
   4. Marketing:
      - Digital focus
      - Traditional focus
      - Mixed approach
      - Strategic approach

   Combinations:
   1. Market Entry:
      - Direct + Digital
      - Partnership + Traditional
      - Acquisition + Strategic
      - Innovation + Mixed
   
   2. Resource Use:
      - Focused + Digital
      - Diversified + Traditional
      - Balanced + Strategic
      - Strategic + Mixed
   
   3. Implementation:
      - Quick + Digital
      - Phased + Traditional
      - Strategic + Mixed
      - Controlled + Balanced
   
   4. Approach:
      - Direct + Focused
      - Partnership + Diversified
      - Acquisition + Strategic
      - Innovation + Balanced

3. PATH EVALUATION

   Path Evaluation:
   1. Direct Entry:
      - Market impact
      - Resource needs
      - Time required
      - Risk level
   
   2. Partnership:
      - Partner value
      - Resource sharing
      - Time efficiency
      - Risk sharing
   
   3. Acquisition:
      - Target value
      - Integration needs
      - Time investment
      - Risk assessment
   
   4. Innovation:
      - Innovation value
      - Resource needs
      - Time to market
      - Risk level

   Trade-offs:
   1. Speed vs. Quality:
      - Quick entry
      - Quality focus
      - Balanced approach
      - Strategic timing
   
   2. Cost vs. Impact:
      - Cost efficiency
      - Impact focus
      - Balanced approach
      - Strategic investment
   
   3. Risk vs. Reward:
      - Risk management
      - Reward focus
      - Balanced approach
      - Strategic risk
   
   4. Focus vs. Scope:
      - Focused approach
      - Broad scope
      - Balanced approach
      - Strategic scope

   Risks:
   1. Market:
      - Competition
      - Market changes
      - Customer behavior
      - Market conditions
   
   2. Business:
      - Financial risk
      - Operational risk
      - Strategic risk
      - Market risk
   
   3. Implementation:
      - Technical risk
      - Resource risk
      - Time risk
      - Quality risk
   
   4. Success:
      - Market success
      - Business success
      - Brand success
      - Customer success

   Benefits:
   1. Market:
      - Market access
      - Market share
      - Market position
      - Market growth
   
   2. Business:
      - Revenue growth
      - Profit margins
      - Business growth
      - Market position
   
   3. Brand:
      - Brand awareness
      - Brand value
      - Brand position
      - Brand growth
   
   4. Customer:
      - Customer base
      - Customer loyalty
      - Customer value
      - Customer growth

4. SOLUTION SELECTION

   Path Comparison:
   1. Market Impact:
      - Market penetration
      - Market share
      - Market position
      - Market growth
   
   2. Resource Use:
      - Resource efficiency
      - Resource impact
      - Resource value
      - Resource growth
   
   3. Time Investment:
      - Time efficiency
      - Time impact
      - Time value
      - Time optimization
   
   4. Risk Level:
      - Risk management
      - Risk impact
      - Risk value
      - Risk optimization

   Choice Optimization:
   1. Market Fit:
      - Market alignment
      - Market needs
      - Market value
      - Market potential
   
   2. Resource Fit:
      - Resource alignment
      - Resource needs
      - Resource value
      - Resource potential
   
   3. Time Fit:
      - Time alignment
      - Time needs
      - Time value
      - Time potential
   
   4. Risk Fit:
      - Risk alignment
      - Risk needs
      - Risk value
      - Risk potential

   Selection Validation:
   1. Market Validation:
      - Market testing
      - Market feedback
      - Market adjustment
      - Market optimization
   
   2. Resource Validation:
      - Resource testing
      - Resource feedback
      - Resource adjustment
      - Resource optimization
   
   3. Time Validation:
      - Time testing
      - Time feedback
      - Time adjustment
      - Time optimization
   
   4. Risk Validation:
      - Risk testing
      - Risk feedback
      - Risk adjustment
      - Risk optimization

   Solution Implementation:
   1. Market Implementation:
      - Market launch
      - Market monitoring
      - Market adjustment
      - Market optimization
   
   2. Resource Implementation:
      - Resource allocation
      - Resource monitoring
      - Resource adjustment
      - Resource optimization
   
   3. Time Implementation:
      - Time management
      - Time monitoring
      - Time adjustment
      - Time optimization
   
   4. Risk Implementation:
      - Risk management
      - Risk monitoring
      - Risk adjustment
      - Risk optimization
```

## LLM Configuration
- Model: Claude 3 Opus or GPT-4
- Temperature: 0.3
- Top-p: 0.95
- Max tokens: 4000
- Presence penalty: 0.1
- Frequency penalty: 0.1

## Notes
- Works best for complex problems
- More effective with clear criteria
- May need domain-specific adjustments
- Consider adding specific metrics
- Can be combined with other frameworks

## Related Templates
- Chain of Thought for reasoning
- Least-to-Most for step-by-step
- ReAct for interactive guidance

## Best Practices
1. **Analysis**
   - Clear aspects
   - Defined constraints
   - Specific goals
   - Clear criteria

2. **Branching**
   - Multiple approaches
   - Clear alternatives
   - Various options
   - Strategic combinations

3. **Evaluation**
   - Systematic assessment
   - Clear trade-offs
   - Risk analysis
   - Benefit analysis

4. **Selection**
   - Path comparison
   - Choice optimization
   - Selection validation
   - Careful implementation 