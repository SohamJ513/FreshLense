# backend/app/crawler.py
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
                # Check if response exists before accessing status_code
                if hasattr(e, 'response') and e.response is not None and e.response.status_code in [404, 403, 401]:
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
                    # Preserve heading tags by getting text with structure
                    text = self._get_structured_text(main_content)
                    if len(text) > 50:
                        logger.debug(f"✅ Found content with selector '{selector}': {len(text)} characters")
                        cleaned_text = self.clean_text(text)
                        if len(cleaned_text) > 30:
                            return cleaned_text
            
            # Try to get content from body tag as fallback
            body_tag = soup.find('body')
            if body_tag:
                text = self._get_structured_text(body_tag)
                if len(text) > 50:
                    cleaned_text = self.clean_text(text)
                    if len(cleaned_text) > 30:
                        logger.debug(f"✅ Extracted from body tag: {len(cleaned_text)} characters")
                        return cleaned_text
            
            # Fallback: Extract from meaningful paragraphs and divs
            meaningful_elements = soup.find_all(['p', 'div', 'section', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            meaningful_text = []
            
            for elem in meaningful_elements:
                # Skip if element contains mostly child elements (likely navigation)
                if len(elem.find_all()) > len(elem.get_text().split()) // 2:
                    continue
                    
                text = elem.get_text(separator=' ', strip=True)
                if self.is_meaningful_text(text):
                    # Preserve heading context
                    if elem.name and elem.name.startswith('h'):
                        meaningful_text.append(f"\n{text}\n")
                    else:
                        meaningful_text.append(text)
            
            if meaningful_text:
                combined_text = '\n'.join(meaningful_text)
                logger.debug(f"✅ Found {len(meaningful_text)} meaningful elements: {len(combined_text)} characters")
                cleaned = self.clean_text(combined_text)
                if len(cleaned) > 30:
                    return cleaned
                
            # Final fallback: get all text
            all_text = self._get_structured_text(soup)
            cleaned_text = self.clean_text(all_text)
            
            # Ultimate rescue fallback - if cleaned_text is empty but original has content
            if not cleaned_text and len(all_text) > 50:
                # Simple cleaning without aggressive filtering
                lines = [line.strip() for line in all_text.split('\n') if len(line.strip()) > 10]
                if lines:
                    cleaned_text = '\n'.join(lines[:20])
                    logger.debug(f"✅ Rescue extraction with basic cleaning: {len(cleaned_text)} characters")
            
            if len(cleaned_text) > 30:
                logger.debug(f"✅ Final fallback extraction: {len(cleaned_text)} characters")
                return cleaned_text
            else:
                logger.warning("No substantial content found")
                return ""
                
        except Exception as e:
            logger.error(f"💥 Content extraction failed for {url}: {e}")
            return ""

    def _get_structured_text(self, element) -> str:
        """Extract text while preserving heading structure"""
        if not element:
            return ""
        
        parts = []
        for child in element.children:
            if child.name and child.name.startswith('h') and len(child.name) == 2:
                # Heading tag - add with newlines for emphasis
                heading_text = child.get_text(strip=True)
                if heading_text:
                    parts.append(f"\n{heading_text}\n")
            elif child.name == 'p':
                # Paragraph tag
                para_text = child.get_text(strip=True)
                if para_text:
                    parts.append(para_text)
            elif child.name == 'li':
                # List item
                li_text = child.get_text(strip=True)
                if li_text:
                    parts.append(f"• {li_text}")
            elif child.name == 'code' or child.name == 'pre':
                # Code block
                code_text = child.get_text(strip=True)
                if code_text:
                    parts.append(f"`{code_text}`")
            elif hasattr(child, 'children'):
                # Recursively process nested elements
                parts.append(self._get_structured_text(child))
            elif hasattr(child, 'string') and child.string and child.string.strip():
                # Direct text
                parts.append(child.string.strip())
        
        return '\n'.join(parts)

    def is_meaningful_text(self, text: str) -> bool:
        """Check if text is meaningful (not navigation, ads, etc.) - MORE LENIENT FOR DOCS"""
        # FIX: Pagination text should be filtered
        pagination_patterns = [
            r'^Page\s+\d+\s+of\s+\d+$',
            r'^\d+\s+of\s+\d+$',
            r'^Page\s+\d+$',
            r'^Go to page\s+\d+$',
            r'^Next$|^Previous$|^First$|^Last$',
        ]
        
        for pattern in pagination_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                logger.debug(f"🔧 Filtering pagination text: '{text}'")
                return False
        
        # Thresholds for technical documentation
        if len(text) < 8:
            return False
        
        word_count = len(text.split())
        if word_count < 2:
            return False
        
        # Skip common non-content patterns
        skip_patterns = [
            r'^\s*\d+\s*$',  # Just numbers
            r'^[A-Z\s]{15,}$',  # All caps (likely navigation)
            r'^(Home|About|Contact|Menu|Login|Sign up|Subscribe|Search)(\s|$)',
            r'Cookie|Privacy Policy|Terms of Service|All rights reserved',
            r'^©\s*\d{4}',
            r'^Back to top$',
            r'^Skip to main content$',
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Explicitly allow technical content patterns
        technical_patterns = [
            r'\b(python|javascript|java|react|node|django|mongodb|docker|kubernetes|fastapi|flask)\b',
            r'\b\d+\.\d+(\.\d+)?\b',  # Version numbers
            r'\b\d+%\b',  # Percentages
            r'\b\d+x\b',  # Multipliers
            r'\b(faster|slower|better|performance|compatible|supports|requires|EOL|Installation|Usage)\b',
            r'\b(memory|cpu|storage|latency|throughput|index|query)\b',
            r'\b(pip|npm|install|import|from|def|class)\b',  # Code keywords
            r'[<>=\+\-\*/]+',  # Operators that might appear in code
        ]
        
        # If it matches technical patterns, be more lenient
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in technical_patterns):
            logger.debug(f"🔧 Allowing technical content: '{text[:50]}...'")
            return True
        
        # Allow text with reasonable length that's not filtered by patterns
        if len(text) > 20 and word_count > 2:
            return True
        
        return False

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing noise and formatting - MORE LENIENT"""
        if not text:
            return ""
        
        # First, split into lines and remove duplicates
        lines = []
        seen_lines = set()
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip duplicate lines (case-insensitive for better deduplication)
            line_lower = line.lower()
            if line_lower in seen_lines:
                logger.debug(f"🔧 Removing duplicate line: '{line[:50]}...'")
                continue
            
            # Keep short lines that contain technical keywords
            technical_keywords = ['python', 'java', 'react', 'docker', 'pip', 'npm', 'eol', 'api', 'v2', 'v3', 
                                  'installation', 'usage', 'example', 'code', 'function', 'class']
            is_technical = any(keyword in line.lower() for keyword in technical_keywords)
            
            # Check if line is meaningful (with new lenient rules)
            if self.is_meaningful_text(line) or (is_technical and len(line) >= 3):
                lines.append(line)
                seen_lines.add(line_lower)
        
        # If no lines were kept but original text has content, try a simpler approach
        if not lines and len(text) > 20:
            # Simple fallback: return unique lines with basic cleaning
            unique_lines = []
            seen = set()
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 5 and line.lower() not in seen:
                    unique_lines.append(line)
                    seen.add(line.lower())
            
            if unique_lines:
                result = '\n'.join(unique_lines[:20])
                if len(result) > 20:
                    logger.debug(f"✅ Fallback cleaning with unique lines: {len(result)} characters")
                    return result
        
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
            domain = urlparse(url).netloc
            # Return empty string for invalid URLs instead of "unknown"
            return domain if domain else ""
        except Exception:
            return ""

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