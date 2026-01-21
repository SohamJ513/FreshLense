# backend/crawler.py
import requests
from bs4 import BeautifulSoup, Comment
import time
from urllib.parse import urlparse
from typing import Optional, Tuple
import re
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

class ContentFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 FreshLenseBot/1.0'
        })
        self.domain_delays = {}  # Track last request time per domain

    def fetch_url(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Fetch HTML content from a URL with retries and error handling"""
        if not url or not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid URL format: {url}")
            return None
            
        domain = urlparse(url).netloc
        
        # Rate limiting per domain
        if domain in self.domain_delays:
            time_since_last = time.time() - self.domain_delays[domain]
            if time_since_last < 1.0:
                time.sleep(1.0 - time_since_last)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"🌐 Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=15, allow_redirects=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if not any(ct in content_type for ct in ['text/html', 'text/plain', 'application/xhtml']):
                    logger.warning(f"Unsupported content type: {content_type}")
                    return None
                
                self.domain_delays[domain] = time.time()
                logger.debug(f"✅ Successfully fetched {url} ({len(response.text)} bytes)")
                return response.text
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout on attempt {attempt + 1} for {url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1} for {url}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"🚫 HTTP error on attempt {attempt + 1} for {url}: {e}")
                if e.response.status_code in [404, 403, 401]:
                    # Don't retry for client errors
                    break
            except requests.RequestException as e:
                logger.warning(f"❌ Request failed on attempt {attempt + 1} for {url}: {e}")
            
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.debug(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"💥 All attempts failed for {url}")
                return None

    def extract_main_content(self, html: str, url: str) -> str:
        """Extract main content from HTML using BeautifulSoup"""
        if not html or not html.strip():
            logger.warning("Empty HTML content provided")
            return ""
            
        logger.debug(f"🔍 Extracting content from {url}")
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            unwanted_selectors = [
                'script', 'style', 'nav', 'footer', 'header', 'aside', 
                'form', 'iframe', '.advertisement', '.ad', '.ads',
                '.social-share', '.share-buttons', '.comments',
                '.cookie-banner', '.newsletter-signup', '.popup',
                '[role="banner"]', '[role="navigation"]', '[role="contentinfo"]'
            ]
            
            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Try to find main content using semantic selectors
            main_selectors = [
                'main', 'article', '[role="main"]', 
                '.content', '.main-content', '#content', '.page-content',
                '.post', '.blog-post', '.entry-content', '.post-content',
                '.documentation', '.docs-content', '.api-content',
                '.technical-content', '.tutorial-content', '.wiki-content',
                '.markdown-body', '.readme', '.doc-content'
            ]
            
            for selector in main_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                    if len(text) > 100:  # Increased threshold for meaningful content
                        logger.debug(f"✅ Found content with selector '{selector}': {len(text)} characters")
                        cleaned_text = self.clean_text(text)
                        if len(cleaned_text) > 50:
                            return cleaned_text
            
            # Fallback: Extract from meaningful paragraphs and divs
            meaningful_elements = soup.find_all(['p', 'div', 'section', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            meaningful_text = []
            
            for elem in meaningful_elements:
                # Skip if element contains mostly child elements (likely navigation)
                if len(elem.find_all()) > len(elem.get_text().split()) // 3:
                    continue
                    
                text = elem.get_text(separator=' ', strip=True)
                if self.is_meaningful_text(text):
                    meaningful_text.append(text)
            
            if meaningful_text:
                combined_text = '\n'.join(meaningful_text)
                logger.debug(f"✅ Found {len(meaningful_text)} meaningful elements: {len(combined_text)} characters")
                cleaned = self.clean_text(combined_text)
                if len(cleaned) > 50:
                    return cleaned
                
            # Final fallback: get all text
            all_text = soup.get_text(separator='\n', strip=True)
            cleaned_text = self.clean_text(all_text)
            
            if len(cleaned_text) > 50:
                logger.debug(f"✅ Final fallback extraction: {len(cleaned_text)} characters")
                return cleaned_text
            else:
                logger.warning("No substantial content found")
                return ""
                
        except Exception as e:
            logger.error(f"💥 Content extraction failed for {url}: {e}")
            return ""

    def is_meaningful_text(self, text: str) -> bool:
        """Check if text is meaningful (not navigation, ads, etc.) - MORE LENIENT FOR DOCS"""
        # 🚨 CRITICAL FIX: Reduced thresholds for technical documentation
        if len(text) < 15:  # Reduced from 30 to 15
            return False
        
        word_count = len(text.split())
        if word_count < 3:   # Reduced from 5 to 3 (technical docs have short factual sentences)
            return False
        
        # Skip common non-content patterns
        skip_patterns = [
            r'^\s*\d+\s*$',  # Just numbers
            r'^[A-Z\s]{10,}$',  # All caps (likely navigation) - made more strict
            r'^(Home|About|Contact|Menu|Login|Sign up|Subscribe|Search)(\s|$)',
            r'Cookie|Privacy Policy|Terms of Service|All rights reserved',
            r'^\d+\s+of\s+\d+$',  # Pagination
            r'^Page\s+\d+$',
            r'^©\s*\d{4}',
            r'^Back to top$',
            r'^Skip to main content$',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # 🚨 NEW: Explicitly allow technical content patterns
        technical_patterns = [
            r'\b(python|javascript|java|react|node|django|mongodb|docker|kubernetes)\b',
            r'\b\d+\.\d+(\.\d+)?\b',  # Version numbers
            r'\b\d+%\b',  # Percentages
            r'\b\d+x\b',  # Multipliers
            r'\b(faster|slower|better|performance|compatible|supports|requires)\b',
            r'\b(memory|cpu|storage|latency|throughput|index|query)\b',
        ]
        
        # If it matches technical patterns, be more lenient
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in technical_patterns):
            logger.debug(f"🔧 Allowing technical content: '{text}'")
            return True
        
        return True

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing noise and formatting - MORE LENIENT"""
        if not text:
            return ""
        
        lines = []
        seen_lines = set()  # Remove duplicates
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # 🚨 CRITICAL FIX: Reduced minimum line length for technical docs
            if len(line) < 10:  # Reduced from 20 to 10
                continue
            
            # Skip duplicate lines
            if line in seen_lines:
                continue
            
            # Check if line is meaningful (with new lenient rules)
            if self.is_meaningful_text(line):
                lines.append(line)
                seen_lines.add(line)
        
        # Join lines and clean up extra whitespace
        result = '\n'.join(lines)
        result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 consecutive newlines
        result = re.sub(r' {2,}', ' ', result)  # Remove extra spaces
        
        logger.debug(f"📝 Cleaned text length: {len(result)} characters")
        if result:
            logger.debug(f"📝 First 200 chars: {result[:200]}...")
        
        return result.strip()

    def get_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting purposes"""
        try:
            return urlparse(url).netloc
        except Exception:
            return "unknown"

    def fetch_and_extract(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch and extract content in one call
        Returns: (html, content) tuple
        """
        try:
            html = self.fetch_url(url)
            if html:
                content = self.extract_main_content(html, url)
                return html, content
            return None, None
        except Exception as e:
            logger.error(f"💥 fetch_and_extract failed for {url}: {e}")
            return None, None

    def validate_url(self, url: str) -> bool:
        """Validate if URL is properly formatted and accessible"""
        if not url or not isinstance(url, str):
            return False
        
        if not url.startswith(('http://', 'https://')):
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc and parsed.scheme)
        except Exception:
            return False

    def get_content_metadata(self, html: str, url: str) -> dict:
        """Extract metadata about the content"""
        if not html:
            return {}
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            metadata = {
                'title': '',
                'description': '',
                'language': '',
                'last_modified': None
            }
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Extract description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if desc_tag:
                metadata['description'] = desc_tag.get('content', '').strip()
            
            # Extract language
            html_tag = soup.find('html')
            if html_tag:
                metadata['language'] = html_tag.get('lang', '').strip()
            
            return metadata
        except Exception as e:
            logger.error(f"Metadata extraction error for {url}: {e}")
            return {}