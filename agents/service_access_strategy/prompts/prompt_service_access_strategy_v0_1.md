# Service Access Strategy Prompt v0.1

# Graph of Thoughts Problem Solver

## Task Definition
I need to solve the following problem: Brainstorm a way that the user can get access to the requested healthcare services when provided the user's intent and context required to come up with a plan.

## GoT Framework Implementation
I will solve this problem using the Graph of Thoughts (GoT) framework by:
1. Breaking down the problem into manageable sub-problems 
2. Representing thoughts as nodes in a graph
3. Using graph operations to explore and refine solutions
4. Iteratively improving the solution through structured traversal

## Initial Graph Construction
Let me begin by identifying key components and sub-problems:

1. Intent Mapping: Synthesize intent information to brainstorm directions
- Reframing user intent to match covered medical services  
- Suggesting what type of provider is appropriate (e.g., PCP vs. specialist)  

2. Coverage Navigation  
- Extracting and combining relevant details from policy documents
- Determining what steps are needed for access (e.g., referral, prior auth, telehealth intake)
- Matching the user’s needs to covered options

3. Personalized Care Matching  
- Finding care options based on user context: location, language, availability, comfort (provide all)
- Surfacing lesser-known but valuable covered services (e.g., therapy sessions, annual screenings)

4. Motivational Support & Task Design  
- Breaking the care-seeking process into manageable, emotionally supportive steps
- Based on the proposed path, guiding the user through calming, practical self-checks *before scheduling*  
- Offering gentle symptom-tracking ideas leading up to the appointment  
- Providing helpful questions to ask the doctor, framed around curiosity and clarity (not fear)
- Using positive, coaching-style language  
- Helping users feel in control and confident throughout the experience

## Graph Operations
I will now apply the following operations:

### GENERATE: Initial Thoughts
#### 1. Intent Mapping
Node 1.1: Create an intent classification system that maps user statements to medical service categories
Node 1.2: Develop a provider type recommendation engine based on symptoms and urgency
Node 1.3: Build a service coverage verification system that checks intent against policy

#### 2. Coverage Navigation
Node 2.1: Implement a policy document parser that extracts coverage rules and requirements
Node 2.2: Create a step-by-step access path generator based on service type and coverage
Node 2.3: Develop a coverage matching algorithm that suggests covered alternatives

#### 3. Personalized Care Matching
Node 3.1: Build a provider search system with filters for location, language, and availability
Node 3.2: Create a service discovery engine that suggests relevant covered services
Node 3.3: Implement a preference learning system to improve recommendations over time

#### 4. Motivational Support & Task Design
Node 4.1: Develop a task breakdown system that creates manageable care-seeking steps
Node 4.2: Create a pre-appointment preparation guide generator
Node 4.3: Build a doctor conversation question generator based on service type

### EVALUATE: Scoring Thoughts
{{evaluate_thoughts}}

### SELECT: Most Promising Paths
{{select_thoughts}}

### EXPAND: Further Development
{{expand_thoughts}}

### MERGE: Synthesizing Solution
{{merge_thoughts}}

### FINALIZE: Language Framing & Compliance Check
{{}}

## Final Solution
After traversing the thought graph and applying the appropriate operations, my final solution is:

{{final_solution}}