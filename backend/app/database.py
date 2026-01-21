from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, timedelta
import os
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

    # Indexes
    def create_indexes():
        users_collection.create_index([("email", ASCENDING)], unique=True)
        pages_collection.create_index([("user_id", ASCENDING), ("url", ASCENDING)], unique=True)
        pages_collection.create_index([("user_id", ASCENDING), ("is_active", ASCENDING)])
        versions_collection.create_index([("page_id", ASCENDING), ("timestamp", DESCENDING)])
        changes_collection.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        changes_collection.create_index([("page_id", ASCENDING), ("timestamp", DESCENDING)])
        
        # Indexes for password reset tokens
        password_reset_tokens_collection.create_index([("token", ASCENDING)], unique=True)
        password_reset_tokens_collection.create_index([("user_id", ASCENDING)])
        password_reset_tokens_collection.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0)  # TTL index
        
        # MFA indexes
        users_collection.create_index([("mfa_code_expires", ASCENDING)], expireAfterSeconds=0)  # Auto-clean expired codes
        
        print("✅ Database indexes created successfully!")

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
    """Get user by email address"""
    if db is None:
        return None
    user = users_collection.find_one({"email": email})
    return user  # Return raw doc (main.py expects ObjectId format)


def get_user_by_id(user_id):
    """Get user by ID"""
    if db is None:
        return None
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        user = users_collection.find_one({"_id": user_id})
        return user
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None


