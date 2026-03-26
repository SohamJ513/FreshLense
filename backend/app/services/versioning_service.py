# backend/app/services/versioning_service.py
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
import logging
import sys
import os

# Import AI service
from .ai_service import ai_service

# Import collections directly from database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import database collections
try:
    from database import versions_collection, pages_collection, change_logs_collection
    print("✅ Successfully imported database collections for versioning service")
except ImportError as e:
    print(f"⚠️ Could not import database collections: {e}")
    # These will be set later by set_collections() method
    versions_collection = None
    pages_collection = None
    change_logs_collection = None

logger = logging.getLogger(__name__)

class VersioningService:
    def __init__(self):
        self.diff_service = None
        
        # Lazy import of diff_service to avoid circular imports
        self._ensure_diff_service()
    
    def _ensure_diff_service(self):
        """Lazy load diff service to avoid circular imports"""
        if self.diff_service is None:
            from .diff_service import DiffService
            self.diff_service = DiffService()
    
    def set_collections(self, versions_coll, pages_coll, change_logs_coll=None):
        """Set collection references directly"""
        global versions_collection, pages_collection, change_logs_collection
        versions_collection = versions_coll
        pages_collection = pages_coll
        change_logs_collection = change_logs_coll
        logger.info(f"✅ Versioning service collections set: "
                   f"versions={versions_collection is not None}, "
                   f"pages={pages_collection is not None}, "
                   f"change_logs={change_logs_collection is not None}")
    
    def calculate_content_hash(self, text: str) -> str:
        """Calculate SHA256 hash of content for quick comparison"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def calculate_quick_checksum(self, text: str) -> str:
        """Calculate MD5 checksum for very fast comparison"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def analyze_change_significance(self, old_text: str, new_text: str, 
                                  config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze if changes are significant enough to store a new version
        
        Returns: {
            "store": bool,
            "reason": str,
            "score": float (0-1),
            "hash": str,
            "checksum": str,
            "metrics": dict,
            "analysis": dict
        }
        """
        # Default configuration
        default_config = {
            "min_change_threshold": 0.05,  # 5% text change required
            "min_semantic_difference": 0.1,  # 10% semantic difference
            "require_significant_keywords": True,
            "check_structural_changes": True,
            "max_versions_kept": 50
        }
        
        if config:
            default_config.update(config)
        
        # Case 1: First version
        if not old_text and new_text:
            return {
                "store": True,
                "reason": "First version",
                "score": 1.0,
                "hash": self.calculate_content_hash(new_text),
                "checksum": self.calculate_quick_checksum(new_text),
                "metrics": {"first_version": True},
                "analysis": {"is_first_version": True}
            }
        
        # Case 2: Identical content
        if old_text == new_text:
            return {
                "store": False,
                "reason": "Identical content",
                "score": 0.0,
                "hash": self.calculate_content_hash(new_text),
                "checksum": self.calculate_quick_checksum(new_text),
                "metrics": {"similarity_score": 100.0},
                "analysis": {"identical": True}
            }
        
        # Case 3: Quick checksum comparison (very fast)
        old_checksum = self.calculate_quick_checksum(old_text)
        new_checksum = self.calculate_quick_checksum(new_text)
        if old_checksum == new_checksum:
            return {
                "store": False,
                "reason": "Identical checksum",
                "score": 0.0,
                "hash": self.calculate_content_hash(new_text),
                "checksum": new_checksum,
                "metrics": {"identical_checksum": True},
                "analysis": {"checksum_match": True}
            }
        
        # Case 4: Calculate detailed metrics
        self._ensure_diff_service()
        metrics = self.diff_service.calculate_change_metrics(old_text, new_text)
        
        # Calculate significance score (0-1)
        score = 0.0
        reasons = []
        
        # 1. Character change (40% weight)
        char_score = min(metrics["change_percentage"] / 100, 1.0)
        score += char_score * 0.4
        if metrics["change_percentage"] >= default_config["min_change_threshold"] * 100:
            reasons.append(f"Text changed by {metrics['change_percentage']:.1f}%")
        
        # 2. Word change (30% weight)
        total_words = max(metrics["total_words_old"], metrics["total_words_new"], 1)
        word_change = (metrics["words_added"] + metrics["words_removed"]) / total_words
        word_score = min(word_change, 1.0)
        score += word_score * 0.3
        if word_change >= default_config["min_change_threshold"]:
            reasons.append(f"{word_change:.1%} of words changed")
        
        # 3. Structural changes (20% weight)
        line_change = 0
        if default_config["check_structural_changes"]:
            old_lines = max(len(old_text.splitlines()), 1)
            line_change = abs(metrics["lines_added"] - metrics["lines_removed"]) / old_lines
            line_score = min(line_change, 1.0)
            score += line_score * 0.2
            if line_change >= 0.1:  # 10% line count change
                reasons.append(f"Line count changed by {line_change:.1%}")
        
        # 4. Important keywords (10% weight)
        keyword_changes = 0
        if default_config["require_significant_keywords"]:
            important_keywords = [
                'security', 'vulnerability', 'update', 'critical', 'bug', 'fix',
                'release', 'version', 'deprecated', 'breaking', 'important',
                'urgent', 'warning', 'alert', 'patch', 'exploit', 'risk',
                'cve-', 'mitigation', 'workaround', 'upgrade', 'downgrade',
                'compatibility', 'performance', 'memory', 'cpu', 'storage',
                'latency', 'throughput', 'regression', 'feature', 'api'
            ]
            
            old_lower = old_text.lower()
            new_lower = new_text.lower()
            
            for keyword in important_keywords:
                old_has = keyword in old_lower
                new_has = keyword in new_lower
                if old_has != new_has:
                    keyword_changes += 1
                    reasons.append(f"Keyword '{keyword}' appeared/disappeared")
            
            keyword_score = min(keyword_changes * 0.05, 0.1)
            score += keyword_score
        
        # Decision
        store_version = score >= default_config["min_change_threshold"]
        
        return {
            "store": store_version,
            "reason": "; ".join(reasons) if reasons else "Minor changes",
            "score": round(score, 3),
            "hash": self.calculate_content_hash(new_text),
            "checksum": new_checksum,
            "metrics": metrics,
            "analysis": {
                "character_similarity": metrics["similarity_score"],
                "word_change_ratio": word_change,
                "line_change_ratio": line_change,
                "significant_keywords_found": keyword_changes
            }
        }
    
    async def save_version_if_significant(self, page_id: str, new_content: str, 
                                        html_content: Optional[str] = None,
                                        url: Optional[str] = None,
                                        user_id: Optional[str] = None,
                                        config: Optional[Dict] = None,
                                        generate_ai_summary: bool = True) -> Optional[str]:
        """
        Save a new version only if changes are significant
        
        Returns: version_id if saved, None if skipped
        """
        # Check if database collections are available
        if versions_collection is None or pages_collection is None:
            logger.error("❌ Database collections not available for versioning")
            return None
        
        try:
            # Get page details
            page = pages_collection.find_one({"_id": ObjectId(page_id)})
            if not page:
                logger.error(f"Page {page_id} not found")
                return None
            
            # Get the latest version
            latest_version = versions_collection.find_one(
                {"page_id": ObjectId(page_id)},
                sort=[("timestamp", -1)]
            )
            
            old_content = latest_version.get("text_content", "") if latest_version else ""
            
            # Analyze change significance
            analysis = self.analyze_change_significance(old_content, new_content, config)
            
            if not analysis["store"]:
                # Update last_checked timestamp but don't create new version
                pages_collection.update_one(
                    {"_id": ObjectId(page_id)},
                    {"$set": {"last_checked": datetime.utcnow()}}
                )
                logger.info(f"ℹ️  Skipping version for page {page_id} - {analysis['reason']} (score: {analysis['score']})")
                return None
            
            # Create new version document
            version_data = {
                "page_id": ObjectId(page_id),
                "timestamp": datetime.utcnow(),
                "text_content": new_content,
                "html_content": html_content,
                "content_hash": analysis["hash"],
                "checksum": analysis["checksum"],
                "change_significance_score": analysis["score"],
                "change_metrics": analysis["metrics"],
                "metadata": {
                    "store_reason": analysis["reason"],
                    "analysis": analysis["analysis"],
                    "config_used": config or {},
                    "previous_version_id": str(latest_version["_id"]) if latest_version else None,
                    "url": url or page.get("url", "")
                }
            }
            
            # Insert the new version
            result = versions_collection.insert_one(version_data)
            version_id = str(result.inserted_id)
            
            # Update page with latest version reference
            pages_collection.update_one(
                {"_id": ObjectId(page_id)},
                {
                    "$set": {
                        "last_checked": datetime.utcnow(),
                        "last_change_detected": datetime.utcnow(),
                        "current_version_id": result.inserted_id
                    }
                }
            )
            
            logger.info(f"✅ Saved version {version_id} for page {page_id} - {analysis['reason']} (score: {analysis['score']})")
            
            # Generate AI summary for significant changes (optional)
            if generate_ai_summary and analysis["score"] > 0.2 and ai_service.enabled and latest_version:
                try:
                    page_title = page.get('display_name') or page.get('url', '')
                    ai_summary = await ai_service.generate_change_summary(
                        old_content=old_content,
                        new_content=new_content,
                        page_title=page_title,
                        url=url or page.get("url", "")
                    )
                    
                    # Add summary to version
                    versions_collection.update_one(
                        {"_id": result.inserted_id},
                        {"$set": {"ai_summary": ai_summary}}
                    )
                    
                    logger.info(f"✅ AI summary generated for version {version_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate AI summary: {e}")
            
            # Create change log if user_id provided
            if user_id:
                self.create_change_log(page_id, user_id, analysis["score"])
            
            # Prune old versions if needed
            self.prune_old_versions(page_id, config)
            
            return version_id
            
        except Exception as e:
            logger.error(f"Error saving version: {e}", exc_info=True)
            return None
    
    def create_change_log(self, page_id: str, user_id: str, significance: float):
        """Create a change log entry"""
        if change_logs_collection is None:
            logger.warning("Change logs collection not available")
            return None
        
        try:
            change_log = {
                "page_id": ObjectId(page_id),
                "user_id": ObjectId(user_id),
                "type": "content_change",
                "timestamp": datetime.utcnow(),
                "change_significance_score": significance,
                "user_viewed": False,
                "viewed_by_user": False,
                "details": {
                    "auto_generated": True,
                    "notification_sent": False
                }
            }
            
            result = change_logs_collection.insert_one(change_log)
            logger.info(f"✅ Change log created for page {page_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to create change log: {e}")
            return None
    
    def prune_old_versions(self, page_id: str, config: Optional[Dict] = None) -> int:
        """Remove old, insignificant versions"""
        # Check if database collection is available
        if versions_collection is None:
            return 0
        
        default_config = {
            "max_versions_kept": 50,
            "keep_significant_threshold": 0.3,
            "keep_time_based": True,
            "keep_oldest": True
        }
        
        if config:
            default_config.update(config)
        
        try:
            # Get all versions sorted by timestamp (newest first)
            all_versions = list(versions_collection.find(
                {"page_id": ObjectId(page_id)},
                sort=[("timestamp", -1)]
            ))
            
            if len(all_versions) <= default_config["max_versions_kept"]:
                return 0
            
            versions_to_keep = []
            version_ids = [str(v["_id"]) for v in all_versions]
            
            # Always keep the oldest version
            if default_config["keep_oldest"] and all_versions:
                oldest = all_versions[-1]
                oldest_id = str(oldest["_id"])
                if oldest_id not in versions_to_keep:
                    versions_to_keep.append(oldest_id)
            
            # Keep versions with high significance scores
            if default_config["keep_significant_threshold"] > 0:
                for version in all_versions:
                    score = version.get("change_significance_score", 0)
                    if score >= default_config["keep_significant_threshold"]:
                        version_id = str(version["_id"])
                        if version_id not in versions_to_keep:
                            versions_to_keep.append(version_id)
            
            # Keep versions based on time distribution
            if default_config["keep_time_based"] and len(versions_to_keep) < default_config["max_versions_kept"]:
                # Try to keep versions spaced over time
                time_span = len(all_versions)
                step = max(1, time_span // (default_config["max_versions_kept"] - len(versions_to_keep)))
                
                for i in range(0, time_span, step):
                    if len(versions_to_keep) >= default_config["max_versions_kept"]:
                        break
                    version_id = str(all_versions[i]["_id"])
                    if version_id not in versions_to_keep:
                        versions_to_keep.append(version_id)
            
            # Ensure we don't keep more than max
            versions_to_keep = versions_to_keep[:default_config["max_versions_kept"]]
            
            # Delete old versions
            deleted_count = 0
            for version in all_versions:
                version_id = str(version["_id"])
                if version_id not in versions_to_keep:
                    result = versions_collection.delete_one({"_id": version["_id"]})
                    if result.deleted_count > 0:
                        deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"🧹 Pruned {deleted_count} old versions for page {page_id}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error pruning versions: {e}")
            return 0
    
    def get_version_with_summary(self, version_id: str) -> Optional[Dict]:
        """Get a version with its AI summary if available"""
        if versions_collection is None:
            return None
        
        try:
            version = versions_collection.find_one({"_id": ObjectId(version_id)})
            if not version:
                return None
            
            # Convert ObjectId to string
            version["_id"] = str(version["_id"])
            version["page_id"] = str(version["page_id"])
            
            return version
            
        except Exception as e:
            logger.error(f"Error getting version: {e}")
            return None
    
    def get_versions_with_summaries(self, page_id: str, limit: int = 50) -> List[Dict]:
        """Get recent versions with their AI summaries"""
        if versions_collection is None:
            return []
        
        try:
            versions = list(versions_collection.find(
                {"page_id": ObjectId(page_id)}
            ).sort("timestamp", -1).limit(limit))
            
            result = []
            for v in versions:
                result.append({
                    "id": str(v["_id"]),
                    "page_id": str(v["page_id"]),
                    "timestamp": v["timestamp"].isoformat(),
                    "change_significance_score": v.get("change_significance_score", 0),
                    "has_ai_summary": "ai_summary" in v,
                    "ai_summary": v.get("ai_summary"),
                    "metadata": v.get("metadata", {})
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting versions: {e}")
            return []