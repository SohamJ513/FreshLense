from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta
import os
import hashlib
from typing import List, Dict, Any, Optional
from bson import ObjectId
from passlib.context import CryptContext

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

    # Collections
    users_collection = db['users']
    pages_collection = db['tracked_pages']
    versions_collection = db['page_versions']
    changes_collection = db['change_logs']
    password_reset_tokens_collection = db['password_reset_tokens']
    audit_logs_collection = db['audit_logs']

    # Indexes
    def create_indexes():
        # Users indexes - SAFE VERSION (NO TTL!)
        users_collection.create_index([("email", ASCENDING)], unique=True)
        users_collection.create_index([("created_at", DESCENDING)])
        users_collection.create_index([("mfa_code_expires", ASCENDING)])
        users_collection.create_index([("is_deleted", ASCENDING)])
        
        # Pages indexes
        pages_collection.create_index([("user_id", ASCENDING), ("url", ASCENDING)], unique=True)
        pages_collection.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
        
        # ✅ ENHANCED: Versions indexes for smart versioning
        versions_collection.create_index([("page_id", ASCENDING), ("timestamp", DESCENDING)])
        versions_collection.create_index([("page_id", ASCENDING), ("change_significance_score", DESCENDING)])
        versions_collection.create_index([("page_id", ASCENDING), ("checksum", ASCENDING)])
        versions_collection.create_index([("page_id", ASCENDING), ("content_hash", ASCENDING)])
        versions_collection.create_index([("change_significance_score", DESCENDING)])
        
        # Changes indexes
        changes_collection.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        changes_collection.create_index([("page_id", ASCENDING), ("timestamp", DESCENDING)])
        
        # Indexes for password reset tokens
        password_reset_tokens_collection.create_index([("token", ASCENDING)], unique=True)
        password_reset_tokens_collection.create_index([("user_id", ASCENDING)])
        password_reset_tokens_collection.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)
        
        # Audit logs indexes
        audit_logs_collection.create_index([("timestamp", DESCENDING)])
        audit_logs_collection.create_index([("user_id", ASCENDING)])
        audit_logs_collection.create_index([("operation", ASCENDING)])
        
        print("✅ Database indexes created successfully with SMART VERSIONING support!")

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


# ---------------- Smart Versioning Helper Functions ----------------
def calculate_content_hash(text: str) -> str:
    """Calculate SHA256 hash of content for accurate comparison"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def calculate_quick_checksum(text: str) -> str:
    """Calculate MD5 checksum for very fast comparison"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_content_duplicate(page_id: str, content_hash: str) -> Optional[Dict]:
    """Check if content with same hash already exists for this page"""
    if db is None:
        return None
    
    try:
        duplicate = versions_collection.find_one({
            "page_id": ObjectId(page_id),
            "content_hash": content_hash
        })
        return duplicate
    except Exception as e:
        print(f"Error checking for duplicate content: {e}")
        return None


# ---------------- User ----------------
def get_user_by_email(email: str):
    """Get user by email address - EXCLUDE DELETED USERS"""
    if db is None:
        return None
    user = users_collection.find_one({
        "email": email,
        "is_deleted": {"$ne": True}
    })
    return user


def get_user_by_id(user_id):
    """Get user by ID - EXCLUDE DELETED USERS"""
    if db is None:
        return None
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        user = users_collection.find_one({
            "_id": user_id,
            "is_deleted": {"$ne": True}
        })
        return user
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


