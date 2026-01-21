# backend/services/serp_service.py
import os
import httpx
import asyncio
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

class SERPService:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"
        print(f"🔧 DEBUG: SERPService initialized with API key: {self.api_key[:10] if self.api_key else 'NOT FOUND'}...")
        
    async def search_technical_claim(self, claim: str, technology_context: List[str] = None) -> Dict[str, Any]:
        """Search for evidence about a technical claim"""
        print(f"🌐 DEBUG: SERP API called for claim: {claim}")
        print(f"🔧 DEBUG: Technology context: {technology_context}")
        
        if not self.api_key:
            error_msg = "SERPAPI_API_KEY not configured"
            print(f"❌ DEBUG: {error_msg}")
            return {"error": error_msg}
        
        # Enhance query with technical context
        query = self._build_technical_query(claim, technology_context)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "q": query,
                    "api_key": self.api_key,
                    "engine": "google",
                    "num": 10  # Increased from 5 to 10 for better coverage
                }
                
                print(f"🌐 DEBUG: Making SERP API request with query: {query}")
                response = await client.get(self.base_url, params=params)
                data = response.json()
                
                print(f"🌐 DEBUG: SERP API response status: {response.status_code}")
                print(f"🌐 DEBUG: Found {len(data.get('organic_results', []))} organic results")
                
                return self._process_serp_results(data, claim)
                
        except Exception as e:
            error_msg = f"SERP API call failed: {str(e)}"
            print(f"❌ DEBUG: {error_msg}")
            return {"error": error_msg}
    
    def _build_technical_query(self, claim: str, technology_context: List[str]) -> str:
        """Build optimized query for technical fact-checking"""
        # Clean and improve the claim
        clean_claim = claim.strip()
        
        # Extract key technical elements for better searching
        key_elements = self._extract_key_elements(clean_claim)
        
        # Build query based on claim type
        if "compatible" in clean_claim.lower() or "supports" in clean_claim.lower():
            # For compatibility claims, search for official compatibility docs
            query = self._build_compatibility_query(clean_claim, key_elements, technology_context)
        elif "performance" in clean_claim.lower() or "faster" in clean_claim.lower() or "reduces" in clean_claim.lower():
            # For performance claims, search for benchmarks
            query = self._build_performance_query(clean_claim, key_elements, technology_context)
        elif "secure" in clean_claim.lower() or "security" in clean_claim.lower():
            # For security claims, search for security documentation
            query = self._build_security_query(clean_claim, key_elements, technology_context)
        else:
            # Generic technical claim
            query = self._build_generic_query(clean_claim, key_elements, technology_context)
        
        print(f"🔍 DEBUG: Final query: {query}")
        return query

    def _extract_key_elements(self, claim: str) -> Dict[str, Any]:
        """Extract key technical elements from claim"""
        elements = {
            "versions": re.findall(r'\b\d+\.\d+(?:\.\d+)?\b', claim),
            "technologies": [],
            "numbers": re.findall(r'\b\d+(?:\.\d+)?%?\b', claim),
            "comparison_terms": []
        }
        
        # Detect technologies - EXPANDED LIST
        tech_patterns = {
            "react": r"\breact\b",
            "node": r"\bnode\.?js\b", 
            "python": r"\bpython\b",
            "docker": r"\bdocker\b",
            "javascript": r"\bjavascript\b",
            "django": r"\bdjango\b",
            "java": r"\bjava\b",
            "kubernetes": r"\bkubernetes\b",
            "mongodb": r"\bmongodb\b",
            "postgresql": r"\bpostgresql\b",
            "mysql": r"\bmysql\b",
            "redis": r"\bredis\b",
            "tensorflow": r"\btensorflow\b",
            "pytorch": r"\bpytorch\b",
            "fastapi": r"\bfastapi\b",
            "flask": r"\bflask\b",
            "spring": r"\bspring\b",
            "aws": r"\baws\b",
            "azure": r"\bazure\b",
            "gcp": r"\bgcp\b|google cloud"
        }
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, claim, re.IGNORECASE):
                elements["technologies"].append(tech)
        
        # Detect comparison terms - EXPANDED LIST
        comparison_terms = ["faster", "slower", "better", "worse", "compatible", "supports", "performance", "reduces", "development", "time", "improves", "handles", "scales"]
        elements["comparison_terms"] = [term for term in comparison_terms if term in claim.lower()]
        
        print(f"🔧 DEBUG: Extracted elements: {elements}")
        return elements

    def _build_compatibility_query(self, claim: str, elements: Dict, technology_context: List[str]) -> str:
        """Build query for compatibility claims"""
        tech_str = " ".join(elements["technologies"])
        version_str = " ".join(elements["versions"])
        
        # Handle "all versions" claims specifically
        if "all" in claim.lower() and "version" in claim.lower():
            if tech_str:
                return f"{tech_str} version compatibility requirements supported versions documentation"
        
        if tech_str and version_str:
            return f"{tech_str} {version_str} compatibility requirements official documentation"
        elif tech_str:
            return f"{tech_str} system requirements compatibility"
        else:
            # Use specific claim for better results
            clean_claim = re.sub(r'\s+', ' ', claim.strip())
            return f'"{clean_claim}" documentation requirements'

    def _build_performance_query(self, claim: str, elements: Dict, technology_context: List[str]) -> str:
        """Build query for performance claims - MORE SPECIFIC"""
        tech_str = " ".join(elements["technologies"])
        
        # 🚨 CRITICAL FIX: Build more specific queries based on claim content
        claim_lower = claim.lower()
        
        # Specific technology performance queries
        if "pypy" in claim_lower and "cpython" in claim_lower:
            return "pypy vs cpython performance benchmarks comparison"
        elif "numpy" in claim_lower and "python loops" in claim_lower:
            return "numpy vectorization performance vs python loops benchmarks"
        elif "docker" in claim_lower and "virtual machines" in claim_lower:
            return "docker containers vs virtual machines performance benchmarks"
        elif "react" in claim_lower and "performance" in claim_lower:
            return "react performance benchmarks optimization"
        elif "python" in claim_lower and elements["versions"]:
            # Python version performance
            version_str = " ".join(elements["versions"])
            return f"python {version_str} performance benchmarks improvements"
        
        # Handle development time reduction claims
        if "development" in claim_lower and "time" in claim_lower:
            if tech_str:
                return f"{tech_str} development productivity benchmarks case studies"
        
        # Fallback to technology-specific performance query
        if tech_str:
            version_str = " ".join(elements["versions"])
            if version_str:
                return f"{tech_str} {version_str} performance benchmarks official"
            else:
                return f"{tech_str} performance benchmarks comparison studies"
        else:
            # Use the claim but make it search-friendly
            clean_claim = re.sub(r'\s+', ' ', claim.strip())
            return f'"{clean_claim}" benchmarks performance tests'

    def _build_security_query(self, claim: str, elements: Dict, technology_context: List[str]) -> str:
        """Build query for security claims"""
        tech_str = " ".join(elements["technologies"])
        
        if tech_str:
            return f"{tech_str} security best practices documentation vulnerabilities"
        else:
            clean_claim = re.sub(r'\s+', ' ', claim.strip())
            return f'"{clean_claim}" security analysis documentation'

    def _build_generic_query(self, claim: str, elements: Dict, technology_context: List[str]) -> str:
        """Build query for generic technical claims"""
        tech_str = " ".join(elements["technologies"])
        
        if tech_str:
            # Use technology + context from claim
            claim_lower = claim.lower()
            if "memory" in claim_lower or "ram" in claim_lower:
                return f"{tech_str} memory requirements usage documentation"
            elif "storage" in claim_lower or "disk" in claim_lower:
                return f"{tech_str} storage requirements documentation"
            elif "concurrent" in claim_lower or "connections" in claim_lower:
                return f"{tech_str} scalability concurrency documentation"
            else:
                return f"{tech_str} official documentation specifications"
        else:
            # Use the original claim but make it more search-friendly
            clean_claim = re.sub(r'\b(all|every|completely|100%)\b', '', claim, flags=re.IGNORECASE)
            clean_claim = re.sub(r'\s+', ' ', clean_claim.strip())
            return f'"{clean_claim}" technical documentation specifications'
    
    def _process_serp_results(self, serp_data: Dict, original_claim: str) -> Dict[str, Any]:
        """Process SERP results to extract evidence"""
        if "error" in serp_data:
            print(f"❌ DEBUG: SERP API error: {serp_data['error']}")
            return {"error": serp_data["error"]}
        
        results = {
            "total_results": 0,
            "authoritative_sources": [],
            "contradicting_sources": [],
            "supporting_sources": [],
            "confidence_score": 0.0,
            "key_evidence": []
        }
        
        organic_results = serp_data.get("organic_results", [])
        results["total_results"] = len(organic_results)
        
        print(f"📊 DEBUG: Processing {len(organic_results)} organic results")
        
        # Analyze each result
        for i, result in enumerate(organic_results[:8]):
            source_analysis = self._analyze_source(result, original_claim)
            
            if source_analysis["authoritative"]:
                results["authoritative_sources"].append(source_analysis)
            
            if source_analysis["supports_claim"]:
                results["supporting_sources"].append(source_analysis)
            elif source_analysis["contradicts_claim"]:
                results["contradicting_sources"].append(source_analysis)
                
            if source_analysis["key_evidence"]:
                results["key_evidence"].append(source_analysis["key_evidence"])
            
            print(f"📖 DEBUG: Result {i+1}: {source_analysis['title'][:50]}... - "
                  f"Auth: {source_analysis['authoritative']}, "
                  f"Supports: {source_analysis['supports_claim']}, "
                  f"Contradicts: {source_analysis['contradicts_claim']}")
        
        # Calculate confidence based on evidence
        results["confidence_score"] = self._calculate_confidence(results)
        
        print(f"✅ DEBUG: SERP Analysis Complete - "
              f"Supporting: {len(results['supporting_sources'])}, "
              f"Contradicting: {len(results['contradicting_sources'])}, "
              f"Authoritative: {len(results['authoritative_sources'])}, "
              f"Confidence: {results['confidence_score']}")
        
        return results
    
    def _analyze_source(self, result: Dict, claim: str) -> Dict[str, Any]:
        """Analyze individual source for authority and relevance"""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        link = result.get("link", "")
        
        # 🚨 CRITICAL FIX: COMPLETE AUTHORITATIVE DOMAINS LIST
        authoritative_domains = [
            # Official Documentation
            "docs.python.org", "nodejs.org", "reactjs.org", "react.dev", "vuejs.org", "angular.io",
            "developer.mozilla.org", "docker.com", "kubernetes.io", "djangoproject.com", "flask.palletsprojects.com",
            "fastapi.tiangolo.com", "spring.io", "laravel.com", "expressjs.com", "nextjs.org", "svelte.dev",
            
            # Cloud Providers
            "aws.amazon.com", "azure.microsoft.com", "cloud.google.com", "digitalocean.com", "heroku.com",
            "vercel.com", "netlify.com",
            
            # Database & Tools
            "mongodb.com", "postgresql.org", "mysql.com", "redis.io", "elastic.co", "cassandra.apache.org",
            "couchbase.com", "neo4j.com", "influxdata.com",
            
            # Package Managers & Repos
            "npmjs.com", "pypi.org", "github.com", "gitlab.com", "bitbucket.org",
            
            # Standards & Security
            "w3.org", "ietf.org", "owasp.org", "nist.gov", "sans.org", "cve.mitre.org",
            
            # Company Documentation
            "python.org", "java.com", "oracle.com", "microsoft.com", "apple.com", "meta.com",
            
            # Community & Learning (high-quality)
            "stackoverflow.com", "stackexchange.com", "freecodecamp.org", "mdn.io", "dev.to",
            "css-tricks.com", "smashingmagazine.com",
            
            # Academic & Research
            "arxiv.org", "research.google", "dl.acm.org", "ieee.org", "usenix.org",
            
            # Benchmarks & Performance
            "speed.python.org", "web.dev", "techempower.com", "arewefastyet.com",
            
            # AI/ML & Data Science
            "tensorflow.org", "pytorch.org", "keras.io", "scikit-learn.org", "numpy.org",
            "pandas.pydata.org", "huggingface.co", "openai.com",
            
            # Linux & Open Source
            "linuxfoundation.org", "ubuntu.com", "redhat.com", "opensource.org", "apache.org"
        ]
        
        is_authoritative = any(domain in link for domain in authoritative_domains)
        
        # Enhanced claim analysis
        claim_lower = claim.lower()
        supports_claim = False
        contradicts_claim = False
        
        # Check for version compatibility claims
        if "compatible" in claim_lower or "supports" in claim_lower:
            # Check for "all versions" claims specifically
            if "all" in claim_lower and "version" in claim_lower:
                # "All versions" claims are usually contradicted
                if any(term in snippet for term in ["not all", "only", "requires", "minimum", "specific version", "limited to"]):
                    contradicts_claim = True
                elif any(term in snippet for term in ["compatible with", "supports", "works with"]):
                    supports_claim = True
            else:
                # Regular compatibility claims
                if any(term in snippet for term in ["compatible", "supports", "works with", "requires"]):
                    supports_claim = True
                elif any(term in snippet for term in ["not compatible", "not supported", "incompatible", "deprecated"]):
                    contradicts_claim = True
        
        # Check for performance claims  
        elif any(term in claim_lower for term in ["faster", "performance", "benchmark", "reduces", "development time", "improves"]):
            if any(term in snippet for term in ["faster", "improved", "performance", "benchmark", "efficient", "optimized", "speed up"]):
                supports_claim = True
            elif any(term in snippet for term in ["slower", "performance issue", "regression", "overhead", "bottleneck", "degradation"]):
                contradicts_claim = True
        
        # Check for security claims
        elif any(term in claim_lower for term in ["secure", "security", "safe", "protected", "vulnerability"]):
            if any(term in snippet for term in ["secure", "security", "safe", "protected", "encryption"]):
                supports_claim = True
            elif any(term in snippet for term in ["vulnerability", "insecure", "risk", "exploit", "breach"]):
                contradicts_claim = True
        
        # If no specific analysis, use simple term matching
        if not supports_claim and not contradicts_claim:
            supporting_terms = ["yes", "correct", "true", "accurate", "confirmed", "verified", "valid"]
            contradicting_terms = ["no", "incorrect", "false", "inaccurate", "myth", "misconception", "wrong"]
            
            supports_claim = any(term in snippet for term in supporting_terms)
            contradicts_claim = any(term in snippet for term in contradicting_terms)
        
        return {
            "title": result.get("title", ""),
            "link": link,
            "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet,
            "authoritative": is_authoritative,
            "supports_claim": supports_claim,
            "contradicts_claim": contradicts_claim,
            "key_evidence": snippet[:150] if is_authoritative else None
        }
    
    def _calculate_confidence(self, results: Dict) -> float:
        """Calculate confidence score based on evidence"""
        total_auth = len(results["authoritative_sources"])
        supporting = len(results["supporting_sources"])
        contradicting = len(results["contradicting_sources"])
        
        if total_auth == 0 and supporting == 0 and contradicting == 0:
            return 0.0
        
        # Higher weight for authoritative sources
        auth_supporting = len([s for s in results["supporting_sources"] if s["authoritative"]])
        auth_contradicting = len([s for s in results["contradicting_sources"] if s["authoritative"]])
        
        # Calculate base score considering all sources
        total_relevant = supporting + contradicting
        if total_relevant > 0:
            base_score = supporting / total_relevant
        else:
            base_score = 0.0
        
        # Authority bonus/penalty
        auth_bonus = (auth_supporting - auth_contradicting) * 0.3
        
        confidence = max(0.0, min(1.0, base_score + auth_bonus))
        
        print(f"📈 DEBUG: Confidence calculation - "
              f"Total Auth: {total_auth}, "
              f"Supporting: {supporting}, "
              f"Contradicting: {contradicting}, "
              f"Auth Supporting: {auth_supporting}, "
              f"Auth Contradicting: {auth_contradicting}, "
              f"Final Confidence: {confidence}")
        
        return confidence