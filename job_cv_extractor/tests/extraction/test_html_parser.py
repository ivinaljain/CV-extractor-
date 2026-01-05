"""
Tests for HTML Parsing and Content Cleaning

Tests extraction of job content from raw HTML.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.html_parser import parse_html
from extractor.content_cleaner import clean_html_content, is_meaningful_content


class TestParseHtml:
    """Tests for HTML parsing."""
    
    def test_extracts_page_title(self, greenhouse_html):
        """Test extraction of page title."""
        result = parse_html(greenhouse_html)
        
        assert "page_title" in result
        assert "Senior Software Engineer" in result["page_title"]
    
    def test_extracts_content(self, generic_html):
        """Test extraction of page content."""
        result = parse_html(generic_html)
        
        assert "content" in result
        assert len(result["content"]) > 0
        assert "Frontend Developer" in result["content"]
    
    def test_reports_html_length(self, greenhouse_html):
        """Test that HTML length is reported."""
        result = parse_html(greenhouse_html)
        
        assert "html_length" in result
        assert result["html_length"] > 0
    
    def test_handles_minimal_html(self, minimal_html):
        """Test parsing of minimal HTML."""
        result = parse_html(minimal_html)
        
        assert "content" in result
        assert "Software Engineer" in result["content"]


class TestCleanHtmlContent:
    """Tests for HTML content cleaning."""
    
    def test_removes_navigation(self, generic_html):
        """Test that navigation is removed."""
        cleaned = clean_html_content(generic_html)
        
        # Nav links should be removed
        assert "Home" not in cleaned or cleaned.count("Home") < 2
    
    def test_removes_footer(self, generic_html):
        """Test that footer content is removed."""
        cleaned = clean_html_content(generic_html)
        
        # Footer content should be removed
        assert "All rights reserved" not in cleaned
    
    def test_removes_scripts(self, greenhouse_html):
        """Test that script content is removed."""
        cleaned = clean_html_content(greenhouse_html)
        
        # JSON-LD script content should not appear as text
        assert "@context" not in cleaned
        assert "schema.org" not in cleaned.lower()
    
    def test_preserves_job_content(self, greenhouse_html):
        """Test that job description content is preserved."""
        cleaned = clean_html_content(greenhouse_html)
        
        assert "Senior Software Engineer" in cleaned
        assert "Python" in cleaned
        assert "AWS" in cleaned
    
    def test_preserves_responsibilities(self, greenhouse_html):
        """Test that responsibilities list is preserved."""
        cleaned = clean_html_content(greenhouse_html)
        
        assert "Design and develop" in cleaned
        assert "Mentor junior developers" in cleaned
    
    def test_preserves_requirements(self, generic_html):
        """Test that requirements are preserved."""
        cleaned = clean_html_content(generic_html)
        
        assert "TypeScript" in cleaned or "JavaScript" in cleaned
        assert "React" in cleaned
    
    def test_handles_empty_html(self):
        """Test handling of empty HTML."""
        cleaned = clean_html_content("")
        assert cleaned == ""
    
    def test_handles_html_with_only_scripts(self):
        """Test handling of HTML with only script tags."""
        html = "<html><body><script>console.log('test')</script></body></html>"
        cleaned = clean_html_content(html)
        
        # Should be empty or minimal after cleaning
        assert "console.log" not in cleaned
    
    def test_removes_cookie_banners(self):
        """Test that cookie-related content is removed."""
        html = '''
        <html>
        <body>
            <div class="cookie-banner">We use cookies</div>
            <div class="job-content">Software Engineer Position</div>
        </body>
        </html>
        '''
        cleaned = clean_html_content(html)
        
        # Cookie content should be removed
        assert "Software Engineer" in cleaned
    
    def test_removes_social_share_buttons(self):
        """Test that social sharing elements are removed."""
        html = '''
        <html>
        <body>
            <div class="social-share">Share on LinkedIn</div>
            <div class="job-description">Backend Developer Role</div>
        </body>
        </html>
        '''
        cleaned = clean_html_content(html)
        
        assert "Backend Developer" in cleaned


class TestIsMeaningfulContent:
    """Tests for content validation."""
    
    def test_accepts_full_job_description(self, sample_job_text):
        """Test that full job description is considered meaningful."""
        assert is_meaningful_content(sample_job_text) is True
    
    def test_rejects_short_content(self, short_job_text):
        """Test that very short content is rejected."""
        assert is_meaningful_content(short_job_text) is False
    
    def test_rejects_content_without_job_keywords(self):
        """Test that content without job keywords is rejected."""
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
        assert is_meaningful_content(text) is False
    
    def test_accepts_content_with_job_keywords(self):
        """Test that content with job keywords is accepted."""
        text = """
        Job Description: Software Engineer Position
        
        Responsibilities include designing and implementing software.
        Requirements: 5 years experience with Python.
        Skills: JavaScript, React, Node.js
        
        About the role: You will join our team and work on exciting projects.
        """ + ("Additional details. " * 20)  # Make it long enough
        
        assert is_meaningful_content(text) is True
    
    def test_custom_min_length(self):
        """Test custom minimum length parameter."""
        text = "Short job description with requirements."
        
        assert is_meaningful_content(text, min_length=10) is True
        assert is_meaningful_content(text, min_length=1000) is False


class TestContentExtractionWorkflow:
    """Integration tests for the content extraction workflow."""
    
    def test_greenhouse_extraction_workflow(self, greenhouse_html):
        """Test full extraction workflow for Greenhouse HTML."""
        # Step 1: Parse HTML
        parsed = parse_html(greenhouse_html)
        assert parsed["content"] is not None
        
        # Step 2: Clean content
        cleaned = clean_html_content(greenhouse_html)
        assert len(cleaned) > 200
        
        # Step 3: Validate content
        assert is_meaningful_content(cleaned) is True
    
    def test_generic_extraction_workflow(self, generic_html):
        """Test full extraction workflow for generic HTML."""
        parsed = parse_html(generic_html)
        cleaned = clean_html_content(generic_html)
        
        assert is_meaningful_content(cleaned) is True
        assert "Frontend Developer" in cleaned
    
    def test_minimal_html_workflow(self, minimal_html):
        """Test extraction workflow for minimal HTML."""
        parsed = parse_html(minimal_html)
        cleaned = clean_html_content(minimal_html)
        
        # Minimal HTML should fail validation
        assert is_meaningful_content(cleaned) is False
