from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta
import os
from bson import ObjectId
from passlib.context import CryptContext
import asyncio
from typing import Optional
import logging
from difflib import SequenceMatcher
import resend  # ✅ ADD RESEND IMPORT

# Import our new safe cleanup services
from .services.mfa_cleanup_service import mfa_cleanup_service
from .services.audit_service import audit_service
# ✅ ADD NEW IMPORT
from .services.versioning_service import VersioningService

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = None
db = None

try:
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')  # Test the connection
    print("✅ MongoDB connection successful!")
    db = client['freshlense']

    # Initialize services with database connection
    mfa_cleanup_service.set_database(db)
    audit_service.set_database(db)

    # Collections
    users_collection = db['users']
    pages_collection = db['tracked_pages']
    versions_collection = db['page_versions']
    changes_collection = db['change_logs']

    # Indexes - ✅ UPDATED: No TTL indexes on users collection
    def create_indexes():
        # Users indexes - SAFE VERSION (NO TTL!)
        users_collection.create_index([("email", ASCENDING)], unique=True)
        users_collection.create_index([("created_at", DESCENDING)])
        users_collection.create_index([("mfa_code_expires", ASCENDING)])  # Regular index, not TTL!
        users_collection.create_index([("is_deleted", ASCENDING)])  # For soft delete queries
        
        # Pages indexes
        pages_collection.create_index([("user_id", ASCENDING), ("url", ASCENDING)], unique=True)
        pages_collection.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
        
        # Versions indexes
        versions_collection.create_index([("page_id", ASCENDING), ("timestamp", DESCENDING)])
        # ✅ ADD NEW INDEXES FOR SMART VERSIONING
        versions_collection.create_index([("page_id", ASCENDING), ("checksum", ASCENDING)])
        versions_collection.create_index([("page_id", ASCENDING), ("change_significance_score", DESCENDING)])
        
        # Changes indexes
        changes_collection.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        changes_collection.create_index([("page_id", ASCENDING), ("timestamp", DESCENDING)])
        
        print("✅ Database indexes created successfully (NO TTL on users)!")

    create_indexes()

except (ConnectionFailure, ServerSelectionTimeoutError) as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None
    db = None


# ---------------- Helper ----------------
def is_db_available():
    return db is not None


def doc_to_dict(doc):
    """Convert MongoDB ObjectIds -> str recursively"""
    if doc is None:
        return None
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, dict):
            doc[key] = doc_to_dict(value)
        elif isinstance(value, list):
            doc[key] = [doc_to_dict(v) if isinstance(v, dict) else str(v) if isinstance(v, ObjectId) else v for v in value]
    return doc


# ---------------- User ----------------
def get_user_by_email(email: str):
    """Get user by email address - EXCLUDE DELETED USERS"""
    if db is None:
        return None
    user = users_collection.find_one({
        "email": email,
        "is_deleted": {"$ne": True}  # ✅ ADDED: Exclude deleted users
    })
    return user


def get_user_by_id(user_id):
    """Get user by ID - EXCLUDE DELETED USERS"""
    if db is None:
        return None
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        user = users_collection.find_one({
            "_id": user_id,
            "is_deleted": {"$ne": True}  # ✅ ADDED: Exclude deleted users
        })
        return user
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


def create_user(user_data: dict):
    """Create a new user with hashed password"""
    if db is None:
        return None
    hashed_password = pwd_context.hash(user_data['password'])
    
    # ✅ ADDED: Soft delete fields with defaults
    user_doc = {
        "email": user_data['email'],
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "notification_preferences": {
            "email_alerts": True,
            "frequency": "immediately"
        },
        # Soft delete protection
        "is_deleted": False,
        "deleted_at": None,
        "deleted_by": None
    }
    
    try:
        result = users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        
        # ✅ Log user creation for audit
        audit_service.log_user_registration(
            user_id=str(user_doc["_id"]),
            email=user_data['email']
        )
        
        return user_doc
    except DuplicateKeyError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------- Tracked Pages ----------------
