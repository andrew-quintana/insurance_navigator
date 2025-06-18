#!/usr/bin/env python3
"""
Healthcare Regulatory Documents for Bulk Processing

Comprehensive list of regulatory documents relevant to:
- American Healthcare System
- Medicaid & Medicare
- Insurance Navigation
- Patient Rights
- HIPAA Compliance
"""

from typing import List, Dict, Any

def get_healthcare_document_urls() -> List[str]:
    """Get a curated list of healthcare regulatory document URLs."""
    documents = get_healthcare_documents_structured()
    return [doc['url'] for doc in documents if 'url' in doc]

def get_healthcare_documents_structured() -> List[Dict[str, Any]]:
    """
    Get structured healthcare regulatory documents with metadata.
    
    Categories:
    1. Medicare/Medicaid Official Documents
    2. CMS Regulations & Guidelines
    3. Patient Rights & Protections
    4. HIPAA & Privacy
    5. ACA/Obamacare
    6. State Insurance Regulations
    7. Healthcare Quality Standards
    """
    
    documents = [
        # =============================================================================
        # 1. MEDICARE & MEDICAID CORE DOCUMENTS
        # =============================================================================
        {
            "title": "Medicare & You 2024 Official Handbook",
            "url": "https://www.medicare.gov/Pubs/pdf/10050-Medicare-and-You.pdf",
            "category": "medicare_core",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 10,
            "description": "Official Medicare handbook covering benefits, enrollment, costs"
        },
        {
            "title": "Medicaid Eligibility Guidelines",
            "url": "https://www.medicaid.gov/medicaid/eligibility/index.html",
            "category": "medicaid_core",
            "jurisdiction": "Federal",
            "programs": ["Medicaid"],
            "priority": 10,
            "description": "Federal Medicaid eligibility requirements and guidelines"
        },
        {
            "title": "Medicare Part D Prescription Drug Coverage",
            "url": "https://www.medicare.gov/drug-coverage-part-d",
            "category": "medicare_part_d",
            "jurisdiction": "Federal", 
            "programs": ["Medicare"],
            "priority": 9,
            "description": "Medicare Part D prescription drug benefit information"
        },
        {
            "title": "Medicare Advantage Plans Overview",
            "url": "https://www.medicare.gov/sign-up-change-plans/types-of-medicare-health-plans/medicare-advantage-plans",
            "category": "medicare_advantage",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 9,
            "description": "Medicare Advantage (Part C) plan information and benefits"
        },
        {
            "title": "Medicaid CHIP State Program Information",
            "url": "https://www.medicaid.gov/chip/index.html",
            "category": "medicaid_chip",
            "jurisdiction": "Federal",
            "programs": ["Medicaid", "CHIP"],
            "priority": 8,
            "description": "Children's Health Insurance Program information"
        },

        # =============================================================================
        # 2. CMS REGULATIONS & GUIDELINES  
        # =============================================================================
        {
            "title": "CMS Medicare Learning Network Publications",
            "url": "https://www.cms.gov/Outreach-and-Education/Medicare-Learning-Network-MLN/MLNProducts",
            "category": "cms_guidelines",
            "jurisdiction": "Federal",
            "programs": ["Medicare", "Medicaid"],
            "priority": 8,
            "description": "CMS educational materials and policy guidance"
        },
        {
            "title": "Medicare Coverage Database",
            "url": "https://www.cms.gov/medicare-coverage-database/",
            "category": "medicare_coverage",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 9,
            "description": "Medicare coverage decisions and local coverage determinations"
        },
        {
            "title": "CMS Quality Measures",
            "url": "https://www.cms.gov/Medicare/Quality-Initiatives-Patient-Assessment-Instruments/QualityMeasures",
            "category": "quality_measures",
            "jurisdiction": "Federal",
            "programs": ["Medicare", "Medicaid"],
            "priority": 7,
            "description": "Healthcare quality measurement and reporting standards"
        },

        # =============================================================================
        # 3. PATIENT RIGHTS & PROTECTIONS
        # =============================================================================
        {
            "title": "Patients' Rights and Responsibilities",
            "url": "https://www.hhs.gov/healthcare/about-the-aca/patients-bill-of-rights/index.html",
            "category": "patient_rights",
            "jurisdiction": "Federal",
            "programs": ["ACA", "General"],
            "priority": 9,
            "description": "Patient Bill of Rights under the Affordable Care Act"
        },
        {
            "title": "Medicare Rights & Protections",
            "url": "https://www.medicare.gov/your-medicare-costs/help-paying-costs/medicare-rights",
            "category": "medicare_rights",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 8,
            "description": "Medicare beneficiary rights and appeal processes"
        },
        {
            "title": "Emergency Medical Treatment and Labor Act (EMTALA)",
            "url": "https://www.cms.gov/Regulations-and-Guidance/Legislation/EMTALA",
            "category": "emergency_care",
            "jurisdiction": "Federal",
            "programs": ["Emergency Care"],
            "priority": 7,
            "description": "Emergency medical screening and treatment requirements"
        },

        # =============================================================================
        # 4. HIPAA & PRIVACY REGULATIONS
        # =============================================================================
        {
            "title": "HIPAA Privacy Rule Summary",
            "url": "https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html",
            "category": "hipaa_privacy",
            "jurisdiction": "Federal",
            "programs": ["HIPAA"],
            "priority": 9,
            "description": "HIPAA Privacy Rule requirements and patient rights"
        },
        {
            "title": "HIPAA Security Rule",
            "url": "https://www.hhs.gov/hipaa/for-professionals/security/index.html",
            "category": "hipaa_security",
            "jurisdiction": "Federal",
            "programs": ["HIPAA"],
            "priority": 8,
            "description": "HIPAA Security Rule for protected health information"
        },
        {
            "title": "Patient Access to Medical Records",
            "url": "https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/access/index.html",
            "category": "medical_records",
            "jurisdiction": "Federal",
            "programs": ["HIPAA"],
            "priority": 8,
            "description": "Patient rights to access their medical records under HIPAA"
        },

        # =============================================================================
        # 5. AFFORDABLE CARE ACT (ACA)
        # =============================================================================
        {
            "title": "ACA Essential Health Benefits",
            "url": "https://www.hhs.gov/healthcare/about-the-aca/benefit-categories/index.html",
            "category": "aca_benefits",
            "jurisdiction": "Federal",
            "programs": ["ACA"],
            "priority": 9,
            "description": "Essential health benefits required under ACA plans"
        },
        {
            "title": "ACA Marketplace Enrollment Guidelines",
            "url": "https://www.healthcare.gov/glossary/",
            "category": "aca_enrollment",
            "jurisdiction": "Federal",
            "programs": ["ACA", "Marketplace"],
            "priority": 8,
            "description": "Health Insurance Marketplace enrollment and eligibility"
        },
        {
            "title": "ACA Preventive Care Coverage",
            "url": "https://www.hhs.gov/healthcare/about-the-aca/preventive-care/index.html",
            "category": "preventive_care",
            "jurisdiction": "Federal",
            "programs": ["ACA"],
            "priority": 7,
            "description": "Preventive care services covered without cost-sharing"
        },

        # =============================================================================
        # 6. INSURANCE REGULATIONS & CONSUMER PROTECTIONS
        # =============================================================================
        {
            "title": "NAIC Consumer Guide to Health Insurance",
            "url": "https://content.naic.org/sites/default/files/inline-files/Consumer_Guide_Health_Ins.pdf",
            "category": "insurance_guide",
            "jurisdiction": "State/Federal",
            "programs": ["Insurance"],
            "priority": 7,
            "description": "National Association of Insurance Commissioners health insurance guide"
        },
        {
            "title": "Mental Health Parity and Addiction Equity Act",
            "url": "https://www.cms.gov/CCIIO/Programs-and-Initiatives/Other-Insurance-Protections/mhpaea_factsheet",
            "category": "mental_health",
            "jurisdiction": "Federal",
            "programs": ["Mental Health"],
            "priority": 8,
            "description": "Mental health and substance use disorder benefit requirements"
        },
        {
            "title": "No Surprises Act Implementation",
            "url": "https://www.cms.gov/nosurprises",
            "category": "surprise_billing",
            "jurisdiction": "Federal",
            "programs": ["Surprise Billing"],
            "priority": 9,
            "description": "Protection from surprise medical bills and balance billing"
        },

        # =============================================================================
        # 7. HEALTHCARE QUALITY & SAFETY
        # =============================================================================
        {
            "title": "Hospital Compare Quality Ratings",
            "url": "https://www.medicare.gov/care-compare/",
            "category": "quality_ratings",
            "jurisdiction": "Federal",
            "programs": ["Medicare", "Quality"],
            "priority": 6,
            "description": "Medicare hospital and provider quality comparison tool"
        },
        {
            "title": "Physician Quality Reporting System",
            "url": "https://www.cms.gov/Medicare/Quality-Initiatives-Patient-Assessment-Instruments/PQRS",
            "category": "physician_quality",
            "jurisdiction": "Federal",
            "programs": ["Medicare", "Quality"],
            "priority": 5,
            "description": "Physician quality reporting requirements and measures"
        },

        # =============================================================================
        # 8. SPECIAL POPULATIONS & PROGRAMS
        # =============================================================================
        {
            "title": "Medicare Special Needs Plans",
            "url": "https://www.medicare.gov/sign-up-change-plans/types-of-medicare-health-plans/medicare-advantage-plans/medicare-advantage-plans-for-people-with-chronic-conditions",
            "category": "special_needs",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 7,
            "description": "Medicare Advantage plans for people with chronic conditions"
        },
        {
            "title": "Medicaid Long-Term Services and Supports",
            "url": "https://www.medicaid.gov/medicaid/long-term-services-supports/index.html",
            "category": "long_term_care",
            "jurisdiction": "Federal",
            "programs": ["Medicaid"],
            "priority": 7,
            "description": "Medicaid coverage for long-term care services"
        },
        {
            "title": "Medicare Extra Help Program",
            "url": "https://www.medicare.gov/your-medicare-costs/help-paying-costs/save-on-drug-costs/medicare-extra-help-paying-prescription-drug-costs",
            "category": "prescription_assistance",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 8,
            "description": "Medicare prescription drug cost assistance program"
        },

        # =============================================================================
        # 9. STATE-SPECIFIC RESOURCES (Major States)
        # =============================================================================
        {
            "title": "California Medicaid (Medi-Cal) Benefits",
            "url": "https://www.dhcs.ca.gov/services/medi-cal/Pages/default.aspx",
            "category": "state_medicaid",
            "jurisdiction": "California",
            "programs": ["Medicaid"],
            "priority": 6,
            "description": "California Medicaid program information and benefits"
        },
        {
            "title": "Texas Health and Human Services",
            "url": "https://www.hhs.texas.gov/services/health",
            "category": "state_health",
            "jurisdiction": "Texas", 
            "programs": ["State Health"],
            "priority": 5,
            "description": "Texas state health programs and services"
        },
        {
            "title": "New York State Health Marketplace",
            "url": "https://nystateofhealth.ny.gov/",
            "category": "state_marketplace",
            "jurisdiction": "New York",
            "programs": ["State Marketplace"],
            "priority": 5,
            "description": "New York state health insurance marketplace"
        },

        # =============================================================================
        # 10. APPEALS & GRIEVANCES
        # =============================================================================
        {
            "title": "Medicare Appeals Process",
            "url": "https://www.medicare.gov/claims-appeals/",
            "category": "appeals",
            "jurisdiction": "Federal",
            "programs": ["Medicare"],
            "priority": 8,
            "description": "Medicare claims appeals and grievance procedures"
        },
        {
            "title": "Medicaid Fair Hearing Process",
            "url": "https://www.medicaid.gov/medicaid/eligibility/medicaid-fair-hearings/index.html",
            "category": "fair_hearings",
            "jurisdiction": "Federal",
            "programs": ["Medicaid"],
            "priority": 7,
            "description": "Medicaid fair hearing and appeals process"
        }
    ]
    
    return documents

