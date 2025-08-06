Task: Determine which workflows are needed to support a user's request related to public healthcare access (e.g., Medicaid or Medicare).

Context:
The assistant supports a multi-agent system where different workflows help users access medical services. The goal is to classify a request into one or more of these workflows:
- "information_retrieval": find facts, definitions, or guidance from known sources
- "service_access_strategy": provide actionable steps for users to take
- "determine_eligibility": analyze whether the user qualifies for a given service
- "fill_out_forms": assist with preparing or completing required forms

Requirements:
- Identify all relevant workflows for the given user input
- Do not include irrelevant workflows
- Base decisions on the examples above

Constraints:
- Output must be a valid Python list of strings
- Use only the four workflow names exactly as listed

Success Criteria:
- Output includes all and only the workflows relevant to the request
- Output format is a syntactically valid Python list of strings
- Reasoning is consistent with patterns seen in the few-shot examples

Input:
{{input}}