def get_tracked_pages(user_id, active_only: bool = True):
    """Get all tracked pages for a user - CHECK USER NOT DELETED"""
    if db is None:
        return []
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    # ✅ CHECK: User must not be deleted
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return []  # User doesn't exist or is deleted
    
    query = {"user_id": user_id}
    if active_only:
        query["is_active"] = True
    pages = pages_collection.find(query).sort("created_at", DESCENDING)
    return list(pages)


def get_tracked_page(page_id: str):
    """Get a single tracked page by ID"""
    if db is None:
        return None
    try:
        page = pages_collection.find_one({"_id": ObjectId(page_id)})
        return page
    except:
        return None


def create_tracked_page(page_data: dict, user_id):
    """Create a new tracked page - CHECK USER NOT DELETED"""
    if db is None:
        return None
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    # ✅ CHECK: User must not be deleted
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return None  # User doesn't exist or is deleted
    
    # ✅ ADD VERSIONING CONFIG TO NEW PAGES
    page_doc = {
        "user_id": user_id,
        "url": page_data["url"],
        "display_name": page_data.get("display_name") or page_data["url"],
        "check_interval_minutes": page_data.get("check_interval_minutes", 1440),
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_checked": None,
        "last_change_detected": None,
        "current_version_id": None,
        # ✅ ADD VERSIONING CONFIG
        "versioning_config": {
            "min_change_threshold": 0.05,  # 5% change required
            "require_significant_keywords": True,
            "max_versions_kept": 50,
            "check_structural_changes": True,
            "prune_strategy": "significant_only"
        }
    }
    try:
        result = pages_collection.insert_one(page_doc)
        page_doc["_id"] = result.inserted_id
        
        # ✅ Log page creation for audit
        audit_service.log_page_operation(
            user_id=str(user_id),
            operation="CREATED",
            page_id=str(page_doc["_id"]),
            details=f"Created tracked page: {page_data['url']}"
        )
        
        return page_doc
    except DuplicateKeyError:
        return None


def update_tracked_page(page_id: str, update_data: dict) -> bool:
    """Update a tracked page"""
    if db is None:
        return False
    
    # Handle ObjectId conversion for current_version_id
    update_data_copy = update_data.copy()
    if "current_version_id" in update_data_copy and isinstance(update_data_copy["current_version_id"], str):
        update_data_copy["current_version_id"] = ObjectId(update_data_copy["current_version_id"])
    
    try:
        result = pages_collection.update_one({"_id": ObjectId(page_id)}, {"$set": update_data_copy})
        return result.modified_count > 0
    except:
        return False


def delete_tracked_page(page_id: str) -> bool:
    """Delete a tracked page by ID"""
    if db is None:
        return False
    try:
        # Get page info before deletion for audit log
        page = get_tracked_page(page_id)
        
        result = pages_collection.delete_one({"_id": ObjectId(page_id)})
        
        if result.deleted_count > 0 and page:
            # ✅ Log page deletion for audit
            audit_service.log_page_operation(
                user_id=str(page.get("user_id", "")),
                operation="DELETED",
                page_id=page_id,
                details=f"Deleted tracked page: {page.get('url', 'unknown')}"
            )
        
        return result.deleted_count > 0
    except:
        return False


