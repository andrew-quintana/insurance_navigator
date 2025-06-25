# Information Retrieval Agent Examples

## Example 1: Basic Coverage Query

### Input
```json
{
    "user_id": "user123",
    "programs": ["Medicare", "Supplemental"],
    "document_types": ["user_documents", "policy"],
    "user_query": "What are my physical therapy benefits?"
}
```

### Self-Consistency Process
```
1. Query Reframing
Original: "What are my physical therapy benefits?"
Expert Reframe: "What are the specific physical therapy coverage limits, requirements, and copayments under the current insurance plan?"

2. Multiple Response Generation
Version 1:
- Coverage: 20 sessions per year
- Prior authorization required
- $30 copay per session

Version 2:
- Annual limit: 20 therapy sessions
- Requires prior approval
- Copayment: $30 each visit

Version 3:
- Physical therapy covered for 20 visits
- Pre-authorization needed
- $30 per visit copayment

3. Consistency Analysis
Common Elements:
- 20 sessions/visits limit
- Prior authorization requirement
- $30 copayment
```

### Output
```json
{
    "expert_reframe": "What are the specific physical therapy coverage limits, requirements, and copayments under the current insurance plan?",
    "direct_answer": "Your plan covers 20 physical therapy sessions per year with a $30 copayment per session. Prior authorization is required.",
    "key_points": [
        "20 session annual limit",
        "Prior authorization required",
        "$30 copayment per session"
    ],
    "confidence_score": 0.95
}
```

### Maintained Context (For Follow-ups)
```json
{
    "supporting_chunks": [
        {
            "content": "Physical therapy benefits include coverage for up to 20 sessions per calendar year. Each session requires a $30 copayment. Prior authorization must be obtained before starting treatment.",
            "source": "Current_Insurance_Policy.pdf",
            "relevance_score": 0.92
        },
        {
            "content": "Additional sessions may be approved based on medical necessity documentation from your provider.",
            "source": "Policy_Guidelines.pdf",
            "relevance_score": 0.85
        }
    ],
    "additional_details": [
        "Medical necessity criteria for additional sessions",
        "In-network vs out-of-network differences",
        "Coordination with other therapy benefits"
    ]
}
```

## Example 2: Medication Coverage Query

### Input
```json
{
    "user_id": "user456",
    "programs": ["Medicare Part D"],
    "document_types": ["formulary", "policy"],
    "user_query": "Is Metformin covered?"
}
```

### Self-Consistency Process
```
1. Query Reframing
Original: "Is Metformin covered?"
Expert Reframe: "What is the coverage status, tier level, and any requirements for Metformin under the current Medicare Part D plan?"

2. Multiple Response Generation
Version 1:
- Covered under Tier 1
- $5 copay for 30-day supply
- No prior authorization

Version 2:
- Tier 1 generic medication
- 30-day supply: $5
- No special requirements

Version 3:
- Covered in Tier 1 formulary
- $5 copayment (30 days)
- Authorization not required

3. Consistency Analysis
Common Elements:
- Tier 1 status
- $5 copay for 30 days
- No authorization needed
```

### Output
```json
{
    "expert_reframe": "What is the coverage status, tier level, and any requirements for Metformin under the current Medicare Part D plan?",
    "direct_answer": "Yes, Metformin is covered as a Tier 1 medication with a $5 copay for a 30-day supply. No prior authorization is required.",
    "key_points": [
        "Tier 1 generic medication",
        "$5 copay (30-day supply)",
        "No prior authorization needed"
    ],
    "confidence_score": 0.98
}
```

### Maintained Context (For Follow-ups)
```json
{
    "supporting_chunks": [
        {
            "content": "Metformin (generic) is covered under Tier 1 of the formulary. Standard copayment is $5 for a 30-day supply at preferred pharmacies.",
            "source": "Medicare_Part_D_Formulary.pdf",
            "relevance_score": 0.95
        },
        {
            "content": "90-day supplies available at mail-order pharmacies for reduced copayment of $10.",
            "source": "Pharmacy_Benefits.pdf",
            "relevance_score": 0.88
        }
    ],
    "additional_details": [
        "Mail order options",
        "Preferred pharmacy locations",
        "Quantity limits"
    ]
}
``` 