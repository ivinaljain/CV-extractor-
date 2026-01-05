"""
Unit Tests for Source Detection Module

Tests the detection of job posting platforms from URLs.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extractor.source_detector import (
    detect_source,
    detect_greenhouse,
    detect_lever,
    detect_workday,
    get_source_display_name
)


class TestDetectGreenhouse:
    """Tests for Greenhouse URL detection."""
    
    def test_direct_greenhouse_url(self):
        """Test detection of direct boards.greenhouse.io URL."""
        url = "https://boards.greenhouse.io/acme/jobs/12345"
        assert detect_greenhouse(url) is True
    
    def test_greenhouse_with_gh_jid_param(self):
        """Test detection of embedded URL with gh_jid parameter."""
        url = "https://careers.company.com/jobs?gh_jid=12345"
        assert detect_greenhouse(url) is True
    
    def test_greenhouse_embed_url(self):
        """Test detection of Greenhouse embed URL."""
        url = "https://company.greenhouse.io/embed/job_board/js?for=company"
        assert detect_greenhouse(url) is True
    
    def test_greenhouse_job_app_url(self):
        """Test detection of job_app.greenhouse.io URL."""
        url = "https://job_app.greenhouse.io/apply/12345"
        assert detect_greenhouse(url) is True
    
    def test_non_greenhouse_url(self):
        """Test that non-Greenhouse URLs return False."""
        url = "https://www.linkedin.com/jobs/view/12345"
        assert detect_greenhouse(url) is False
    
    def test_greenhouse_case_insensitive(self):
        """Test that detection is case-insensitive."""
        url = "https://BOARDS.GREENHOUSE.IO/acme/jobs/12345"
        assert detect_greenhouse(url) is True


class TestDetectLever:
    """Tests for Lever URL detection."""
    
    def test_direct_lever_url(self):
        """Test detection of jobs.lever.co URL."""
        url = "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert detect_lever(url) is True
    
    def test_lever_with_apply(self):
        """Test detection of Lever URL with /apply suffix."""
        url = "https://jobs.lever.co/acme/a1b2c3d4-e5f6-7890-abcd-ef1234567890/apply"
        assert detect_lever(url) is True
    
    def test_lever_co_pattern(self):
        """Test detection of lever.co URL pattern."""
        url = "https://lever.co/company/abc123def-456"
        assert detect_lever(url) is True
    
    def test_non_lever_url(self):
        """Test that non-Lever URLs return False."""
        url = "https://boards.greenhouse.io/acme/jobs/12345"
        assert detect_lever(url) is False


class TestDetectWorkday:
    """Tests for Workday URL detection."""
    
    def test_myworkdayjobs_url(self):
        """Test detection of myworkdayjobs.com URL."""
        url = "https://company.wd5.myworkdayjobs.com/en-US/Careers/job/Engineer_R12345"
        assert detect_workday(url) is True
    
    def test_workday_job_url(self):
        """Test detection of workday.com job URL."""
        url = "https://company.workday.com/en-US/job/Software-Engineer/12345"
        assert detect_workday(url) is True
    
    def test_myworkdaysite_url(self):
        """Test detection of myworkdaysite.com URL."""
        url = "https://wd1.myworkdaysite.com/recruiting/company"
        assert detect_workday(url) is True
    
    def test_non_workday_url(self):
        """Test that non-Workday URLs return False."""
        url = "https://jobs.lever.co/company/12345"
        assert detect_workday(url) is False


class TestDetectSource:
    """Tests for the main detect_source function."""
    
    def test_detect_greenhouse(self, greenhouse_urls):
        """Test source detection for Greenhouse URLs."""
        assert detect_source(greenhouse_urls["direct"]) == "greenhouse"
        assert detect_source(greenhouse_urls["embedded"]) == "greenhouse"
    
    def test_detect_lever(self, lever_urls):
        """Test source detection for Lever URLs."""
        assert detect_source(lever_urls["direct"]) == "lever"
        assert detect_source(lever_urls["with_apply"]) == "lever"
    
    def test_detect_workday(self, workday_urls):
        """Test source detection for Workday URLs."""
        assert detect_source(workday_urls["direct"]) == "workday"
    
    def test_detect_generic(self, generic_urls):
        """Test source detection for generic URLs."""
        assert detect_source(generic_urls["linkedin"]) == "generic"
        assert detect_source(generic_urls["indeed"]) == "generic"
        assert detect_source(generic_urls["company"]) == "generic"
    
    def test_priority_greenhouse_over_generic(self):
        """Test that Greenhouse detection takes priority."""
        # URL that could be mistaken for generic but has gh_jid
        url = "https://careers.techcompany.com/apply?gh_jid=98765"
        assert detect_source(url) == "greenhouse"


class TestGetSourceDisplayName:
    """Tests for source display name function."""
    
    def test_greenhouse_display_name(self):
        assert get_source_display_name("greenhouse") == "Greenhouse"
    
    def test_lever_display_name(self):
        assert get_source_display_name("lever") == "Lever"
    
    def test_workday_display_name(self):
        assert get_source_display_name("workday") == "Workday"
    
    def test_generic_display_name(self):
        assert get_source_display_name("generic") == "Generic Job Site"
    
    def test_unknown_display_name(self):
        assert get_source_display_name("unknown_platform") == "Unknown"
