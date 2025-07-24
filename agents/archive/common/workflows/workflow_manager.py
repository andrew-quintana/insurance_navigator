# Advanced Multi-Step Workflow Manager - Phase 7
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WorkflowState(Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"

class WorkflowManager:
    """Manages complex multi-step processes for insurance navigation."""
    
    def __init__(self):
        self.active_workflows = {}
        self.workflow_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load predefined workflow templates."""
        return {
            "claim_filing": {
                "steps": [
                    "collect_service_type",
                    "collect_date", 
                    "collect_receipt",
                    "verify_details",
                    "submit_claim"
                ],
                "description": "File insurance claim step by step",
                "step_prompts": {
                    "collect_service_type": "What type of medical service was this for? (e.g., doctor visit, prescription, lab work)",
                    "collect_date": "When did this service take place?",
                    "collect_receipt": "Please upload your receipt or bill",
                    "verify_details": "Let me verify the details before submitting",
                    "submit_claim": "Submitting your claim now"
                }
            },
            "doctor_search": {
                "steps": [
                    "collect_location",
                    "collect_specialty", 
                    "check_insurance",
                    "provide_options"
                ],
                "description": "Find in-network doctors",
                "step_prompts": {
                    "collect_location": "What area are you looking for a doctor in?",
                    "collect_specialty": "What type of doctor do you need? (e.g., primary care, cardiologist, dermatologist)",
                    "check_insurance": "Let me check which doctors accept your insurance",
                    "provide_options": "Here are your in-network options"
                }
            },
            "benefit_verification": {
                "steps": [
                    "collect_service",
                    "check_coverage",
                    "calculate_costs",
                    "provide_summary"
                ],
                "description": "Verify insurance benefits for a service",
                "step_prompts": {
                    "collect_service": "What medical service do you need coverage information for?",
                    "check_coverage": "Checking your policy coverage",
                    "calculate_costs": "Calculating your expected costs",
                    "provide_summary": "Here's your benefit summary"
                }
            }
        }
    
    async def start_workflow(self, workflow_type: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """Start a new workflow for a user."""
        workflow_id = f"{user_id}_{session_id}_{workflow_type}_{int(datetime.utcnow().timestamp())}"
        
        if workflow_type not in self.workflow_templates:
            return {"error": f"Unknown workflow type: {workflow_type}"}
        
        template = self.workflow_templates[workflow_type]
        workflow = {
            "id": workflow_id,
            "type": workflow_type,
            "user_id": user_id,
            "session_id": session_id,
            "state": WorkflowState.STARTED.value,
            "current_step": 0,
            "steps": template["steps"],
            "step_prompts": template["step_prompts"],
            "collected_data": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        self.active_workflows[workflow_id] = workflow
        
        first_step = workflow["steps"][0]
        first_prompt = workflow["step_prompts"].get(first_step, f"Starting step: {first_step}")
        
        return {
            "workflow_id": workflow_id,
            "next_step": first_step,
            "prompt": first_prompt,
            "progress": f"1/{len(workflow['steps'])}"
        }
    
    async def process_step(self, workflow_id: str, user_input: str) -> Dict[str, Any]:
        """Process the current step of a workflow."""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.active_workflows[workflow_id]
        current_step_index = workflow["current_step"]
        
        if current_step_index >= len(workflow["steps"]):
            return {"completed": True, "message": "Workflow already completed"}
        
        current_step = workflow["steps"][current_step_index]
        
        # Store the user input for current step
        workflow["collected_data"][current_step] = user_input
        workflow["current_step"] += 1
        workflow["updated_at"] = datetime.utcnow().isoformat()
        workflow["state"] = WorkflowState.IN_PROGRESS.value
        
        # Check if workflow is complete
        if workflow["current_step"] >= len(workflow["steps"]):
            workflow["state"] = WorkflowState.COMPLETED.value
            return {
                "completed": True,
                "message": "Workflow completed successfully!",
                "data": workflow["collected_data"],
                "workflow_type": workflow["type"]
            }
        
        # Get next step
        next_step = workflow["steps"][workflow["current_step"]]
        next_prompt = workflow["step_prompts"].get(next_step, f"Please provide: {next_step}")
        
        return {
            "next_step": next_step,
            "prompt": next_prompt,
            "progress": f"{workflow['current_step'] + 1}/{len(workflow['steps'])}",
            "collected_so_far": workflow["collected_data"]
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the current status of a workflow."""
        if workflow_id not in self.active_workflows:
            return {"error": "Workflow not found"}
        
        workflow = self.active_workflows[workflow_id]
        return {
            "id": workflow_id,
            "type": workflow["type"],
            "state": workflow["state"],
            "progress": f"{workflow['current_step']}/{len(workflow['steps'])}",
            "current_step": workflow["steps"][workflow["current_step"]] if workflow["current_step"] < len(workflow["steps"]) else "completed",
            "collected_data": workflow["collected_data"]
        }
    
    def list_workflow_types(self) -> List[str]:
        """List available workflow types."""
        return list(self.workflow_templates.keys())
    
    def cleanup_completed_workflows(self, hours_old: int = 24):
        """Clean up workflows older than specified hours."""
        current_time = datetime.utcnow()
        to_remove = []
        
        for workflow_id, workflow in self.active_workflows.items():
            created_time = datetime.fromisoformat(workflow["created_at"])
            age_hours = (current_time - created_time).total_seconds() / 3600
            
            if age_hours > hours_old and workflow["state"] == WorkflowState.COMPLETED.value:
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.active_workflows[workflow_id]
        
        return len(to_remove)
