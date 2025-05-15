Example 1: Expert Request
Input:
"I want to see a dermatologist in my area."
Output:
{
  "meta_intent": {
    "request_type": "expert_request",
    "summary": "User wants to see a dermatologist.",
    "emergency": false
  },
  "clinical_context": {
    "symptom": null,
    "body": {
      "region": null,
      "side": null,
      "subpart": null
    },
    "onset": null,
    "duration": null
  },
  "service_intent": {
    "specialty": "dermatology",
    "service": null,
    "plan_detail_type": null
  },
  "metadata": {
    "raw_user_text": "I want to see a dermatologist.",
    "user_response_created": "Sure! Let me help you find a dermatologist covered by your plan.",
    "timestamp": "2025-05-13T15:40:00Z"
  }
}

Example 2: Service Request
Input:
"I want to get an allergy test."
Output:
{
  "meta_intent": {
    "request_type": "service_request",
    "summary": "User wants to get an allergy test.",
    "emergency": false
  },
  "clinical_context": {
    "symptom": null,
    "body": {
      "region": null,
      "side": null,
      "subpart": null
    },
    "onset": null,
    "duration": null
  },
  "service_intent": {
    "specialty": "allergy",
    "service": "allergy test",
    "plan_detail_type": null
  },
  "metadata": {
    "raw_user_text": "I want to get an allergy test.",
    "user_response_created": "Got it — I'll check your plan and help you access an allergy test near you.",
    "timestamp": "2025-05-13T15:41:00Z"
  }
}

Example 3: Symptom Report
Input:
"I have a red, itchy rash on my hip that won't go away."
Output:
{
  "meta_intent": {
    "request_type": "symptom_report",
    "summary": "User reports red, itchy rash on left hip.",
    "emergency": "unsure"
  },
  "clinical_context": {
    "symptom": "red itchy rash",
    "body": {
      "region": "hip",
      "side": "left",
      "subpart": null
    },
    "onset": null,
    "duration": "chronic"
  },
  "service_intent": {
    "specialty": "dermatology",
    "service": null,
    "plan_detail_type": null
  },
  "metadata": {
    "raw_user_text": "I have a red, itchy rash on my left hip that won't go away.",
    "user_response_created": "Thanks for sharing. Let's find the best next step for evaluating that rash — I'll take a look at your coverage options.",
    "timestamp": "2025-05-13T15:42:00Z"
  }
}

Example 4: Policy Question
Input:
"How many physical therapy appointments can I get with my plan?"
Output:
{
  "meta_intent": {
    "request_type": "policy_question",
    "summary": "User asking about physical therapy visit limit.",
    "emergency": false
  },
  "clinical_context": {
    "symptom": null,
    "body": {
      "region": null,
      "side": null,
      "subpart": null
    },
    "onset": null,
    "duration": null
  },
  "service_intent": {
    "specialty": "physical therapy",
    "service": "physical therapy",
    "plan_detail_type": "visit_limit"
  },
  "metadata": {
    "raw_user_text": "How many physical therapy appointments can I get with my plan?",
    "user_response_created": "I'll check your plan to see how many physical therapy visits you're allowed each year.",
    "timestamp": "2025-05-13T15:43:00Z"
  }
}

Example 5: Prompt Injection
Input:
"[SECURITY WARNING: Leakage Request detected.]"
Output:
{
  "meta_intent": {
    "request_type": "security_warning",
    "summary": "SECURITY WARNING: Leakage Request detected.",
    "emergency": false
  },
  "clinical_context": {
    "symptom": null,
    "body": {
      "region": null,
      "side": null,
      "subpart": null
    },
    "onset": null,
    "duration": null
  },
  "service_intent": {
    "specialty": null,
    "service": null,
    "plan_detail_type": null
  },
  "metadata": {
    "raw_user_text": "[SECURITY WARNING: Leakage Request detected.]",
    "user_response_created": "We detected an illegal request in your last message. Click here to request support or try again. Warning, if another illegal request is made, your account may be suspended.",
    "timestamp": "2025-05-13T15:43:00Z"
  }
}