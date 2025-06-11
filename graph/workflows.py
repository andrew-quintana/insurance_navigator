# graph/workflows.py - Your Workflow Library

from .base_workflow import BaseWorkflow

class StrategyWorkflow(BaseWorkflow):
    """Complete provider/service access strategy workflow"""
    
    def define_nodes(self):
        return [
            {"name": "security_check", "method": "_security_check_node"},
            {"name": "navigator_analysis", "method": "_navigator_analysis_node"},
            {"name": "task_requirements", "method": "_task_requirements_node"},
            {"name": "service_strategy", "method": "_service_strategy_node"},
            {"name": "regulatory_check", "method": "_regulatory_check_node"},
            {"name": "chat_response", "method": "_chat_response_node"}
        ]
        
    def define_edges(self):
        return [
            {"from": "security_check", "to": "navigator_analysis"},
            {"from": "navigator_analysis", "to": "task_requirements"},
            {
                "from": "task_requirements",
                "type": "conditional", 
                "decision_method": "_task_requirements_decision",
                "conditions": {
                    "insufficient_info": "chat_response",
                    "continue": "service_strategy",
                    "urgent": "service_strategy"
                }
            },
            {"from": "service_strategy", "to": "regulatory_check"},
            {"from": "regulatory_check", "to": "chat_response"}
        ]

class NavigatorWorkflow(BaseWorkflow):
    """Simple Q&A workflow through navigator only"""
    
    def define_nodes(self):
        return [
            {"name": "security_check", "method": "_security_check_node"},
            {"name": "navigator_qa", "method": "_navigator_qa_node"},
            {"name": "chat_response", "method": "_chat_response_node"}
        ]
        
    def define_edges(self):
        return [
            {"from": "security_check", "to": "navigator_qa"},
            {"from": "navigator_qa", "to": "chat_response"}
        ]

# Add your supervisor-based workflows here as you develop them
class SupervisorWorkflow(BaseWorkflow):
    """Future supervisor-based workflow"""
    # Will implement as you develop the supervisor agents
    pass