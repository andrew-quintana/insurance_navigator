#!/usr/bin/env python3
"""
Create Test Insurance Document
Generate a realistic insurance document with specific deductible, copay, and coverage information
"""

from fpdf import FPDF
import os

def create_test_insurance_document():
    """Create a test insurance document with specific information for RAG testing."""
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    
    # Title
    pdf.cell(0, 10, 'SCAN Classic HMO - Evidence of Coverage 2025', 0, 1, 'C')
    pdf.ln(10)
    
    # Table of Contents
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Table of Contents', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, '1. Plan Overview and Eligibility', 0, 1)
    pdf.cell(0, 8, '2. Cost Sharing and Deductibles', 0, 1)
    pdf.cell(0, 8, '3. Copayments and Coinsurance', 0, 1)
    pdf.cell(0, 8, '4. Covered Services and Benefits', 0, 1)
    pdf.cell(0, 8, '5. Provider Network and Access', 0, 1)
    pdf.cell(0, 8, '6. Prescription Drug Benefits', 0, 1)
    pdf.cell(0, 8, '7. Prior Authorization Requirements', 0, 1)
    pdf.cell(0, 8, '8. Appeals and Grievances', 0, 1)
    pdf.ln(15)
    
    # Section 1: Plan Overview
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '1. Plan Overview and Eligibility', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    plan_overview = """
    SCAN Classic HMO is a Medicare Advantage plan offered by SCAN Health Plan. This plan provides comprehensive 
    healthcare coverage for eligible Medicare beneficiaries in Alameda and San Mateo Counties. The plan combines 
    Medicare Part A (hospital insurance) and Part B (medical insurance) benefits with additional coverage for 
    prescription drugs and other services not covered by Original Medicare.
    
    To be eligible for SCAN Classic HMO, you must be enrolled in both Medicare Part A and Part B, live in our 
    service area, and not have End-Stage Renal Disease (ESRD) at the time of enrollment. The plan operates on a 
    calendar year basis from January 1st through December 31st.
    
    This Evidence of Coverage (EOC) document explains your benefits, rights, and responsibilities as a member 
    of SCAN Classic HMO. It is important to read this document carefully and keep it for your records. If you 
    have questions about your coverage, please contact Member Services at 1-800-559-3500.
    """
    pdf.multi_cell(0, 5, plan_overview)
    pdf.ln(10)
    
    # Section 2: Cost Sharing and Deductibles
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Cost Sharing and Deductibles', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    deductible_info = """
    ANNUAL DEDUCTIBLE: $0
    
    SCAN Classic HMO has a $0 annual deductible for both medical and prescription drug benefits. This means 
    you do not need to pay a specific amount out-of-pocket before your plan begins covering your healthcare 
    services. Unlike Original Medicare, which has deductibles for Part A ($1,632 in 2024) and Part B ($240 in 2024), 
    SCAN Classic HMO eliminates these deductibles to make healthcare more affordable for our members.
    
    The $0 deductible applies to all covered services, including:
    - Primary care physician visits
    - Specialist visits
    - Hospital stays
    - Emergency room visits
    - Prescription medications
    - Preventive services
    
    This benefit is one of the key advantages of choosing SCAN Classic HMO over Original Medicare, as it 
    provides predictable healthcare costs without the burden of meeting annual deductibles.
    """
    pdf.multi_cell(0, 5, deductible_info)
    pdf.ln(10)
    
    # Section 3: Copayments and Coinsurance
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. Copayments and Coinsurance', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    copay_info = """
    COPAYMENT SCHEDULE:
    
    Primary Care Physician Visits: $0 copay
    Specialist Visits: $45 copay
    Emergency Room Visits: $90 copay
    Urgent Care Visits: $25 copay
    Mental Health Visits: $20 copay
    Physical Therapy: $20 copay per visit
    Occupational Therapy: $20 copay per visit
    Speech Therapy: $20 copay per visit
    
    COINSURANCE:
    
    Inpatient Hospital Stays: $0 per day (unlimited days)
    Outpatient Surgery: $0 copay
    Diagnostic Tests and Lab Work: $0 copay
    X-rays and Imaging: $0 copay
    Preventive Services: $0 copay (100% covered)
    
    The copayment amounts listed above are the maximum you will pay for each service. These copayments 
    apply to in-network providers only. If you receive services from out-of-network providers without 
    prior authorization, you may be responsible for the full cost of those services.
    """
    pdf.multi_cell(0, 5, copay_info)
    pdf.ln(10)
    
    # Section 4: Covered Services
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '4. Covered Services and Benefits', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    covered_services = """
    SCAN Classic HMO covers all services that are covered by Original Medicare, plus additional benefits:
    
    MEDICARE PART A COVERED SERVICES:
    - Inpatient hospital care
    - Skilled nursing facility care
    - Home health care
    - Hospice care
    - Inpatient mental health care
    
    MEDICARE PART B COVERED SERVICES:
    - Doctor visits and outpatient services
    - Preventive services (annual wellness visits, screenings, vaccinations)
    - Durable medical equipment
    - Ambulance services
    - Laboratory tests and X-rays
    - Physical and occupational therapy
    - Mental health services
    
    ADDITIONAL SCAN BENEFITS:
    - Prescription drug coverage (Part D)
    - Routine dental care (up to $1,500 per year)
    - Routine vision care (annual eye exam and $200 toward glasses)
    - Routine hearing care (annual hearing exam and $1,000 toward hearing aids)
    - Fitness program membership
    - Transportation to medical appointments
    - Over-the-counter benefit ($50 per quarter)
    
    All covered services must be provided by in-network providers unless prior authorization is obtained 
    for out-of-network care.
    """
    pdf.multi_cell(0, 5, covered_services)
    pdf.ln(10)
    
    # Section 5: Provider Network and Access
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '5. Provider Network and Access', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    provider_info = """
    FINDING A DOCTOR:
    
    To find a doctor or other healthcare provider in the SCAN Classic HMO network, you can:
    
    1. Visit our website at www.scanhealthplan.com and use our online provider directory
    2. Call Member Services at 1-800-559-3500 and speak with a representative
    3. Use our mobile app to search for providers by location, specialty, or name
    4. Request a printed provider directory by calling Member Services
    
    NETWORK REQUIREMENTS:
    
    You must use in-network providers for all non-emergency care.     The SCAN Classic HMO network includes:
    - Over 5,000 primary care physicians
    - Over 15,000 specialists
    - Over 200 hospitals
    - Over 1,000 pharmacies
    - Mental health providers
    - Physical therapy providers
    - Home health agencies
    
    If you need to see a specialist, you must first get a referral from your primary care physician (PCP). 
    Your PCP will coordinate your care and ensure you receive the most appropriate treatment.
    
    EMERGENCY CARE:
    
    For emergency situations, you can go to any hospital emergency room, whether in-network or out-of-network. 
    Emergency care is covered at the same cost-sharing level regardless of the hospital's network status.
    """
    pdf.multi_cell(0, 5, provider_info)
    pdf.ln(10)
    
    # Section 6: Prescription Drug Benefits
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '6. Prescription Drug Benefits', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    prescription_info = """
    PRESCRIPTION DRUG COVERAGE:
    
    SCAN Classic HMO includes comprehensive prescription drug coverage through Medicare Part D. The plan 
    uses a formulary (list of covered drugs) to determine which medications are covered and at what cost.
    
    COST SHARING FOR PRESCRIPTIONS:
    
    Generic Drugs (Tier 1): $0 copay
    Preferred Brand Drugs (Tier 2): $10 copay
    Non-Preferred Brand Drugs (Tier 3): $40 copay
    Specialty Drugs (Tier 4): $100 copay
    
    PHARMACY NETWORK:
    
    You can fill your prescriptions at any of the 1,000+ pharmacies in our network, including:
    - CVS Pharmacy
    - Walgreens
    - Rite Aid
    - Safeway
    - Costco
    - Independent pharmacies
    
    MAIL ORDER PHARMACY:
    
    For maintenance medications (drugs you take regularly), you can use our mail order pharmacy service 
    and receive up to a 90-day supply with significant savings on copayments.
    
    PRIOR AUTHORIZATION:
    
    Some medications require prior authorization before they will be covered. Your doctor can submit 
    prior authorization requests online or by calling our pharmacy department.
    """
    pdf.multi_cell(0, 5, prescription_info)
    pdf.ln(10)
    
    # Section 7: Prior Authorization
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '7. Prior Authorization Requirements', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    prior_auth_info = """
    PRIOR AUTHORIZATION REQUIRED FOR:
    
    - MRI and CT scans
    - Certain surgical procedures
    - Durable medical equipment over $500
    - Home health services beyond 60 days
    - Skilled nursing facility stays beyond 20 days
    - Some prescription medications
    
    HOW TO GET PRIOR AUTHORIZATION:
    
    1. Your doctor submits a request to SCAN Classic HMO
    2. We review the request within 14 days (72 hours for urgent requests)
    3. We notify you and your doctor of the decision
    4. If approved, you can proceed with the service
    5. If denied, you have the right to appeal
    
    You can check the status of prior authorization requests online or by calling Member Services.
    """
    pdf.multi_cell(0, 5, prior_auth_info)
    pdf.ln(10)
    
    # Section 8: Appeals and Grievances
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '8. Appeals and Grievances', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    appeals_info = """
    IF YOU DISAGREE WITH A COVERAGE DECISION:
    
    You have the right to appeal any decision we make about your coverage. There are several levels of appeal:
    
    LEVEL 1 APPEAL:
    - Submit a written request within 60 days
    - We will review and respond within 30 days
    - For urgent requests, we respond within 72 hours
    
    LEVEL 2 APPEAL:
    - If you disagree with Level 1 decision
    - Submit within 60 days of Level 1 decision
    - Independent review organization makes decision
    
    LEVEL 3 APPEAL:
    - Administrative Law Judge hearing
    - Available for claims over $180 (2024 amount)
    
    HOW TO FILE AN APPEAL:
    
    1. Call Member Services at 1-800-559-3500
    2. Submit online at www.scanhealthplan.com
    3. Mail to: SCAN Health Plan, Appeals Department, P.O. Box 12345, Long Beach, CA 90802
    
    You can also file a complaint (grievance) about the quality of care or service you received.
    """
    pdf.multi_cell(0, 5, appeals_info)
    pdf.ln(10)
    
    # Footer
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, 'This document is for testing purposes only. Not an actual insurance policy.', 0, 1, 'C')
    
    # Save the PDF
    output_path = "examples/test_insurance_document.pdf"
    pdf.output(output_path)
    print(f"✅ Created test insurance document: {output_path}")
    
    return output_path

if __name__ == "__main__":
    create_test_insurance_document()
