#!/usr/bin/env python3
"""
Debug Translation Validation
Test what's happening with the LLM translation validation
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.patient_navigator.shared.terminology import InsuranceTerminologyTranslator

def test_translation_validation():
    """Test the translation validation logic."""
    print("🔍 Debugging Translation Validation")
    print("=" * 50)
    
    translator = InsuranceTerminologyTranslator()
    
    # Test cases
    test_cases = [
        "What is my annual deductible?",
        "Does my plan cover physical therapy?", 
        "What is my copay for a doctor visit?",
        "How do I find a doctor in my network?",
        "What are my prescription drug benefits?"
    ]
    
    print("1️⃣ Testing LLM Translation Simulation")
    print("-" * 30)
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ Query: '{query}'")
        
        # Simulate what the LLM might return
        # The LLM is probably returning something like the original query
        simulated_llm_response = query  # This is likely what's happening
        
        print(f"   Simulated LLM Response: '{simulated_llm_response}'")
        
        # Test validation
        is_valid = translator.validate_translation(query, simulated_llm_response)
        print(f"   Validation Result: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        if not is_valid:
            print("   ❌ Why it failed:")
            if not simulated_llm_response or len(simulated_llm_response.strip()) == 0:
                print("      - Empty response")
            if query.lower() == simulated_llm_response.lower():
                print("      - Same as original (no translation occurred)")
            
            # Check insurance terms
            has_insurance_terms = any(term in simulated_llm_response.lower() for term in translator._insurance_terms)
            print(f"      - Contains insurance terms: {has_insurance_terms}")
            print(f"      - Insurance terms checked: {translator._insurance_terms}")
        
        # Test fallback
        fallback = translator.get_fallback_translation(query)
        print(f"   Fallback Translation: '{fallback}'")
        
        # Test if fallback would be valid
        fallback_valid = translator.validate_translation(query, fallback)
        print(f"   Fallback Validation: {'✅ Valid' if fallback_valid else '❌ Invalid'}")

if __name__ == "__main__":
    test_translation_validation()
