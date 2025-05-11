"""
Guide to PDF Agent

This agent is responsible for:
1. Creating PDF guides for users based on healthcare navigation guidance
2. Converting structured guide information into formatted documents
3. Ensuring guides are visually appealing and easy to understand
4. Generating consistent and professional documentation
5. Implementing automatic performance evaluation (APE) for continuous improvement

Based on FMEA analysis, this agent implements controls for:
- PDF generation failures
- Formatting inconsistencies
- Missing critical information
- Output quality verification
- Performance optimization
"""

import os
import json
import logging
import time
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
logger = logging.getLogger("guide_to_pdf_agent")
if not logger.handlers:
    handler = logging.FileHandler(os.path.join("logs", "agents", "guide_to_pdf.log"))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs(os.path.join("logs", "agents"), exist_ok=True)

# Define output schema for the PDF generation result
class PDFGenerationResult(BaseModel):
    """Output schema for the PDF generation result."""
    success: bool = Field(description="Whether the PDF was generated successfully")
    file_path: Optional[str] = Field(description="Path to the generated PDF file", default=None)
    file_size: Optional[int] = Field(description="Size of the generated PDF in bytes", default=None)
    generation_time: float = Field(description="Time taken to generate the PDF in seconds")
    quality_score: float = Field(description="Quality score for the generated PDF (0-1)")
    error: Optional[str] = Field(description="Error message if generation failed", default=None)
    performance_metrics: Dict[str, Any] = Field(description="Performance metrics", default_factory=dict)
    improvement_suggestions: List[str] = Field(description="Suggestions for improvement", default_factory=list)

class GuideSection(BaseModel):
    """Schema for a section in the guide content."""
    title: str = Field(description="Section title")
    content: str = Field(description="Section content")
    order: int = Field(description="Order of the section in the guide")

class GuideContent(BaseModel):
    """Schema for the guide content."""
    title: str = Field(description="Guide title")
    subtitle: Optional[str] = Field(description="Guide subtitle", default=None)
    user_name: str = Field(description="Name of the user")
    summary: str = Field(description="Brief summary of the guide")
    sections: List[GuideSection] = Field(description="Guide sections", default_factory=list)
    action_items: List[str] = Field(description="Action items for the user", default_factory=list)
    provider_details: Dict[str, Any] = Field(description="Provider details", default_factory=dict)
    contact_info: Dict[str, str] = Field(description="Contact information", default_factory=dict)
    footer_text: Optional[str] = Field(description="Footer text", default=None)
    date_generated: str = Field(description="Date the guide was generated")

class PDFStyle(BaseModel):
    """Schema for PDF styling options."""
    primary_color: str = Field(description="Primary color for headings and highlights")
    secondary_color: str = Field(description="Secondary color for subheadings")
    font_family: str = Field(description="Main font family")
    header_image_path: Optional[str] = Field(description="Path to header image", default=None)
    footer_image_path: Optional[str] = Field(description="Path to footer image", default=None)
    logo_path: Optional[str] = Field(description="Path to logo image", default=None)
    page_size: str = Field(description="Page size (e.g., 'A4', 'Letter')")
    margins: Dict[str, float] = Field(description="Page margins in inches", default_factory=dict)

