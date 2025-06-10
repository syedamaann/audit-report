import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv(find_dotenv('.env.local'))

class Email(BaseModel):
    """Represents a single email message in a conversation thread."""
    sender: str = Field(..., description="The sender's name or email address.")
    timestamp: str = Field(..., description="The timestamp of when the email was sent.")
    recipient: str = Field(..., description="The primary recipient's email address.")
    cc: List[str] = Field(default_factory=list, description="A list of CC'd recipients.")
    subject: str = Field(..., description="The subject line of the email.")
    body: str = Field(..., description="The main content of the email body.")

class EmailConversation(BaseModel):
    """Represents a structured email conversation thread."""
    email_conversations: List[Email] = Field(..., description="A list of email messages, ordered chronologically (oldest first).")

class StepResult(BaseModel):
    """Structured result for a single audit step."""
    step_id: str = Field(..., description="The unique identifier for the audit step.")
    title: str = Field(..., description="The title of the audit step.")
    passed: bool = Field(..., description="Whether the audit criteria for this step were met (score >= 0.7).")
    score: float = Field(..., description="The score assigned for this step, from 0.0 to 1.0.")
    analysis: str = Field(..., description="The detailed analysis of how the conversation performed against the criteria.")
    reasoning: str = Field(..., description="The reasoning behind the assigned score.")
    improvements: Optional[str] = Field(None, description="Suggestions for improvement, if any.")

class AuditReport(BaseModel):
    """The full audit report containing results for all steps."""
    results: List[StepResult] = Field(..., description="A list of results for each audit step performed.")

