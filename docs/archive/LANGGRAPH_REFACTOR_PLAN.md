# LangGraph Prototyping Studio Refactoring Plan

## Goal
Refactor the prototyping studio to use **exact LangGraph implementation** matching `agent_orchestrator.py` for authentic workflow prototyping.

## Current vs Target Architecture

### Current (Simple Python Classes)
```python
class WorkflowStep:
    agent: AgentPrototype
    condition: Optional[Callable] = None

class WorkflowPrototype:
    def __init__(self):
        self.steps = []
        
    def execute(self, input_data):
        # Simple while loop execution
```

### Target (LangGraph Exact Match)
```python
from langgraph.graph import StateGraph

class WorkflowPrototype:
    def __init__(self, name: str):
        self.graph = StateGraph(dict)  # Exact match to agent_orchestrator
        self.compiled_workflow = None
        
    def add_agent_node(self, node_name: str, agent: AgentPrototype):
        async def agent_node(state_dict: Dict[str, Any]) -> Dict[str, Any]:
            return await self._execute_agent_node(agent, state_dict)
        self.graph.add_node(node_name, agent_node)
        
    def add_edge(self, from_node: str, to_node: str):
        self.graph.add_edge(from_node, to_node)
        
    def add_conditional_edge(self, source_node: str, condition_func: Callable, path_map: Dict[str, str]):
        self.graph.add_conditional_edges(source_node, condition_func, path_map)
        
    def compile(self):
        self.compiled_workflow = self.graph.compile()
        
    async def execute(self, state: Dict[str, Any]):
        return await self.compiled_workflow.ainvoke(state)
```

## Required Refactoring Changes

### 1. **Update Imports in prototyping_studio.py**
```python
# Add LangGraph imports (currently missing)
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
import asyncio
from uuid import uuid4
```

### 2. **Replace WorkflowStep and WorkflowPrototype Classes**

**Remove:**
```python
@dataclass
class WorkflowStep:
    agent: Union[AgentPrototype, str]
    condition: Optional[Callable] = None
    # ... simple step-based logic

class WorkflowPrototype:
    def __init__(self, name: str):
        self.steps = []
        # ... simple execution
```

**Replace With:**
```python
class WorkflowPrototype:
    """LangGraph-based workflow engine matching agent_orchestrator.py patterns."""
    
    def __init__(self, name: str):
        self.name = name
        self.graph = StateGraph(dict)  # Exact match to agent_orchestrator
        self.agents = {}  # Store agents by node name
        self.nodes = []  # Track node order
        self.compiled_workflow = None
        self.execution_log = []
        
    def add_agent_node(self, node_name: str, agent: AgentPrototype):
        """Add an agent as a node to the LangGraph workflow."""
        self.agents[node_name] = agent
        
        async def agent_node(state_dict: Dict[str, Any]) -> Dict[str, Any]:
            return await self._execute_agent_node(node_name, state_dict)
        
        self.graph.add_node(node_name, agent_node)
        self.nodes.append(node_name)
        
    def add_edge(self, from_node: str, to_node: str):
        """Add a simple edge between two nodes."""
        self.graph.add_edge(from_node, to_node)
        
    def add_conditional_edge(self, source_node: str, condition_func: Callable, path_map: Dict[str, str]):
        """Add conditional edges based on a condition function."""
        self.graph.add_conditional_edges(source_node, condition_func, path_map)
        
    def set_entry_point(self, node_name: str):
        """Set the entry point for the workflow."""
        self.graph.set_entry_point(node_name)
        
    def compile(self):
        """Compile the LangGraph workflow."""
        self.compiled_workflow = self.graph.compile()
        
    async def execute(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Execute the LangGraph workflow."""
        # Initialize state like agent_orchestrator
        state = {
            "message": str(input_data),
            "current_data": input_data,
            "workflow_name": self.name,
            "execution_id": uuid4().hex[:8],
            **kwargs
        }
        
        # Execute the workflow
        final_state = await self.compiled_workflow.ainvoke(state)
        return final_state
        
    async def _execute_agent_node(self, node_name: str, state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an agent node and update state."""
        agent = self.agents[node_name]
        current_data = state_dict.get("current_data", state_dict.get("message", ""))
        
        # Execute agent (handle both prototype and existing agents)
        if isinstance(agent, AgentPrototype):
            result = await agent.aprocess(current_data)
        else:
            # Handle existing agents
            result = await agent.process(current_data)
        
        # Update state
        state_dict["current_data"] = result.get('result', result)
        state_dict[f"{node_name}_result"] = result
        
        return state_dict
```

