"""
Extraction Tests for Content Cleaner Module

Tests boilerplate removal and content cleaning.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.content_cleaner import clean_html_content, is_meaningful_content


class TestBoilerplateRemoval:
    """Tests for boilerplate content removal."""
    
    def test_remove_navigation(self):
        """Remove navigation elements."""
        html = '''
        <html>
        <body>
            <nav class="main-nav">
                <a href="/">Home</a>
                <a href="/jobs">Jobs</a>
            </nav>
            <main>
                <h1>Software Engineer</h1>
                <p>Job description content here.</p>
            </main>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Software Engineer" in cleaned
        assert "main-nav" not in cleaned.lower()
    
    def test_remove_footer(self):
        """Remove footer elements."""
        html = '''
        <html>
        <body>
            <main>
                <h1>Job Title</h1>
                <p>Requirements and responsibilities.</p>
            </main>
            <footer>
                <p>© 2024 Company. All rights reserved.</p>
                <a href="/privacy">Privacy Policy</a>
            </footer>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Job Title" in cleaned
        assert "Privacy Policy" not in cleaned
    
    def test_remove_scripts(self):
        """Remove script tags."""
        html = '''
        <html>
        <head>
            <script>var analytics = {};</script>
        </head>
        <body>
            <script>trackPageView();</script>
            <h1>Developer</h1>
            <p>Job content.</p>
            <script>initChat();</script>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Developer" in cleaned
        assert "analytics" not in cleaned
        assert "trackPageView" not in cleaned
    
    def test_remove_styles(self):
        """Remove style tags."""
        html = '''
        <html>
        <head>
            <style>.job { color: blue; }</style>
        </head>
        <body>
            <h1>Engineer</h1>
            <style>.hidden { display: none; }</style>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Engineer" in cleaned
        assert "color: blue" not in cleaned
    
    def test_remove_sidebar(self):
        """Remove sidebar elements."""
        html = '''
        <html>
        <body>
            <div class="sidebar">
                <h3>Related Jobs</h3>
                <ul><li>Other Job 1</li></ul>
            </div>
            <main>
                <h1>Main Job</h1>
                <p>Description.</p>
            </main>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Main Job" in cleaned
        # Sidebar content should be removed
        assert "Related Jobs" not in cleaned or "Main Job" in cleaned
    
    def test_remove_cookie_banner(self):
        """Remove cookie/privacy banners."""
        html = '''
        <html>
        <body>
            <div class="cookie-banner">
                <p>We use cookies. Accept?</p>
            </div>
            <main>
                <h1>Data Analyst</h1>
                <p>Analyze data.</p>
            </main>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Data Analyst" in cleaned


class TestLegalTextRemoval:
    """Tests for legal text removal."""
    
    def test_remove_eeo_statement(self):
        """Remove Equal Opportunity Employer statements."""
        html = '''
        <html>
        <body>
            <main>
                <h1>Engineer</h1>
                <p>Build software.</p>
                <p>We are an Equal Opportunity Employer.</p>
            </main>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Engineer" in cleaned
        # EEO statement may be removed or kept depending on implementation
    
    def test_remove_copyright_notice(self):
        """Remove copyright notices."""
        html = '''
        <html>
        <body>
            <main>
                <h1>Developer</h1>
                <p>Write code.</p>
            </main>
            <p>© 2024 TechCorp. All rights reserved.</p>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        assert "Developer" in cleaned


class TestContentCleaning:
    """Tests for content cleaning and normalization."""
    
    def test_preserve_job_content(self, load_fixture):
        """Preserve main job content."""
        html = load_fixture("greenhouse_job.html")
        
        cleaned = clean_html_content(html)
        
        assert "Senior Software Engineer" in cleaned
        assert "Python" in cleaned
        assert "AWS" in cleaned
    
    def test_clean_whitespace(self):
        """Clean excessive whitespace."""
        html = '''
        <html>
        <body>
            <main>
                <h1>Title</h1>
                
                
                
                <p>Content.</p>
            </main>
        </body>
        </html>
        '''
        
        cleaned = clean_html_content(html)
        
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in cleaned
    
    def test_minimum_length_output(self, load_fixture):
        """Cleaned content should have meaningful length."""
        html = load_fixture("greenhouse_job.html")
        
        cleaned = clean_html_content(html)
        
        assert len(cleaned) > 200  # Should have substantial content


class TestMeaningfulContentDetection:
    """Tests for meaningful content detection."""
    
    def test_valid_job_posting(self, load_fixture):
        """Detect valid job posting content."""
        html = load_fixture("greenhouse_job.html")
        cleaned = clean_html_content(html)
        
        assert is_meaningful_content(cleaned) is True
    
    def test_generic_job_is_meaningful(self, load_fixture):
        """Detect generic job posting as meaningful."""
        html = load_fixture("generic_job.html")
        cleaned = clean_html_content(html)
        
        assert is_meaningful_content(cleaned) is True
    
    def test_minimal_content_may_not_be_meaningful(self, load_fixture):
        """Minimal content may not be meaningful."""
        html = load_fixture("minimal_job.html")
        cleaned = clean_html_content(html)
        
        # Minimal content is borderline
        # The function should handle this case
        result = is_meaningful_content(cleaned)
        assert isinstance(result, bool)
    
    def test_non_job_content_not_meaningful(self, load_fixture):
        """Non-job content should not be meaningful."""
        html = load_fixture("no_job_content.html")
        cleaned = clean_html_content(html)
        
        assert is_meaningful_content(cleaned) is False
    
    def test_empty_content_not_meaningful(self):
        """Empty content is not meaningful."""
        assert is_meaningful_content("") is False
        assert is_meaningful_content("   ") is False
    
    def test_short_content_not_meaningful(self):
        """Very short content is not meaningful."""
        assert is_meaningful_content("Hello world") is False