def create_user(user_data: dict):
    """Create a new user with hashed password and MFA enabled by default"""
    if db is None:
        return None
    
    # ✅ Hash the password
    hashed_password = pwd_context.hash(user_data.get('password', ''))
    
    # ✅ Create user document with MFA enabled by default
    user_doc = {
        "email": user_data.get('email'),
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow(),
        "notification_preferences": {
            "email_alerts": True,
            "frequency": "immediately"
        },
        # ✅ MFA fields with defaults - ENABLED BY DEFAULT
        "mfa_enabled": True,  # ✅ Enable MFA by default for all new users
        "mfa_email": user_data.get('email'),  # ✅ Use same email for MFA
        "mfa_code": None,
        "mfa_code_expires": None,
        "mfa_setup_completed": True,  # ✅ Mark as setup completed since MFA is enabled by default
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = users_collection.insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return user_doc  # Return with ObjectId for main.py normalize_doc
    except DuplicateKeyError:
        print(f"User with email {user_data.get('email')} already exists")
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ---------------- MFA Database Functions ----------------
def get_user_mfa_status(user_id):
    """Get MFA status for a user"""
    if db is None:
        return None
    
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        user = users_collection.find_one(
            {"_id": user_id},
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
    """Update user MFA settings"""
    if db is None:
        return False
    
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        result = users_collection.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user MFA status: {e}")
        return False


def update_user_mfa_code(user_id, mfa_code: str, expires_at: datetime):
    """Store MFA code for user"""
    if db is None:
        return False
    
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = users_collection.update_one(
            {"_id": user_id},
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
    """Clear MFA code after successful verification"""
    if db is None:
        return False
    
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        result = users_collection.update_one(
            {"_id": user_id},
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
    """Verify if MFA code is valid"""
    if db is None:
        return False, "Database not available"
    
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        user = users_collection.find_one(
            {"_id": user_id},
            {"mfa_code": 1, "mfa_code_expires": 1, "mfa_enabled": 1}
        )
        
        if not user:
            return False, "User not found"
        
        # ✅ Check if MFA is enabled (default to True for new users)
        if not user.get("mfa_enabled", True):
            return False, "MFA not enabled for this account"
        
        stored_code = user.get("mfa_code")
        expires_at = user.get("mfa_code_expires")
        
        # Check if code exists
        if not stored_code:
            return False, "No MFA code found. Please request a new code."
        
        # Check if code expired
        if expires_at and datetime.utcnow() >= expires_at:
            return False, "MFA code has expired. Please request a new code."
        
        # Check if codes match
        if stored_code != input_code:
            return False, "Invalid MFA code. Please try again."
        
        return True, "Code is valid"
    except Exception as e:
        print(f"Error verifying MFA code: {e}")
        return False, "Internal server error"


def get_users_with_mfa_enabled():
    """Get all users with MFA enabled (for analytics or admin purposes)"""
    if db is None:
        return []
    
    try:
        users = users_collection.find(
            {"mfa_enabled": True},
            {"email": 1, "mfa_email": 1, "mfa_setup_completed": 1, "created_at": 1}
        )
        return list(users)
    except Exception as e:
        print(f"Error getting users with MFA enabled: {e}")
        return []


def get_expired_mfa_codes():
    """Get expired MFA codes that should be cleaned up"""
    if db is None:
        return []
    
    try:
        expired_users = users_collection.find(
            {
                "mfa_code": {"$ne": None},
                "mfa_code_expires": {"$lt": datetime.utcnow()}
            },
            {"email": 1, "mfa_code_expires": 1}
        )
        return list(expired_users)
    except Exception as e:
        print(f"Error getting expired MFA codes: {e}")
        return []


# ---------------- Password Reset Token Operations ----------------
def create_password_reset_token(token: str, user_id: ObjectId, expires_at: datetime) -> bool:
    """Create a new password reset token"""
    if db is None:
        return False
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
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
        # Token already exists (should be very rare with secure tokens)
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
            "expires_at": {"$gt": datetime.utcnow()}  # Not expired
        })
        return token_record  # Return raw doc
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
    """Update a user's password"""
    if db is None:
        return False
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
            return False
    
    hashed_password = pwd_context.hash(new_password)
    
    try:
        result = users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "updated_at": datetime.utcnow()  # Optional: track password updates
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user password: {e}")
        return False


# ---------------- Tracked Pages ----------------
def get_tracked_pages(user_id, active_only: bool = True):
    """Get all tracked pages for a user"""
    if db is None:
        return []
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    query = {"user_id": user_id}
    if active_only:
        query["is_active"] = True
    pages = pages_collection.find(query).sort("created_at", DESCENDING)
    return list(pages)  # Return raw docs for main.py normalize_doc


def get_tracked_page(page_id: str):
    """Get a single tracked page by ID"""
    if db is None:
        return None
    try:
        page = pages_collection.find_one({"_id": ObjectId(page_id)})
        return page  # Return raw doc
    except:
        return None


def create_tracked_page(page_data: dict, user_id):
    """Create a new tracked page"""
    if db is None:
        return None
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
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
    }
    try:
        result = pages_collection.insert_one(page_doc)
        page_doc["_id"] = result.inserted_id
        return page_doc  # Return raw doc for main.py normalize_doc
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
        result = pages_collection.delete_one({"_id": ObjectId(page_id)})
        return result.deleted_count > 0
    except:
        return False


def get_tracked_page_by_url(url: str, user_id):
    """Find a tracked page by its URL for a specific user."""
    if db is None:
        return None

    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        try:
            user_id = ObjectId(user_id)
        except:
            return None  # Invalid string ID

    try:
        # Return raw doc for main.py normalize_doc
        return pages_collection.find_one({"url": url, "user_id": user_id})
    except Exception as e:
        print(f"Error finding page by URL: {e}")
        return None


def get_user_page_count(user_id: str) -> int:
    """Count how many pages a user currently has"""
    if db is None:
        return 0
    
    try:
        # Handle both ObjectId and string user_id
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        
        count = pages_collection.count_documents({"user_id": user_id})
        return count
    except Exception as e:
        print(f"Error counting user pages: {e}")
        return 0


# ---------------- Page Versions ----------------
def create_page_version(page_id: str, text_content: str, url: str, html_content: str = None):
    """Create a new page version with both HTML and text content"""
    if db is None:
        return None
    
    version = {
        "page_id": ObjectId(page_id),
        "timestamp": datetime.utcnow(),
        "text_content": text_content,
        "html_content": html_content,  # Now optional
        "metadata": {
            "url": url,
            "content_length": len(text_content),
            "word_count": len(text_content.split()) if text_content else 0,
            "html_content_length": len(html_content) if html_content else 0,
            "fetched_at": datetime.utcnow().isoformat(),
        },
    }
    try:
        result = versions_collection.insert_one(version)
        version["_id"] = result.inserted_id
        return version  # Return raw doc for main.py normalize_doc
    except:
        return None


def get_page_versions(page_id: str, limit: int = 10):
    """Get page versions for a specific page"""
    if db is None:
        return []
    try:
        versions = versions_collection.find({"page_id": ObjectId(page_id)}).sort("timestamp", DESCENDING).limit(limit)
        return list(versions)  # Return raw docs for main.py normalize_doc
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
        return list(changes)  # Return raw docs for main.py normalize_doc
    except:
        return []


def get_change_logs_for_user(user_id, limit: int = 20):
    """Get change logs for a specific user"""
    if db is None:
        return []
    
    # Handle both ObjectId and string user_id
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)
    
    try:
        changes = changes_collection.find({"user_id": user_id}).sort("timestamp", DESCENDING).limit(limit)
        return list(changes)  # Return raw docs for main.py normalize_doc
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
                {"last_checked": {"$lte": now}}  # This would need more complex logic for intervals
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
        version = versions_collection.find_one(
            {"page_id": ObjectId(page_id)},
            sort=[("timestamp", DESCENDING)]
        )
        return version
    except:
        return None


# ---------------- MFA Cleanup Task ----------------
def cleanup_expired_mfa_codes():
    """Clean up expired MFA codes from database"""
    if db is None:
        return 0
    
    try:
        result = users_collection.update_many(
            {
                "mfa_code": {"$ne": None},
                "mfa_code_expires": {"$lt": datetime.utcnow()}
            },
            {
                "$set": {
                    "mfa_code": None,
                    "mfa_code_expires": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        print(f"✅ Cleaned up {result.modified_count} expired MFA codes")
        return result.modified_count
    except Exception as e:
        print(f"Error cleaning up expired MFA codes: {e}")
        return 0


# ---------------- Database Health Check ----------------
def check_database_health():
    """Check database connection and health"""
    if db is None:
        return {
            "status": "unhealthy",
            "message": "Database connection not established"
        }
    
    try:
        # Test connection
        client.admin.command('ping')
        
        # Get some basic stats
        user_count = users_collection.count_documents({})
        page_count = pages_collection.count_documents({})
        mfa_enabled_count = users_collection.count_documents({"mfa_enabled": True})
        
        return {
            "status": "healthy",
            "message": "Database connection is working",
            "stats": {
                "total_users": user_count,
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
    """
    Get database connection for FastAPI dependency injection.
    This function is required by auth.py router.
    """
    return db