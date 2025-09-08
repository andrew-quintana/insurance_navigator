#!/usr/bin/env python3
"""
Test Realistic Insurance Responses
Test the agent processing pipeline with proper UUIDs and realistic insurance scenarios
"""

import asyncio
import sys
import os
import time
import uuid
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_realistic_insurance_responses():
    """Test the agent with realistic insurance scenarios and proper UUIDs."""
    print("🏥 Testing Realistic Insurance Responses")
    print("=" * 50)
    
    try:
        from agents.patient_navigator.chat_interface import PatientNavigatorChatInterface, ChatMessage
        
        # Initialize chat interface
        print("1️⃣ Initializing chat interface...")
        chat_interface = PatientNavigatorChatInterface()
        print("   ✅ Chat interface initialized")
        
        # Test scenarios with realistic insurance questions
        test_scenarios = [
            {
                "question": "What is my annual deductible?",
                "expected_keywords": ["deductible", "annual", "cost", "out-of-pocket"],
                "scenario": "Basic deductible inquiry"
            },
            {
                "question": "Does my plan cover physical therapy?",
                "expected_keywords": ["physical therapy", "coverage", "benefits", "rehabilitation"],
                "scenario": "Coverage inquiry"
            },
            {
                "question": "What is my copay for a doctor visit?",
                "expected_keywords": ["copay", "doctor", "visit", "cost-sharing"],
                "scenario": "Cost-sharing inquiry"
            },
            {
                "question": "How do I find a doctor in my network?",
                "expected_keywords": ["doctor", "network", "provider", "find"],
                "scenario": "Provider network inquiry"
            },
            {
                "question": "What are my prescription drug benefits?",
                "expected_keywords": ["prescription", "drug", "benefits", "pharmacy"],
                "scenario": "Prescription benefits inquiry"
            }
        ]
        
        results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{i}️⃣ Testing: {scenario['scenario']}")
            print(f"   Question: {scenario['question']}")
            
            # Create a proper UUID for the user
            user_id = str(uuid.uuid4())
            
            # Create test message
            test_message = ChatMessage(
                user_id=user_id,
                content=scenario['question'],
                timestamp=time.time(),
                message_type="text",
                language="en"
            )
            
            # Process message
            print("   ⏳ Processing message...")
            start_time = time.time()
            response = await chat_interface.process_message(test_message)
            processing_time = time.time() - start_time
            
            print(f"   ✅ Processed in {processing_time:.2f}s")
            print(f"   📝 Response: {response.content[:150]}...")
            print(f"   📊 Confidence: {response.confidence}")
            print(f"   🤖 Sources: {response.agent_sources}")
            
            # Analyze response quality
            response_lower = response.content.lower()
            keyword_matches = sum(1 for keyword in scenario['expected_keywords'] if keyword in response_lower)
            
            # Check if response is generic error
            is_generic_error = any(phrase in response.content.lower() for phrase in [
                "i'm sorry, but it looks like there was an issue",
                "i encountered an error while processing",
                "please try again",
                "there was a problem"
            ])
            
            # Evaluate response quality
            if is_generic_error:
                quality_score = 0.0
                quality_status = "❌ Generic Error"
            elif keyword_matches >= 2:
                quality_score = 0.8
                quality_status = "✅ Good"
            elif keyword_matches >= 1:
                quality_score = 0.6
                quality_status = "⚠️  Partial"
            else:
                quality_score = 0.3
                quality_status = "❌ Poor"
            
            result = {
                "scenario": scenario['scenario'],
                "question": scenario['question'],
                "response": response.content,
                "processing_time": processing_time,
                "confidence": response.confidence,
                "sources": response.agent_sources,
                "keyword_matches": keyword_matches,
                "quality_score": quality_score,
                "quality_status": quality_status,
                "is_generic_error": is_generic_error
            }
            
            results.append(result)
            print(f"   📊 Quality: {quality_status} (Score: {quality_score:.1f})")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return []