def create_user(user_data: dict):
    """Create a new user with hashed password and MFA enabled by default"""
    if db is None:
        return None
    
    hashed_password = pwd_context.hash(user_data.get('password', ''))
    
    user_doc = {
        "email": user_data.get('email'),
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "notification_preferences": {
            "email_alerts": True,
            "frequency": "immediately"
        },
        "is_deleted": False,
        "deleted_at": None,
        "deleted_by": None,
        "mfa_enabled": True,
        "mfa_email": user_data.get('email'),
        "mfa_code": None,
        "mfa_code_expires": None,
        "mfa_setup_completed": True,
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return user_doc
    except DuplicateKeyError:
        print(f"User with email {user_data.get('email')} already exists")
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def soft_delete_user(user_id: str, deleted_by: str = "system", reason: str = "") -> bool:
    """Soft delete a user (mark as deleted instead of removing)"""
    if db is None:
        return False
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = users_collection.update_one(
            {"_id": user_id, "is_deleted": {"$ne": True}},
            {
                "$set": {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": deleted_by,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            log_audit_event(
                operation="USER_SOFT_DELETED",
                user_id=str(user_id),
                performed_by=deleted_by,
                details=f"Soft deleted user: {reason}"
            )
            print(f"✅ User {user_id} soft deleted by {deleted_by}")
        
        return result.modified_count > 0
    except Exception as e:
        print(f"Error soft deleting user: {e}")
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------- MFA Database Functions ----------------
def get_user_mfa_status(user_id):
    """Get MFA status for a user - EXCLUDE DELETED USERS"""
    if db is None:
        return None
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        user = users_collection.find_one(
            {
                "_id": user_id,
                "is_deleted": {"$ne": True}
            },
            {
                "email": 1,
                "mfa_enabled": 1,
                "mfa_email": 1,
                "mfa_setup_completed": 1,
                "notification_preferences": 1
            }
        )
        return user
    except Exception as e:
        print(f"Error getting user MFA status: {e}")
        return None


def update_user_mfa_status(user_id, update_data: dict):
    """Update user MFA settings - EXCLUDE DELETED USERS"""
    if db is None:
        return False
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        update_data["updated_at"] = datetime.utcnow()
        
        result = users_collection.update_one(
            {
                "_id": user_id,
                "is_deleted": {"$ne": True}
            },
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user MFA status: {e}")
        return False


def update_user_mfa_code(user_id, mfa_code: str, expires_at: datetime):
    """Store MFA code for user - EXCLUDE DELETED USERS"""
    if db is None:
        return False
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = users_collection.update_one(
            {
                "_id": user_id,
                "is_deleted": {"$ne": True}
            },
            {
                "$set": {
                    "mfa_code": mfa_code,
                    "mfa_code_expires": expires_at,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user MFA code: {e}")
        return False


def clear_user_mfa_code(user_id):
    """Clear MFA code after successful verification - EXCLUDE DELETED USERS"""
    if db is None:
        return False
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = users_collection.update_one(
            {
                "_id": user_id,
                "is_deleted": {"$ne": True}
            },
            {
                "$set": {
                    "mfa_code": None,
                    "mfa_code_expires": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error clearing user MFA code: {e}")
        return False


def verify_user_mfa_code(user_id, input_code: str):
    """Verify if MFA code is valid - EXCLUDE DELETED USERS"""
    if db is None:
        return False, "Database not available"
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        user = users_collection.find_one(
            {
                "_id": user_id,
                "is_deleted": {"$ne": True}
            },
            {"mfa_code": 1, "mfa_code_expires": 1, "mfa_enabled": 1}
        )
        
        if not user:
            return False, "User not found or deleted"
        
        if not user.get("mfa_enabled", True):
            return False, "MFA not enabled for this account"
        
        stored_code = user.get("mfa_code")
        expires_at = user.get("mfa_code_expires")
        
        if not stored_code:
            return False, "No MFA code found. Please request a new code."
        
        if expires_at and datetime.utcnow() >= expires_at:
            return False, "MFA code has expired. Please request a new code."
        
        if stored_code != input_code:
            return False, "Invalid MFA code. Please try again."
        
        return True, "Code is valid"
    except Exception as e:
        print(f"Error verifying MFA code: {e}")
        return False, "Internal server error"


def get_users_with_mfa_enabled():
    """Get all users with MFA enabled - EXCLUDE DELETED USERS"""
    if db is None:
        return []
    
    try:
        users = users_collection.find(
            {
                "mfa_enabled": True,
                "is_deleted": {"$ne": True}
            },
            {"email": 1, "mfa_email": 1, "mfa_setup_completed": 1, "created_at": 1}
        )
        return list(users)
    except Exception as e:
        print(f"Error getting users with MFA enabled: {e}")
        return []


def get_expired_mfa_codes():
    """Get expired MFA codes that should be cleaned up - EXCLUDE DELETED USERS"""
    if db is None:
        return []
    
    try:
        expired_users = users_collection.find(
            {
                "mfa_code": {"$ne": None},
                "mfa_code_expires": {"$lt": datetime.utcnow()},
                "is_deleted": {"$ne": True}
            },
            {"email": 1, "mfa_code_expires": 1}
        )
        return list(expired_users)
    except Exception as e:
        print(f"Error getting expired MFA codes: {e}")
        return []


# ---------------- Password Reset Token Operations ----------------
def create_password_reset_token(token: str, user_id: ObjectId, expires_at: datetime) -> bool:
    """Create a new password reset token - CHECK USER NOT DELETED"""
    if db is None:
        return False
    
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
            return False
    
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return False
    
    token_doc = {
        "token": token,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "used": False,
        "used_at": None
    }
    
    try:
        result = password_reset_tokens_collection.insert_one(token_doc)
        return result.inserted_id is not None
    except DuplicateKeyError:
        return False
    except Exception as e:
        print(f"Error creating password reset token: {e}")
        return False


def get_valid_password_reset_token(token: str):
    """Get a valid, unused password reset token"""
    if db is None:
        return None
    
    try:
        token_record = password_reset_tokens_collection.find_one({
            "token": token,
            "used": False,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        return token_record
    except Exception as e:
        print(f"Error getting password reset token: {e}")
        return None


def mark_password_reset_token_used(token: str) -> bool:
    """Mark a password reset token as used"""
    if db is None:
        return False
    
    try:
        result = password_reset_tokens_collection.update_one(
            {"token": token},
            {
                "$set": {
                    "used": True,
                    "used_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error marking password reset token as used: {e}")
        return False


def update_user_password(user_id: ObjectId, new_password: str) -> bool:
    """Update a user's password - CHECK USER NOT DELETED"""
    if db is None:
        return False
    
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
            return False
    
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return False
    
    hashed_password = pwd_context.hash(new_password)
    
    try:
        result = users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user password: {e}")
        return False


# ---------------- Tracked Pages ----------------
def get_tracked_pages(user_id, active_only: bool = True):
    """Get all tracked pages for a user - CHECK USER NOT DELETED"""
    if db is None:
        return []
    
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return []
    
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
    """Create a new tracked page with versioning config - CHECK USER NOT DELETED"""
    if db is None:
        return None
    
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return None
    
    # ✅ ADDED: Default versioning configuration
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
        # ✅ SMART VERSIONING CONFIG
        "versioning_config": {
            "min_change_threshold": 0.05,
            "require_significant_keywords": True,
            "max_versions_kept": 50,
            "check_structural_changes": True,
            "prune_strategy": "significant_only",
            "notification_threshold": 0.3
        }
    }
    
    try:
        result = pages_collection.insert_one(page_doc)
        page_doc["_id"] = result.inserted_id
        return page_doc
    except DuplicateKeyError:
        return None


def update_tracked_page(page_id: str, update_data: dict) -> bool:
    """Update a tracked page"""
    if db is None:
        return False
    
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
        result = pages_collection.delete_one({"_id": ObjectId(page_id)})
        return result.deleted_count > 0
    except:
        return False


def get_tracked_page_by_url(url: str, user_id):
    """Find a tracked page by its URL for a specific user - CHECK USER NOT DELETED"""
    if db is None:
        return None

    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
            return None
    
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return None

    try:
        return pages_collection.find_one({"url": url, "user_id": user_id})
    except Exception as e:
        print(f"Error finding page by URL: {e}")
        return None


def get_user_page_count(user_id: str) -> int:
    """Count how many pages a user currently has - CHECK USER NOT DELETED"""
    if db is None:
        return 0
    
    try:
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        user = users_collection.find_one({
            "_id": user_id,
            "is_deleted": {"$ne": True}
        })
        
        if not user:
            return 0
        
        count = pages_collection.count_documents({"user_id": user_id})
        return count
    except Exception as e:
        print(f"Error counting user pages: {e}")
        return 0


# ---------------- Page Versions - UPDATED FOR SMART VERSIONING ----------------
def create_page_version(
    page_id: str, 
    text_content: str, 
    url: str, 
    html_content: str = None,
    significance_score: float = 1.0,
    change_metrics: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """✅ UPDATED: Create a new page version with smart versioning fields"""
    if db is None:
        return None
    
    # Calculate hashes for content
    content_hash = calculate_content_hash(text_content)
    checksum = calculate_quick_checksum(text_content)
    
    # Check for duplicate content
    duplicate = get_content_duplicate(page_id, content_hash)
    if duplicate:
        print(f"⚠️  Duplicate content detected for page {page_id}. Skipping version creation.")
        return duplicate
    
    version = {
        "page_id": ObjectId(page_id),
        "timestamp": datetime.utcnow(),
        "text_content": text_content,
        "html_content": html_content,
        
        # ✅ SMART VERSIONING FIELDS
        "content_hash": content_hash,
        "checksum": checksum,
        "change_significance_score": significance_score,
        "change_metrics": change_metrics or {
            "content_length": len(text_content),
            "word_count": len(text_content.split()) if text_content else 0,
            "similarity_score": 100.0,
            "change_percentage": 0.0
        },
        "metadata": {
            "url": url,
            "content_length": len(text_content),
            "word_count": len(text_content.split()) if text_content else 0,
            "html_content_length": len(html_content) if html_content else 0,
            "fetched_at": datetime.utcnow().isoformat(),
            "store_reason": "significant_change" if significance_score >= 0.3 else "first_version",
            "versioning_metadata": metadata or {}
        },
    }
    
    try:
        result = versions_collection.insert_one(version)
        version["_id"] = result.inserted_id
        
        print(f"✅ Created version {version['_id']} for page {page_id} with significance score: {significance_score}")
        return version
    except Exception as e:
        print(f"❌ Error creating page version: {e}")
        return None


def get_page_versions(page_id: str, limit: int = 10, significant_only: bool = False):
    """✅ UPDATED: Get page versions for a specific page with filtering"""
    if db is None:
        return []
    
    try:
        query = {"page_id": ObjectId(page_id)}
        if significant_only:
            query["change_significance_score"] = {"$gte": 0.3}
        
        versions = versions_collection.find(query).sort("timestamp", DESCENDING).limit(limit)
        return list(versions)
    except Exception as e:
        print(f"Error getting page versions: {e}")
        return []


def get_significant_page_versions(page_id: str, limit: int = 10):
    """✅ NEW: Get only significant versions for a page"""
    return get_page_versions(page_id, limit=limit, significant_only=True)


def get_latest_page_version(page_id: str, significant_only: bool = False):
    """✅ UPDATED: Get the most recent version of a page with filtering"""
    if db is None:
        return None
    
    try:
        query = {"page_id": ObjectId(page_id)}
        if significant_only:
            query["change_significance_score"] = {"$gte": 0.3}
        
        version = versions_collection.find_one(
            query,
            sort=[("timestamp", DESCENDING)]
        )
        return version
    except Exception as e:
        print(f"Error getting latest page version: {e}")
        return None


def get_previous_version(page_id: str, current_version_id: str = None):
    """✅ NEW: Get the version before the specified one (or latest if not specified)"""
    if db is None:
        return None
    
    try:
        if current_version_id:
            # Get timestamp of current version
            current_version = versions_collection.find_one(
                {"_id": ObjectId(current_version_id)}
            )
            if not current_version:
                return None
            
            # Find version before this timestamp
            previous = versions_collection.find_one(
                {
                    "page_id": ObjectId(page_id),
                    "timestamp": {"$lt": current_version["timestamp"]}
                },
                sort=[("timestamp", DESCENDING)]
            )
            return previous
        else:
            # Get the second most recent version
            versions = list(versions_collection.find(
                {"page_id": ObjectId(page_id)},
                sort=[("timestamp", DESCENDING)],
                limit=2
            ))
            return versions[1] if len(versions) > 1 else None
    except Exception as e:
        print(f"Error getting previous version: {e}")
        return None


def get_version_by_id(version_id: str):
    """✅ NEW: Get a specific version by ID"""
    if db is None:
        return None
    
    try:
        version = versions_collection.find_one({"_id": ObjectId(version_id)})
        return version
    except Exception as e:
        print(f"Error getting version by ID: {e}")
        return None


def prune_old_versions(page_id: str, keep_count: int = 50, keep_significant: bool = True):
    """✅ NEW: Prune old versions, keeping only the most important ones"""
    if db is None:
        return 0
    
    try:
        # Get all versions sorted by timestamp
        all_versions = list(versions_collection.find(
            {"page_id": ObjectId(page_id)},
            sort=[("timestamp", -1)]
        ))
        
        if len(all_versions) <= keep_count:
            return 0  # Nothing to prune
        
        versions_to_keep = []
        
        # Always keep the oldest version
        oldest = all_versions[-1]
        versions_to_keep.append(str(oldest["_id"]))
        
        # Keep versions with high significance scores
        if keep_significant:
            for version in all_versions:
                if version.get("change_significance_score", 0) >= 0.3:
                    version_id = str(version["_id"])
                    if version_id not in versions_to_keep:
                        versions_to_keep.append(version_id)
        
        # If we still need more, keep versions spaced over time
        if len(versions_to_keep) < keep_count:
            time_step = len(all_versions) // (keep_count - len(versions_to_keep))
            for i in range(0, len(all_versions), max(1, time_step)):
                if len(versions_to_keep) >= keep_count:
                    break
                version_id = str(all_versions[i]["_id"])
                if version_id not in versions_to_keep:
                    versions_to_keep.append(version_id)
        
        # Ensure we don't keep more than max
        versions_to_keep = versions_to_keep[:keep_count]
        
        # Delete old versions
        deleted_count = 0
        for version in all_versions:
            version_id = str(version["_id"])
            if version_id not in versions_to_keep:
                versions_collection.delete_one({"_id": version["_id"]})
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"✅ Pruned {deleted_count} old versions for page {page_id}")
        
        return deleted_count
    except Exception as e:
        print(f"Error pruning old versions: {e}")
        return 0


def get_versioning_statistics(page_id: str):
    """✅ NEW: Get statistics about versions for a page"""
    if db is None:
        return {}
    
    try:
        all_versions = list(versions_collection.find(
            {"page_id": ObjectId(page_id)}
        ))
        
        total_versions = len(all_versions)
        significant_versions = len([v for v in all_versions if v.get("change_significance_score", 0) >= 0.3])
        
        avg_significance = 0.0
        if total_versions > 0:
            avg_significance = sum(v.get("change_significance_score", 0) for v in all_versions) / total_versions
        
        # Get size information
        total_size = sum(len(v.get("text_content", "")) for v in all_versions)
        
        return {
            "total_versions": total_versions,
            "significant_versions": significant_versions,
            "insignificant_versions": total_versions - significant_versions,
            "average_significance_score": round(avg_significance, 3),
            "total_content_size_kb": round(total_size / 1024, 2),
            "storage_efficiency_percentage": round((significant_versions / total_versions * 100) if total_versions > 0 else 100, 1),
            "oldest_version": all_versions[-1]["timestamp"] if all_versions else None,
            "newest_version": all_versions[0]["timestamp"] if all_versions else None
        }
    except Exception as e:
        print(f"Error getting versioning statistics: {e}")
        return {}


# ---------------- Change Logs ----------------
def create_change_log(change_data: dict):
    """Create a new change log entry"""
    if db is None:
        return None
    
    change_data_copy = change_data.copy()
    
    if "page_id" in change_data_copy and isinstance(change_data_copy["page_id"], str):
        change_data_copy["page_id"] = ObjectId(change_data_copy["page_id"])
    if "user_id" in change_data_copy and isinstance(change_data_copy["user_id"], str):
        change_data_copy["user_id"] = ObjectId(change_data_copy["user_id"])
    
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
    
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    user = users_collection.find_one({
        "_id": user_id,
        "is_deleted": {"$ne": True}
    })
    
    if not user:
        return []
    
    try:
        changes = changes_collection.find({"user_id": user_id}).sort("timestamp", DESCENDING).limit(limit)
        return list(changes)
    except:
        return []


# ---------------- Additional utility functions for scheduler ----------------
def get_all_active_pages():
    """Get all active pages across all users"""
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


# ---------------- MFA Cleanup Task ----------------
def cleanup_expired_mfa_codes():
    """Clean up expired MFA codes safely (doesn't delete users)"""
    if db is None:
        return 0
    
    try:
        result = users_collection.update_many(
            {
                "mfa_code": {"$ne": None},
                "mfa_code_expires": {"$lt": datetime.utcnow()},
                "is_deleted": {"$ne": True}
            },
            {
                "$set": {
                    "mfa_code": None,
                    "mfa_code_expires": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            print(f"✅ Cleaned {result.modified_count} expired MFA codes (users not deleted)")
        
        return result.modified_count
    except Exception as e:
        print(f"Error cleaning up expired MFA codes: {e}")
        return 0


# ---------------- Audit Logging ----------------
def log_audit_event(operation: str, user_id: str, performed_by: str = "system", details: str = "", ip_address: str = None):
    """Log audit events for tracking user operations"""
    if db is None:
        return False
    
    try:
        audit_log = {
            "timestamp": datetime.utcnow(),
            "operation": operation,
            "user_id": user_id,
            "performed_by": performed_by,
            "details": details,
            "ip_address": ip_address
        }
        
        result = audit_logs_collection.insert_one(audit_log)
        
        sensitive_operations = ["USER_DELETED", "USER_SOFT_DELETED", "LOGIN_FAILED", "PASSWORD_RESET"]
        if operation in sensitive_operations:
            print(f"🔍 AUDIT: {operation} - User: {user_id} - By: {performed_by}")
        
        return result.inserted_id is not None
    except Exception as e:
        print(f"⚠️  Audit logging failed: {e}")
        return False


def get_audit_logs(user_id: str = None, operation: str = None, limit: int = 100):
    """Retrieve audit logs (admin function)"""
    if db is None:
        return []
    
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        if operation:
            query["operation"] = operation
        
        logs = audit_logs_collection.find(query).sort("timestamp", DESCENDING).limit(limit)
        return list(logs)
    except Exception as e:
        print(f"Error getting audit logs: {e}")
        return []


# ---------------- Database Health Check ----------------
def check_database_health():
    """Check database connection and health"""
    if db is None:
        return {
            "status": "unhealthy",
            "message": "Database connection not established"
        }
    
    try:
        client.admin.command('ping')
        
        user_count = users_collection.count_documents({"is_deleted": {"$ne": True}})
        deleted_user_count = users_collection.count_documents({"is_deleted": True})
        page_count = pages_collection.count_documents({})
        mfa_enabled_count = users_collection.count_documents({"mfa_enabled": True, "is_deleted": {"$ne": True}})
        
        # Version statistics
        total_versions = versions_collection.count_documents({})
        significant_versions = versions_collection.count_documents({"change_significance_score": {"$gte": 0.3}})
        efficiency = (significant_versions / total_versions * 100) if total_versions > 0 else 0
        
        # Check for TTL indexes
        indexes = users_collection.index_information()
        ttl_indexes = []
        for name, idx in indexes.items():
            if idx.get("expireAfterSeconds"):
                ttl_indexes.append({
                    "name": name,
                    "expireAfterSeconds": idx.get("expireAfterSeconds"),
                    "key": idx.get("key", {})
                })
        
        return {
            "status": "healthy",
            "message": "Database connection is working",
            "user_protection": {
                "active_users": user_count,
                "deleted_users": deleted_user_count,
                "ttl_indexes_found": len(ttl_indexes),
                "ttl_indexes": ttl_indexes,
                "protection_status": "SAFE" if len(ttl_indexes) == 0 else "WARNING"
            },
            "versioning_stats": {
                "total_versions": total_versions,
                "significant_versions": significant_versions,
                "storage_efficiency": round(efficiency, 1)
            },
            "stats": {
                "total_pages": page_count,
                "users_with_mfa": mfa_enabled_count,
                "mfa_coverage_percentage": round((mfa_enabled_count / user_count * 100) if user_count > 0 else 100, 1)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database health check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


# ---------------- Database Dependency Function ----------------
def get_db():
    """Get database connection for FastAPI dependency injection"""
    return db