# ---------------- Page Versions ----------------
def create_page_version(page_id: str, text_content: str, url: str, html_content: str = None):
    """✅ UPDATED: Create a new page version with smart versioning fields"""
    if db is None:
        return None
    
    # ✅ ADD SMART VERSIONING FIELDS
    from .services.versioning_service import VersioningService
    versioning_service = VersioningService()
    
    version = {
        "page_id": ObjectId(page_id),
        "timestamp": datetime.utcnow(),
        "text_content": text_content,
        "html_content": html_content,
        # ✅ SMART VERSIONING FIELDS
        "content_hash": versioning_service.calculate_content_hash(text_content),
        "checksum": versioning_service.calculate_quick_checksum(text_content),
        "change_significance_score": 1.0,  # Default for first version
        "change_metrics": {
            "content_length": len(text_content),
            "word_count": len(text_content.split()) if text_content else 0,
        },
        "metadata": {
            "url": url,
            "content_length": len(text_content),
            "word_count": len(text_content.split()) if text_content else 0,
            "fetched_at": datetime.utcnow().isoformat(),
        },
    }
    try:
        result = versions_collection.insert_one(version)
        version["_id"] = result.inserted_id
        return version
    except:
        return None


def get_page_versions(page_id: str, limit: int = 10):
    """Get page versions for a specific page"""
    if db is None:
        return []
    try:
        versions = versions_collection.find({"page_id": ObjectId(page_id)}).sort("timestamp", DESCENDING).limit(limit)
        return list(versions)
    except:
        return []


# ---------------- Change Logs ----------------
def create_change_log(change_data: dict):
    """Create a new change log entry"""
    if db is None:
        return None
    
    change_data_copy = change_data.copy()
    
    # Handle ObjectId conversion
    if "page_id" in change_data_copy and isinstance(change_data_copy["page_id"], str):
        change_data_copy["page_id"] = ObjectId(change_data_copy["page_id"])
    if "user_id" in change_data_copy and isinstance(change_data_copy["user_id"], str):
        change_data_copy["user_id"] = ObjectId(change_data_copy["user_id"])
    
    # Ensure timestamp is set
    if "timestamp" not in change_data_copy:
        change_data_copy["timestamp"] = datetime.utcnow()
    
    try:
        result = changes_collection.insert_one(change_data_copy)
        return str(result.inserted_id)
    except:
        return None


def get_change_logs_for_page(page_id: str, limit: int = 20):
    """Get change logs for a specific page"""
    if db is None:
        return []
    try:
        changes = changes_collection.find({"page_id": ObjectId(page_id)}).sort("timestamp", DESCENDING).limit(limit)
        return list(changes)
    except:
        return []


def get_change_logs_for_user(user_id, limit: int = 20):
    """Get change logs for a specific user - CHECK USER NOT DELETED"""
    if db is None:
        return []
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    # ✅ CHECK: User must not be deleted
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return []  # User doesn't exist or is deleted
    
    try:
        changes = changes_collection.find({"user_id": user_id}).sort("timestamp", DESCENDING).limit(limit)
        return list(changes)
    except:
        return []


# ---------------- Additional utility functions for scheduler ----------------
def get_all_active_pages():
    """Get all active pages across all users (for scheduler)"""
    if db is None:
        return []
    try:
        pages = pages_collection.find({"is_active": True})
        return list(pages)
    except:
        return []


def get_pages_due_for_check():
    """Get pages that are due for checking based on their interval"""
    if db is None:
        return []
    try:
        # Get pages that have never been checked or are due for checking
        now = datetime.utcnow()
        pages = pages_collection.find({
            "is_active": True,
            "$or": [
                {"last_checked": None},
                {"last_checked": {"$lte": now}}
            ]
        })
        return list(pages)
    except:
        return []


def get_latest_page_version(page_id: str):
    """Get the most recent version of a page (for scheduler comparison)"""
    if db is None:
        return None
    try:
        # Get the second-to-last version for comparison (skip the most recent)
        versions = list(versions_collection.find(
            {"page_id": ObjectId(page_id)},
            sort=[("timestamp", DESCENDING)],
            limit=2
        ))
        
        # Return the previous version if we have at least 2 versions
        if len(versions) > 1:
            return versions[1]  # Second most recent
        elif len(versions) == 1:
            return None  # Only one version exists, no comparison possible
        else:
            return None  # No versions exist
    except:
        return None


