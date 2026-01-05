"""
Tests for LLM Analyzer Module

Tests OpenAI API integration with mocked responses.
No real API calls are made.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.analyzer import (
    analyze_job_posting,
    JobAnalysisResult,
    _parse_llm_response,
    _extract_json_from_text,
    validate_api_key
)


class TestJobAnalysisResult:
    """Tests for JobAnalysisResult dataclass."""
    
    def test_from_dict_valid_response(self, valid_llm_response):
        """Test creating result from valid LLM response dict."""
        result = JobAnalysisResult.from_dict(valid_llm_response)
        
        assert result.success is True
        assert result.job_title == "Senior Software Engineer"
        assert result.company == "Acme Corp"
        assert "Python" in result.hard_skills
        assert "Communication" in result.soft_skills
        assert result.seniority_level == "Senior"
    
    def test_from_dict_partial_response(self, partial_llm_response):
        """Test creating result from partial LLM response."""
        result = JobAnalysisResult.from_dict(partial_llm_response)
        
        assert result.success is True
        assert result.job_title == "Software Engineer"
        assert result.company is None
        assert result.responsibilities == []
    
    def test_from_dict_empty_response(self):
        """Test creating result from empty dict."""
        result = JobAnalysisResult.from_dict({})
        
        assert result.success is True
        assert result.job_title is None
        assert result.responsibilities == []
        assert result.hard_skills == []
    
    def test_error_factory(self):
        """Test error factory method."""
        result = JobAnalysisResult.error("Test error message")
        
        assert result.success is False
        assert result.error_message == "Test error message"
        assert result.job_title is None


class TestParseLlmResponse:
    """Tests for LLM response parsing."""
    
    def test_parse_valid_json(self, valid_llm_response):
        """Test parsing valid JSON response."""
        json_str = json.dumps(valid_llm_response)
        result = _parse_llm_response(json_str)
        
        assert result.success is True
        assert result.job_title == "Senior Software Engineer"
    
    def test_parse_json_with_extra_whitespace(self, valid_llm_response):
        """Test parsing JSON with extra whitespace."""
        json_str = "  \n" + json.dumps(valid_llm_response) + "\n  "
        result = _parse_llm_response(json_str)
        
        assert result.success is True
    
    def test_parse_malformed_json(self, malformed_llm_response):
        """Test handling of malformed JSON."""
        result = _parse_llm_response(malformed_llm_response)
        
        assert result.success is False
        assert "parse" in result.error_message.lower() or "json" in result.error_message.lower()
    
    def test_parse_non_object_json(self):
        """Test handling of JSON that isn't an object."""
        result = _parse_llm_response('["array", "not", "object"]')
        
        assert result.success is False


class TestExtractJsonFromText:
    """Tests for JSON extraction from mixed text."""
    
    def test_extracts_json_from_mixed_text(self):
        """Test extracting JSON from text with surrounding content."""
        text = '''Here's the analysis:
        
        {"job_title": "Engineer", "company": "Test Corp"}
        
        I hope this helps!
        '''
        result = _extract_json_from_text(text)
        
        assert result is not None
        assert result["job_title"] == "Engineer"
    
    def test_extracts_json_with_markdown(self):
        """Test extracting JSON from markdown-wrapped response."""
        text = '''```json
        {"job_title": "Developer"}
        ```'''
        result = _extract_json_from_text(text)
        
        assert result is not None
        assert result["job_title"] == "Developer"
    
    def test_returns_none_for_no_json(self):
        """Test that None is returned when no JSON found."""
        text = "This is just plain text with no JSON."
        result = _extract_json_from_text(text)
        
        assert result is None
    
    def test_returns_none_for_invalid_json(self):
        """Test that None is returned for invalid JSON."""
        text = "{ invalid: json }"
        result = _extract_json_from_text(text)
        
        assert result is None


class TestAnalyzeJobPosting:
    """Tests for the main analyze_job_posting function."""
    
    def test_returns_error_without_api_key(self, sample_job_text):
        """Test that error is returned without API key."""
        with patch.dict('os.environ', {}, clear=True):
            result = analyze_job_posting(sample_job_text, api_key=None)
        
        assert result.success is False
        assert "API key" in result.error_message
    
    def test_successful_analysis_with_mock(self, sample_job_text, mock_openai_success):
        """Test successful analysis with mocked OpenAI."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                sample_job_text,
                api_key="test-key",
                model="gpt-4o-mini"
            )
        
        assert result.success is True
        assert result.job_title == "Senior Software Engineer"
        assert result.tokens_used == 500
        assert result.model_used == "gpt-4o-mini"
    
    def test_handles_malformed_response(self, sample_job_text, mock_openai_malformed):
        """Test handling of malformed LLM response."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_malformed
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                sample_job_text,
                api_key="test-key"
            )
        
        assert result.success is False
    
    def test_handles_api_exception(self, sample_job_text):
        """Test handling of OpenAI API exceptions."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                sample_job_text,
                api_key="test-key"
            )
        
        assert result.success is False
        assert "error" in result.error_message.lower()
    
    def test_uses_correct_model(self, sample_job_text, mock_openai_success):
        """Test that specified model is used."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            analyze_job_posting(
                sample_job_text,
                api_key="test-key",
                model="gpt-4-turbo"
            )
            
            # Check that the call was made with correct model
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4-turbo"
    
    def test_uses_json_response_format(self, sample_job_text, mock_openai_success):
        """Test that JSON response format is requested."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            analyze_job_posting(
                sample_job_text,
                api_key="test-key"
            )
            
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["response_format"] == {"type": "json_object"}


class TestValidateApiKey:
    """Tests for API key validation."""
    
    def test_valid_key_returns_true(self):
        """Test that valid key returns True."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.models.list.return_value = []
            mock_openai_class.return_value = mock_client
            
            result = validate_api_key("valid-key")
            assert result is True
    
    def test_invalid_key_returns_false(self):
        """Test that invalid key returns False."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.models.list.side_effect = Exception("Invalid key")
            mock_openai_class.return_value = mock_client
            
            result = validate_api_key("invalid-key")
            assert result is False


class TestTokenUsageTracking:
    """Tests for token usage tracking."""
    
    def test_tracks_token_usage(self, sample_job_text, mock_openai_success):
        """Test that token usage is tracked."""
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                sample_job_text,
                api_key="test-key"
            )
        
        assert result.tokens_used == 500
    
    def test_handles_missing_usage(self, sample_job_text, valid_llm_response):
        """Test handling when usage info is missing."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(valid_llm_response)
        mock_response.usage = None  # No usage info
        
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                sample_job_text,
                api_key="test-key"
            )
        
        assert result.success is True
        assert result.tokens_used is None