async def evaluate_with_claude_haiku(responses):
    """Use Claude Haiku to evaluate response quality and realism."""
    print("\n🤖 Evaluating Responses with Claude Haiku")
    print("=" * 50)
    
    try:
        from agents.base_agent import BaseAgent
        
        # Create a simple agent for evaluation
        evaluator = BaseAgent(
            name="response_evaluator",
            prompt="You are an expert insurance customer service evaluator. Rate the quality of insurance responses on a scale of 1-10.",
            mock=False
        )
        
        evaluations = []
        
        for i, result in enumerate(responses, 1):
            print(f"\n{i}️⃣ Evaluating: {result['scenario']}")
            
            evaluation_prompt = f"""
Evaluate this insurance customer service response:

**User Question:** {result['question']}
**Agent Response:** {result['response']}

Rate the response on these criteria (1-10 scale):
1. **Relevance**: Does it address the user's question?
2. **Accuracy**: Is the information correct and helpful?
3. **Clarity**: Is it easy to understand?
4. **Completeness**: Does it provide sufficient information?
5. **Tone**: Is it professional and empathetic?

Provide a single overall score (1-10) and brief explanation.
"""
            
            try:
                evaluation = await evaluator._call_llm(evaluation_prompt)
                print(f"   📊 Claude Evaluation: {evaluation[:200]}...")
                
                # Extract score if possible
                import re
                score_match = re.search(r'(\d+(?:\.\d+)?)/10', evaluation)
                claude_score = float(score_match.group(1)) if score_match else 5.0
                
                evaluations.append({
                    "scenario": result['scenario'],
                    "claude_score": claude_score,
                    "claude_evaluation": evaluation,
                    "our_score": result['quality_score'],
                    "response": result['response']
                })
                
            except Exception as e:
                print(f"   ❌ Claude evaluation failed: {e}")
                evaluations.append({
                    "scenario": result['scenario'],
                    "claude_score": 5.0,
                    "claude_evaluation": "Evaluation failed",
                    "our_score": result['quality_score'],
                    "response": result['response']
                })
        
        return evaluations
        
    except Exception as e:
        print(f"❌ Claude evaluation failed: {e}")
        return []

async def main():
    """Run the realistic response testing."""
    print("🚀 Starting Realistic Insurance Response Testing")
    print()
    
    # Test 1: Test realistic responses
    results = await test_realistic_insurance_responses()
    
    if not results:
        print("❌ No results to evaluate")
        return
    
    # Test 2: Evaluate with Claude Haiku
    evaluations = await evaluate_with_claude_haiku(results)
    
    # Generate summary
    print("\n" + "=" * 70)
    print("📊 REALISTIC RESPONSE TEST RESULTS")
    print("=" * 70)
    
    total_scenarios = len(results)
    generic_errors = sum(1 for r in results if r['is_generic_error'])
    good_responses = sum(1 for r in results if r['quality_score'] >= 0.7)
    average_processing_time = sum(r['processing_time'] for r in results) / total_scenarios
    average_confidence = sum(r['confidence'] for r in results) / total_scenarios
    
    print(f"Total Scenarios: {total_scenarios}")
    print(f"Generic Errors: {generic_errors} ({generic_errors/total_scenarios*100:.1f}%)")
    print(f"Good Responses: {good_responses} ({good_responses/total_scenarios*100:.1f}%)")
    print(f"Average Processing Time: {average_processing_time:.2f}s")
    print(f"Average Confidence: {average_confidence:.2f}")
    
    print("\n📋 Detailed Results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['scenario']}: {result['quality_status']} (Score: {result['quality_score']:.1f})")
        if result['is_generic_error']:
            print(f"     ❌ Generic error response")
        else:
            print(f"     📝 {result['response'][:100]}...")
    
    if evaluations:
        print("\n🤖 Claude Haiku Evaluations:")
        claude_scores = [e['claude_score'] for e in evaluations]
        average_claude_score = sum(claude_scores) / len(claude_scores)
        print(f"Average Claude Score: {average_claude_score:.1f}/10")
        
        for i, eval_result in enumerate(evaluations, 1):
            print(f"  {i}. {eval_result['scenario']}: {eval_result['claude_score']:.1f}/10")
            print(f"     Our Score: {eval_result['our_score']:.1f}")
    
    # Overall assessment
    if generic_errors == total_scenarios:
        print("\n❌ CRITICAL ISSUE: All responses are generic error messages")
        print("   The agent processing pipeline is not working correctly")
        print("   Need to fix UUID validation, RAG system, or data availability")
    elif generic_errors > total_scenarios * 0.5:
        print("\n⚠️  MAJOR ISSUE: Most responses are generic error messages")
        print("   The system needs significant fixes before production")
    elif good_responses >= total_scenarios * 0.7:
        print("\n✅ GOOD: Most responses are meaningful and relevant")
        print("   The system is working well for realistic scenarios")
    else:
        print("\n⚠️  MIXED: Some responses are good, others need improvement")
        print("   The system needs optimization for better consistency")
    
    return results, evaluations

if __name__ == "__main__":
    asyncio.run(main())
