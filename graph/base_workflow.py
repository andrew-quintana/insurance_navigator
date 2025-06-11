"""
Base Workflow Class for Class-Based Workflow Definitions

This module provides the foundation for defining workflows as classes,
allowing for better separation of concerns, testability, and maintainability.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph
import logging

logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """
    Abstract base class for defining workflows.
    
    Each workflow should inherit from this class and implement the required methods
    to define nodes, edges, and any custom logic.
    """
    
    def __init__(self, orchestrator, name: Optional[str] = None):
        """
        Initialize the workflow.
        
        Args:
            orchestrator: The AgentOrchestrator instance containing agent methods
            name: Optional name for the workflow (defaults to class name)
        """
        self.orchestrator = orchestrator
        self.name = name or self.__class__.__name__
        self.graph = None
        self._compiled_graph = None
        
    @abstractmethod
    def define_nodes(self) -> List[Dict[str, Any]]:
        """
        Define the nodes for this workflow.
        
        Returns:
            List of node definitions with the following structure:
            [
                {
                    "name": "node_name",
                    "method": "_method_name_on_orchestrator",
                    "description": "Optional description"
                },
                ...
            ]
        """
        pass
        
    @abstractmethod  
    def define_edges(self) -> List[Dict[str, Any]]:
        """
        Define the edges for this workflow.
        
        Returns:
            List of edge definitions with the following structure:
            [
                {
                    "from": "source_node",
                    "to": "target_node"
                },
                {
                    "from": "source_node",
                    "type": "conditional",
                    "decision_method": "_decision_method_name",
                    "conditions": {
                        "condition_key": "target_node",
                        ...
                    }
                },
                ...
            ]
        """
        pass
        
    def get_entry_point(self) -> str:
        """
        Get the entry point node for this workflow.
        
        Returns:
            Name of the first node to execute (defaults to first node in define_nodes)
        """
        nodes = self.define_nodes()
        if not nodes:
            raise ValueError(f"Workflow {self.name} has no nodes defined")
        return nodes[0]["name"]
        
    def validate_definition(self) -> bool:
        """
        Validate the workflow definition for consistency.
        
        Returns:
            True if valid, raises ValueError if invalid
        """
        nodes = self.define_nodes()
        edges = self.define_edges()
        
        if not nodes:
            raise ValueError(f"Workflow {self.name} must define at least one node")
            
        node_names = {node["name"] for node in nodes}
        
        # Validate all edge references exist as nodes
        for edge in edges:
            if edge["from"] not in node_names:
                raise ValueError(f"Edge references unknown source node: {edge['from']}")
                
            if edge.get("type") == "conditional":
                # Validate conditional edge targets
                conditions = edge.get("conditions", {})
                for target in conditions.values():
                    if target not in node_names:
                        raise ValueError(f"Conditional edge references unknown target node: {target}")
            else:
                # Validate simple edge target
                if edge["to"] not in node_names:
                    raise ValueError(f"Edge references unknown target node: {edge['to']}")
                    
        # Validate all nodes have corresponding methods on orchestrator
        for node in nodes:
            method_name = node["method"]
            if not hasattr(self.orchestrator, method_name):
                raise ValueError(f"Node {node['name']} references unknown orchestrator method: {method_name}")
                
        return True
        
    def build(self) -> StateGraph:
        """
        Build and compile the LangGraph StateGraph from the workflow definition.
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Validate before building
        self.validate_definition()
        
        # Create new StateGraph
        graph = StateGraph(dict)
        
        # Add nodes
        nodes = self.define_nodes()
        for node in nodes:
            method = getattr(self.orchestrator, node["method"])
            graph.add_node(node["name"], method)
            logger.debug(f"Added node {node['name']} -> {node['method']}")
            
        # Add edges
        edges = self.define_edges()
        for edge in edges:
            if edge.get("type") == "conditional":
                # Add conditional edge
                decision_method = getattr(self.orchestrator, edge["decision_method"])
                conditions = edge["conditions"]
                
                graph.add_conditional_edges(
                    edge["from"],
                    decision_method,
                    conditions
                )
                logger.debug(f"Added conditional edge from {edge['from']} with conditions: {list(conditions.keys())}")
            else:
                # Add simple edge
                graph.add_edge(edge["from"], edge["to"])
                logger.debug(f"Added edge {edge['from']} -> {edge['to']}")
                
        # Set entry point
        entry_point = self.get_entry_point()
        graph.set_entry_point(entry_point)
        logger.debug(f"Set entry point: {entry_point}")
        
        # Compile and cache
        self.graph = graph
        self._compiled_graph = graph.compile()
        
        logger.info(f"Successfully built workflow: {self.name}")
        return self._compiled_graph
        
    def get_compiled_graph(self) -> StateGraph:
        """
        Get the compiled graph, building it if necessary.
        
        Returns:
            Compiled StateGraph
        """
        if self._compiled_graph is None:
            return self.build()
        return self._compiled_graph
        
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Get information about this workflow.
        
        Returns:
            Dictionary with workflow metadata
        """
        nodes = self.define_nodes()
        edges = self.define_edges()
        
        return {
            "name": self.name,
            "class": self.__class__.__name__,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "entry_point": self.get_entry_point(),
            "nodes": [node["name"] for node in nodes],
            "has_conditional_edges": any(edge.get("type") == "conditional" for edge in edges)
        } 