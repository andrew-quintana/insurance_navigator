# Graph of Thoughts (GoT)

**Type:** Graph of Thoughts  
**Domain:** Complex Problem Solving  
**Version:** 1.1  
**Last Updated:** 2024-07-10  

## Purpose
This template implements the Graph of Thoughts (GoT) framework to solve complex problems by constructing, exploring, and traversing thought graphs. GoT enables more structured reasoning than linear approaches by treating thoughts as nodes in a graph with defined operations.

## System Prompt
```
You are an expert problem solver who uses the Graph of Thoughts (GoT) framework to tackle complex problems through structured graph-based reasoning.

You solve problems by:
1. Breaking down complex problems into manageable sub-problems
2. Representing thoughts and insights as nodes in a conceptual graph
3. Using graph operations (GENERATE, EVALUATE, SELECT, EXPAND, MERGE) to explore and refine solutions
4. Iteratively improving solutions through structured traversal of the thought graph

Your approach follows this systematic process:

### GENERATE: Create multiple thought nodes for each sub-problem or aspect
### EVALUATE: Score and assess the quality, relevance, and potential of each thought
### SELECT: Choose the most promising thoughts and paths for further development
### EXPAND: Develop selected thoughts in greater detail and depth
### MERGE: Synthesize expanded thoughts into coherent solution components

Always show your graph construction process clearly, making the reasoning transparent and systematic.
```

## Human Message Template
```
Problem: {{problem_statement}}

Initial Sub-problems to Consider:
{{initial_subproblems}}

Generated Thoughts:
{{generate_thoughts}}

Thought Evaluations:
{{evaluate_thoughts}}

Selected Paths:
{{select_thoughts}}

Expanded Development:
{{expand_thoughts}}

Synthesis and Merging:
{{merge_thoughts}}

Expected Final Solution:
{{final_solution}}

Please solve this problem using the Graph of Thoughts framework, showing your systematic reasoning process.
```

## Variables
- **problem_statement**: The complex problem that needs to be solved
  - Example: "Design an efficient evacuation plan for a 10-story office building in case of a fire emergency."
  - Example: "Determine the most effective strategy for a city to reduce carbon emissions by 50% within 15 years."

- **initial_subproblems**: Numbered list of main components or sub-problems to address
  - Example:
    ```
    1. Building structure analysis
    2. Occupant flow management
    3. Communication systems
    4. Emergency response coordination
    5. Evacuation route optimization
    ```

- **generate_thoughts**: Create multiple thought nodes for each subproblem
  - Example:
    ```
    Node 1.1: The building has 10 floors with approximately 100 people per floor
    Node 1.2: There are 2 main staircases and 4 elevators (unusable during fire)
    Node 1.3: Fire exits are located on both ends of each floor
    
    Node 2.1: Peak evacuation times would be during work hours (9am-5pm)
    Node 2.2: Some occupants may have mobility limitations
    ```

- **evaluate_thoughts**: Assign quality scores or assessments to each thought node
  - Example:
    ```
    Node 1.1 (Score: 7/10): Important baseline information but needs verification
    Node 1.2 (Score: 9/10): Critical infrastructure insight, highly relevant
    Node 2.1 (Score: 6/10): Useful timing consideration but somewhat obvious
    ```

- **select_thoughts**: Choose highest-scoring or most promising thought combinations
  - Example:
    ```
    Selected core nodes for further development:
    - Node 1.2: Staircase and elevator infrastructure (Score: 9/10)
    - Node 3.2: Fire alarm system components (Score: 8/10)
    - Node 4.1: Floor warden system (Score: 9/10)
    ```

- **expand_thoughts**: Develop selected thoughts with more detail
  - Example:
    ```
    Expanding Node 4.1 (Floor warden system):
    - Each floor needs primary and backup wardens (Node 4.1.1)
    - Wardens need distinct identification items (Node 4.1.2)
    - Wardens require specialized training and regular drills (Node 4.1.3)
    - Communication protocol between wardens and central command (Node 4.1.4)
    ```

- **merge_thoughts**: Synthesize expanded thoughts into coherent solution components
  - Example:
    ```
    Merging Node 1.2, Node 3.2, and Node 4.1 insights:
    - Staircase capacity and floor warden system must be aligned (combined insight)
    - Floor wardens need direct access to fire alarm control for local announcements
    - Evacuation flow should be directed by wardens based on real-time staircase capacity
    ```

- **final_solution**: Comprehensive solution with clear reasoning trail
  - Example:
    ```
    1. Dual evacuation routes from each floor with clear signage
    2. Floor warden system with trained personnel and backup designees
    3. Phased evacuation starting with fire-affected floors and those immediately above
    4. Integrated communication system with redundancies
    ```

## Example Usage

### Full Internal Process Example
This example shows both the internal reasoning process and the final output. In practice, the internal GoT operations could be hidden from the final presentation to users.

**Input (Problem Statement):**
```
Design an efficient evacuation plan for a 10-story office building in case of a fire emergency.
```

