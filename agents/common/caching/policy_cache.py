# Structured Policy Data Caching - Phase 7
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class PolicyCache:
    """Structured caching system for insurance policy data with quick field retrieval."""
    
    def __init__(self):
        self.policy_data = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=24)
        self.quick_lookup = {}  # For common field lookups
    
    def get_policy_structure(self) -> Dict[str, Any]:
        """Standard JSON structure for policy data with common fields and caveats."""
        return {
            "basic_info": {
                "policy_number": "",
                "plan_name": "",
                "plan_type": "",  # HMO, PPO, EPO, etc.
                "effective_date": "",
                "expiration_date": "",
                "premium": 0.0,
                "carrier": "",
                "group_number": ""
            },
            "financial": {
                "deductible": {
                    "individual": 0.0,
                    "family": 0.0,
                    "remaining": 0.0,
                    "caveats": [
                        "Deductible applies to most services except preventive care",
                        "Some services may have separate deductibles"
                    ]
                },
                "out_of_pocket_max": {
                    "individual": 0.0,
                    "family": 0.0,
                    "remaining": 0.0,
                    "caveats": [
                        "Includes deductibles, copays, and coinsurance",
                        "Does not include premiums or out-of-network costs"
                    ]
                },
                "copays": {
                    "primary_care": 0.0,
                    "specialist": 0.0,
                    "emergency": 0.0,
                    "urgent_care": 0.0,
                    "mental_health": 0.0,
                    "prescription": {
                        "generic": 0.0,
                        "brand": 0.0,
                        "specialty": 0.0
                    },
                    "caveats": [
                        "Copays may not apply until deductible is met",
                        "Emergency room copay may be waived if admitted"
                    ]
                },
                "coinsurance": {
                    "in_network": 0.8,  # 80% coverage
                    "out_of_network": 0.6,  # 60% coverage
                    "caveats": [
                        "Coinsurance applies after deductible is met",
                        "Preventive care typically covered at 100%"
                    ]
                }
            },
            "coverage": {
                "medical": {
                    "covered": True,
                    "percentage": 80,
                    "limitations": [],
                    "caveats": ["Subject to deductible and coinsurance"]
                },
                "dental": {
                    "covered": False,
                    "percentage": 0,
                    "limitations": [],
                    "caveats": ["May require separate dental plan"]
                },
                "vision": {
                    "covered": False,
                    "percentage": 0,
                    "limitations": [],
                    "caveats": ["May require separate vision plan"]
                },
                "prescription": {
                    "covered": True,
                    "percentage": 80,
                    "formulary_tiers": ["generic", "brand", "specialty"],
                    "caveats": [
                        "Coverage varies by formulary tier",
                        "Prior authorization may be required for some medications"
                    ]
                },
                "mental_health": {
                    "covered": True,
                    "percentage": 80,
                    "session_limits": 0,
                    "caveats": ["Parity with medical benefits required by law"]
                }
            },
            "network": {
                "provider_network": "",
                "out_of_network_coverage": False,
                "emergency_coverage": True,
                "provider_directory_url": "",
                "caveats": [
                    "Always verify provider is in-network before service",
                    "Out-of-network costs may not count toward deductible"
                ]
            },
            "special_benefits": {
                "preventive_care": {
                    "covered": True,
                    "percentage": 100,
                    "caveats": ["No cost sharing for ACA-required preventive services"]
                },
                "telemedicine": {
                    "covered": False,
                    "percentage": 0,
                    "caveats": []
                },
                "wellness_programs": {
                    "available": False,
                    "description": "",
                    "caveats": []
                }
            },
            "claim_info": {
                "how_to_file": "",
                "claim_address": "",
                "phone_number": "",
                "online_portal": "",
                "typical_processing_time": "14-21 days",
                "caveats": [
                    "Claims must be filed within timely filing limits",
                    "Pre-authorization required for some services"
                ]
            },
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "manual_entry",
                "confidence_score": 1.0,
                "verification_status": "pending"
            }
        }
    
    def cache_policy_data(self, user_id: str, policy_data: Dict[str, Any]):
        """Cache structured policy data for quick retrieval."""
        # Ensure the policy data follows our structure
        structured_data = self._validate_and_structure_policy(policy_data)
        
        self.policy_data[user_id] = structured_data
        self.cache_expiry[user_id] = datetime.utcnow() + self.cache_duration
        
        # Create quick lookup entries for common queries
        self._build_quick_lookup(user_id, structured_data)
        
        logger.info(f"Cached policy data for user {user_id}")
    
    def get_cached_policy(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached policy data if not expired."""
        if user_id not in self.policy_data:
            return None
        
        if datetime.utcnow() > self.cache_expiry.get(user_id, datetime.min):
            # Cache expired
            self._remove_user_cache(user_id)
            return None
        
        return self.policy_data[user_id]
    
    def get_quick_answer(self, user_id: str, query_type: str) -> Optional[Dict[str, Any]]:
        """Get quick answers for common policy questions with caveats."""
        if user_id not in self.quick_lookup:
            return None
        
        lookup = self.quick_lookup[user_id]
        
        # Map common queries to structured responses
        query_mappings = {
            "deductible": {
                "field": "financial.deductible",
                "answer_template": "Your deductible is ${individual} individual / ${family} family"
            },
            "copay": {
                "field": "financial.copays",
                "answer_template": "Primary care: ${primary_care}, Specialist: ${specialist}"
            },
            "out_of_pocket": {
                "field": "financial.out_of_pocket_max",
                "answer_template": "Your out-of-pocket maximum is ${individual} individual / ${family} family"
            },
            "prescription_copay": {
                "field": "financial.copays.prescription",
                "answer_template": "Generic: ${generic}, Brand: ${brand}, Specialty: ${specialty}"
            },
            "dental_coverage": {
                "field": "coverage.dental",
                "answer_template": "Dental coverage: ${covered} at ${percentage}%"
            },
            "vision_coverage": {
                "field": "coverage.vision", 
                "answer_template": "Vision coverage: ${covered} at ${percentage}%"
            }
        }
        
        if query_type not in query_mappings:
            return None
        
        mapping = query_mappings[query_type]
        field_path = mapping["field"]
        
        # Navigate to the requested field
        value = self._get_nested_value(lookup, field_path)
        if not value:
            return None
        
        # Include caveats if available
        caveats = value.get("caveats", [])
        
        return {
            "field": query_type,
            "value": value,
            "caveats": caveats,
            "answer_template": mapping["answer_template"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def update_policy_field(self, user_id: str, field_path: str, new_value: Any, caveats: List[str] = None):
        """Update a specific field in cached policy data."""
        if user_id not in self.policy_data:
            return False
        
        policy = self.policy_data[user_id]
        
        # Navigate to parent and update field
        parts = field_path.split('.')
        current = policy
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Update the final field
        final_field = parts[-1]
        if isinstance(current.get(final_field), dict):
            if isinstance(new_value, dict):
                current[final_field].update(new_value)
            else:
                current[final_field]["value"] = new_value
        else:
            current[final_field] = new_value
        
        # Add caveats if provided
        if caveats and isinstance(current.get(final_field), dict):
            current[final_field]["caveats"] = caveats
        
        # Update timestamp
        policy["metadata"]["last_updated"] = datetime.utcnow().isoformat()
        
        # Rebuild quick lookup
        self._build_quick_lookup(user_id, policy)
        
        return True
    
    def _validate_and_structure_policy(self, policy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and ensure policy data follows our standard structure."""
        template = self.get_policy_structure()
        
        # Merge provided data with template, keeping template structure
        return self._deep_merge(template, policy_data)
    
    def _deep_merge(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge data into template structure."""
        result = template.copy()
        
        for key, value in data.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _build_quick_lookup(self, user_id: str, policy_data: Dict[str, Any]):
        """Build quick lookup cache for common queries."""
        self.quick_lookup[user_id] = policy_data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        current = data
        for key in path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _remove_user_cache(self, user_id: str):
        """Remove all cached data for a user."""
        if user_id in self.policy_data:
            del self.policy_data[user_id]
        if user_id in self.cache_expiry:
            del self.cache_expiry[user_id]
        if user_id in self.quick_lookup:
            del self.quick_lookup[user_id]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cache usage."""
        return {
            "total_cached_policies": len(self.policy_data),
            "cache_hit_potential": len(self.quick_lookup),
            "cache_duration_hours": self.cache_duration.total_seconds() / 3600,
            "oldest_cache_entry": min(self.cache_expiry.values()) if self.cache_expiry else None
        }

# Global cache instance
policy_cache = PolicyCache()
