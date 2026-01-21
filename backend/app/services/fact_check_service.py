# backend/app/services/fact_check_service.py
import re
import asyncio
import httpx
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..schemas.fact_check import FactCheckItem, ClaimType, Verdict
from .serp_service import SERPService  # Import the separate service

class FactCheckService:
    def __init__(self):
        self.technical_indicators = {
            "code_snippets": [r"```[\s\S]*?```", r"<code>[\s\S]*?</code>", r"def\s+\w+\s*\([^)]*\):"],
            "version_numbers": [r"\b\d+\.\d+(\.\d+)?\b", r"\bv?\d+(\.\d+)*\b"],
            "api_references": [r"API\s+key", r"endpoint", r"GET|POST|PUT|DELETE", r"status code"],
            "error_messages": [r"error", r"exception", r"failed", r"cannot", r"invalid"],
            "technical_terms": [r"framework", r"library", r"dependency", r"configuration", r"deployment"]
        }
        
        # Enhanced technical knowledge base
        self.technical_knowledge = {
            "eol_versions": {
                "python": {"3.6": "2018-12-23", "3.7": "2023-06-27", "3.8": "2024-10-14"},
                "nodejs": {"12": "2022-04-30", "14": "2023-04-30", "16": "2023-09-11"},
                "react": {"16": "2020-10-20", "17": "2022-03-29"},
                "django": {"2.2": "2022-04-11", "3.1": "2021-04-06", "3.2": "2024-04-01"},
                "mongodb": {"3.6": "2021-04-30", "4.0": "2022-04-30", "4.2": "2023-04-30"}
            },
            "common_misconceptions": [
                {
                    "pattern": r"blockchain.*(completely secure|100% safe|unhackable)",
                    "truth": "Blockchain has specific security properties but isn't universally secure against all threats",
                    "severity": "medium"
                },
                {
                    "pattern": r"ai.*(replace|take over).*developer",
                    "truth": "AI augments developer capabilities but doesn't replace human judgment and creativity",
                    "severity": "low"
                },
                {
                    "pattern": r"microservices.*always.*better.*monolith",
                    "truth": "Microservices have trade-offs and aren't always better than monoliths",
                    "severity": "medium"
                },
                {
                    "pattern": r"python.*fastest.*language",
                    "truth": "Python prioritizes readability and productivity over raw execution speed",
                    "severity": "medium"
                },
                {
                    "pattern": r"completely secure.*all.*cyber attacks",
                    "truth": "No technology is completely secure against all cyber attacks; security requires multiple layers and ongoing maintenance",
                    "severity": "high"
                }
            ],
            "performance_claims": [
                r"(\d+)x faster",
                r"(\d+)% performance improvement",
                r"benchmark.*shows",
                r"reduces.*time.*\d+%",
                r"improves.*performance.*\d+"
            ]
        }
        
        # Add SERP service
        self.serp_service = SERPService()
        print("🔧 DEBUG: FactCheckService initialized with SERP service")
        
    def check_serp_status(self):
        """Check SERP API configuration status"""
        if not hasattr(self, 'serp_service'):
            return "❌ SERP service not initialized"
        
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "❌ SERPAPI_API_KEY not found in environment"
        
        return f"✅ SERP API configured (key: {api_key[:10]}...)"
    
    async def check_content(self, text_content: str) -> List[FactCheckItem]:
        """Perform fact checking on technical content with better filtering"""
        
        print(f"🔍 DEBUG: Starting fact check for content: {text_content[:200]}...")
        print(f"🔧 DEBUG: SERP Status: {self.check_serp_status()}")
        
        # First, check if this is actually technical content
        if not self.is_technical_content(text_content):
            return [FactCheckItem(
                claim="Content screening",
                claim_type=ClaimType.OTHER,
                context="This appears to be non-technical content",
                verdict=Verdict.UNVERIFIED,
                confidence=0.9,
                sources=[],
                explanation="The fact-checker is designed for technical blogs and documentation. Please use content about programming, frameworks, or software development."
            )]
        
        # Extract only meaningful factual claims
        claims = self.extract_claims(text_content)
        print(f"📊 DEBUG: Extracted {len(claims)} claims")
        
        if not claims:
            return [FactCheckItem(
                claim="No verifiable technical claims found",
                claim_type=ClaimType.OTHER,
                context="The content doesn't contain specific technical claims to verify",
                verdict=Verdict.UNVERIFIED,
                confidence=0.8,
                sources=[],
                explanation="The content appears to be announcements or general information without specific factual claims about versions, performance, or capabilities."
            )]
        
        checked_claims = []
        
        # Process claims in parallel for better performance
        verification_tasks = []
        for claim in claims:
            verification_tasks.append(self.verify_claim_enhanced(claim))
        
        results = await asyncio.gather(*verification_tasks)
        
        for claim, result in zip(claims, results):
            checked_claims.append(FactCheckItem(
                claim=claim["text"],
                claim_type=claim["type"],
                context=claim.get("context", ""),
                verdict=result["verdict"],
                confidence=result["confidence"],
                sources=result.get("sources", []),
                explanation=result["explanation"]
            ))
        
        print(f"✅ DEBUG: Fact check completed. Results: {len(checked_claims)} claims")
        return checked_claims
    
    def is_technical_content(self, text: str) -> bool:
        """Check if content is actually technical (programming, software, etc.)"""
        technical_keywords = [
            'python', 'javascript', 'java', 'react', 'vue', 'angular', 'node', 
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'api', 'database',
            'framework', 'library', 'function', 'class', 'method', 'variable',
            'git', 'github', 'deploy', 'server', 'backend', 'frontend', 'code',
            'programming', 'development', 'software', 'algorithm', 'bug', 'debug',
            'npm', 'package', 'import', 'export', 'component', 'hook', 'state',
            'django', 'flask', 'fastapi', 'version', 'supports', 'compatible',
            'mongodb', 'performance', 'index', 'query', 'memory', 'cpu', 'storage',
            'latency', 'throughput', 'benchmark', 'optimization', 'execution'
        ]
        
        text_lower = text.lower()
        found_keywords = [kw for kw in technical_keywords if kw in text_lower]
        technical_matches = len(found_keywords)
        
        print(f"🔍 DEBUG: Technical content check - Found {technical_matches} keywords: {found_keywords}")
        
        # More flexible threshold
        if len(text) < 100:
            result = technical_matches >= 1
        else:
            result = technical_matches >= 2
            
        print(f"🔍 DEBUG: Technical content result: {result}")
        return result
    
    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """Improved claim extraction focusing on complete technical facts"""
        claims = []
        
        # Better sentence splitting that preserves version numbers
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10 or len(sentence) > 500:  # More lenient length
                continue
                
            # Only extract if it's a verifiable factual claim
            if self.is_verifiable_technical_claim(sentence):
                claim_type = self.classify_claim_type(sentence)
                claims.append({
                    "text": sentence,
                    "type": claim_type,
                    "context": self.get_surrounding_context(text, sentence),
                    "technical_indicators": self.extract_technical_indicators(sentence)
                })
        
        return claims
    
    def is_verifiable_technical_claim(self, text: str) -> bool:
        """MUCH MORE LENIENT: Detect claims in documentation content"""
        text_lower = text.lower().strip()
        
        print(f"🔍 DEBUG: Checking if verifiable claim: '{text}'")
        
        # Skip very short or very long sentences
        if len(text) < 10 or len(text) > 500:
            print(f"❌ DEBUG: Failed length check: {len(text)} chars")
            return False
        
        # Skip questions
        if text_lower.startswith(('how', 'what', 'why', 'when', 'where', 'can ', 'is ', 'are ')) and '?' in text:
            print("❌ DEBUG: Failed question check")
            return False
        
        # Skip pure opinion/advice phrases (but allow documentation facts)
        strong_opinion_phrases = [
            'we think', 'we believe', 'in our opinion', 'we recommend', 'you should',
            'we suggest', 'best practice', 'we hope', 'for more information'
        ]
        if any(phrase in text_lower for phrase in strong_opinion_phrases):
            print("❌ DEBUG: Failed opinion phrase check")
            return False
        
        # 🚨 CRITICAL FIX: Don't filter documentation-style content
        # Documentation often contains factual technical information that should be verified
        
        # EXPANDED technical terms for documentation content
        technical_terms = [
            'python', 'react', 'node', 'javascript', 'java', 'docker', 'kubernetes', 
            'api', 'database', 'framework', 'library', 'algorithm', 'performance',
            'security', 'compatible', 'version', 'requires', 'supports', 'django',
            'mongodb', 'index', 'query', 'memory', 'cpu', 'storage', 'latency',
            'throughput', 'benchmark', 'optimization', 'execution', 'operation',
            'faster', 'slower', 'better', 'improves', 'reduces', 'handles',
            'supports', 'compatible', 'requires', 'works with'
        ]
        has_technical_terms = any(term in text_lower for term in technical_terms)
        
        if not has_technical_terms:
            print("❌ DEBUG: No technical terms found")
            return False
        
        # 🚨 EXPANDED: Much more lenient claim patterns for documentation
        verifiable_patterns = [
            # Version compatibility (expanded)
            r"requires.*\d+\.\d+", r"compatible with.*\d+\.\d+", r"supports.*\d+\.\d+",
            r"version.*\d+\.\d+", r"\d+\.\d+.*required", r"works with.*\d+\.\d+",
            
            # Performance numbers (much more flexible)
            r"\d+%.*(faster|slower|improvement|reduction|better|increase|decrease)",
            r"\d+x.*(faster|performance|improvement)",
            r"\d+.*(performance|throughput|latency|memory|storage|speed|time)",
            r"reduces.*by.*\d+", r"improves.*by.*\d+", r"increases.*by.*\d+",
            r"handles.*\d+", r"supports.*\d+", r"scales.*\d+",
            
            # Capacity/scale claims
            r"up to.*\d+", r"maximum.*\d+", r"minimum.*\d+", r"at least.*\d+",
            
            # Technical capability claims
            r"can.*\d+", r"able to.*\d+", r"capable of.*\d+", r"processes.*\d+",
            
            # Comparative claims
            r"better than", r"faster than", r"more efficient", r"less memory",
            
            # Security claims
            r"secure against", r"vulnerability", r"safe from", r"protects",
            r"encryption", r"authentication",
            
            # Database-specific patterns
            r"query.*\d+", r"index.*\d+", r"document.*\d+", r"operation.*\d+",
            r"throughput.*\d+", r"latency.*\d+",
            
            # General technical facts
            r"provides.*\d+", r"offers.*\d+", r"includes.*\d+", r"contains.*\d+"
        ]
        
        has_verifiable_pattern = any(re.search(pattern, text_lower) for pattern in verifiable_patterns)
        
        # 🚨 NEW: Also allow sentences with technical terms AND numbers (common in documentation)
        has_numbers = bool(re.search(r'\b\d+(?:\.\d+)?%?\b', text_lower))
        
        result = has_verifiable_pattern or (has_technical_terms and has_numbers)
        print(f"✅ DEBUG: Verifiable claim result: {result} (patterns: {has_verifiable_pattern}, terms: {has_technical_terms}, numbers: {has_numbers})")
        return result
    
    def extract_technical_indicators(self, text: str) -> Dict[str, Any]:
        """Extract technical elements from claim with better version detection"""
        # Improved version detection
        versions = re.findall(r'\b(?:Python|React|Node\.?js|Django|MongoDB)\s+(\d+\.\d+(?:\.\d+)?)\b', text, re.IGNORECASE)
        if not versions:
            versions = re.findall(r'\b\d+\.\d+(?:\.\d+)?\b', text)
        
        indicators = {
            "versions": versions,
            "technologies": self.detect_technologies(text),
            "numbers": re.findall(r'\b\d+(?:\.\d+)?%?\b', text),
            "comparisons": re.findall(r'\b(faster|slower|better|worse|more|less|improves|improvement|reduces|increases|handles|supports)\b', text, re.IGNORECASE),
            "absolute_terms": re.findall(r'\b(always|never|every|all|none|completely|100%|unhackable|secure|perfect)\b', text, re.IGNORECASE)
        }
        
        print(f"🔧 DEBUG: Extracted technical indicators: {indicators}")
        return indicators
    
    def detect_technologies(self, text: str) -> List[str]:
        """Detect mentioned technologies"""
        technologies = []
        tech_keywords = {
            "python": ["python", "django", "flask"],
            "javascript": ["javascript", "node", "react", "vue", "angular"],
            "java": ["java", "spring"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"],
            "database": ["mongodb", "postgresql", "mysql", "redis", "elasticsearch"]
        }
        
        text_lower = text.lower()
        for tech, keywords in tech_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                technologies.append(tech)
        
        return technologies
    
    async def verify_claim_enhanced(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced claim verification with SERP API"""
        claim_text = claim["text"]
        claim_type = claim["type"]
        indicators = claim.get("technical_indicators", {})
        
        print(f"🔍 DEBUG: Verifying claim: {claim_text}")
        print(f"📊 DEBUG: Claim type: {claim_type}")
        print(f"🔧 DEBUG: Technical indicators: {indicators}")
        
        # First, try rule-based verification (fast)
        rule_based_result = await self.verify_with_rules(claim_text, claim_type, indicators)
        
        print(f"📋 DEBUG: Rule-based result: {rule_based_result['verdict']} (confidence: {rule_based_result['confidence']})")
        
        # If rule-based gives low confidence or unverified, use SERP API
        if rule_based_result["confidence"] < 0.8 or rule_based_result["verdict"] == Verdict.UNVERIFIED:
            print("🚀 DEBUG: Falling back to SERP API...")
            serp_result = await self.verify_with_serp(claim_text, claim_type, indicators)
            print(f"🌐 DEBUG: SERP API result: {serp_result['verdict']} (confidence: {serp_result['confidence']})")
            
            # Combine results intelligently
            final_result = self._combine_verification_results(rule_based_result, serp_result)
            print(f"✅ DEBUG: Final result: {final_result['verdict']} (confidence: {final_result['confidence']})")
            return final_result
        
        print("✅ DEBUG: Using rule-based result (high confidence)")
        return rule_based_result
    
    async def verify_with_serp(self, claim: str, claim_type: ClaimType, indicators: Dict) -> Dict[str, Any]:
        """Verify claim using SERP API evidence"""
        technologies = indicators.get("technologies", [])
        
        print(f"🌐 DEBUG: Calling SERP API for: {claim}")
        print(f"🔧 DEBUG: Technologies context: {technologies}")
        
        # Get evidence from SERP API
        serp_results = await self.serp_service.search_technical_claim(claim, technologies)
        
        print(f"🌐 DEBUG: SERP API raw response: {serp_results}")
        
        if "error" in serp_results:
            print(f"❌ DEBUG: SERP API error: {serp_results['error']}")
            return {
                "verdict": Verdict.UNVERIFIED,
                "confidence": 0.3,
                "explanation": f"Unable to verify claim due to search API error: {serp_results['error']}",
                "sources": []
            }
        
        # Analyze SERP results to determine verdict
        return self._analyze_serp_evidence(claim, serp_results, claim_type)
    
    def _analyze_serp_evidence(self, claim: str, serp_results: Dict, claim_type: ClaimType) -> Dict[str, Any]:
        """Analyze SERP evidence to determine fact-check verdict - IMPROVED SOURCE HANDLING"""
        supporting = len(serp_results["supporting_sources"])
        contradicting = len(serp_results["contradicting_sources"])
        total_auth = len(serp_results["authoritative_sources"])
        
        confidence = serp_results["confidence_score"]
        
        print(f"📊 DEBUG: SERP Analysis - Supporting: {supporting}, Contradicting: {contradicting}, Total Auth: {total_auth}, Confidence: {confidence}")
        
        # Determine verdict based on evidence balance
        if total_auth == 0 and supporting == 0 and contradicting == 0:
            verdict = Verdict.UNVERIFIED
            explanation = "No sources found to verify this claim"
        elif supporting > contradicting * 2:  # Strong support
            verdict = Verdict.TRUE
            explanation = f"Claim supported by {supporting} sources"
        elif contradicting > supporting * 2:  # Strong contradiction
            verdict = Verdict.FALSE
            explanation = f"Claim contradicted by {contradicting} sources"
        else:  # Mixed evidence
            verdict = Verdict.INCONCLUSIVE
            explanation = f"Mixed evidence: {supporting} supporting vs {contradicting} contradicting sources"
        
        # 🚨 CRITICAL FIX: Include ALL relevant sources, not just authoritative ones
        all_sources = []
        
        # Add supporting sources first (most relevant)
        for src in serp_results["supporting_sources"][:5]:
            source_info = f"✅ {src['title']} ({src['link']})"
            if src.get('snippet'):
                source_info += f" - {src['snippet'][:100]}..."
            all_sources.append(source_info)
        
        # Add contradicting sources
        for src in serp_results["contradicting_sources"][:3]:
            source_info = f"❌ {src['title']} ({src['link']})"
            if src.get('snippet'):
                source_info += f" - {src['snippet'][:100]}..."
            all_sources.append(source_info)
        
        # Add authoritative sources that don't take a clear position
        for src in serp_results["authoritative_sources"][:3]:
            if src not in serp_results["supporting_sources"] and src not in serp_results["contradicting_sources"]:
                source_info = f"📚 {src['title']} ({src['link']})"
                if src.get('snippet'):
                    source_info += f" - {src['snippet'][:100]}..."
                all_sources.append(source_info)
        
        print(f"📚 DEBUG: All sources prepared: {len(all_sources)}")
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "explanation": explanation,
            "sources": all_sources
        }
    
    def _combine_verification_results(self, rule_result: Dict, serp_result: Dict) -> Dict[str, Any]:
        """Intelligently combine rule-based and SERP-based results - IMPROVED SOURCE COMBINING"""
        # If SERP has sources, prefer it even with moderate confidence
        has_sources = len(serp_result.get("sources", [])) > 0
        
        if has_sources and serp_result["confidence"] > 0.5:
            print("🔀 DEBUG: Using SERP result (has sources)")
            return serp_result
        
        # If SERP has high confidence, prefer it
        if serp_result["confidence"] > 0.8:
            print("🔀 DEBUG: Using SERP result (high confidence)")
            return serp_result
        
        # If both have similar confidence, use SERP for evidence
        if serp_result["confidence"] > 0.6:
            print("🔀 DEBUG: Combining rule-based and SERP results")
            # Enhance rule-based result with SERP sources
            combined_sources = rule_result.get("sources", []) + serp_result.get("sources", [])
            return {
                "verdict": serp_result["verdict"],
                "confidence": (rule_result["confidence"] + serp_result["confidence"]) / 2,
                "explanation": f"{rule_result['explanation']} | Web evidence: {serp_result['explanation']}",
                "sources": combined_sources
            }
        
        print("🔀 DEBUG: Falling back to rule-based result")
        # Fall back to rule-based but include any SERP sources found
        if has_sources:
            rule_result["sources"] = rule_result.get("sources", []) + serp_result.get("sources", [])
            rule_result["explanation"] = f"{rule_result['explanation']} | Additional sources found but inconclusive"
        
        return rule_result
    
    async def verify_with_rules(self, claim: str, claim_type: ClaimType, indicators: Dict) -> Dict[str, Any]:
        """Rule-based verification using technical knowledge"""
        if claim_type == ClaimType.VERSION_INFO:
            return await self.verify_version_claim_enhanced(claim, indicators)
        elif claim_type == ClaimType.PERFORMANCE:
            return await self.verify_performance_claim_enhanced(claim, indicators)
        elif claim_type == ClaimType.SECURITY:
            return await self.verify_security_claim_enhanced(claim, indicators)
        elif claim_type == ClaimType.COMPATIBILITY:
            return await self.verify_compatibility_claim_enhanced(claim, indicators)
        else:
            return await self.verify_general_claim(claim, indicators)
    
    async def verify_version_claim_enhanced(self, claim: str, indicators: Dict) -> Dict[str, Any]:
        """Enhanced version claim verification"""
        versions = indicators.get("versions", [])
        technologies = indicators.get("technologies", [])
        
        # Check for "all versions" claims which are usually false
        if "all" in claim.lower() and "version" in claim.lower():
            return {
                "verdict": Verdict.FALSE,
                "confidence": 0.90,
                "explanation": "No software supports 'all' versions indefinitely. There are always version constraints and deprecated versions.",
                "sources": ["Software development best practices"]
            }
        
        for tech in technologies:
            for version in versions:
                if tech in self.technical_knowledge["eol_versions"]:
                    if version in self.technical_knowledge["eol_versions"][tech]:
                        return {
                            "verdict": Verdict.FALSE,
                            "confidence": 0.95,
                            "explanation": f"{tech.capitalize()} {version} reached end-of-life on {self.technical_knowledge['eol_versions'][tech][version]} and should not be used in new projects",
                            "sources": [f"Official {tech} documentation", f"{tech.capitalize()} release notes"]
                        }
        
        # If we found versions but they're not EOL, consider it true
        if versions and technologies:
            return {
                "verdict": Verdict.TRUE,
                "confidence": 0.85,
                "explanation": "Version information appears to be accurate and up-to-date",
                "sources": [f"Official {technologies[0]} documentation"]
            }
        
        return {
            "verdict": Verdict.UNVERIFIED,
            "confidence": 0.70,
            "explanation": "Unable to verify version claim with current knowledge base",
            "sources": []
        }
    
    async def verify_performance_claim_enhanced(self, claim: str, indicators: Dict) -> Dict[str, Any]:
        """Verify performance claims"""
        # Check for unrealistic performance numbers
        numbers = indicators.get("numbers", [])
        
        for number in numbers:
            if '%' in number:
                try:
                    percentage = float(number.replace('%', ''))
                    if percentage > 1000:  # Unrealistic improvement
                        return {
                            "verdict": Verdict.FALSE,
                            "confidence": 0.85,
                            "explanation": f"Performance improvement of {percentage}% seems unrealistic without specific benchmark evidence",
                            "sources": ["Software engineering best practices", "Performance benchmarking standards"]
                        }
                except ValueError:
                    pass
        
        # Check for development time reduction claims
        if "reduces" in claim.lower() and "development" in claim.lower() and "time" in claim.lower():
            return {
                "verdict": Verdict.UNVERIFIED,
                "confidence": 0.60,
                "explanation": "Development time reduction claims are subjective and vary by project context. They require specific benchmark evidence for verification.",
                "sources": []
            }
        
        return {
            "verdict": Verdict.UNVERIFIED,
            "confidence": 0.70,
            "explanation": "Performance claims require specific benchmark context and evidence for verification",
            "sources": []
        }
    
    async def verify_security_claim_enhanced(self, claim: str, indicators: Dict) -> Dict[str, Any]:
        """Verify security-related claims"""
        claim_lower = claim.lower()
        
        # Check for absolute security claims
        absolute_terms = ["completely secure", "100% safe", "unhackable", "no vulnerabilities", "immune to", "all cyber attacks"]
        if any(term in claim_lower for term in absolute_terms):
            return {
                "verdict": Verdict.FALSE,
                "confidence": 0.95,
                "explanation": "Absolute security claims are generally inaccurate; all systems have potential vulnerabilities and require ongoing maintenance",
                "sources": ["Security best practices", "OWASP guidelines", "Cybersecurity standards"]
            }
        
        return {
            "verdict": Verdict.UNVERIFIED,
            "confidence": 0.75,
            "explanation": "Security claims require specific threat model context for proper verification",
            "sources": []
        }
    
    async def verify_compatibility_claim_enhanced(self, claim: str, indicators: Dict) -> Dict[str, Any]:
        """Verify compatibility claims"""
        versions = indicators.get("versions", [])
        technologies = indicators.get("technologies", [])
        
        if versions and technologies:
            return {
                "verdict": Verdict.UNVERIFIED,
                "confidence": 0.65,
                "explanation": f"Compatibility between {', '.join(technologies)} versions {', '.join(versions)} requires specific testing documentation",
                "sources": []
            }
        
        return {
            "verdict": Verdict.UNVERIFIED,
            "confidence": 0.60,
            "explanation": "Compatibility claims require specific version testing for verification",
            "sources": []
        }
    
    async def verify_general_claim(self, claim: str, indicators: Dict) -> Dict[str, Any]:
        """Verify general technical claims"""
        # Check against common misconceptions
        for misconception in self.technical_knowledge["common_misconceptions"]:
            if re.search(misconception["pattern"], claim, re.IGNORECASE):
                return {
                    "verdict": Verdict.FALSE,
                    "confidence": 0.85,
                    "explanation": f"This appears to be a common misconception. {misconception['truth']}",
                    "sources": ["Technical best practices", "Industry standards", "Expert consensus"]
                }
        
        return {
            "verdict": Verdict.UNVERIFIED,
            "confidence": 0.60,
            "explanation": "Unable to verify with current technical knowledge base",
            "sources": []
        }
    
    def classify_claim_type(self, text: str) -> ClaimType:
        """Enhanced claim type classification"""
        text_lower = text.lower()
        
        # Check for version claims
        if re.search(r"\b(version|v)\s*\d+\.\d+", text_lower) or re.search(r"\b\d+\.\d+(\.\d+)?\b", text_lower):
            return ClaimType.VERSION_INFO
        
        # Check for performance claims
        if any(term in text_lower for term in ["faster", "slower", "performance", "benchmark", "speed", "efficient", "reduces", "improves"]):
            return ClaimType.PERFORMANCE
        
        # Check for compatibility claims
        if any(term in text_lower for term in ["compatible", "requires", "works with", "supports", "dependency"]):
            return ClaimType.COMPATIBILITY
        
        # Check for security claims
        if any(term in text_lower for term in ["secure", "vulnerability", "safe", "protection", "encryption", "cyber"]):
            return ClaimType.SECURITY
        
        # Check for API claims
        if any(re.search(pattern, text_lower) for pattern in self.technical_indicators["api_references"]):
            return ClaimType.API_REFERENCE
        
        # Check for code examples
        if any(re.search(pattern, text_lower) for pattern in self.technical_indicators["code_snippets"]):
            return ClaimType.CODE_EXAMPLE
        
        return ClaimType.OTHER
    
    def get_surrounding_context(self, full_text: str, sentence: str) -> str:
        """Extract context around a claim"""
        index = full_text.find(sentence)
        if index == -1:
            return ""
        
        start = max(0, index - 100)
        end = min(len(full_text), index + len(sentence) + 100)
        return full_text[start:end]