def get_documents_by_category(category: str) -> List[Dict[str, Any]]:
    """Get documents filtered by category."""
    all_docs = get_healthcare_documents_structured()
    return [doc for doc in all_docs if doc.get('category') == category]

def get_high_priority_documents() -> List[Dict[str, Any]]:
    """Get high priority documents (priority >= 8)."""
    all_docs = get_healthcare_documents_structured()
    return [doc for doc in all_docs if doc.get('priority', 0) >= 8]

def get_documents_by_program(program: str) -> List[Dict[str, Any]]:
    """Get documents filtered by program (Medicare, Medicaid, etc.)."""
    all_docs = get_healthcare_documents_structured()
    return [doc for doc in all_docs if program in doc.get('programs', [])]

def print_document_summary():
    """Print a summary of available documents."""
    docs = get_healthcare_documents_structured()
    
    print(f"Total Healthcare Regulatory Documents: {len(docs)}")
    print("\nBy Category:")
    
    categories = {}
    for doc in docs:
        cat = doc.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    
    print("\nBy Program:")
    programs = {}
    for doc in docs:
        for program in doc.get('programs', []):
            programs[program] = programs.get(program, 0) + 1
    
    for program, count in sorted(programs.items()):
        print(f"  {program}: {count}")
    
    print(f"\nHigh Priority Documents (≥8): {len(get_high_priority_documents())}")

if __name__ == "__main__":
    print_document_summary() 