# Patient Navigator Supervisor Workflow - API Documentation

**Version**: 1.0.0  
**Date**: August 5, 2025  
**Status**: Production Ready  

## Overview

The Patient Navigator Supervisor Workflow provides intelligent orchestration between workflow prescription and document availability checking to route users through appropriate healthcare access paths. This API documentation covers the complete LangGraph workflow implementation for the MVP.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Input/Output Models](#inputoutput-models)
3. [Workflow Execution](#workflow-execution)
4. [Configuration](#configuration)
5. [Error Handling](#error-handling)
6. [Usage Examples](#usage-examples)
7. [Performance Guidelines](#performance-guidelines)

## Core Classes

### SupervisorWorkflow

The main LangGraph workflow orchestrator that coordinates workflow prescription and document availability checking.

```python
class SupervisorWorkflow:
    """
    LangGraph supervisor workflow for patient navigator orchestration.
    
    This workflow coordinates workflow prescription and document availability
    checking to make routing decisions for user requests.
    
    Attributes:
        use_mock (bool): If True, use mock responses for testing
        workflow_agent (WorkflowPrescriptionAgent): Agent for workflow prescription
        document_checker (DocumentAvailabilityChecker): Document availability checker
        graph (StateGraph): Compiled LangGraph workflow
    """
```

#### Methods

##### `__init__(use_mock: bool = False)`

Initialize the supervisor workflow.

**Parameters:**
- `use_mock` (bool): If True, use mock responses for testing

**Example:**
```python
# Production mode
workflow = SupervisorWorkflow(use_mock=False)

# Development/testing mode
workflow = SupervisorWorkflow(use_mock=True)
```

##### `async execute(input_data: SupervisorWorkflowInput) -> SupervisorWorkflowOutput`

Execute the complete supervisor workflow.

**Parameters:**
- `input_data` (SupervisorWorkflowInput): User query and context

**Returns:**
- `SupervisorWorkflowOutput`: Structured workflow results

**Example:**
```python
input_data = SupervisorWorkflowInput(
    user_query="What is my copay for doctor visits?",
    user_id="user_123"
)
result = await workflow.execute(input_data)
```

### WorkflowPrescriptionAgent

LLM-based agent for prescribing appropriate workflows based on user queries.

```python
class WorkflowPrescriptionAgent(BaseAgent):
    """
    Agent for prescribing workflows based on user queries.
    
    Uses LLM-based classification with few-shot learning to determine
    which workflows are appropriate for a given user request.
    
    Attributes:
        name (str): Agent name
        prompt (str): System prompt for workflow classification
        output_schema (Type): Pydantic model for structured output
        mock (bool): Mock mode for testing
    """
```

#### Methods

##### `async prescribe_workflows(user_query: str) -> WorkflowPrescriptionResult`

Prescribe workflows for a user query.

**Parameters:**
- `user_query` (str): Natural language user query

**Returns:**
- `WorkflowPrescriptionResult`: Prescribed workflows with confidence scores

**Example:**
```python
result = await agent.prescribe_workflows("What is my copay for doctor visits?")
print(f"Prescribed workflows: {result.prescribed_workflows}")
print(f"Confidence: {result.confidence_score}")
```

### DocumentAvailabilityChecker

Deterministic checker for document availability in Supabase storage.

```python
class DocumentAvailabilityChecker:
    """
    Deterministic document availability checker.
    
    Checks document availability in Supabase storage without LLM processing,
    providing fast and reliable document presence verification.
    
    Attributes:
        supabase_client: Supabase client for database queries
        use_mock (bool): Mock mode for testing
    """
```

#### Methods

##### `async check_availability(workflows: List[WorkflowType], user_id: str) -> DocumentAvailabilityResult`

Check document availability for prescribed workflows.

**Parameters:**
- `workflows` (List[WorkflowType]): List of prescribed workflows
- `user_id` (str): User identifier for document access

**Returns:**
- `DocumentAvailabilityResult`: Document availability status

**Example:**
```python
result = await checker.check_availability(
    workflows=[WorkflowType.INFORMATION_RETRIEVAL],
    user_id="user_123"
)
print(f"Ready: {result.is_ready}")
print(f"Missing: {result.missing_documents}")
```

## Input/Output Models

### SupervisorWorkflowInput

Input model for supervisor workflow requests.

```python
class SupervisorWorkflowInput(BaseModel):
    """
    Input model for supervisor workflow requests.
    
    This represents the structured input from users or other system components,
    containing the user query and context information.
    """
    
    user_query: str = Field(
        description="The user's natural language query about healthcare access"
    )
    
    user_id: str = Field(
        description="User identifier for access control and document retrieval"
    )
    
    workflow_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context from previous workflow executions"
    )
```

**Example:**
```python
input_data = SupervisorWorkflowInput(
    user_query="What is my copay for doctor visits?",
    user_id="user_123",
    workflow_context={"previous_workflows": ["information_retrieval"]}
)
```

### SupervisorWorkflowOutput

Output model for supervisor workflow responses.

```python
class SupervisorWorkflowOutput(BaseModel):
    """
    Output model for supervisor workflow responses.
    
    This provides structured output with routing decisions, prescribed workflows,
    document availability, and next steps for the user.
    """
    
    routing_decision: Literal["PROCEED", "COLLECT"] = Field(
        description="Final routing decision for the user request"
    )
    
    prescribed_workflows: List[WorkflowType] = Field(
        description="Workflows prescribed for the user request"
    )
    
    execution_order: List[WorkflowType] = Field(
        description="Deterministic execution order for prescribed workflows"
    )
    
    document_availability: DocumentAvailabilityResult = Field(
        description="Results from document availability checking"
    )
    
    workflow_prescription: WorkflowPrescriptionResult = Field(
        description="Results from workflow prescription agent"
    )
    
    next_steps: List[str] = Field(
        description="List of next steps for the user"
    )
    
    confidence_score: float = Field(
        description="Overall confidence score for the routing decision (0.0-1.0)"
    )
    
    processing_time: float = Field(
        description="Total processing time in seconds"
    )
```

**Example:**
```python
output = SupervisorWorkflowOutput(
    routing_decision="PROCEED",
    prescribed_workflows=[WorkflowType.INFORMATION_RETRIEVAL],
    execution_order=[WorkflowType.INFORMATION_RETRIEVAL],
    document_availability=DocumentAvailabilityResult(is_ready=True),
    workflow_prescription=WorkflowPrescriptionResult(...),
    next_steps=["Proceeding with information retrieval workflow"],
    confidence_score=0.85,
    processing_time=1.2
)
```

### WorkflowPrescriptionResult

Result from workflow prescription agent.

```python
class WorkflowPrescriptionResult(BaseModel):
    """
    Result from workflow prescription agent with confidence scoring.
    """
    
    prescribed_workflows: List[WorkflowType] = Field(
        description="List of workflows prescribed for the user request"
    )
    
    confidence_score: float = Field(
        description="Confidence score for the prescription (0.0-1.0)"
    )
    
    reasoning: str = Field(
        description="Explanation of why these workflows were prescribed"
    )
    
    execution_order: List[WorkflowType] = Field(
        description="Deterministic execution order for prescribed workflows"
    )
```

### DocumentAvailabilityResult

Result from document availability checking.

```python
class DocumentAvailabilityResult(BaseModel):
    """
    Result from document availability checking.
    """
    
    is_ready: bool = Field(
        description="Whether all required documents are available for workflow execution"
    )
    
    available_documents: List[str] = Field(
        description="List of document types that are available"
    )
    
    missing_documents: List[str] = Field(
        description="List of document types that are missing"
    )
    
    document_status: Dict[str, bool] = Field(
        description="Mapping of document types to availability status"
    )
```

## Workflow Execution

### LangGraph Workflow Structure

The supervisor workflow follows a sequential LangGraph structure:

```
prescribe_workflow → check_documents → route_decision → [execute_workflows] → end
```

### Node Methods

#### `_prescribe_workflow_node(state: SupervisorState) -> SupervisorState`

Executes workflow prescription using the WorkflowPrescriptionAgent.

**Parameters:**
- `state` (SupervisorState): Current workflow state

**Returns:**
- `SupervisorState`: Updated state with prescribed workflows

#### `_check_documents_node(state: SupervisorState) -> SupervisorState`

Checks document availability using the DocumentAvailabilityChecker.

**Parameters:**
- `state` (SupervisorState): Current workflow state

**Returns:**
- `SupervisorState`: Updated state with document availability results

#### `_route_decision_node(state: SupervisorState) -> SupervisorState`

Makes routing decisions based on workflow prescription and document availability.

**Parameters:**
- `state` (SupervisorState): Current workflow state

**Returns:**
- `SupervisorState`: Updated state with routing decision

#### `_execute_information_retrieval_node(state: SupervisorState) -> SupervisorState`

Executes the information retrieval workflow.

**Parameters:**
- `state` (SupervisorState): Current workflow state

**Returns:**
- `SupervisorState`: Updated state with workflow execution results

#### `_execute_strategy_node(state: SupervisorState) -> SupervisorState`

Executes the strategy workflow.

**Parameters:**
- `state` (SupervisorState): Current workflow state

**Returns:**
- `SupervisorState`: Updated state with workflow execution results

## Configuration

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# LLM Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key

# Workflow Configuration
SUPERVISOR_WORKFLOW_MOCK_MODE=false
SUPERVISOR_WORKFLOW_TIMEOUT=30
SUPERVISOR_WORKFLOW_MAX_RETRIES=3

# Performance Configuration
DOCUMENT_CHECK_TIMEOUT=500
WORKFLOW_PRESCRIPTION_TIMEOUT=1000
```

### Mock Mode Configuration

```python
# Enable mock mode for testing
workflow = SupervisorWorkflow(use_mock=True)

# Mock mode provides consistent test responses
# - WorkflowPrescriptionAgent returns predefined prescriptions
# - DocumentAvailabilityChecker returns mock availability results
# - Workflow execution nodes return mock results
```

## Error Handling

### Error Types

#### WorkflowPrescriptionError
Raised when workflow prescription fails.

```python
class WorkflowPrescriptionError(Exception):
    """Error during workflow prescription."""
    pass
```

#### DocumentAvailabilityError
Raised when document availability checking fails.

```python
class DocumentAvailabilityError(Exception):
    """Error during document availability checking."""
    pass
```

#### WorkflowExecutionError
Raised when workflow execution fails.

```python
class WorkflowExecutionError(Exception):
    """Error during workflow execution."""
    pass
```

### Error Handling Strategy

The workflow implements comprehensive error handling with graceful degradation:

1. **LLM Failures**: Fallback to default workflow prescription
2. **Database Failures**: Fallback to mock document availability
3. **Workflow Component Failures**: Skip execution with error logging
4. **Network Failures**: Retry with exponential backoff

### Error Response Format

```python
{
    "routing_decision": "COLLECT",
    "error_message": "Workflow prescription failed: LLM service unavailable",
    "fallback_used": True,
    "processing_time": 0.5
}
```

## Usage Examples

### Basic Workflow Execution

```python
from agents.patient_navigator.supervisor import SupervisorWorkflow, SupervisorWorkflowInput

# Initialize workflow
workflow = SupervisorWorkflow(use_mock=False)

# Create input
input_data = SupervisorWorkflowInput(
    user_query="What is my copay for doctor visits?",
    user_id="user_123"
)

# Execute workflow
result = await workflow.execute(input_data)

# Process results
print(f"Routing decision: {result.routing_decision}")
print(f"Prescribed workflows: {result.prescribed_workflows}")
print(f"Processing time: {result.processing_time}s")
```

### Mock Mode Testing

```python
# Initialize with mock mode
workflow = SupervisorWorkflow(use_mock=True)

# Test various scenarios
test_queries = [
    "What is my copay?",
    "How do I find a doctor?",
    "What are my benefits?"
]

for query in test_queries:
    input_data = SupervisorWorkflowInput(
        user_query=query,
        user_id="test_user"
    )
    result = await workflow.execute(input_data)
    print(f"Query: {query}")
    print(f"Decision: {result.routing_decision}")
    print(f"Workflows: {result.prescribed_workflows}")
```

### Error Handling Example

```python
try:
    result = await workflow.execute(input_data)
    if result.error_message:
        print(f"Warning: {result.error_message}")
        print(f"Fallback used: {result.fallback_used}")
except Exception as e:
    print(f"Workflow execution failed: {e}")
    # Handle critical errors
```

## Performance Guidelines

### Performance Targets

- **Total Execution Time**: <2 seconds
- **Document Checking**: <500ms per document
- **Workflow Prescription**: <1 second
- **Concurrent Requests**: Support for 100+ simultaneous workflows

### Optimization Strategies

1. **Async Execution**: All workflow nodes are async for non-blocking operation
2. **Connection Pooling**: Supabase client uses connection pooling
3. **Caching**: Mock mode provides fast responses for testing
4. **Parallel Processing**: Document availability checks can be parallelized

### Monitoring

```python
# Performance tracking is built into the workflow
result = await workflow.execute(input_data)
print(f"Total time: {result.processing_time}s")
print(f"Node performance: {result.node_performance}")
```

### Scaling Considerations

1. **Horizontal Scaling**: Stateless design enables load balancing
2. **Resource Management**: Proper cleanup of connections and resources
3. **Memory Optimization**: Efficient state management in LangGraph
4. **Database Optimization**: Indexed queries for document availability

## Security Considerations

### HIPAA Compliance

- **Audit Logging**: All workflow decisions are logged with user_id
- **Data Minimization**: Only necessary document metadata is accessed
- **Access Control**: Supabase RLS enforces user data isolation
- **Secure Error Handling**: No sensitive information in error messages

### Authentication & Authorization

- **User Authentication**: Integration with existing authentication system
- **Document Access**: Respects existing document access permissions
- **API Security**: Secure endpoints following existing patterns
- **Token Management**: Secure handling of authentication tokens

## Troubleshooting

### Common Issues

1. **LLM Service Unavailable**
   - Check ANTHROPIC_API_KEY configuration
   - Verify network connectivity
   - Use mock mode for testing

2. **Supabase Connection Issues**
   - Verify SUPABASE_URL and SUPABASE_ANON_KEY
   - Check database connectivity
   - Review RLS policies

3. **Workflow Component Failures**
   - Check component availability
   - Verify import paths
   - Review error logs

4. **Performance Issues**
   - Monitor execution times
   - Check resource usage
   - Review database query performance

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("supervisor_workflow").setLevel(logging.DEBUG)

# Execute with detailed logging
result = await workflow.execute(input_data)
```

## Version History

- **v1.0.0** (2025-08-05): Initial MVP release with LangGraph workflow orchestration
- **v1.0.1** (2025-08-05): Performance optimizations and error handling improvements

## Support

For technical support and questions:

1. **Documentation**: Review this API documentation
2. **Testing**: Use mock mode for development and testing
3. **Logging**: Check application logs for detailed error information
4. **Monitoring**: Use built-in performance tracking for optimization

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-08-05  
**Status**: Production Ready 