### 3. **Update AgentPrototype for Async Support**

```python
class AgentPrototype:
    def process(self, input_data: Any, use_model: bool = True) -> Dict[str, Any]:
        """Process input data (synchronous wrapper)."""
        return asyncio.run(self.aprocess(input_data, use_model))
    
    async def aprocess(self, input_data: Any, use_model: bool = True) -> Dict[str, Any]:
        """Process input data with optional model inference (asynchronous)."""
        # ... existing logic but with await self.llm.ainvoke()
```

### 4. **Update PrototypingLab Methods**

```python
class PrototypingLab:
    def quick_workflow(self, name: str) -> WorkflowPrototype:
        """Create a LangGraph-based workflow prototype."""
        workflow = WorkflowPrototype(name)
        self.workflows[name] = workflow
        return workflow
        
    async def run_test_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run test suite with async workflow execution."""
        # ... update to use await workflow.execute()
```

### 5. **Add Helper Methods for Common Patterns**

```python
class WorkflowPrototype:
    def create_agent_orchestrator_style_workflow(self):
        """Create a workflow matching agent_orchestrator.py patterns."""
        # Security → Navigator → Task Requirements → Strategy → Regulatory → Chat
        self.add_agent_node("security_check", self.agents['security'])
        self.add_agent_node("navigator_analysis", self.agents['navigator'])
        self.add_agent_node("task_requirements", self.agents['task_requirements'])
        self.add_agent_node("service_strategy", self.agents['strategy'])
        self.add_agent_node("regulatory_check", self.agents['regulatory'])
        self.add_agent_node("chat_response", self.agents['chat'])
        
        # Add edges
        self.add_edge("security_check", "navigator_analysis")
        self.add_edge("navigator_analysis", "task_requirements")
        
        # Add conditional edge
        self.add_conditional_edge(
            "task_requirements",
            self._task_requirements_decision,
            {
                "insufficient_info": "chat_response",
                "continue": "service_strategy",
                "urgent": "service_strategy"
            }
        )
        
        self.add_edge("service_strategy", "regulatory_check")
        self.add_edge("regulatory_check", "chat_response")
        
        self.set_entry_point("security_check")
        self.compile()
```

## Implementation Steps

### **Step 1: Update prototyping_studio.py**
1. Add LangGraph imports
2. Replace WorkflowStep and WorkflowPrototype classes
3. Add async support to AgentPrototype
4. Update PrototypingLab methods
5. Add orchestrator-style workflow helpers

### **Step 2: Update examples.py**
1. Update workflow examples to use LangGraph patterns
2. Add agent_orchestrator-style workflow examples
3. Update all async execution patterns

### **Step 3: Update notebook**
1. Revert notebook cells to use LangGraph patterns
2. Add examples matching agent_orchestrator workflows
3. Add cells for testing real agent integration
4. Update all workflow creation to use add_node, add_edge, compile patterns

### **Step 4: Add Integration Helpers**
1. Add methods to load existing agents into workflows
2. Add methods to test workflows with real agent configurations
3. Add visualization for LangGraph workflows
4. Add performance testing and comparison tools

## Benefits of This Approach

1. **✅ Exact Production Match** - Workflows prototyped will work identically in production
2. **✅ Real Agent Testing** - Can test actual agent configurations and integrations
3. **✅ LangGraph Features** - Access to full LangGraph debugging, visualization, persistence
4. **✅ Conditional Logic** - Proper conditional routing matching orchestrator patterns
5. **✅ Async Execution** - Authentic async execution patterns for performance testing
6. **✅ State Management** - Proper state handling matching production systems

## Next Actions

1. **Refactor prototyping_studio.py** with LangGraph classes
2. **Update examples.py** with LangGraph workflow patterns  
3. **Update notebook** to use LangGraph patterns
4. **Add agent_orchestrator integration** for testing real workflows
5. **Test compatibility** with existing agent configurations

Would you like me to start implementing these changes? 