**Internal GoT Process:**
```
# Graph of Thoughts Problem Solver

## Task Definition
I need to solve the following problem: Design an efficient evacuation plan for a 10-story office building in case of a fire emergency.

## GoT Framework Implementation
I will solve this problem using the Graph of Thoughts (GoT) framework by:
1. Breaking down the problem into manageable sub-problems 
2. Representing thoughts as nodes in a graph
3. Using graph operations to explore and refine solutions
4. Iteratively improving the solution through structured traversal

## Initial Graph Construction
Let me begin by identifying key components and sub-problems:

1. Building structure analysis
2. Occupant flow management
3. Communication systems
4. Emergency response coordination
5. Evacuation route optimization

## Graph Operations

### GENERATE: Initial Thoughts
Node 1.1: The building has 10 floors with approximately 100 people per floor
Node 1.2: There are 2 main staircases and 4 elevators (unusable during fire)
Node 1.3: Fire exits are located on both ends of each floor

Node 2.1: Peak evacuation times would be during work hours (9am-5pm)
Node 2.2: Some occupants may have mobility limitations
Node 2.3: Crowd behavior tends toward main exits unless directed

Node 3.1: PA system for building-wide announcements
Node 3.2: Fire alarm with visual and auditory components
Node 3.3: Emergency information displays at strategic locations

Node 4.1: Designated floor wardens needed for each floor
Node 4.2: Coordination with local fire department response
Node 4.3: Central command post for information management

Node 5.1: Primary and secondary evacuation routes for each floor
Node 5.2: Assembly points outside the building
Node 5.3: Prioritization system for floor evacuation sequence

### EVALUATE: Scoring Thoughts
Node 1.1 (Score: 7/10): Important baseline information but needs verification
Node 1.2 (Score: 9/10): Critical infrastructure insight, highly relevant
Node 1.3 (Score: 8/10): Essential for route planning, high relevance

Node 2.1 (Score: 6/10): Useful timing consideration but somewhat obvious
Node 2.2 (Score: 9/10): Critical for inclusive planning, often overlooked
Node 2.3 (Score: 8/10): Key behavioral insight affecting design

[Additional evaluations...]

### SELECT: Most Promising Paths
Selected for further development:
- Node cluster 1.2 + 1.3: Staircase/exit infrastructure (Avg score: 8.5/10)
- Node 2.2: Mobility limitations (Score: 9/10)
- Node 4.1: Floor warden system (Score: 9/10)
- Node 5.1 + 5.3: Route prioritization (Avg score: 8/10)

### EXPAND: Further Development
Expanding Node 4.1 (Floor warden system):
- Each floor needs primary and backup wardens (Node 4.1.1)
- Wardens need distinct identification items (Node 4.1.2)
- Wardens require specialized training and regular drills (Node 4.1.3)
- Communication protocol between wardens and central command (Node 4.1.4)

[Additional expansions...]

### MERGE: Synthesizing Solution
Merging Node 1.2, Node 1.3, Node 4.1 insights:
- Staircase capacity and floor warden system must be aligned
- Floor wardens need direct access to both staircases for routing decisions
- Evacuation flow should be directed by wardens based on real-time staircase capacity

[Additional merges...]
```

**Final Output:**
```
# Evacuation Plan Solution

## Key Components
1. Building structure analysis
2. Occupant flow management
3. Communication systems
4. Emergency response coordination
5. Evacuation route optimization

## Final Solution
After analyzing the problem through multiple perspectives and evaluating various approaches, here is the comprehensive evacuation plan:

1. Dual evacuation routes from each floor with clear signage
2. Floor warden system with trained personnel and backup designees
3. Phased evacuation starting with fire-affected floors and those immediately above
4. Integrated communication system with redundancies
5. Designated assembly points with accountability procedures
6. Accessibility provisions for mobility-impaired occupants
7. Quarterly drills and plan evaluation
8. Coordination protocol with emergency services

This solution optimizes for both evacuation speed and safety while accounting for real-world constraints and human factors.
```

### Concise Output Example
This example shows only the final output format, hiding the internal graph operations.

**Input:**
```
Design an efficient evacuation plan for a 10-story office building in case of a fire emergency.
```

**Output:**
```
# Evacuation Plan Solution

## Key Components Identified
1. Building structure analysis
2. Occupant flow management
3. Communication systems
4. Emergency response coordination
5. Evacuation route optimization

## Final Solution
After analyzing the problem through multiple perspectives and evaluating various approaches, here is the comprehensive evacuation plan:

1. Dual evacuation routes from each floor with clear signage
2. Floor warden system with trained personnel and backup designees
3. Phased evacuation starting with fire-affected floors and those immediately above
4. Integrated communication system with redundancies
5. Designated assembly points with accountability procedures
6. Accessibility provisions for mobility-impaired occupants
7. Quarterly drills and plan evaluation
8. Coordination protocol with emergency services

This solution optimizes for both evacuation speed and safety while accounting for real-world constraints and human factors.
```

## LLM Configuration
- Model: GPT-4, Claude 3 Opus, or equivalent
- Temperature: 0.7
- Top-p: 0.95
- Max tokens: 4000

## Notes
- Best suited for complex, multi-faceted problems requiring structured exploration
- More effective than linear Chain-of-Thought or Tree-of-Thoughts for problems with interdependent components
- Requires sufficient context window to maintain the graph state
- The internal graph operations (GENERATE, EVALUATE, etc.) can be kept as internal reasoning and not shown in the final output when presenting to users
- Can be extended with domain-specific operations beyond the core set
- Most effective when evaluation criteria are well-defined
- May require multiple passes through the graph for optimal solutions
- Consider visualizing the graph structure for complex problems 