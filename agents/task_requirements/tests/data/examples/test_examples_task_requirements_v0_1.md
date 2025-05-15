
# Example 3: Service Request — Allergy Test (PPO, No Referral Required)

**Input:**
```json
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
    "user_response_created": "Got it — I'll check your plan and try to help you access an allergy test near you.",
    "timestamp": "2025-05-13T15:41:00Z"
  }
}
```

**Thought 1**: I need to determine what documentation or plan rules are required for allergy test access.  
**Act 1**: determine_required_context[service_intent]  
**Obs 1 (required_context)**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "Photo or scan of the user’s active insurance card",
    "date_added": null,
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "System must confirm allergy testing is covered under user plan",
    "date_added": null,
    "document_id": null
  },
  "referral_note": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "Referral from PCP for allergy testing",
    "date_added": null,
    "document_id": null
  }
}
```

**Thought 2**: I need to check the insurance card to confirm coverage and plan type.  
**Act 2**: read_document[insurance_id_card]  
**Obs 2**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": false,
    "source": "user_documents_database",
    "description": "Active Anthem PPO card, valid through 2026.",
    "date_added": "2025-05-11",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "System must confirm allergy testing is covered under user plan",
    "date_added": null,
    "document_id": null
  },
  "referral_note": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "Referral from PCP for allergy testing",
    "date_added": null,
    "document_id": null
  }
}
```

**Thought 3**: I now need to confirm whether allergy testing is covered under PPO and if referral is needed.  
**Act 3**: read_document[insurance_plan]  
**Obs 3**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": false,
    "source": "user_documents_database",
    "description": "Active Anthem PPO card, valid through 2026.",
    "date_added": "2025-05-11",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": false,
    "source": "user_documents_database",
    "description": "Allergy testing is covered under Anthem PPO without referral.",
    "date_added": "2025-05-13",
    "document_id": null
  },
  "referral_note": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "Referral from PCP for allergy testing",
    "date_added": null,
    "document_id": null
  }
}
```

**Thought 4**: Looking at the required context, I do see the referral note is not required so I will remove the referral_note key and properties. I need to request validation of the documents I found before moving forward. 
**Act 4**: request_user[required_context]
**Obs 4 (final context)**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Active Anthem PPO card, valid through 2026.",
    "date_added": "2025-05-11",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Allergy testing is covered under Anthem PPO without referral.",
    "date_added": "2025-05-13",
    "document_id": null
  }
}
```

**Thought 5**: I see all documents are included and valid. I will now request and add unique ids now that I won't be requesting anything else from the user.
**Act 5**: add_doc_unique_ids[required_context]
**Obs 5 (uid added required_context)**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Active Anthem PPO card, valid through 2026.",
    "date_added": "2025-05-11",
    "document_id": "doc_abc123"
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Allergy testing is covered under Anthem PPO without referral.",
    "date_added": "2025-05-13",
    "document_id": "covcheck_0333"
  }
}
```

**Thought 6**: I have all required documentation. Proceeding to next step.  
**Act 6**: finish[(input, required_context)]

---

# Example 4: Policy Question — PT Visit Limit

**Input:**
```json
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
```

**Thought 1**: This is a policy question — I need to identify the user's plan details and visit limit for physical therapy.  
**Act 1**: determine_required_context[service_intent]  
**Obs 1**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "User’s active insurance card",
    "date_added": null,
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": null,
    "source": null,
    "user_validated": false,
    "description": "System must look up the PT visit limit under this plan.",
    "date_added": null,
    "document_id": null
  },
  "referral_note": {
      "type": "document",
      "present": null,
      "source": null,
      "user_validated": false,
      "description": "Referral from primary care doctor for podiatry",
      "date_added": null,
      "document_id": null
  }
}
```

**Thought 2**: I need to check the insurance card to confirm the user's plan.  
**Act 2**: read_document[insurance_id_card]  
**Obs 2**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": false,
    "source": "user_documents_database",
    "description": "Cigna HMO insurance card valid through 2025",
    "date_added": "2025-05-12",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": null,
    "user_validated": false,
    "source": null,
    "description": "System must look up the PT visit limit under this plan.",
    "date_added": null,
    "document_id": null
  }
}
```

**Thought 3**: Now I’ll check the coverage rules to retrieve PT visit limits.  
**Act 3**: read_document[insurance_plan]  
**Obs 3**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": false,
    "source": "user_documents_database",
    "description": "Cigna HMO insurance card valid through 2025",
    "date_added": "2025-05-12",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": false,
    "source": "user_documents_database",
    "description": "Plan allows up to 25 physical therapy visits per year. Access requires a referral",
    "date_added": "2025-05-13",
    "document_id": null
  }
}
```

**Thought 4**: Looking at the required context, we seem to have everything. I will now request the user for document validation. 
**Act 4**: request_user[required_context]
**Obs 4 (verified and updated required_context)**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Cigna HMO insurance card valid through 2025",
    "date_added": "2025-05-12",
    "document_id": null
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Plan allows up to 25 physical therapy visits per year. Access requires a referral",
    "date_added": "2025-05-13",
    "document_id": null
  }
}
```

**Thought 5**: I see all documents are included and valid. I will now request and add unique ids now that I won't be requesting anything else from the user.
**Act 5**: add_doc_unique_ids[required_context]
**Obs 5 (uid added required_context)**:
```json
{
  "insurance_id_card": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Cigna HMO insurance card valid through 2025",
    "date_added": "2025-05-12",
    "document_id": "laks837dajslf"
  },
  "insurance_plan": {
    "type": "document",
    "present": true,
    "user_validated": true,
    "source": "user_documents_database",
    "description": "Plan allows up to 25 physical therapy visits per year. Access requires a referral",
    "date_added": "2025-05-13",
    "document_id": "vbo8276sju"
  }
}
```

**Thought 6**: Coverage data retrieved and validated. Proceeding to output.  
**Act 6**: finish[(input, required_context)]
