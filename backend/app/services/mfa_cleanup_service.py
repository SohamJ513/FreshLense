# backend/app/services/mfa_cleanup_service.py
"""
Safe MFA cleanup service that clears expired MFA codes without deleting users.
This replaces the dangerous TTL index approach.
"""

from datetime import datetime
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class MFACleanupService:
    """Safely clean up expired MFA codes without deleting users"""
    
    def __init__(self, db=None):
        """Initialize with database connection"""
        self.db = db
    
    def set_database(self, db):
        """Set database connection (can be called later)"""
        self.db = db
    
    def cleanup_expired_mfa_codes(self) -> int:
        """
        Remove expired MFA codes from active users.
        Returns number of users cleaned.
        """
        if not self.db:
            logger.error("Database connection not available")
            return 0
        
        try:
            result = self.db.users.update_many(
                {
                    "mfa_code": {"$ne": None},
                    "mfa_code_expires": {"$lt": datetime.utcnow()},
                    "is_deleted": {"$ne": True}  # Only clean active users
                },
                {
                    "$set": {
                        "mfa_code": None,
                        "mfa_code_expires": None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            cleaned_count = result.modified_count
            
            if cleaned_count > 0:
                logger.info(f"✅ Cleaned {cleaned_count} expired MFA codes")
                
                # Log the cleanup for audit
                self._log_cleanup_operation(
                    operation="MFA_CLEANUP",
                    details=f"Cleaned {cleaned_count} expired MFA codes",
                    affected_count=cleaned_count
                )
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up expired MFA codes: {e}")
            return 0
    
    def cleanup_expired_mfa_for_user(self, user_id: str) -> bool:
        """
        Clean expired MFA code for a specific user.
        Returns True if cleaned, False otherwise.
        """
        if not self.db:
            logger.error("Database connection not available")
            return False
        
        try:
            from bson import ObjectId
            
            # Convert string ID to ObjectId if needed
            if isinstance(user_id, str):
                user_id = ObjectId(user_id)
            
            result = self.db.users.update_one(
                {
                    "_id": user_id,
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
                logger.info(f"✅ Cleaned expired MFA code for user: {user_id}")
                
                # Log the cleanup
                self._log_cleanup_operation(
                    operation="MFA_CLEANUP_SINGLE",
                    details=f"Cleaned expired MFA code for user {user_id}",
                    user_id=str(user_id)
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error cleaning MFA code for user {user_id}: {e}")
            return False
    
    def get_users_with_expired_mfa_codes(self) -> List[Dict[str, Any]]:
        """
        Get list of users with expired MFA codes.
        Useful for monitoring or manual intervention.
        """
        if not self.db:
            logger.error("Database connection not available")
            return []
        
        try:
            users = self.db.users.find(
                {
                    "mfa_code": {"$ne": None},
                    "mfa_code_expires": {"$lt": datetime.utcnow()},
                    "is_deleted": {"$ne": True}
                },
                {
                    "email": 1,
                    "mfa_code_expires": 1,
                    "created_at": 1,
                    "_id": 1
                }
            ).limit(100)  # Limit to prevent memory issues
            
            users_list = list(users)
            
            # Convert ObjectId to string for JSON serialization
            for user in users_list:
                if "_id" in user:
                    user["id"] = str(user["_id"])
                    del user["_id"]
            
            logger.debug(f"Found {len(users_list)} users with expired MFA codes")
            return users_list
            
        except Exception as e:
            logger.error(f"Error getting users with expired MFA codes: {e}")
            return []
    
    def get_mfa_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about MFA cleanup.
        Useful for monitoring dashboard.
        """
        if not self.db:
            return {"error": "Database not available"}
        
        try:
            # Count users with active MFA codes
            total_with_mfa = self.db.users.count_documents({
                "mfa_code": {"$ne": None},
                "is_deleted": {"$ne": True}
            })
            
            # Count users with expired MFA codes
            expired_mfa = self.db.users.count_documents({
                "mfa_code": {"$ne": None},
                "mfa_code_expires": {"$lt": datetime.utcnow()},
                "is_deleted": {"$ne": True}
            })
            
            # Count users with valid MFA codes
            valid_mfa = self.db.users.count_documents({
                "mfa_code": {"$ne": None},
                "mfa_code_expires": {"$gte": datetime.utcnow()},
                "is_deleted": {"$ne": True}
            })
            
            # Get MFA coverage
            total_active_users = self.db.users.count_documents({
                "is_deleted": {"$ne": True}
            })
            
            mfa_coverage = 0
            if total_active_users > 0:
                users_with_mfa_enabled = self.db.users.count_documents({
                    "mfa_enabled": True,
                    "is_deleted": {"$ne": True}
                })
                mfa_coverage = round((users_with_mfa_enabled / total_active_users) * 100, 1)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "stats": {
                    "total_active_users": total_active_users,
                    "users_with_mfa_enabled_percentage": mfa_coverage,
                    "users_with_active_mfa_codes": total_with_mfa,
                    "users_with_expired_mfa_codes": expired_mfa,
                    "users_with_valid_mfa_codes": valid_mfa
                },
                "cleanup_needed": expired_mfa > 0,
                "expired_count": expired_mfa
            }
            
        except Exception as e:
            logger.error(f"Error getting MFA cleanup stats: {e}")
            return {"error": str(e)}
    
    def _log_cleanup_operation(self, operation: str, details: str = "", 
                              user_id: str = None, affected_count: int = 0):
        """
        Internal method to log cleanup operations.
        Can be extended to write to audit logs.
        """
        try:
            # Log to console
            log_message = f"🔧 {operation}: {details}"
            if user_id:
                log_message += f" | User: {user_id}"
            if affected_count > 0:
                log_message += f" | Affected: {affected_count}"
            
            logger.info(log_message)
            
            # Optionally log to audit collection if it exists
            if hasattr(self.db, 'audit_logs'):
                audit_log = {
                    "timestamp": datetime.utcnow(),
                    "operation": operation,
                    "user_id": user_id or "system",
                    "performed_by": "mfa_cleanup_service",
                    "details": details,
                    "affected_count": affected_count,
                    "ip_address": None
                }
                
                self.db.audit_logs.insert_one(audit_log)
                
        except Exception as e:
            # Don't fail cleanup if logging fails
            logger.warning(f"Failed to log cleanup operation: {e}")

# Singleton instance for easy import
mfa_cleanup_service = MFACleanupService()