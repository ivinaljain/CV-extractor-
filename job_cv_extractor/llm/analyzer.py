"""
LLM Analyzer Module

Handles OpenAI API calls for job posting analysis.
Includes response validation and error handling.
"""

import json
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import logger
from .prompts import get_system_prompt, get_user_prompt

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI SDK not available")


@dataclass
class JobAnalysisResult:
    """Structured result from job posting analysis."""
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_summary: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
    hard_skills: List[str] = field(default_factory=list)
    soft_skills: List[str] = field(default_factory=list)
    ats_keywords: List[str] = field(default_factory=list)
    inferred_skills: List[str] = field(default_factory=list)
    seniority_level: Optional[str] = None
    years_of_experience: Optional[str] = None
    
    # Metadata
    success: bool = False
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobAnalysisResult':
        """Create JobAnalysisResult from parsed JSON response."""
        required_skills = data.get('required_skills', {})
        
        return cls(
            job_title=data.get('job_title'),
            company=data.get('company'),
            job_summary=data.get('job_summary'),
            responsibilities=data.get('responsibilities', []),
            hard_skills=required_skills.get('hard_skills', []),
            soft_skills=required_skills.get('soft_skills', []),
            ats_keywords=data.get('ats_keywords', []),
            inferred_skills=data.get('inferred_skills', []),
            seniority_level=data.get('seniority_level'),
            years_of_experience=data.get('years_of_experience'),
            success=True
        )
    
    @classmethod
    def error(cls, message: str) -> 'JobAnalysisResult':
        """Create an error result."""
        return cls(success=False, error_message=message)


def analyze_job_posting(
    job_text: str,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini"
) -> JobAnalysisResult:
    """
    Analyze job posting text using OpenAI API.
    
    Args:
        job_text: Cleaned job posting text
        api_key: OpenAI API key (uses env var if not provided)
        model: Model to use (default: gpt-4o-mini for cost efficiency)
    
    Returns:
        JobAnalysisResult with extracted information
    """
    if not OPENAI_AVAILABLE:
        return JobAnalysisResult.error("OpenAI SDK not installed. Run: pip install openai")
    
    # Get API key
    api_key = api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return JobAnalysisResult.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
    
    logger.info(f"Analyzing job posting with {model}")
    
    try:
        client = OpenAI(api_key=api_key)
        
        # Make API call
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": get_system_prompt()},
                {"role": "user", "content": get_user_prompt(job_text)}
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=2000,
            response_format={"type": "json_object"}  # Enforce JSON response
        )
        
        # Extract response content
        content = response.choices[0].message.content
        
        # Log token usage
        tokens_used = None
        if response.usage:
            tokens_used = response.usage.total_tokens
            logger.info(f"Tokens used: {tokens_used} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")
        
        # Parse JSON response
        result = _parse_llm_response(content)
        result.tokens_used = tokens_used
        result.model_used = model
        
        return result
    
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        logger.error(error_msg)
        return JobAnalysisResult.error(error_msg)
    
    except Exception as e:
        error_msg = f"OpenAI API error: {str(e)}"
        logger.error(error_msg)
        return JobAnalysisResult.error(error_msg)


def _parse_llm_response(content: str) -> JobAnalysisResult:
    """
    Parse and validate LLM response.
    
    Args:
        content: Raw response content from LLM
    
    Returns:
        JobAnalysisResult
    """
    # Try to parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        data = _extract_json_from_text(content)
        if data is None:
            return JobAnalysisResult.error("Could not parse response as JSON")
    
    # Validate required fields
    if not isinstance(data, dict):
        return JobAnalysisResult.error("Response is not a JSON object")
    
    # Create result
    result = JobAnalysisResult.from_dict(data)
    
    # Validate result
    if not result.job_title and not result.job_summary and not result.responsibilities:
        logger.warning("LLM response missing key fields")
    
    logger.info(f"Successfully parsed job analysis: {result.job_title or 'Unknown Title'}")
    
    return result


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to extract JSON object from text that may contain other content.
    
    Args:
        text: Text that may contain a JSON object
    
    Returns:
        Parsed JSON dict or None
    """
    import re
    
    # Try to find JSON object in text
    # Look for content between { and }
    match = re.search(r'\{[\s\S]*\}', text)
    
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    return None


def validate_api_key(api_key: str) -> bool:
    """
    Validate OpenAI API key by making a minimal API call.
    
    Args:
        api_key: OpenAI API key to validate
    
    Returns:
        True if key is valid
    """
    if not OPENAI_AVAILABLE:
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        # Make minimal API call to validate
        client.models.list()
        return True
    except Exception:
        return False
