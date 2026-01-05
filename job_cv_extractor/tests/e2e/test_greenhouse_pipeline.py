"""
End-to-End Tests for Greenhouse Job Pipeline

Tests the complete extraction pipeline for Greenhouse job postings.
All HTTP and OpenAI calls are mocked.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.source_detector import detect_source
from extractor.url_resolver import resolve_url
from extractor.fetcher import fetch_url
from extractor.html_parser import extract_schema_job_posting
from extractor.content_cleaner import clean_html_content, is_meaningful_content
from llm.analyzer import analyze_job_posting


@dataclass
class MockHttpResponse:
    """Mock HTTP response for requests."""
    status_code: int
    text: str
    url: str
    encoding: str = "utf-8"
    apparent_encoding: str = "utf-8"


class TestGreenhouseEmbeddedPipeline:
    """
    Tests for Greenhouse embedded job pages.
    
    Simulates: Company career page with gh_jid parameter
    → Resolves to Greenhouse
    → Fetches from resolved URL
    → Extracts job intelligence
    """
    
    def test_full_embedded_greenhouse_pipeline(
        self, 
        greenhouse_html, 
        valid_llm_response,
        mock_openai_success
    ):
        """Test complete pipeline for embedded Greenhouse job."""
        
        # Input: Embedded URL with gh_jid
        input_url = "https://careers.acme.com/jobs/software-engineer?gh_jid=12345"
        
        # Step 1: Detect source
        source = detect_source(input_url)
        assert source == "greenhouse"
        
        # Step 2: Resolve URL
        resolved_url, was_resolved = resolve_url(input_url, source)
        assert was_resolved is True
        assert "greenhouse.io" in resolved_url
        assert "12345" in resolved_url
        
        # Step 3: Mock HTTP fetch
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = greenhouse_html
            mock_response.url = resolved_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(resolved_url)
            
            assert fetch_result.success is True
            assert len(fetch_result.html) > 0
        
        # Step 4: Extract Schema.org data
        schema_data = extract_schema_job_posting(fetch_result.html)
        assert schema_data is not None
        assert schema_data["title"] == "Senior Software Engineer"
        assert schema_data["company"] == "Acme Corp"
        
        # Step 5: Clean HTML (fallback if needed)
        cleaned = clean_html_content(fetch_result.html)
        assert is_meaningful_content(cleaned) is True
        
        # Step 6: LLM Analysis (mocked)
        job_text = schema_data.get("description", cleaned)
        
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(job_text, api_key="test-key")
        
        # Verify final result
        assert result.success is True
        assert result.job_title is not None
        assert len(result.hard_skills) > 0
        assert len(result.ats_keywords) > 0


class TestGreenhouseDirectPipeline:
    """
    Tests for direct Greenhouse job pages.
    
    Simulates: Direct boards.greenhouse.io URL
    → No resolution needed
    → Direct fetch and extraction
    """
    
    def test_full_direct_greenhouse_pipeline(
        self,
        greenhouse_html,
        valid_llm_response,
        mock_openai_success
    ):
        """Test complete pipeline for direct Greenhouse URL."""
        
        # Input: Direct Greenhouse URL
        input_url = "https://boards.greenhouse.io/acme/jobs/12345"
        
        # Step 1: Detect source
        source = detect_source(input_url)
        assert source == "greenhouse"
        
        # Step 2: Resolve URL (should remain unchanged)
        resolved_url, was_resolved = resolve_url(input_url, source)
        assert was_resolved is False
        assert resolved_url == input_url
        
        # Step 3: Mock fetch and continue pipeline
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = greenhouse_html
            mock_response.url = input_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(input_url)
        
        # Extract and analyze
        schema_data = extract_schema_job_posting(fetch_result.html)
        assert schema_data is not None
        
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                schema_data.get("description", ""),
                api_key="test-key"
            )
        
        assert result.success is True


class TestGreenhouseErrorHandling:
    """Tests for error handling in Greenhouse pipeline."""
    
    def test_handles_fetch_failure(self):
        """Test handling when Greenhouse URL fetch fails."""
        input_url = "https://boards.greenhouse.io/acme/jobs/99999"
        
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            mock_response.url = input_url
            mock_response.reason = "Not Found"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(input_url)
        
        assert fetch_result.success is False
        assert fetch_result.status_code == 404
    
    def test_handles_missing_schema(self, workday_html):
        """Test handling when Greenhouse page lacks Schema.org data."""
        # Use HTML without Schema.org
        schema_data = extract_schema_job_posting(workday_html)
        
        # Should fall back to HTML parsing
        assert schema_data is None
        
        cleaned = clean_html_content(workday_html)
        assert len(cleaned) > 0
    
    def test_handles_llm_failure(self, greenhouse_html):
        """Test handling when LLM analysis fails."""
        job_text = clean_html_content(greenhouse_html)
        
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("Rate limit")
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(job_text, api_key="test-key")
        
        assert result.success is False
        assert "error" in result.error_message.lower()


class TestGreenhouseUrlVariations:
    """Tests for various Greenhouse URL formats."""
    
    @pytest.mark.parametrize("url,expected_resolved", [
        (
            "https://careers.company.com?gh_jid=12345",
            True
        ),
        (
            "https://boards.greenhouse.io/company/jobs/12345",
            False
        ),
        (
            "https://apply.company.com/job?gh_jid=99999&source=linkedin",
            True
        ),
    ])
    def test_url_resolution_variations(self, url, expected_resolved):
        """Test URL resolution for various Greenhouse URL formats."""
        source = detect_source(url)
        assert source == "greenhouse"
        
        resolved, was_resolved = resolve_url(url, source)
        assert was_resolved == expected_resolved
        
        if was_resolved:
            assert "greenhouse.io" in resolved