# ---------------- Safe Cleanup Functions ----------------
def safe_cleanup_expired_mfa_codes() -> int:
    """
    ✅ SAFE VERSION: Clean up expired MFA codes without deleting users
    Returns number of codes cleaned
    """
    if db is None:
        return 0
    
    try:
        # Use our safe cleanup service
        cleaned_count = mfa_cleanup_service.cleanup_expired_mfa_codes()
        
        if cleaned_count > 0:
            logger.info(f"✅ Safe MFA cleanup completed: {cleaned_count} codes cleared")
        
        return cleaned_count
    except Exception as e:
        logger.error(f"❌ Error in safe MFA cleanup: {e}")
        return 0


def safe_cleanup_old_audit_logs(days_to_keep: int = 90) -> int:
    """
    ✅ SAFE VERSION: Clean up old audit logs
    Returns number of logs cleaned
    """
    if db is None:
        return 0
    
    try:
        # Use audit service cleanup
        cleaned_count = audit_service.cleanup_old_audit_logs(days_to_keep)
        
        if cleaned_count > 0:
            logger.info(f"✅ Safe audit log cleanup: {cleaned_count} logs removed")
        
        return cleaned_count
    except Exception as e:
        logger.error(f"❌ Error cleaning old audit logs: {e}")
        return 0


# ---------------- MonitoringScheduler Class ----------------
from .crawler import ContentFetcher

# Set up logging for scheduler module
logger = logging.getLogger(__name__)

