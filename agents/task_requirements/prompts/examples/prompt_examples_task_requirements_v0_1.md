# Example 1: Expert Request

**Input:**
```json
{
    "meta_intent": {
        "request_type": "expert_request",
        "summary": "User is requesting to see a podiatrist.",
        "emergency": false
    },
    "clinical_context": {
        "symptom": null,
        "body": {
            "region": "foot",
            "side": null,
            "subpart": null
        },
        "onset": null,
        "duration": null
    },
    "service_intent": {
        "specialty": "podiatry",
        "service": null,
        "plan_detail_type": null
    },
    "metadata": {
        "raw_user_text": "Can I book an appointment with a podiatrist?",
        "user_response_created": "Sure! I'll help you figure out how to get support from a podiatrist based on your insurance.",
        "timestamp": "2025-05-13T15:51:00Z"
    }
}
```

**Thought 1**: I need to determine what documentation or plan rules are required based on the users intent, to get access to a podiatrist and schedule an appointment.
**Act 1**: determine_required_context[service_intent]
**Obs 1 (required_context)**:
```json
{
    "insurance_id_card": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "Photo or scan of the user's active insurance card",
        "date_added": null,
        "document_id": null
    },
    "plan_coverage_verified": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "System must confirm podiatry services are covered under this plan",
        "date_added": null,
        "document_id": null
    },
    "referral_note": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    }
}
```

**Thought 2**: I need to examine the insurance ID card to confirm coverage is valid and current.
**Act 2**: read_document[insurance_id_card]
**Obs 2**: The insurance card is active with UnitedHealthcare, valid through 2026. Member ID and plan type confirmed. Updated required_context:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_info_docs_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
        "date_added": "2025-05-10",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": null,
        "user_validated": false,
        "source": null,
        "description": "System must confirm podiatry services are covered under this plan",
        "date_added": null,
        "document_id": null
    },
    "referral_note": {
        "type": "document",
        "present": null,
        "user_validated": false,
        "source": null,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    },
}
```

**Thought 3**: I need to check the plan coverage info to see if podiatry services are covered and if a referral is required.
**Act 3**: read_document[insurance_plan]
**Obs 3**: The plan HMO-X23 requires a referral from a primary care provider for specialist visits including podiatry. Updated required_context:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
        "date_added": "2025-05-10",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Plan HMO-X23 requires a referral from a PCP for podiatry.",
        "date_added": "2025-05-13",
        "document_id": null
    },
    "referral_note": {
        "type": "document",
        "present": null,
        "user_validated": false,
        "source": null,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    },
}
```

**Thought 3**: I need to check if the referral note is present and valid.
**Act 3**: read_document[referral_note]
**Obs 3**: The referral note is missing. It must be requested from the user. Updated required_context:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
        "date_added": "2025-05-10",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Plan HMO-X23 requires a referral from a PCP for podiatry.",
        "date_added": "2025-05-13",
        "document_id": null
    },
    "referral_note": {
        "type": "document",
        "present": false,
        "user_validated": false,
        "source": "user_info_docs_database",
        "description": "Referral from primary care doctor for podiatry. Missing document.",
        "date_added": null,
        "document_id": null
    }
}
```

**Thought 5**: Looking at the required context, I do see the referral note is missing so I need to request it from the user. 
**Act 5**: request_user[required_context]
**Obs 5 (verified and updated required_context)**:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card",
        "date_added": "2025-05-10",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Access to podiatry services requires referral under plan HMO-X23.",
        "date_added": "2025-05-13",
        "document_id": null
    },
    "referral_note": {
        "type": "document",
        "present": false,
        "user_validated": true,
        "source": null,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    },
}
```