class EmailAuditor:
    def __init__(self):
        # Get API key from environment variables
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Debug logging
        logger.debug(f"API Key present: {bool(openai_api_key)}")
        logger.debug(f"API Key length: {len(openai_api_key) if openai_api_key else 0}")
        
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize multiple models for different aspects of analysis
        try:
            logger.debug("Initializing primary_llm...")
            self.primary_llm = ChatOpenAI(
                model='gpt-4o',
                temperature=0.0,  # For factual analysis
                api_key=openai_api_key
            )
            logger.debug("Initializing reasoning_llm...")
            self.reasoning_llm = ChatOpenAI(
                model='gpt-4o',
                temperature=0.3,  # For nuanced understanding and reasoning
                api_key=openai_api_key
            )
            logger.debug("Initializing detail_llm...")
            self.detail_llm = ChatOpenAI(
                model='gpt-4o',
                temperature=0.1,  # For detailed analysis
                api_key=openai_api_key
            )
            logger.debug("All LLMs initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing LLMs: {str(e)}")
            raise
        
        # Define audit steps
        self.audit_steps = [
            {
                "id": "communication",
                "title": "Overall Communication",
                "purpose": "Check if the overall communication is clear and concise",
                "prompt": """Given the conversation, check if the overall communication is up to the standards of a travel service. 
                Analyze first if the agent made a no-mistake conversation, then check for standard conversation flow. 
                Some examples to check for:
                - Detailed messages
                - Empathy if they got the wrong info the first time
                - Does not expose or asks for sensitive info to be shared on the email itself
                - Is zealous to help""",
                "isCritical": False,
                "score": 3.0,
                "category": "communication",
                "model": "reasoning"  # Use reasoning model for communication analysis
            },
            {
                "id": "logical_itinerary",
                "title": "Logical Itinerary",
                "purpose": "Check if locations and time are logical in the itinerary",
                "prompt": "Given the conversation, check if a logical itinerary was followed. If not, provide a reason why you think so",
                "isCritical": False,
                "score": 3.0,
                "category": "PNR",
                "model": "primary"  # Use primary model for factual analysis
            },
            {
                "id": "limo_offering",
                "title": "Limo Offering",
                "purpose": "Check if limo service was offered where applicable",
                "prompt": "Given the conversation, check if limo service was offered where appropriate. If it was, check if the address and phone number was captured",
                "isCritical": True,
                "score": 5.40,
                "category": "PNR",
                "model": "detail"  # Use detail model for thorough checking
            },
            {
                "id": "transit_visa_advisory",
                "title": "Transit Visa Advisory",
                "purpose": "Check if transit visa requirements were properly advised",
                "prompt": "Given the conversation, check if transit visa requirements were properly communicated to the customer for any layovers in their itinerary",
                "isCritical": True,
                "score": 5.40,
                "category": "policy and service",
                "model": "reasoning"  # Use reasoning model for policy analysis
            },
            {
                "id": "case_reference",
                "title": "Case Number Reference",
                "purpose": "Check if the case number reference was captured",
                "prompt": "Given the conversation, check if the case number reference was captured atop the conversation",
                "isCritical": False,
                "score": 3.0,
                "category": "policy and service",
                "model": "primary"  # Use primary model for factual analysis
            },
            {
                "id": "cross_sell",
                "title": "Cross-sell",
                "purpose": "Check if the agent was able to cross-sell the customer",
                "prompt": "Given the conversation, check if the agent was able to cross-sell the customer, suggesting options of other services when ONLY air request is there. Such as Hotel, Car & Insurance. Does not apply if the customer asks for it.",
                "isCritical": False,
                "score": 3.0,
                "category": "communication",
                "model": "reasoning"  # Use reasoning model for communication analysis
            },
            {
                "id": "accuracy",
                "title": "Quotation Accuracy",
                "purpose": "Check if the agent provided accurate quotations",
                "prompt": "Given the conversation, check how well the agent was able to provide an accurate quotation",
                "isCritical": True,
                "score": 5.40,
                "category": "communication",
                "model": "detail"  # Use detail model for thorough checking
            }
        ]
    
    async def audit_email(self, html_path: Path) -> Dict[str, Any]:
        """
        Audits an email by directly parsing the HTML file, structuring the content,
        and then performing a comprehensive analysis. This updated method avoids
        browser automation for significant speed improvements.
        
        Args:
            html_path: Path to the HTML file to analyze (from eml-html folder)
            
        Returns:
            Dictionary containing the audit results
        """
        try:
            # Step 1: Direct HTML Parsing (Fast)
            logger.info(f"Directly parsing HTML file: {html_path}")
            if not html_path.exists():
                raise FileNotFoundError(f"HTML file not found at {html_path}")
            if not str(html_path).endswith('.html'):
                raise ValueError(f"Expected HTML file, got {html_path}")

            html_content = html_path.read_text(encoding='utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            # Use get_text() to extract all text content, which is faster and simpler
            email_text_content = soup.get_text(separator='\n', strip=True)

            # Step 2: Structure the conversation with a reliable, structured LLM call
            logger.info("Structuring conversation from raw text using a LLM...")
            structuring_llm = self.primary_llm.with_structured_output(EmailConversation)
            
            structuring_prompt = f"""
            Based on the raw text extracted from an email HTML file, your task is to parse it into a chronological list of email messages. Pay close attention to headers like "From:", "Sent:", "To:", "Cc:", and "Subject:". The messages are typically in reverse chronological order in the text; please return them in chronological order (oldest first).

            Raw Text Content (first 20000 characters):
            ---
            {email_text_content[:20000]}
            ---

            Please return the data as a JSON object conforming to the required schema.
            """
            
            structured_data = await structuring_llm.ainvoke(structuring_prompt)

            messages = {
                "messages": [
                    {
                        "timestamp": msg.timestamp,
                        "sender": msg.sender,
                        "recipients": [msg.recipient] + msg.cc,
                        "subject": msg.subject,
                        "content": msg.body,
                        "attachments": [],  # Assuming no attachment parsing for now
                        "images": []        # Assuming no image parsing for now
                    }
                    for msg in structured_data.email_conversations
                ]
            }
            logger.info(f"Successfully structured {len(messages['messages'])} messages.")

            # Step 3: Perform the comprehensive audit (this part is already efficient)
            logger.info("Building comprehensive analysis prompt...")
            analysis_task_prompt = f"""
Analyze the following email conversation based on a comprehensive set of audit criteria.

Conversation History (chronological order):
{json.dumps(messages['messages'], indent=2, default=str)}

Please evaluate the conversation against each of the following audit steps and provide a structured JSON response that conforms to the required format.

Audit Criteria:
"""
            for step in self.audit_steps:
                analysis_task_prompt += f"""
- Step ID: {step['id']}
  - Title: {step['title']}
  - Purpose: {step['purpose']}
  - Prompt: {step['prompt']}
"""
            analysis_task_prompt += """
For each step, provide:
1. A boolean 'passed' field (true if score is >= 0.7).
2. A float 'score' from 0.0 to 1.0.
3. A detailed 'analysis' of what happened.
4. The 'reasoning' for your score.
5. Concrete 'improvements' if applicable.
"""
            structured_llm = self.reasoning_llm.with_structured_output(AuditReport)

            logger.info("Performing comprehensive audit with a single, structured LLM call...")
            comprehensive_report = await structured_llm.ainvoke(analysis_task_prompt)
            
            step_metadata = {step['id']: step for step in self.audit_steps}
            audit_results = []
            
            for result_pydantic in comprehensive_report.results:
                result_dict = result_pydantic.model_dump()
                metadata = step_metadata.get(result_dict['step_id'])
                
                if metadata:
                    result_dict['is_critical'] = metadata['isCritical']
                    result_dict['category'] = metadata['category']
                    result_dict['max_score'] = metadata['score']
                    audit_results.append(result_dict)

            # Step 4: Calculate scores and prepare final report
            total_score = sum(res['max_score'] for res in audit_results if res['passed'])
            max_score = sum(step['score'] for step in self.audit_steps)
            overall_score = total_score / max_score if max_score > 0 else 0
            
            return {
                "context": self._extract_context(audit_results),
                "participants": self._extract_participants(messages['messages']),
                "tone": self._analyze_tone(audit_results),
                "security": self._check_security(audit_results),
                "effectiveness": self._assess_effectiveness(audit_results),
                "recommendations": self._generate_recommendations(audit_results),
                "score": overall_score,
                "detailed_results": audit_results,
                "reasoning": self._generate_reasoning(audit_results),
                "conversation_history": messages['messages']
            }
            
        except Exception as e:
            logger.error(f"Error during efficient HTML-based audit: {str(e)}")
            raise
    
    def _extract_context_for_step(self, messages: List[Dict[str, Any]], step: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context for a specific audit step."""
        context = {
            "relevant_messages": [],
            "key_events": [],
            "participants": set()
        }
        
        for message in messages:
            # Add message if it's relevant to the step
            if self._is_message_relevant(message, step):
                context["relevant_messages"].append(message)
                context["participants"].add(message["sender"])
                if message["recipients"]:
                    context["participants"].update(message["recipients"])
                
                # Extract key events
                if self._is_key_event(message, step):
                    context["key_events"].append({
                        "timestamp": message["timestamp"],
                        "type": self._get_event_type(message, step),
                        "description": message["content"][:100] + "..."
                    })
        
        return context
    
    def _is_message_relevant(self, message: Dict[str, Any], step: Dict[str, Any]) -> bool:
        """Determine if a message is relevant to a specific audit step."""
        # Add logic to determine relevance based on step type
        if step["category"] == "PNR":
            return any(keyword in message["content"].lower() for keyword in ["itinerary", "flight", "booking", "reservation"])
        elif step["category"] == "communication":
            return True  # All messages are relevant for communication analysis
        elif step["category"] == "policy and service":
            return any(keyword in message["content"].lower() for keyword in ["policy", "service", "requirement", "visa"])
        return False
    
    def _is_key_event(self, message: Dict[str, Any], step: Dict[str, Any]) -> bool:
        """Determine if a message represents a key event for the audit step."""
        # Add logic to identify key events based on step type
        if step["id"] == "limo_offering":
            return "limo" in message["content"].lower() or "car service" in message["content"].lower()
        elif step["id"] == "transit_visa_advisory":
            return "visa" in message["content"].lower() or "transit" in message["content"].lower()
        return False
    
    def _get_event_type(self, message: Dict[str, Any], step: Dict[str, Any]) -> str:
        """Get the type of event for a message."""
        # Add logic to categorize events based on step type
        if step["id"] == "limo_offering":
            return "limo_service_mentioned"
        elif step["id"] == "transit_visa_advisory":
            return "visa_requirement_discussed"
        return "general_message"
    
    def _generate_reasoning(self, audit_results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive reasoning for the audit results."""
        reasoning_parts = []
        
        # Group results by category
        category_results = {}
        for result in audit_results:
            category = result["category"]
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(result)
        
        # Generate reasoning for each category
        for category, results in category_results.items():
            reasoning_parts.append(f"\n{category.upper()} Analysis:")
            for result in results:
                reasoning_parts.append(f"\n{result['title']}:")
                reasoning_parts.append(f"Score: {result['score']}")
                reasoning_parts.append(f"Analysis: {result['analysis']}")
                if not result["passed"]:
                    reasoning_parts.append(f"Areas for Improvement: {result.get('improvements', 'None specified')}")
        
        return "\n".join(reasoning_parts)
    
    def _extract_context(self, audit_results: List[Dict[str, Any]]) -> str:
        """Extract context from audit results."""
        context_parts = []
        for result in audit_results:
            if result["category"] == "PNR":
                context_parts.append(f"{result['title']}: {result['analysis']}")
        return " | ".join(context_parts) if context_parts else "No specific context found"
    
    def _extract_participants(self, messages: List[Dict[str, Any]]) -> str:
        """Extract participants from email thread."""
        # This is a simple implementation - you might want to enhance it
        return "Participants extracted from email thread"
    
    def _analyze_tone(self, audit_results: List[Dict[str, Any]]) -> str:
        """Analyze the tone from audit results."""
        tone_parts = []
        for result in audit_results:
            if result["category"] == "communication":
                tone_parts.append(f"{result['title']}: {result['analysis']}")
        return " | ".join(tone_parts) if tone_parts else "No tone analysis available"
    
    def _check_security(self, audit_results: List[Dict[str, Any]]) -> str:
        """Check security aspects from audit results."""
        security_parts = []
        for result in audit_results:
            if "sensitive" in result["analysis"].lower() or "security" in result["analysis"].lower():
                security_parts.append(f"{result['title']}: {result['analysis']}")
        return " | ".join(security_parts) if security_parts else "No security concerns found"
    
    def _assess_effectiveness(self, audit_results: List[Dict[str, Any]]) -> str:
        """Assess communication effectiveness from audit results."""
        effectiveness_parts = []
        for result in audit_results:
            if result["category"] in ["communication", "policy and service"]:
                effectiveness_parts.append(f"{result['title']}: {result['analysis']}")
        return " | ".join(effectiveness_parts) if effectiveness_parts else "No effectiveness assessment available"
    
    def _generate_recommendations(self, audit_results: List[Dict[str, Any]]) -> str:
        """Generate recommendations based on audit results."""
        recommendations = []
        for result in audit_results:
            if not result["passed"] and result["is_critical"]:
                recommendations.append(f"Critical: {result['title']} - {result['analysis']}")
            elif not result["passed"]:
                recommendations.append(f"Improvement: {result['title']} - {result['analysis']}")
        return " | ".join(recommendations) if recommendations else "No specific recommendations" 