class MonitoringScheduler:
    """Background scheduler for monitoring webpage changes with smart versioning"""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize the scheduler
        
        Args:
            check_interval: How often to check for pages needing monitoring (seconds)
        """
        self.check_interval = check_interval
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self._loop = None
        self.content_fetcher = ContentFetcher()  # Initialize the content fetcher
        # ✅ ADD SMART VERSIONING SERVICE
        self.versioning_service = VersioningService()
        
        # ✅ EMAIL CONFIGURATION
        self.email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
        if self.email_enabled:
            resend.api_key = os.getenv("RESEND_API_KEY")
            if not resend.api_key:
                logger.warning("EMAIL_ENABLED is true but RESEND_API_KEY is missing")
                self.email_enabled = False
            else:
                logger.info("✅ Email notifications enabled for scheduler")
        
        # ✅ Cleanup configuration
        self.cleanup_interval_cycles = 10  # Run cleanup every 10 cycles (~10 minutes)
        self.cleanup_counter = 0
        
        logger.info("✅ MonitoringScheduler initialized with SMART VERSIONING")
        
    async def start(self):
        """Start the monitoring scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        self._loop = asyncio.get_event_loop()
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("✅ Monitoring scheduler started with SMART VERSIONING")
        
    async def stop(self):
        """Stop the monitoring scheduler"""
        if not self.running:
            return
            
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring scheduler stopped")
        
    async def _run_scheduler(self):
        """Main scheduler loop with smart versioning"""
        while self.running:
            try:
                # Check pages for changes
                await self._check_pages()
                
                # ✅ SAFE CLEANUP: Run cleanup tasks periodically
                self.cleanup_counter += 1
                if self.cleanup_counter >= self.cleanup_interval_cycles:
                    await self._run_safe_cleanup_tasks()
                    self.cleanup_counter = 0
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _run_safe_cleanup_tasks(self):
        """✅ Run safe cleanup tasks that won't delete users"""
        try:
            logger.debug("🔄 Running safe cleanup tasks...")
            
            # 1. Clean expired MFA codes (SAFE - doesn't delete users)
            mfa_cleaned = safe_cleanup_expired_mfa_codes()
            if mfa_cleaned > 0:
                logger.info(f"🔧 Cleaned {mfa_cleaned} expired MFA codes")
            
            # 2. Clean old audit logs (optional, configurable)
            audit_cleaned = safe_cleanup_old_audit_logs(days_to_keep=90)
            if audit_cleaned > 0:
                logger.info(f"🧹 Cleaned {audit_cleaned} old audit logs")
            
            # 3. Get MFA cleanup stats for monitoring
            stats = mfa_cleanup_service.get_mfa_cleanup_stats()
            if "stats" in stats:
                expired_count = stats["stats"].get("users_with_expired_mfa_codes", 0)
                if expired_count > 50:  # Alert threshold
                    logger.warning(f"⚠️  High number of expired MFA codes: {expired_count}")
            
            logger.debug("✅ Safe cleanup tasks completed")
            
        except Exception as e:
            logger.error(f"❌ Error in safe cleanup tasks: {e}")
                
    async def _check_pages(self):
        """Check all pages that are due for monitoring"""
        try:
            # Get pages due for checking
            pages = self._get_pages_due_for_check()
            
            if not pages:
                return
                
            logger.debug(f"Checking {len(pages)} pages for changes")
            
            # Process pages concurrently (but limit concurrency)
            semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
            tasks = [self._check_single_page_smart(page, semaphore) for page in pages]
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Error checking pages: {e}")
    
    def _get_pages_due_for_check(self):
        """Get pages that are actually due for checking based on their interval"""
        try:
            all_active_pages = get_pages_due_for_check()
            now = datetime.utcnow()
            due_pages = []
            
            for page in all_active_pages:
                last_checked = page.get("last_checked")
                interval_minutes = page.get("check_interval_minutes", 1440)  # Default 24 hours
                
                # If never checked, or interval has passed
                if not last_checked:
                    due_pages.append(page)
                else:
                    next_check = last_checked + timedelta(minutes=interval_minutes)
                    if now >= next_check:
                        due_pages.append(page)
            
            return due_pages
        except Exception as e:
            logger.error(f"Error getting pages due for check: {e}")
            return []
            
    async def _check_single_page_smart(self, page, semaphore):
        """✅ UPDATED: Check a single page for changes with SMART VERSIONING"""
        async with semaphore:
            try:
                page_id = str(page["_id"])
                url = page["url"]
                
                # Get current page content
                current_content = await self._fetch_page_content(url)
                if not current_content:
                    logger.warning(f"Failed to fetch content for {url}")
                    # Still update last_checked even if fetch failed
                    update_tracked_page(page_id, {"last_checked": datetime.utcnow()})
                    return
                    
                # Get page-specific versioning config
                page_config = page.get("versioning_config", {
                    "min_change_threshold": 0.05,  # 5% change required
                    "require_significant_keywords": True,
                    "max_versions_kept": 50,
                    "check_structural_changes": True,
                    "prune_strategy": "significant_only"
                })
                
                # ✅ USE SMART VERSIONING: Only save if significant
                new_version_id = self.versioning_service.save_version_if_significant(
                    page_id=page_id,
                    new_content=current_content,
                    html_content=None,  # You can pass HTML if you store it
                    config=page_config
                )
                
                # Update last_checked timestamp
                update_tracked_page(page_id, {"last_checked": datetime.utcnow()})
                
                # If no new version was saved (insignificant change)
                if not new_version_id:
                    logger.debug(f"ℹ️  Skipped version for {url} - insignificant changes")
                    return
                
                # Get the new version to calculate metrics
                new_version = versions_collection.find_one({"_id": ObjectId(new_version_id)})
                if not new_version:
                    logger.error(f"Failed to retrieve new version {new_version_id}")
                    return
                
                # ✅ GET OLD VERSION FOR COMPARISON
                old_version = get_latest_page_version(page_id)
                old_content = old_version.get("text_content", "") if old_version else ""
                
                # Calculate change percentage for notification
                change_percentage = self._calculate_change_percentage(old_content, current_content)
                
                # Update page with new version ID
                update_data = {
                    "current_version_id": new_version_id,
                    "last_change_detected": datetime.utcnow()
                }
                update_tracked_page(page_id, update_data)
                
                # ✅ SEND EMAIL NOTIFICATION IF ENABLED AND CHANGE IS SIGNIFICANT
                if (self.email_enabled and change_percentage > 0 and 
                    new_version.get("change_significance_score", 0) >= page_config.get("min_change_threshold", 0.05)):
                    
                    await self._send_change_notification(
                        page=page,
                        change_percentage=change_percentage,
                        new_version=new_version,
                        old_content_length=len(old_content),
                        new_content_length=len(current_content)
                    )
                
                # Create change log entry
                change_data = {
                    "user_id": page["user_id"],
                    "page_id": page_id,
                    "change_type": "content_changed",
                    "timestamp": datetime.utcnow(),
                    "details": {
                        "url": url,
                        "content_length": len(current_content),
                        "previous_length": len(old_content),
                        "change_percentage": change_percentage,
                        "significance_score": new_version.get("change_significance_score", 0),
                        "notification_sent": self.email_enabled,
                        "version_id": new_version_id
                    }
                }
                
                change_log_id = create_change_log(change_data)
                if change_log_id:
                    significance = new_version.get("change_significance_score", 0)
                    logger.info(f"✅ Saved SIGNIFICANT version for {url}: {change_percentage}% change (score: {significance})")
                else:
                    logger.error(f"Failed to create change log for page {page_id}")
                    
            except Exception as e:
                logger.error(f"Error checking page {page.get('url', 'unknown')}: {e}")
    
    # Keep old method for backward compatibility
    async def _check_single_page(self, page, semaphore):
        """Legacy method - calls new smart method"""
        return await self._check_single_page_smart(page, semaphore)
    
    # ✅ ADDED: UPDATE EXISTING PAGES CONFIG
    def update_existing_pages_config(self):
        """Update existing tracked pages with versioning configuration"""
        try:
            all_pages = get_all_active_pages()
            updated_count = 0
            
            for page in all_pages:
                page_id = str(page["_id"])
                
                # Check if page already has versioning config
                if "versioning_config" not in page:
                    update_data = {
                        "versioning_config": {
                            "min_change_threshold": 0.05,
                            "require_significant_keywords": True,
                            "max_versions_kept": 50,
                            "check_structural_changes": True,
                            "prune_strategy": "significant_only"
                        }
                    }
                    
                    if update_tracked_page(page_id, update_data):
                        updated_count += 1
            
            logger.info(f"✅ Updated {updated_count} pages with versioning configuration")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating page configs: {e}")
            return 0
    
    # ✅ ADDED: CLEANUP EXISTING VERSIONS
    async def cleanup_existing_versions(self):
        """Clean up existing insignificant versions (one-time migration)"""
        try:
            logger.info("🧹 Starting cleanup of existing insignificant versions...")
            
            all_pages = get_all_active_pages()
            total_pruned = 0
            
            for page in all_pages:
                page_id = str(page["_id"])
                
                # Use default config
                config = {
                    "max_versions_kept": 50,
                    "keep_significant_threshold": 0.3,
                    "keep_time_based": True,
                    "keep_oldest": True
                }
                
                pruned = self.versioning_service.prune_old_versions(page_id, config)
                total_pruned += pruned
                
                # Small delay to avoid overwhelming the database
                await asyncio.sleep(0.1)
            
            logger.info(f"✅ Cleanup completed: {total_pruned} versions pruned")
            return total_pruned
            
        except Exception as e:
            logger.error(f"Error during version cleanup: {e}")
            return 0
    
    # ✅ ADDED: CALCULATE CHANGE PERCENTAGE
    def _calculate_change_percentage(self, old_content: str, new_content: str) -> float:
        """Calculate percentage of content changed"""
        try:
            if not old_content:
                return 100.0  # First version is 100% change
            
            if not new_content:
                return 0.0
            
            # Use difflib to calculate similarity
            similarity = SequenceMatcher(None, old_content, new_content).ratio()
            change_percentage = (1 - similarity) * 100
            return round(change_percentage, 1)
        except Exception as e:
            logger.error(f"Error calculating change percentage: {e}")
            return 0.0
    
    # ✅ ADDED: SEND CHANGE NOTIFICATION
    async def _send_change_notification(self, page: dict, change_percentage: float, 
                                       new_version: dict, old_content_length: int, 
                                       new_content_length: int):
        """Send email notification when page change is detected"""
        try:
            # Get user information
            user = get_user_by_id(page["user_id"])
            if not user or not user.get("email"):
                logger.warning(f"No user or email found for page {page.get('_id')}")
                return
            
            # Check user notification preferences
            prefs = user.get("notification_preferences", {})
            if not prefs.get("email_alerts", True):
                logger.info(f"Email alerts disabled for user {user.get('email')}")
                return
            
            user_email = user["email"]
            page_title = page.get("display_name", page.get("url", "Monitored Page"))
            page_url = page.get("url", "")
            
            # Determine change severity
            if change_percentage > 50:
                change_severity = "Major"
                color = "#ef4444"  # Red
            elif change_percentage > 20:
                change_severity = "Moderate" 
                color = "#f59e0b"  # Orange
            else:
                change_severity = "Minor"
                color = "#10b981"  # Green
            
            # Get from email
            from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
            
            # Create email
            params = {
                "from": f"FreshLense <{from_email}>",
                "to": [user_email],
                "subject": f"🔄 {change_severity} Change Detected: {page_title[:40]}{'...' if len(page_title) > 40 else ''}",
                "html": self._generate_change_email_html(
                    page_title=page_title,
                    page_url=page_url,
                    change_percentage=change_percentage,
                    change_severity=change_severity,
                    color=color,
                    old_length=old_content_length,
                    new_length=new_content_length
                ),
                "text": self._generate_change_email_text(
                    page_title=page_title,
                    page_url=page_url,
                    change_percentage=change_percentage,
                    change_severity=change_severity,
                    old_length=old_content_length,
                    new_length=new_content_length
                )
            }
            
            # Send email
            email = resend.Emails.send(params)
            logger.info(f"✅ Change notification sent to {user_email} for {page_url} (ID: {email['id']})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send change notification: {e}")
            return False
    
    # ✅ ADDED: GENERATE HTML EMAIL
    def _generate_change_email_html(self, page_title: str, page_url: str, 
                                   change_percentage: float, change_severity: str, 
                                   color: str, old_length: int, new_length: int) -> str:
        """Generate HTML email template for change notifications"""
        return f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, {color} 0%, #7c3aed 100%); padding: 30px; color: white; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🔄 {change_severity} Change Detected</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">A monitored page has been updated</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 25px; border-radius: 0 0 10px 10px;">
                <!-- Page Info -->
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #333;">{page_title}</h3>
                    <p style="color: #666; margin-bottom: 5px;">
                        <strong>URL:</strong> <a href="{page_url}" style="color: #3b82f6;">{page_url}</a>
                    </p>
                    <p style="color: #666; margin: 0;">
                        <strong>Detected:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
                    </p>
                </div>
                
                <!-- Change Details -->
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h3 style="margin-top: 0; color: #333;">Change Analysis</h3>
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <div style="font-size: 48px; font-weight: bold; color: {color};">
                            {change_percentage}%
                        </div>
                        <p style="color: #666; margin-top: 10px;">
                            Content Change Detected
                        </p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
                        <div style="text-align: center; padding: 15px; background: #f0f9ff; border-radius: 8px;">
                            <div style="font-size: 20px; font-weight: bold; color: #0ea5e9;">
                                {old_length}
                            </div>
                            <div style="color: #666; font-size: 14px;">Previous Length</div>
                        </div>
                        
                        <div style="text-align: center; padding: 15px; background: #f0f9ff; border-radius: 8px;">
                            <div style="font-size: 20px; font-weight: bold; color: #0ea5e9;">
                                {new_length}
                            </div>
                            <div style="color: #666; font-size: 14px;">New Length</div>
                        </div>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center;">
                        <p style="margin: 0; color: #666; font-size: 14px;">
                            <strong>Change Severity:</strong> <span style="color: {color}; font-weight: bold;">{change_severity}</span><br>
                            {change_severity.lower()} changes may require your review
                        </p>
                    </div>
                </div>
                
                <!-- Action Buttons -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 20px;">
                    <a href="{page_url}" 
                       style="display: block; background: #3b82f6; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center;"
                       target="_blank">
                        🔍 View Updated Page
                    </a>
                    
                    <a href="#" 
                       style="display: block; background: #8b5cf6; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; text-align: center;"
                       target="_blank">
                        📊 Run Fact-Check
                    </a>
                </div>
                
                <!-- Footer -->
                <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; text-align: center;">
                    <p style="color: #666; font-size: 12px; margin: 0;">
                        You're receiving this email because you're monitoring this page with FreshLense.<br>
                        <a href="#" style="color: #3b82f6; text-decoration: none;">Manage notification preferences</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    # ✅ ADDED: GENERATE PLAIN TEXT EMAIL
    def _generate_change_email_text(self, page_title: str, page_url: str, 
                                   change_percentage: float, change_severity: str,
                                   old_length: int, new_length: int) -> str:
        """Generate plain text email for change notifications"""
        return f"""FreshLense Page Change Alert

🚨 {change_severity} Change Detected

📄 Page: {page_title}
🔗 URL: {page_url}
📊 Change Percentage: {change_percentage}%
📏 Content Size: {old_length} → {new_length} characters
🕐 Detected: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

The content of this monitored page has changed. 
{change_severity} changes may require your review.

🔍 View updated page: {page_url}
📊 Run fact-check in FreshLense app

You're receiving this email because you're monitoring this page with FreshLense.
Manage notification preferences in your account settings."""
                
    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page content asynchronously using ContentFetcher"""
        try:
            # Run the synchronous crawler in a thread pool
            loop = asyncio.get_event_loop()
            html, content = await loop.run_in_executor(
                None, 
                self.content_fetcher.fetch_and_extract, 
                url
            )
            return content  # Return the extracted text content
        except Exception as e:
            logger.error(f"Error fetching content from {url}: {e}")
            return None
            
    async def shutdown(self):
        """Alias for stop() method to match main.py expectations"""
        await self.stop()
        
    def schedule_page(self, page_doc):
        """
        Schedule a page for monitoring (called when new page is created)
        This is mainly for compatibility with main.py - the scheduler will pick up
        new pages automatically on its next check cycle
        """
        logger.debug(f"Page scheduled for monitoring: {page_doc.get('url', 'unknown')}")
        # No immediate action needed - scheduler will pick it up automatically
        
    @property 
    def is_running(self) -> bool:
        """Property accessor to match main.py expectations"""
        return self.running

    # ✅ NEW: Manual cleanup trigger for testing/debugging
    async def trigger_safe_cleanup(self):
        """Manually trigger safe cleanup tasks (for testing/debugging)"""
        logger.info("🚀 Manually triggering safe cleanup tasks...")
        await self._run_safe_cleanup_tasks()
        logger.info("✅ Manual cleanup completed")

    # ✅ NEW: Run migration to update existing pages
    async def run_migration(self):
        """Run migration to update existing pages and versions"""
        logger.info("🚀 Starting versioning migration...")
        
        # 1. Update existing pages with versioning config
        updated_pages = self.update_existing_pages_config()
        logger.info(f"✅ Updated {updated_pages} pages with versioning config")
        
        # 2. Clean up existing insignificant versions
        pruned_versions = await self.cleanup_existing_versions()
        logger.info(f"✅ Pruned {pruned_versions} insignificant versions")
        
        logger.info("🎉 Migration completed successfully!")