class GuideToPDFAgent(BaseAgent):
    """Agent responsible for converting healthcare guides to PDF documents."""
    
    def __init__(self, llm: Optional[BaseLanguageModel] = None):
        """Initialize the agent with an optional language model."""
        # Initialize the base agent
        super().__init__(name="guide_to_pdf", llm=llm or ChatAnthropic(model="claude-3-sonnet-20240229", temperature=0))
        
        self.result_parser = PydanticOutputParser(pydantic_object=PDFGenerationResult)
        
        # Define system prompt for PDF generation evaluation
        # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("guide_to_pdf")
        except FileNotFoundError:
            self.logger.warning("Could not find guide_to_pdf.md prompt file, using default prompt")
            # Load the self.system_prompt from file
        try:
            self.system_prompt = load_prompt("guide_to_pdf")
        except FileNotFoundError:
            self.logger.warning("Could not find guide_to_pdf.md prompt file, using default prompt")
            self.system_prompt = """
            Default prompt for self.system_prompt. Replace with actual prompt if needed.
            """
        
        
        
        # Define the evaluation prompt template
        self.evaluation_template = PromptTemplate(
            template="""
            {system_prompt}
            
            GUIDE CONTENT:
            {guide_content}
            
            PDF GENERATION RESULTS:
            {generation_results}
            
            Evaluate the quality of the generated PDF and provide feedback.
            
            {format_instructions}
            """,
            input_variables=["system_prompt", "guide_content", "generation_results"],
            partial_variables={"format_instructions": self.result_parser.get_format_instructions()}
        )
        
        # Create the HTML template for PDF generation
        self._init_html_template()
        
        # Default PDF style
        self.default_style = PDFStyle(
            primary_color="#005A9C",
            secondary_color="#6C757D",
            font_family="Arial, Helvetica, sans-serif",
            page_size="Letter",
            margins={"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0}
        )
        
        logger.info("Guide to PDF Agent initialized")
    
    def _init_html_template(self):
        """Initialize the HTML template for PDF generation."""
        self.html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{title}}</title>
            <style>
                body {
                    font-family: {{font_family}};
                    margin: 0;
                    padding: 0;
                    color: #333;
                    line-height: 1.6;
                }
                .container {
                    width: 100%;
                    max-width: 8.5in;
                    margin: 0 auto;
                    padding: {{margins.top}}in {{margins.right}}in {{margins.bottom}}in {{margins.left}}in;
                }
                .header {
                    text-align: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid {{primary_color}};
                    padding-bottom: 10px;
                }
                h1 {
                    color: {{primary_color}};
                    margin-bottom: 10px;
                }
                h2 {
                    color: {{primary_color}};
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }
                h3 {
                    color: {{secondary_color}};
                }
                .summary {
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-left: 4px solid {{primary_color}};
                    margin-bottom: 20px;
                }
                .section {
                    margin-bottom: 20px;
                }
                .action-items {
                    background-color: #f0f7ff;
                    padding: 15px;
                    border-radius: 5px;
                }
                .action-items h2 {
                    margin-top: 0;
                }
                .action-items ul {
                    padding-left: 20px;
                }
                .provider-details {
                    background-color: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                }
                .contact-info {
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 10px;
                    border-top: 1px solid #eee;
                    font-size: 0.8em;
                    color: #777;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }
                table, th, td {
                    border: 1px solid #ddd;
                }
                th, td {
                    padding: 10px;
                    text-align: left;
                }
                th {
                    background-color: {{primary_color}};
                    color: white;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{title}}</h1>
                    {% if subtitle %}<h3>{{subtitle}}</h3>{% endif %}
                    <p>Prepared for: {{user_name}} | Date: {{date_generated}}</p>
                </div>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p>{{summary}}</p>
                </div>
                
                {% for section in sections %}
                <div class="section">
                    <h2>{{section.title}}</h2>
                    {{section.content}}
                </div>
                {% endfor %}
                
                <div class="action-items">
                    <h2>Action Items</h2>
                    <ul>
                        {% for item in action_items %}
                        <li>{{item}}</li>
                        {% endfor %}
                    </ul>
                </div>
                
                <div class="provider-details">
                    <h2>Provider Information</h2>
                    {% if provider_details %}
                    <table>
                        <tr>
                            <th>Name</th>
                            <th>Address</th>
                            <th>Contact</th>
                            <th>Specialties</th>
                        </tr>
                        {% for provider in provider_details %}
                        <tr>
                            <td>{{provider.name}}</td>
                            <td>{{provider.address}}</td>
                            <td>{{provider.phone}}</td>
                            <td>{{provider.specialties|join(', ')}}</td>
                        </tr>
                        {% endfor %}
                    </table>
                    {% else %}
                    <p>No provider information available.</p>
                    {% endif %}
                </div>
                
                <div class="contact-info">
                    <h2>Important Contacts</h2>
                    <ul>
                        {% for name, contact in contact_info.items() %}
                        <li><strong>{{name}}:</strong> {{contact}}</li>
                        {% endfor %}
                    </ul>
                </div>
                
                <div class="footer">
                    <p>{{footer_text}}</p>
                    <p>Generated on {{date_generated}}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _render_html(self, guide_content: GuideContent, style: PDFStyle) -> str:
        """
        Render HTML from the guide content and style.
        
        Args:
            guide_content: Guide content
            style: PDF style settings
            
        Returns:
            Rendered HTML string
        """
        # In a real implementation, this would use a proper template engine like Jinja2
        # For this demo, we'll use a simplified approach
        
        # Replace style variables
        html = self.html_template
        html = html.replace("{{font_family}}", style.font_family)
        html = html.replace("{{primary_color}}", style.primary_color)
        html = html.replace("{{secondary_color}}", style.secondary_color)
        
        # Replace margins
        margins_json = json.dumps(style.margins)
        html = html.replace("{{margins.top}}", str(style.margins.get("top", 1.0)))
        html = html.replace("{{margins.right}}", str(style.margins.get("right", 1.0)))
        html = html.replace("{{margins.bottom}}", str(style.margins.get("bottom", 1.0)))
        html = html.replace("{{margins.left}}", str(style.margins.get("left", 1.0)))
        
        # Replace content variables
        html = html.replace("{{title}}", guide_content.title)
        html = html.replace("{{subtitle}}", guide_content.subtitle or "")
        html = html.replace("{{user_name}}", guide_content.user_name)
        html = html.replace("{{date_generated}}", guide_content.date_generated)
        html = html.replace("{{summary}}", guide_content.summary)
        html = html.replace("{{footer_text}}", guide_content.footer_text or "")
        
        # Handle conditional subtitle
        if guide_content.subtitle:
            html = html.replace("{% if subtitle %}<h3>{{subtitle}}</h3>{% endif %}", f"<h3>{guide_content.subtitle}</h3>")
        else:
            html = html.replace("{% if subtitle %}<h3>{{subtitle}}</h3>{% endif %}", "")
        
        # Replace sections
        sections_html = ""
        for section in sorted(guide_content.sections, key=lambda s: s.order):
            section_html = f"""
            <div class="section">
                <h2>{section.title}</h2>
                {section.content}
            </div>
            """
            sections_html += section_html
        
        html = html.replace("{% for section in sections %}\n                <div class=\"section\">\n                    <h2>{{section.title}}</h2>\n                    {{section.content}}\n                </div>\n                {% endfor %}", sections_html)
        
        # Replace action items
        action_items_html = ""
        for item in guide_content.action_items:
            action_items_html += f"<li>{item}</li>\n                        "
        
        html = html.replace("{% for item in action_items %}\n                        <li>{{item}}</li>\n                        {% endfor %}", action_items_html)
        
        # Replace provider details
        if guide_content.provider_details:
            providers_html = ""
            for provider in guide_content.provider_details.get("providers", []):
                specialties = ", ".join(provider.get("specialties", []))
                providers_html += f"""
                <tr>
                    <td>{provider.get('name', 'N/A')}</td>
                    <td>{provider.get('address', 'N/A')}</td>
                    <td>{provider.get('phone', 'N/A')}</td>
                    <td>{specialties}</td>
                </tr>
                """
            
            provider_table = f"""
            <table>
                <tr>
                    <th>Name</th>
                    <th>Address</th>
                    <th>Contact</th>
                    <th>Specialties</th>
                </tr>
                {providers_html}
            </table>
            """
            
            html = html.replace("{% if provider_details %}\n                    <table>\n                        <tr>\n                            <th>Name</th>\n                            <th>Address</th>\n                            <th>Contact</th>\n                            <th>Specialties</th>\n                        </tr>\n                        {% for provider in provider_details %}\n                        <tr>\n                            <td>{{provider.name}}</td>\n                            <td>{{provider.address}}</td>\n                            <td>{{provider.phone}}</td>\n                            <td>{{provider.specialties|join(', ')}}</td>\n                        </tr>\n                        {% endfor %}\n                    </table>\n                    {% else %}\n                    <p>No provider information available.</p>\n                    {% endif %}", provider_table)
        else:
            html = html.replace("{% if provider_details %}\n                    <table>\n                        <tr>\n                            <th>Name</th>\n                            <th>Address</th>\n                            <th>Contact</th>\n                            <th>Specialties</th>\n                        </tr>\n                        {% for provider in provider_details %}\n                        <tr>\n                            <td>{{provider.name}}</td>\n                            <td>{{provider.address}}</td>\n                            <td>{{provider.phone}}</td>\n                            <td>{{provider.specialties|join(', ')}}</td>\n                        </tr>\n                        {% endfor %}\n                    </table>\n                    {% else %}\n                    <p>No provider information available.</p>\n                    {% endif %}", "<p>No provider information available.</p>")
        
        # Replace contact info
        contacts_html = ""
        for name, contact in guide_content.contact_info.items():
            contacts_html += f"<li><strong>{name}:</strong> {contact}</li>\n                        "
        
        html = html.replace("{% for name, contact in contact_info.items() %}\n                        <li><strong>{{name}}:</strong> {{contact}}</li>\n                        {% endfor %}", contacts_html)
        
        return html
    
    def _convert_html_to_pdf(self, html: str, output_path: str) -> Tuple[bool, str, int]:
        """
        Convert HTML to PDF.
        
        Args:
            html: HTML content to convert
            output_path: Path to save the PDF
            
        Returns:
            Tuple of (success, file_path, file_size)
        """
        # In a real implementation, this would use a library like WeasyPrint, pdfkit, or reportlab
        # For this demo, we'll simply write the HTML to a file and simulate PDF generation
        
        try:
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write HTML to a temporary file
            html_path = output_path.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            # Simulate PDF generation (in a real implementation, this would convert HTML to PDF)
            self.logger.info(f"HTML file written to {html_path}")
            self.logger.info(f"Simulating PDF generation to {output_path}")
            
            # In a real implementation, we would call a PDF generation library here
            # For this demo, we'll create a simple text file instead
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"SIMULATED PDF CONTENT\n\nThis is a placeholder for the actual PDF file.\nIn a real implementation, this would be a PDF generated from the HTML content.\n\nSource HTML: {html_path}")
            
            # Get the file size
            file_size = os.path.getsize(output_path)
            
            return True, output_path, file_size
            
        except Exception as e:
            self.logger.error(f"Error converting HTML to PDF: {str(e)}")
            return False, "", 0
    
    def _evaluate_pdf_quality(self, guide_content: Dict[str, Any], generation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the quality of the generated PDF.
        
        Args:
            guide_content: Guide content
            generation_results: PDF generation results
            
        Returns:
            Evaluation results
        """
        try:
            # Prepare input for the evaluation
            input_dict = {
                "system_prompt": self.system_prompt,
                "guide_content": json.dumps(guide_content),
                "generation_results": json.dumps(generation_results)
            }
            
            # Format the prompt
            prompt = self.evaluation_template.format(**input_dict)
            
            # Call the language model
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([SystemMessage(content=self.system_prompt), message])
            
            # Parse the response
            result = self.result_parser.parse(response.content)
            
            return result.dict()
        
        except Exception as e:
            self.logger.error(f"Error evaluating PDF quality: {str(e)}")
            
            # Return default evaluation result
            return {
                "success": generation_results.get("success", False),
                "file_path": generation_results.get("file_path", ""),
                "file_size": generation_results.get("file_size", 0),
                "generation_time": generation_results.get("generation_time", 0.0),
                "quality_score": 0.5,  # Default quality score
                "error": str(e),
                "performance_metrics": {},
                "improvement_suggestions": ["Error during evaluation, unable to provide detailed feedback"]
            }
    
    @BaseAgent.track_performance
    def generate_pdf(self, 
                    guide_content: Dict[str, Any], 
                    output_path: str,
                    style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a PDF from the guide content.
        
        Args:
            guide_content: Guide content
            output_path: Path to save the PDF
            style: Optional PDF style settings
            
        Returns:
            PDF generation result
        """
        start_time = time.time()
        
        # Log the request
        self.logger.info(f"Generating PDF for guide: {guide_content.get('title', 'Unnamed Guide')}")
        
        try:
            # Convert dictionaries to models
            content_model = GuideContent(**guide_content)
            style_model = PDFStyle(**(style or self.default_style.dict()))
            
            # Render HTML
            html = self._render_html(content_model, style_model)
            
            # Convert HTML to PDF
            success, file_path, file_size = self._convert_html_to_pdf(html, output_path)
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Create generation results
            generation_results = {
                "success": success,
                "file_path": file_path,
                "file_size": file_size,
                "generation_time": generation_time,
                "quality_score": 0.0,  # Will be updated by evaluation
                "error": None if success else "PDF generation failed"
            }
            
            # Evaluate PDF quality
            evaluation_results = self._evaluate_pdf_quality(content_model.dict(), generation_results)
            
            # Log the result
            if success:
                self.logger.info(f"PDF generated successfully: {file_path} ({file_size} bytes)")
                self.logger.info(f"Quality score: {evaluation_results['quality_score']}")
            else:
                self.logger.error(f"PDF generation failed: {evaluation_results.get('error', 'Unknown error')}")
            
            # Log execution time
            self.logger.info(f"PDF generation completed in {generation_time:.2f}s")
            
            return evaluation_results
            
        except Exception as e:
            self.logger.error(f"Error in PDF generation: {str(e)}")
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Return error result
            return {
                "success": False,
                "file_path": None,
                "file_size": None,
                "generation_time": generation_time,
                "quality_score": 0.0,
                "error": str(e),
                "performance_metrics": {},
                "improvement_suggestions": ["Fix the error in the PDF generation process"]
            }
    
    def process(self, 
               guide_content: Dict[str, Any],
               output_path: str,
               style: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a PDF generation request.
        
        Args:
            guide_content: Guide content
            output_path: Path to save the PDF
            style: Optional PDF style settings
            
        Returns:
            Tuple of (success, file_path, full_result)
        """
        result = self.generate_pdf(guide_content, output_path, style)
        return result["success"], result.get("file_path", ""), result

# Example usage
if __name__ == "__main__":
    # Initialize the agent
    agent = GuideToPDFAgent()
    
    # Test with sample data
    guide_content = {
        "title": "Diabetes Management Guide",
        "subtitle": "Medicare Coverage and Resource Guide",
        "user_name": "John Doe",
        "summary": "This guide provides information on managing diabetes under your Medicare Advantage plan, including covered services, local providers, and important action steps.",
        "sections": [
            {
                "title": "Understanding Your Coverage",
                "content": "<p>Your Medicare Advantage plan covers a range of diabetes-related services, including:</p><ul><li>Quarterly endocrinologist visits</li><li>Diabetes self-management training</li><li>Blood glucose monitors and supplies</li><li>Therapeutic shoes or inserts if needed</li></ul>",
                "order": 1
            },
            {
                "title": "Recommended Services",
                "content": "<p>Based on your needs and coverage, we recommend the following services:</p><ul><li>Quarterly endocrinology consultations</li><li>Annual diabetic eye exam</li><li>Regular blood glucose monitoring</li><li>Diabetes education program</li></ul>",
                "order": 2
            }
        ],
        "action_items": [
            "Schedule appointment with Dr. Smith at Boston Diabetes Center",
            "Register for diabetes self-management training",
            "Refill glucose testing supplies",
            "Schedule annual diabetic eye exam"
        ],
        "provider_details": {
            "providers": [
                {
                    "name": "Boston Diabetes Center",
                    "address": "123 Medical Parkway, Boston, MA 02215",
                    "phone": "617-555-1234",
                    "specialties": ["endocrinology", "diabetes care"]
                },
                {
                    "name": "Metro Eye Specialists",
                    "address": "456 Vision Blvd, Boston, MA 02116",
                    "phone": "617-555-5678",
                    "specialties": ["ophthalmology", "diabetic eye care"]
                }
            ]
        },
        "contact_info": {
            "Insurance Customer Service": "1-800-MEDICARE",
            "Boston Diabetes Center": "617-555-1234",
            "24/7 Nurse Line": "1-888-555-9000"
        },
        "footer_text": "This guide was created based on your Medicare Advantage plan coverage as of January 2025",
        "date_generated": "May 10, 2025"
    }
    
    # Generate PDF
    output_path = "output/guides/diabetes_management_guide.pdf"
    success, file_path, result = agent.process(guide_content, output_path)
    
    if success:
        print(f"PDF generated successfully: {file_path}")
        print(f"Quality score: {result['quality_score']}")
        if result.get('improvement_suggestions'):
            print("Improvement suggestions:")
            for suggestion in result['improvement_suggestions']:
                print(f"- {suggestion}")
    else:
        print(f"PDF generation failed: {result.get('error', 'Unknown error')}") 