**Thought 6**: I need to check if the referral note is present and valid.
**Act 6**: read_document[referral_note]
**Obs 6**: I see the user indeed uploaded the document. Updated required_context:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
        "date_added": "2025-05-10",
        "document_id": null
    },
    "referral_note": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Referral from primary care doctor for podiatry",
        "date_added": "2025-05-14",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Plan HMO-X23 requires a referral from a PCP for podiatry.",
        "date_added": "2025-05-13",
        "document_id": null
    }
}
```

**Thought 7**: I see all documents are included and valid. I will now request and add unique ids now that I won't be requesting anything else from the user.
**Act 7**: add_doc_unique_ids[required_context]
**Obs 7 (uid added required_context)**:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with UnitedHealthcare, valid through 2026.",
        "date_added": "2025-05-10",
        "document_id": "doc_328uwh"
    },
    "referral_note": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Referral from primary care doctor for podiatry",
        "date_added": "2025-05-14",
        "document_id": "muhoh351fxq"
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": true,
        "source": "user_documents_database",
        "description": "Plan HMO-X23 requires a referral from a PCP for podiatry.",
        "date_added": "2025-05-13",
        "document_id": "covcheck_00281"
    }
}
```

**Thought 8**: I now see all required context has been attained and user_validated. I'll now send the request to the next agent.
**Act 8**: finish[(input, required_context)]

# Example 2: Service Request — Allergy Test with PPO (No Referral Required)

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

**Thought 1**: I need to determine what documentation or plan rules are required based on the user's intent, to get access to an allergy test.
**Act 1**: determine_required_context[service_intent]  
**Obs 1 (required_context)**:
```json
{
    "insurance_id_card": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "Photo or scan of the user's active insurance card",
        "date_added": null,
        "document_id": null
    },
    "insurance_plan": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "System must confirm allergy test is covered under this plan",
        "date_added": null,
        "document_id": null
    },
    "referral_note": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    },
}
```

**Thought 2**: I need to examine the insurance ID card to confirm coverage is valid and current.  
**Act 2**: read_document[insurance_id_card]  
**Obs 2 (updated required_context)**:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with Anthem PPO, valid through 2026.",
        "date_added": "2025-05-11",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": null,
        "user_validated": false,
        "source": null,
        "description": "System must confirm allergy test is covered under this plan",
        "date_added": null,
        "document_id": null
    },
    "referral_note": {
        "present": null,
        "source": null,
        "user_validated": false,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    },
}
```

**Thought 3**: I need to check the plan coverage info to confirm allergy testing is covered and whether a referral is needed.  
**Act 3**: read_document[insurance_plan]  
**Obs 3 (updated required_context)**:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with Anthem PPO, valid through 2026.",
        "date_added": "2025-05-11",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Allergy testing is covered with no referral required under Anthem PPO plan.",
        "date_added": "2025-05-13",
        "document_id": null
    },
    "referral_note": {
        "present": null,
        "source": null,
        "description": "Referral from primary care doctor for podiatry",
        "date_added": null,
        "document_id": null
    },
}
```

**Thought 4**: Looking at the required context, I do see the referral note is not required so I will remove the referral_note key and properties. I need to request validation of the documents I found before moving forward. 
**Act 4**: request_user[required_context]
**Obs 4 (verified and updated required_context)**:
```json
{
    "insurance_id_card": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with Anthem PPO, valid through 2026.",
        "date_added": "2025-05-11",
        "document_id": null
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Allergy testing is covered with no referral required under Anthem PPO plan.",
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
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Photo or scan of the user's active insurance card. Confirmed active with Anthem PPO, valid through 2026.",
        "date_added": "2025-05-11",
        "document_id": "asdf713tl"
    },
    "insurance_plan": {
        "type": "document",
        "present": true,
        "user_validated": false,
        "source": "user_documents_database",
        "description": "Allergy testing is covered with no referral required under Anthem PPO plan.",
        "date_added": "2025-05-13",
        "document_id": "ads6g902g"
    }
}
```

**Thought 6**: All documentation is valid and coverage is confirmed with no referral required. Proceeding to next agent.
**Act 6**: finish[(input, required_context)]
