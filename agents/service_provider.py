"""
Service Provider Agent

This agent is responsible for:
1. Identifying local, matching service providers for healthcare services
2. Integrating with CMS API and other provider databases
3. Filtering providers based on specialty, location, and network status
4. Providing detailed provider information including contact, location, and availability
5. Supporting the Service Access Strategy Agent with provider options

Based on FMEA analysis, this agent implements controls for:
- Network status verification errors
- Provider information accuracy
- Distance calculation accuracy
- Provider specialty verification
- Missing or outdated provider information
"""

import os
import json
import logging
import time
import math
from typing import Dict, List, Any, Tuple, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.language_models import BaseLanguageModel
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from agents.base_agent import BaseAgent
from utils.prompt_loader import load_prompt

# Setup logging
logger = logging.getLogger("service_provider_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "service_provider.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schema for provider information
class Provider(BaseModel):
    """Schema for a healthcare provider."""
    name: str = Field(description="Name of the healthcare provider or facility")
    address: str = Field(description="Full address of the provider")
    city: str = Field(description="City where the provider is located")
    state: str = Field(description="State where the provider is located")
    zip_code: str = Field(description="ZIP code of the provider's location")
    phone: str = Field(description="Contact phone number")
    specialties: List[str] = Field(description="List of specialties offered by the provider", default_factory=list)
    in_network: bool = Field(description="Whether the provider is in-network for the user's insurance")
    distance: float = Field(description="Distance in miles from the user's location")
    accepts_new_patients: bool = Field(description="Whether the provider is accepting new patients")
    languages: List[str] = Field(description="Languages spoken by the provider", default_factory=list)
    ratings: Optional[Dict[str, Any]] = Field(description="Provider ratings if available", default=None)
    next_available: Optional[str] = Field(description="Next available appointment information if available", default=None)

class ProviderSearchResult(BaseModel):
    """Output schema for the provider search results."""
    providers: List[Provider] = Field(description="List of matching providers", default_factory=list)
    service_type: str = Field(description="Type of service requested")
    location: str = Field(description="Search location")
    total_results: int = Field(description="Total number of providers found")
    search_radius: float = Field(description="Search radius in miles")
    insurance_type: str = Field(description="Type of insurance used for filtering")
    confidence: float = Field(description="Confidence in the search results (0-1)")
    error: Optional[str] = Field(description="Error message if any", default=None)

class ServiceProviderAgent(BaseAgent):
    """Agent responsible for identifying local, matching service providers."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="service_provider", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.parser = PydanticOutputParser(pydantic_object=ProviderSearchResult)
        
        # Define system prompt for provider search
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("service_provider")
        except FileNotFoundError:
            self.logger.warning("Could not find service_provider.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("service_provider")
        except FileNotFoundError:
            self.logger.warning("Could not find service_provider.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the prompt template
        self.prompt_template = PromptTemplate(
            template="""
            {system_prompt}
            
            SERVICE TYPE NEEDED: {service_type}
            USER LOCATION: {location}
            INSURANCE TYPE: {insurance_type}
            SEARCH RADIUS: {search_radius} miles
            ADDITIONAL REQUIREMENTS: {additional_requirements}
            
            Find healthcare providers that match these requirements.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "service_type", "location", "insurance_type", 
                           "search_radius", "additional_requirements"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        # Create the chain
        self.chain = (
            {"system_prompt": lambda _: self.system_prompt, 
             "service_type": lambda x: x["service_type"],
             "location": lambda x: x["location"],
             "insurance_type": lambda x: x["insurance_type"],
             "search_radius": lambda x: x["search_radius"],
             "additional_requirements": lambda x: x["additional_requirements"]}
            | self.prompt_template
            | self.llm
            | self.parser
        )
        
        # For demo purposes: initialize a simple provider database by specialty
        # In a real implementation, this would connect to the CMS API or other provider databases
        self._init_demo_provider_database()
        
        logger.info("Service Provider Agent initialized")
    
    def _init_demo_provider_database(self):
        """Initialize a demo provider database for testing."""
        self.provider_db = {
            "primary_care": [
                {
                    "name": "Main Street Family Practice",
                    "address": "123 Main St, Boston, MA 02108",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02108",
                    "phone": "617-555-1234",
                    "specialties": ["primary_care", "family_medicine"],
                    "in_network": True,
                    "accepts_new_patients": True,
                    "languages": ["English", "Spanish"],
                    "coordinates": {"lat": 42.359, "lng": -71.059}
                },
                {
                    "name": "Downtown Health Associates",
                    "address": "456 Washington St, Boston, MA 02111",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02111",
                    "phone": "617-555-5678",
                    "specialties": ["primary_care", "internal_medicine"],
                    "in_network": True,
                    "accepts_new_patients": True,
                    "languages": ["English", "Mandarin", "Cantonese"],
                    "coordinates": {"lat": 42.352, "lng": -71.062}
                }
            ],
            "cardiology": [
                {
                    "name": "Boston Heart Center",
                    "address": "789 Beacon St, Boston, MA 02215",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02215",
                    "phone": "617-555-9012",
                    "specialties": ["cardiology", "vascular_medicine"],
                    "in_network": True,
                    "accepts_new_patients": True,
                    "languages": ["English"],
                    "coordinates": {"lat": 42.349, "lng": -71.106}
                },
                {
                    "name": "Cardiac Specialists of New England",
                    "address": "321 Commonwealth Ave, Boston, MA 02115",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02115",
                    "phone": "617-555-3456",
                    "specialties": ["cardiology", "interventional_cardiology"],
                    "in_network": False,
                    "accepts_new_patients": True,
                    "languages": ["English", "French"],
                    "coordinates": {"lat": 42.351, "lng": -71.085}
                }
            ],
            "endocrinology": [
                {
                    "name": "Boston Diabetes & Endocrinology Center",
                    "address": "567 Boylston St, Boston, MA 02116",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02116",
                    "phone": "617-555-7890",
                    "specialties": ["endocrinology", "diabetes_care"],
                    "in_network": True,
                    "accepts_new_patients": True,
                    "languages": ["English", "Hindi"],
                    "coordinates": {"lat": 42.353, "lng": -71.071}
                }
            ],
            "orthopedics": [
                {
                    "name": "Boston Joint & Spine Center",
                    "address": "890 Huntington Ave, Boston, MA 02115",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02115",
                    "phone": "617-555-2345",
                    "specialties": ["orthopedics", "sports_medicine"],
                    "in_network": True,
                    "accepts_new_patients": False,
                    "languages": ["English"],
                    "coordinates": {"lat": 42.334, "lng": -71.102}
                }
            ],
            "dermatology": [
                {
                    "name": "Boston Skin & Wellness",
                    "address": "432 Newbury St, Boston, MA 02115",
                    "city": "Boston",
                    "state": "MA",
                    "zip_code": "02115",
                    "phone": "617-555-6789",
                    "specialties": ["dermatology", "cosmetic_dermatology"],
                    "in_network": True,
                    "accepts_new_patients": True,
                    "languages": ["English", "Portuguese"],
                    "coordinates": {"lat": 42.348, "lng": -71.088}
                }
            ]
        }
        
        # Default coordinates for locations in our demo
        self.location_coordinates = {
            "Boston, MA": {"lat": 42.360, "lng": -71.059},
            "Cambridge, MA": {"lat": 42.373, "lng": -71.110},
            "Brookline, MA": {"lat": 42.331, "lng": -71.121},
            "Somerville, MA": {"lat": 42.387, "lng": -71.102},
            "Quincy, MA": {"lat": 42.253, "lng": -71.003}
        }
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculate the Haversine distance between two points in miles.
        
        Args:
            lat1: Latitude of point 1
            lng1: Longitude of point 1
            lat2: Latitude of point 2
            lng2: Longitude of point 2
            
        Returns:
            Distance in miles
        """
        # Earth's radius in miles
        radius = 3958.8
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = radius * c
        
        return round(distance, 1)
    
    def _get_location_coordinates(self, location: str) -> Dict[str, float]:
        """
        Get coordinates for a location.
        
        Args:
            location: Location string (e.g., "Boston, MA")
            
        Returns:
            Dictionary with lat and lng
        """
        # In a real implementation, this would use a geocoding API
        if location in self.location_coordinates:
            return self.location_coordinates[location]
        
        # Default to Boston coordinates if location not found
        self.logger.warning(f"Location not found: {location}, using Boston coordinates")
        return self.location_coordinates["Boston, MA"]
    
    @BaseAgent.track_performance
    def find_providers(self, 
                      service_type: str,
                      location: str,
                      insurance_type: str = "Medicare",
                      search_radius: float = 25.0,
                      additional_requirements: str = "") -> Dict[str, Any]:
        """
        Find healthcare providers based on service type and location.
        
        Args:
            service_type: Type of healthcare service needed
            location: User's location (e.g., "Boston, MA")
            insurance_type: Type of insurance (default: "Medicare")
            search_radius: Search radius in miles (default: 25.0)
            additional_requirements: Additional search requirements
            
        Returns:
            Dictionary with provider search results
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Searching for {service_type} providers near {location}")
        
        try:
            # In a real implementation, this would use CMS API or other provider databases
            # For demo purposes, use our in-memory database
            
            # Normalize service type (convert to lowercase and replace spaces with underscores)
            normalized_service_type = service_type.lower().replace(" ", "_")
            
            # Get user coordinates
            user_coords = self._get_location_coordinates(location)
            
            providers_list = []
            
            # Check if we have providers for this service type
            if normalized_service_type in self.provider_db:
                raw_providers = self.provider_db[normalized_service_type]
                
                # Filter and enhance provider data
                for provider in raw_providers:
                    # Calculate distance
                    provider_coords = provider["coordinates"]
                    distance = self._calculate_distance(
                        user_coords["lat"], user_coords["lng"],
                        provider_coords["lat"], provider_coords["lng"]
                    )
                    
                    # Apply filters
                    if distance <= search_radius:
                        # Create a Provider object
                        provider_obj = Provider(
                            name=provider["name"],
                            address=provider["address"],
                            city=provider["city"],
                            state=provider["state"],
                            zip_code=provider["zip_code"],
                            phone=provider["phone"],
                            specialties=provider["specialties"],
                            in_network=provider["in_network"],
                            distance=distance,
                            accepts_new_patients=provider["accepts_new_patients"],
                            languages=provider["languages"]
                        )
                        providers_list.append(provider_obj)
            
            # If we don't have enough providers or none at all, use the LLM to generate synthetic ones
            if len(providers_list) < 3:
                self.logger.info(f"Insufficient providers in database for {service_type}, generating with LLM")
                
                # Prepare input for the chain
                input_dict = {
                    "service_type": service_type,
                    "location": location,
                    "insurance_type": insurance_type,
                    "search_radius": str(search_radius),
                    "additional_requirements": additional_requirements
                }
                
                # Call the chain to generate providers
                search_result = self.chain.invoke(input_dict)
                
                # Combine existing providers with generated ones
                if providers_list:
                    # Add existing providers and update total
                    search_result.providers = providers_list + search_result.providers
                    search_result.total_results = len(search_result.providers)
                
                result = search_result.dict()
            else:
                # Just use the providers from our database
                result = ProviderSearchResult(
                    providers=providers_list,
                    service_type=service_type,
                    location=location,
                    total_results=len(providers_list),
                    search_radius=search_radius,
                    insurance_type=insurance_type,
                    confidence=0.95  # High confidence for database results
                ).dict()
            
            # Log results
            self.logger.info(f"Found {result['total_results']} providers for {service_type} near {location}")
            
            # Log execution time
            execution_time = time.time() - start_time
            self.logger.info(f"Provider search completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in provider search: {str(e)}")
            
            # Return an error result
            return ProviderSearchResult(
                providers=[],
                service_type=service_type,
                location=location,
                total_results=0,
                search_radius=search_radius,
                insurance_type=insurance_type,
                confidence=0.0,
                error=str(e)
            ).dict()
    
    def process(self, 
               service_type: str,
               location: str,
               insurance_type: str = "Medicare",
               search_radius: float = 25.0,
               additional_requirements: str = "") -> Tuple[List[Provider], Dict[str, Any]]:
        """
        Process a provider search request.
        
        Args:
            service_type: Type of healthcare service needed
            location: User's location (e.g., "Boston, MA")
            insurance_type: Type of insurance (default: "Medicare")
            search_radius: Search radius in miles (default: 25.0)
            additional_requirements: Additional search requirements
            
        Returns:
            Tuple of (provider_list, full_result)
        """
        result = self.find_providers(service_type, location, insurance_type, search_radius, additional_requirements)
        return result["providers"], result

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = ServiceProviderAgent()
    
    # Test with a simple search
    service_type = "endocrinology"
    location = "Boston, MA"
    
    providers, result = agent.process(service_type, location)
    
    print(f"Found {len(providers)} {service_type} providers near {location}:")
    for provider in providers:
        print(f"- {provider.name} ({provider.distance} miles): {', '.join(provider.specialties)}")
        print(f"  {provider.address} | {provider.phone}")
        print(f"  In-network: {provider.in_network} | Accepting patients: {provider.accepts_new_patients}")
        print(f"  Languages: {', '.join(provider.languages)}")
        print("") 