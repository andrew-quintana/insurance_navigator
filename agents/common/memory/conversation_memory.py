# Long-term Conversation Memory - Phase 7
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """Manages long-term conversation context and user preferences."""
    
    def __init__(self):
        self.user_memories = {}
        self.session_summaries = {}
        self.user_preferences = {}
        self.memory_limit = 100  # Max interactions per session to keep in memory
    
    async def store_interaction(self, user_id: str, session_id: str, query: str, response: str, metadata: Dict[str, Any]):
        """Store a conversation interaction with metadata."""
        memory_key = f"{user_id}_{session_id}"
        
        if memory_key not in self.user_memories:
            self.user_memories[memory_key] = []
        
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata,
            "query_type": self._classify_query_type(query),
            "response_length": len(response)
        }
        
        self.user_memories[memory_key].append(interaction)
        
        # Keep memory size manageable
        if len(self.user_memories[memory_key]) > self.memory_limit:
            # Remove oldest interactions but keep recent ones
            self.user_memories[memory_key] = self.user_memories[memory_key][-self.memory_limit:]
        
        # Update user preferences based on interaction
        await self._update_user_preferences(user_id, interaction)
    
    async def get_conversation_context(self, user_id: str, session_id: str, limit: int = 5) -> str:
        """Get recent conversation context for continuity."""
        memory_key = f"{user_id}_{session_id}"
        
        if memory_key not in self.user_memories:
            return ""
        
        recent_interactions = self.user_memories[memory_key][-limit:]
        
        if not recent_interactions:
            return ""
        
        context_parts = []
        context_parts.append("RECENT CONVERSATION CONTEXT:")
        
        for interaction in recent_interactions:
            # Use first 150 chars of query and response to keep context manageable
            query_snippet = interaction["query"][:150]
            response_snippet = interaction["response"][:200]
            
            context_parts.append(f"User: {query_snippet}")
            context_parts.append(f"Assistant: {response_snippet}...")
        
        return "\n".join(context_parts)
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get learned user preferences and patterns."""
        if user_id not in self.user_preferences:
            return {}
        
        return self.user_preferences[user_id]
    
    async def extract_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Extract user preferences from all conversation history."""
        user_interactions = []
        
        # Collect all interactions for this user across sessions
        for key, interactions in self.user_memories.items():
            if key.startswith(user_id):
                user_interactions.extend(interactions)
        
        if not user_interactions:
            return {}
        
        # Analyze patterns
        preferences = {
            "common_question_types": {},
            "preferred_communication_style": "standard",
            "frequent_topics": [],
            "interaction_patterns": {
                "avg_session_length": 0,
                "most_active_time": "unknown",
                "total_interactions": len(user_interactions)
            }
        }
        
        # Count question types
        question_types = [interaction.get("query_type", "general") for interaction in user_interactions]
        for q_type in question_types:
            preferences["common_question_types"][q_type] = preferences["common_question_types"].get(q_type, 0) + 1
        
        # Determine preferred communication style based on query patterns
        formal_indicators = sum(1 for interaction in user_interactions if any(word in interaction["query"].lower() for word in ["please", "thank you", "would you", "could you"]))
        casual_indicators = sum(1 for interaction in user_interactions if any(word in interaction["query"].lower() for word in ["what's", "how's", "can't", "won't"]))
        
        if formal_indicators > casual_indicators:
            preferences["preferred_communication_style"] = "formal"
        elif casual_indicators > formal_indicators:
            preferences["preferred_communication_style"] = "casual"
        
        # Store preferences
        self.user_preferences[user_id] = preferences
        
        return preferences
    
    async def summarize_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Create a summary of a conversation session."""
        memory_key = f"{user_id}_{session_id}"
        
        if memory_key not in self.user_memories:
            return {"error": "No session found"}
        
        interactions = self.user_memories[memory_key]
        
        if not interactions:
            return {"error": "No interactions in session"}
        
        summary = {
            "session_id": session_id,
            "user_id": user_id,
            "interaction_count": len(interactions),
            "session_start": interactions[0]["timestamp"],
            "session_end": interactions[-1]["timestamp"],
            "main_topics": [],
            "resolution_status": "completed",
            "user_satisfaction": "unknown"
        }
        
        # Extract main topics from queries
        all_queries = " ".join([interaction["query"] for interaction in interactions])
        topics = self._extract_topics(all_queries)
        summary["main_topics"] = topics
        
        # Store session summary
        self.session_summaries[memory_key] = summary
        
        return summary
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of user query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["claim", "file claim", "submit claim"]):
            return "claim_filing"
        elif any(word in query_lower for word in ["doctor", "physician", "find doctor", "appointment"]):
            return "doctor_search"
        elif any(word in query_lower for word in ["coverage", "covered", "benefit", "deductible", "copay"]):
            return "benefit_inquiry"
        elif any(word in query_lower for word in ["prescription", "medication", "pharmacy", "drug"]):
            return "prescription_help"
        elif any(word in query_lower for word in ["policy", "plan", "insurance"]):
            return "policy_question"
        else:
            return "general"
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text."""
        text_lower = text.lower()
        topics = []
        
        topic_keywords = {
            "claims": ["claim", "billing", "payment", "reimbursement"],
            "doctors": ["doctor", "physician", "appointment", "specialist"],
            "prescriptions": ["prescription", "medication", "pharmacy", "drug"],
            "coverage": ["coverage", "benefit", "deductible", "copay", "out-of-pocket"],
            "network": ["network", "in-network", "out-of-network", "provider"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics[:3]  # Return top 3 topics
    
    async def _update_user_preferences(self, user_id: str, interaction: Dict[str, Any]):
        """Update user preferences based on new interaction."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "common_question_types": {},
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Update question type frequency
        query_type = interaction.get("query_type", "general")
        prefs = self.user_preferences[user_id]
        prefs["common_question_types"][query_type] = prefs["common_question_types"].get(query_type, 0) + 1
        prefs["last_updated"] = datetime.utcnow().isoformat()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage."""
        total_interactions = sum(len(interactions) for interactions in self.user_memories.values())
        
        return {
            "total_sessions": len(self.user_memories),
            "total_interactions": total_interactions,
            "users_with_preferences": len(self.user_preferences),
            "session_summaries": len(self.session_summaries),
            "avg_interactions_per_session": total_interactions / len(self.user_memories) if self.user_memories else 0
        }

# Global memory instance
conversation_memory = ConversationMemory()
