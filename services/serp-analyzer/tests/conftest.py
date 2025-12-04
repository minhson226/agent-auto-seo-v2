"""Pytest configuration for SERP Analyzer tests."""

import pytest


@pytest.fixture
def mock_html_page():
    """Return mock HTML for content analysis tests."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page Title</title>
        <meta name="description" content="This is a test page description.">
    </head>
    <body>
        <h1>Main Heading</h1>
        <p>This is the first paragraph with some content.</p>
        
        <h2>First Section</h2>
        <p>More content here in the first section.</p>
        <img src="image1.jpg" alt="Image 1">
        
        <h2>Second Section</h2>
        <p>Content in the second section.</p>
        <img src="image2.jpg">
        
        <h3>Subsection</h3>
        <p>Subsection content.</p>
        
        <a href="/internal-page">Internal Link</a>
        <a href="https://external.com/page">External Link</a>
    </body>
    </html>
    """
