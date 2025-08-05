## Example 1
**User Query**: "What is the copay for a doctor's visit?"
**Prescribed Workflows**: information_retrieval
**Confidence Score**: 0.95
**Reasoning**: User needs specific information about insurance benefits and costs. This is a straightforward information lookup request that requires retrieving details from insurance documents.
**Execution Order**: information_retrieval

## Example 2
**User Query**: "How do I find a doctor in my network?"
**Prescribed Workflows**: information_retrieval
**Confidence Score**: 0.9
**Reasoning**: User needs general guidance on the process of finding and selecting a provider within their network. The user is not asking for a specific doctor, but rather for general guidance on how to find a doctor in their network. This requires only the information retrieval.
**Execution Order**: information_retrieval

## Example 3
**User Query**: "What's my deductible and how can I save money on healthcare costs?"
**Prescribed Workflows**: information_retrieval, strategy
**Confidence Score**: 0.85
**Reasoning**: User needs information about their deductible (information_retrieval) and then guidance on cost-saving strategies (strategy). Information should be gathered first to inform the strategy.
**Execution Order**: information_retrieval, strategy

## Example 4
**User Query**: "Does my plan cover physical therapy and how do I get pre-authorization?"
**Prescribed Workflows**: information_retrieval, strategy
**Confidence Score**: 0.9
**Reasoning**: User needs to know if physical therapy is covered (information_retrieval) and then guidance on the pre-authorization process (strategy). Coverage information is needed first to determine next steps.
**Execution Order**: information_retrieval, strategy

## Example 5
**User Query**: "What are my prescription drug benefits?"
**Prescribed Workflows**: information_retrieval
**Confidence Score**: 0.95
**Reasoning**: User needs specific information about prescription drug coverage from their insurance documents. This is a direct information retrieval request.
**Execution Order**: information_retrieval

## Example 6
**User Query**: "How can I maximize my benefits and minimize out-of-pocket costs?"
**Prescribed Workflows**: strategy
**Confidence Score**: 0.8
**Reasoning**: User needs strategic guidance on benefit optimization and cost management. This requires planning and decision-making support rather than simple information lookup.
**Execution Order**: strategy

## Example 7
**User Query**: "What's the difference between in-network and out-of-network coverage?"
**Prescribed Workflows**: information_retrieval
**Confidence Score**: 0.9
**Reasoning**: User needs educational information about network coverage differences. This requires retrieving and explaining policy details from insurance documents.
**Execution Order**: information_retrieval

## Example 8
**User Query**: "What are my mental health benefits and how do I get access to a therapist?"
**Prescribed Workflows**: information_retrieval, strategy
**Confidence Score**: 0.9
**Reasoning**: User needs information about mental health coverage (information_retrieval) and then guidance on finding a therapist (strategy). Coverage information is needed first to understand what's available.
**Execution Order**: information_retrieval, strategy

## Example 9
**User Query**: "How do I appeal a denied claim?"
**Prescribed Workflows**: []
**Confidence Score**: 0.9
**Reasoning**: Claim support is not a workflow that we currently support.
**Execution Order**: []

## Example 10
**User Query**: "What's my annual maximum and how much have I used so far?"
**Prescribed Workflows**: information_retrieval
**Confidence Score**: 0.95
**Reasoning**: User needs specific information about their annual maximum and current usage. This is a direct information retrieval request from insurance documents.
**Execution Order**: information_retrieval

## Example 11
**User Query**: "I'm confused about my insurance"
**Prescribed Workflows**: information_retrieval
**Confidence Score**: 0.6
**Reasoning**: User has a vague query about insurance confusion. Default to information_retrieval to help them understand their coverage, but with lower confidence due to lack of specificity.
**Execution Order**: information_retrieval 