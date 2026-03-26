# backend/app/services/ai_service.py
import os
import json
import logging
from groq import Groq
from typing import Dict, Any, Optional, List
from datetime import datetime
import difflib
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")  # Reusing same env var for simplicity
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. AI features will be disabled.")
            self.enabled = False
            return
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        self.enabled = True
        
        # Groq model selection
        self.model = os.getenv("OPENAI_MODEL", "llama-3.3-70b-versatile")
        self.temperature = 0.3  # Low temperature for consistent results
        
        logger.info(f"✅ AI Service initialized with Groq model: {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_change_summary(
        self, 
        old_content: str, 
        new_content: str,
        page_title: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Generate AI summary of what changed between two versions using Groq
        """
        if not self.enabled:
            return self._get_disabled_response()
        
        try:
            # Truncate content if too long (to save tokens)
            max_content_length = 4000  # Characters
            if len(old_content) > max_content_length:
                old_content = old_content[:max_content_length] + "... [truncated]"
            if len(new_content) > max_content_length:
                new_content = new_content[:max_content_length] + "... [truncated]"
            
            logger.info(f"Generating summary for '{page_title}'")
            
            # Create the prompt
            prompt = self._create_summary_prompt(old_content, new_content, page_title, url)
            
            # Call Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at analyzing content changes. Provide concise, accurate summaries in valid JSON format. Return ONLY the JSON, no other text."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse the JSON response
            result_text = response.choices[0].message.content.strip()
            
            # Clean up if response is wrapped in markdown code blocks
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0]
            elif result_text.startswith("```"):
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text)
            
            # Add metadata
            result["generated_at"] = datetime.utcnow().isoformat()
            result["model_used"] = self.model
            
            logger.info(f"Summary generated successfully")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {result_text if 'result_text' in locals() else 'No response'}")
            return self._get_fallback_summary(old_content, new_content, "JSON parsing error")
            
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}", exc_info=True)
            return self._get_fallback_summary(old_content, new_content, str(e))
    
    def _create_summary_prompt(
        self, 
        old_content: str, 
        new_content: str,
        page_title: str,
        url: str
    ) -> str:
        """Create the prompt for the AI"""
        return f"""
        Analyze the changes between two versions of content from: {page_title}
        URL: {url}
        
        OLD VERSION:
        {old_content}
        
        NEW VERSION:
        {new_content}
        
        Provide a JSON response with this EXACT structure:
        {{
            "summary": "A 2-3 sentence summary of what changed",
            "key_changes": ["list of 3-5 most important specific changes"],
            "change_type": "major" or "minor" or "cosmetic",
            "technical_impact": "How this affects developers/users (1 sentence)",
            "sentiment": "positive" or "negative" or "neutral",
            "recommendation": "What users should do about this change (1 sentence)"
        }}
        
        Focus on:
        - Technical accuracy
        - Actionable insights
        - Impact on users
        - Keep it concise
        
        Return ONLY the JSON object, no other text.
        """
    
    def _get_fallback_summary(self, old_content: str, new_content: str, error_msg: str) -> Dict[str, Any]:
        """Generate a simple fallback summary when AI fails"""
        # Simple diff-based summary
        old_lines = old_content.split('\n')
        new_lines = new_content.split('\n')
        
        diff = list(difflib.unified_diff(old_lines, new_lines, n=0))
        
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        if added == 0 and removed == 0:
            summary = "No significant changes detected."
        else:
            summary = f"Content changed: {added} lines added, {removed} lines removed."
        
        return {
            "summary": summary,
            "key_changes": [f"{added} lines added", f"{removed} lines removed"],
            "change_type": "major" if added + removed > 10 else "minor",
            "technical_impact": "Content was modified.",
            "sentiment": "neutral",
            "recommendation": "Review the changes to ensure accuracy.",
            "error": error_msg,
            "is_fallback": True,
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": "fallback"
        }
    
    def _get_disabled_response(self) -> Dict[str, Any]:
        """Return when AI service is disabled"""
        return {
            "summary": "AI summaries are disabled. Set OPENAI_API_KEY to enable.",
            "key_changes": [],
            "change_type": "unknown",
            "technical_impact": "N/A",
            "sentiment": "neutral",
            "recommendation": "Enable AI service in settings.",
            "disabled": True,
            "generated_at": datetime.utcnow().isoformat()
        }

# Add retry decorator if not already imported
from tenacity import retry, stop_after_attempt, wait_exponential

# Singleton instance
ai_service = AIService()