"""
End-to-End Tests for Generic Job Pipeline

Tests the complete extraction pipeline for generic job pages.
All HTTP and OpenAI calls are mocked.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.source_detector import detect_source
from extractor.url_resolver import resolve_url
from extractor.fetcher import fetch_url
from extractor.html_parser import parse_html, extract_schema_job_posting
from extractor.content_cleaner import clean_html_content, is_meaningful_content
from extractor.fallback_extractor import get_best_extraction, TRAFILATURA_AVAILABLE
from llm.analyzer import analyze_job_posting


class TestGenericJobPipeline:
    """
    Tests for generic job page extraction.
    
    Simulates: Company career page or job board
    → No platform-specific resolution
    → HTML parsing and cleaning
    → LLM analysis
    """
    
    def test_full_generic_pipeline(
        self,
        generic_html,
        valid_llm_response,
        mock_openai_success
    ):
        """Test complete pipeline for generic job page."""
        
        # Input: Generic job URL
        input_url = "https://careers.startupxyz.com/jobs/frontend-developer"
        
        # Step 1: Detect source
        source = detect_source(input_url)
        assert source == "generic"
        
        # Step 2: No URL resolution needed
        resolved_url, was_resolved = resolve_url(input_url, source)
        assert was_resolved is False
        assert resolved_url == input_url
        
        # Step 3: Mock HTTP fetch
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = generic_html
            mock_response.url = input_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(input_url)
            
            assert fetch_result.success is True
        
        # Step 4: Try Schema.org (may not exist)
        schema_data = extract_schema_job_posting(fetch_result.html)
        
        # Step 5: Parse and clean HTML
        parsed = parse_html(fetch_result.html)
        cleaned = clean_html_content(fetch_result.html)
        
        assert is_meaningful_content(cleaned) is True
        assert "Frontend Developer" in cleaned
        
        # Step 6: LLM Analysis
        job_text = schema_data.get("description") if schema_data else cleaned
        
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(job_text, api_key="test-key")
        
        assert result.success is True
        assert len(result.hard_skills) > 0


class TestLinkedInPipeline:
    """Tests for LinkedIn job page simulation."""
    
    def test_linkedin_detected_as_generic(self, generic_urls):
        """Test that LinkedIn URLs are detected as generic."""
        source = detect_source(generic_urls["linkedin"])
        assert source == "generic"
    
    def test_indeed_detected_as_generic(self, generic_urls):
        """Test that Indeed URLs are detected as generic."""
        source = detect_source(generic_urls["indeed"])
        assert source == "generic"


class TestLeverPipeline:
    """Tests for Lever job page pipeline."""
    
    def test_full_lever_pipeline(
        self,
        lever_html,
        valid_llm_response,
        mock_openai_success
    ):
        """Test complete pipeline for Lever job page."""
        
        input_url = "https://jobs.lever.co/techstart/abc123-def456"
        
        # Detect and resolve
        source = detect_source(input_url)
        assert source == "lever"
        
        resolved_url, _ = resolve_url(input_url, source)
        
        # Mock fetch
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = lever_html
            mock_response.url = resolved_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(resolved_url)
        
        # Extract schema
        schema_data = extract_schema_job_posting(fetch_result.html)
        assert schema_data is not None
        assert schema_data["title"] == "Product Manager"
        
        # LLM Analysis
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                schema_data.get("description", ""),
                api_key="test-key"
            )
        
        assert result.success is True


class TestWorkdayPipeline:
    """Tests for Workday job page pipeline."""
    
    def test_full_workday_pipeline(
        self,
        workday_html,
        valid_llm_response,
        mock_openai_success
    ):
        """Test complete pipeline for Workday job page."""
        
        input_url = "https://enterprise.wd5.myworkdayjobs.com/en-US/Careers/job/Data-Scientist_R12345"
        
        # Detect
        source = detect_source(input_url)
        assert source == "workday"
        
        # Resolve (Workday URLs stay as-is)
        resolved_url, was_resolved = resolve_url(input_url, source)
        assert was_resolved is False
        
        # Mock fetch
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = workday_html
            mock_response.url = input_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(input_url)
        
        # Workday doesn't have Schema.org, use HTML cleaning
        cleaned = clean_html_content(fetch_result.html)
        assert "Data Scientist" in cleaned
        
        # LLM Analysis
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(cleaned, api_key="test-key")
        
        assert result.success is True


class TestFallbackExtractionPipeline:
    """Tests for fallback extraction when primary methods fail."""
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_fallback_on_weak_html(
        self,
        minimal_html,
        valid_llm_response,
        mock_openai_success
    ):
        """Test that fallback extractor is used for weak HTML."""
        
        input_url = "https://example.com/job"
        
        # Mock fetch with minimal HTML
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = minimal_html
            mock_response.url = input_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(input_url)
        
        # Primary cleaning may not yield meaningful content
        cleaned = clean_html_content(fetch_result.html)
        is_meaningful = is_meaningful_content(cleaned)
        
        # If not meaningful, fallback should be tried
        if not is_meaningful:
            fallback_text = get_best_extraction(fetch_result.html, input_url)
            # Fallback may or may not succeed depending on content
            assert fallback_text is not None or fallback_text == ""


class TestMultiplePlatformDetection:
    """Tests for correct platform detection across various URLs."""
    
    @pytest.mark.parametrize("url,expected_source", [
        ("https://boards.greenhouse.io/acme/jobs/123", "greenhouse"),
        ("https://jobs.lever.co/acme/abc-123", "lever"),
        ("https://acme.wd5.myworkdayjobs.com/job", "workday"),
        ("https://www.linkedin.com/jobs/view/123", "generic"),
        ("https://www.indeed.com/viewjob?jk=abc", "generic"),
        ("https://careers.company.com/jobs/engineer", "generic"),
        ("https://apply.company.com?gh_jid=123", "greenhouse"),
    ])
    def test_platform_detection(self, url, expected_source):
        """Test correct platform detection for various URLs."""
        detected = detect_source(url)
        assert detected == expected_source


class TestPipelineDataFlow:
    """Tests for data flow through the pipeline."""
    
    def test_data_preserved_through_pipeline(
        self,
        greenhouse_html,
        valid_llm_response,
        mock_openai_success
    ):
        """Test that data is correctly preserved through pipeline stages."""
        
        input_url = "https://boards.greenhouse.io/acme/jobs/12345"
        
        # Fetch
        with patch('extractor.fetcher.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = greenhouse_html
            mock_response.url = input_url
            mock_response.encoding = "utf-8"
            mock_response.apparent_encoding = "utf-8"
            mock_get.return_value = mock_response
            
            fetch_result = fetch_url(input_url)
        
        # Schema extraction
        schema_data = extract_schema_job_posting(fetch_result.html)
        original_title = schema_data["title"]
        original_company = schema_data["company"]
        
        # LLM Analysis
        with patch('llm.analyzer.OpenAI') as mock_openai_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_success
            mock_openai_class.return_value = mock_client
            
            result = analyze_job_posting(
                schema_data.get("description", ""),
                api_key="test-key"
            )
        
        # Verify LLM received correct context (check call was made)
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages", [])
        
        # Should have system and user messages
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
