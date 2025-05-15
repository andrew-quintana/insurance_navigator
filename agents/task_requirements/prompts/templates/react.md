# ReAct (Reason + Act) Template

**Type:** ReAct  
**Domain:** Universal  
**Version:** 1.0  
**Last Updated:** 2024-03-20  

## Purpose
Enable the model to solve complex problems through an iterative cycle of Thought, Action, and Observation. This template follows the ReAct (Reasoning+Acting) paradigm as described in the original research paper.

## Template
```
You are an expert {{role}} with deep knowledge in {{domain}}.
Your task is to {{task_description}}.

Follow the ReAct framework exactly:

1. For each step in solving this problem:
   - Thought: Reason about the current situation, what you know, and what you need to find out
   - Act: Take an action (Search, Lookup, Finish, etc.) with appropriate arguments
   - Obs: Observe the results of your action

2. Continue this cycle until you've solved the problem, then end with:
   - Thought: [Your final reasoning]
   - Act: Finish[Your output]

Examples:

Example 1:
Thought 1: I need to find out what the capital of France is.
Act 1: Search[capital of France]
Obs 1: According to search results, Paris is the capital of France.

Thought 2: Now I know the capital of France is Paris.
Act 2: Finish[The capital of France is Paris]

Example 2:
Thought 1: I need to calculate 15% of $85.
Act 1: Calculate[15% of 85]
Obs 1: 15% of $85 is $12.75.

Thought 2: Now I know that 15% of $85 is $12.75.
Act 2: Finish[$12.75]

Remember to:
1. Think step-by-step
2. Take actions to gather information when needed
3. Clearly state your observations
4. End with a "Finish" action when you have the answer

Task Context:
{{context}}

Input:
{{input}}

Available Actions:
{{available_actions}}
```

## Variables
- **role**: The expert role (e.g., research assistant, problem solver)
- **domain**: The specific domain of expertise
- **task_description**: Clear description of the task to accomplish
- **context**: Relevant background information
- **input**: The specific query or problem to solve
- **available_actions**: List of actions the agent can take (e.g., Search, Calculate, Lookup, Finish)

## Example
**Input:**
```
role: research assistant
domain: general knowledge
task_description: Answer the user's question by reasoning step-by-step and taking appropriate actions to gather information
context: You can search for information, perform calculations, and look up facts to answer questions accurately.
input: What is the boiling point of water in Fahrenheit?
available_actions: |
  - Search[query]: Search for information using the given query
  - Calculate[expression]: Perform a calculation
  - Lookup[term]: Look up a specific term or concept
  - Finish[answer]: Provide the final answer
```

**Output:**
```
Thought 1: I need to find out the boiling point of water. I know it's 100 degrees Celsius, but I need to convert it to Fahrenheit.

Act 1: Search[boiling point of water]

Obs 1: The boiling point of water at standard atmospheric pressure is 100°C or 212°F.

Thought 2: I've found that the boiling point of water is 212 degrees Fahrenheit. I can now provide the answer.

Act 2: Finish[The boiling point of water is 212 degrees Fahrenheit (100 degrees Celsius) at standard atmospheric pressure.]
```

## LLM Configuration
- Model: Claude 3 Opus or GPT-4
- Temperature: 0.2
- Top-p: 0.95
- Max tokens: 2000
- Presence penalty: 0.0
- Frequency penalty: 0.0

## Notes
- The structured Thought-Act-Observation cycle is essential to proper ReAct implementation
- Thoughts should be detailed and show reasoning
- Actions should be specific with clear parameters
- Observations should report results objectively
- The cycle continues until the problem is solved
- Always end with a Finish action

## Related Templates
- Chain of Thought for pure reasoning without actions
- Tree of Thoughts for exploring multiple reasoning paths
- Few-shot for example-based learning

## Best Practices
1. **Thinking**
   - Be explicit about reasoning
   - Break down complex problems
   - Consider what information is needed
   - Explain your thought process

2. **Acting**
   - Use specific, well-defined actions
   - Include clear parameters
   - Choose appropriate actions for each situation
   - Take one action at a time

3. **Observing**
   - Report observations objectively
   - Distinguish between facts and assumptions
   - Note important details
   - Update your understanding based on observations

4. **Solution Process**
   - Continue the cycle until problem is solved
   - Clearly state final conclusions
   - Use Finish action with the answer
   - Verify answer meets all requirements 