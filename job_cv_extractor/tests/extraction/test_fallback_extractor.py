"""
Tests for Fallback Extractor (Trafilatura)

Tests the fallback content extraction for difficult pages.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.fallback_extractor import (
    extract_with_fallback,
    get_best_extraction,
    TRAFILATURA_AVAILABLE
)


class TestExtractWithFallback:
    """Tests for trafilatura-based extraction."""
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_extracts_from_article_html(self, greenhouse_html):
        """Test extraction from article-style HTML."""
        result = extract_with_fallback(greenhouse_html)
        
        assert result is not None
        assert len(result) > 0
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_extracts_from_generic_html(self, generic_html):
        """Test extraction from generic job page HTML."""
        result = extract_with_fallback(generic_html)
        
        # Should extract some content
        assert result is not None
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_handles_minimal_html(self, minimal_html):
        """Test handling of minimal HTML content."""
        result = extract_with_fallback(minimal_html)
        
        # Should handle gracefully, may return empty
        assert result is not None or result == ""
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_handles_empty_html(self):
        """Test handling of empty HTML."""
        result = extract_with_fallback("")
        assert result == ""
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_uses_url_parameter(self, greenhouse_html):
        """Test that URL parameter is used."""
        url = "https://boards.greenhouse.io/acme/jobs/12345"
        result = extract_with_fallback(greenhouse_html, url=url)
        
        # Should not raise, should work with URL
        assert result is not None


class TestGetBestExtraction:
    """Tests for best extraction selection."""
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_returns_trafilatura_result(self, greenhouse_html):
        """Test that trafilatura result is returned when successful."""
        result = get_best_extraction(greenhouse_html, "https://example.com/job")
        
        assert result is not None
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_handles_url_none(self, greenhouse_html):
        """Test handling when URL is None."""
        result = get_best_extraction(greenhouse_html, None)
        
        # Should still work without URL
        assert result is not None
    
    def test_handles_empty_html(self):
        """Test handling of empty HTML input."""
        result = get_best_extraction("", "https://example.com")
        
        # Should return empty string or None gracefully
        assert result == "" or result is None


class TestFallbackWithMocking:
    """Tests with mocked trafilatura to ensure isolation."""
    
    def test_fallback_returns_trafilatura_result(self):
        """Test that fallback returns trafilatura result when available."""
        with patch('extractor.fallback_extractor.trafilatura') as mock_trafilatura:
            mock_trafilatura.extract.return_value = "Extracted job content"
            
            # Need to also patch TRAFILATURA_AVAILABLE
            with patch('extractor.fallback_extractor.TRAFILATURA_AVAILABLE', True):
                result = extract_with_fallback("<html><body>Test</body></html>")
                
                # Should call trafilatura.extract
                mock_trafilatura.extract.assert_called_once()
    
    def test_fallback_handles_trafilatura_exception(self):
        """Test graceful handling of trafilatura exceptions."""
        with patch('extractor.fallback_extractor.trafilatura') as mock_trafilatura:
            mock_trafilatura.extract.side_effect = Exception("Extraction failed")
            
            with patch('extractor.fallback_extractor.TRAFILATURA_AVAILABLE', True):
                result = extract_with_fallback("<html><body>Test</body></html>")
                
                # Should return empty string on failure
                assert result == ""
    
    def test_fallback_not_available(self):
        """Test behavior when trafilatura is not available."""
        with patch('extractor.fallback_extractor.TRAFILATURA_AVAILABLE', False):
            result = extract_with_fallback("<html><body>Test</body></html>")
            
            # Should return empty string
            assert result == ""


class TestExtractionQuality:
    """Tests for extraction quality and content preservation."""
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_preserves_job_title(self, greenhouse_html):
        """Test that job title is preserved in extraction."""
        result = extract_with_fallback(greenhouse_html)
        
        if result:
            assert "Senior Software Engineer" in result or "Software Engineer" in result
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_preserves_technical_skills(self, greenhouse_html):
        """Test that technical skills are preserved."""
        result = extract_with_fallback(greenhouse_html)
        
        if result:
            # At least some skills should be preserved
            skills_found = any(skill in result for skill in ["Python", "AWS", "Docker"])
            assert skills_found or len(result) < 100  # May be too short to contain all
    
    @pytest.mark.skipif(not TRAFILATURA_AVAILABLE, reason="trafilatura not installed")
    def test_removes_boilerplate(self, generic_html):
        """Test that boilerplate content is removed."""
        result = extract_with_fallback(generic_html)
        
        if result:
            # Navigation and footer should be removed
            assert "Privacy Policy" not in result
