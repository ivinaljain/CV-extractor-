"""
Tests for LLM Prompts Module

Tests prompt generation and formatting.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.prompts import get_system_prompt, get_user_prompt


class TestGetSystemPrompt:
    """Tests for system prompt generation."""
    
    def test_returns_non_empty_string(self):
        """Test that system prompt is not empty."""
        prompt = get_system_prompt()
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_mentions_json_format(self):
        """Test that prompt requests JSON format."""
        prompt = get_system_prompt()
        
        assert "JSON" in prompt or "json" in prompt
    
    def test_mentions_key_fields(self):
        """Test that prompt mentions key extraction fields."""
        prompt = get_system_prompt()
        
        assert "job_title" in prompt
        assert "responsibilities" in prompt
        assert "skills" in prompt
        assert "ats_keywords" in prompt or "ATS" in prompt
    
    def test_mentions_seniority_levels(self):
        """Test that prompt describes seniority levels."""
        prompt = get_system_prompt()
        
        # Should mention various levels
        levels_found = any(level in prompt for level in 
                          ["Entry", "Junior", "Mid", "Senior", "Lead"])
        assert levels_found


class TestGetUserPrompt:
    """Tests for user prompt generation."""
    
    def test_includes_job_text(self, sample_job_text):
        """Test that user prompt includes the job text."""
        prompt = get_user_prompt(sample_job_text)
        
        assert sample_job_text in prompt or "Senior Software Engineer" in prompt
    
    def test_includes_json_structure(self, sample_job_text):
        """Test that prompt shows expected JSON structure."""
        prompt = get_user_prompt(sample_job_text)
        
        assert "job_title" in prompt
        assert "hard_skills" in prompt
        assert "soft_skills" in prompt
    
    def test_truncates_long_text(self):
        """Test that very long text is truncated."""
        # Create text longer than 15000 chars
        long_text = "A" * 20000
        prompt = get_user_prompt(long_text)
        
        # Should be truncated
        assert len(prompt) < len(long_text) + 1000  # Allow for template
        assert "truncated" in prompt.lower()
    
    def test_handles_empty_text(self):
        """Test handling of empty job text."""
        prompt = get_user_prompt("")
        
        # Should still return valid prompt
        assert "job_title" in prompt
    
    def test_handles_special_characters(self):
        """Test handling of special characters in job text."""
        job_text = """Job with "quotes" and {braces} and <tags>"""
        prompt = get_user_prompt(job_text)
        
        # Should not raise, should contain the text
        assert "quotes" in prompt


class TestPromptConsistency:
    """Tests for prompt consistency and quality."""
    
    def test_prompts_compatible(self, sample_job_text):
        """Test that system and user prompts work together."""
        system = get_system_prompt()
        user = get_user_prompt(sample_job_text)
        
        # Both should mention JSON
        assert "JSON" in system or "json" in system
        assert "JSON" in user or "json" in user
    
    def test_user_prompt_format_matches_system(self, sample_job_text):
        """Test that user prompt format matches system prompt description."""
        system = get_system_prompt()
        user = get_user_prompt(sample_job_text)
        
        # Check key fields appear in both
        for field in ["job_title", "responsibilities", "required_skills"]:
            assert field in system
            assert field in user
