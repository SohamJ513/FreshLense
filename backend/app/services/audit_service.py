# backend/app/services/audit_service.py
"""
Audit logging service to track user operations for security and debugging.
"""

from datetime import datetime
import logging
from typing import Optional, Dict, Any, List
import traceback

logger = logging.getLogger(__name__)

class AuditService:
    """Track all user-related operations for security and debugging"""
    
    def __init__(self, db=None):
        """Initialize with database connection"""
        self.db = db
    
    def set_database(self, db):
        """Set database connection (can be called later)"""
        self.db = db
    
    def log_event(self, operation: str, user_id: str, 
                 performed_by: str = "system", details: str = "", 
                 ip_address: str = None, metadata: Dict = None) -> bool:
        """
        Log any audit event.
        Returns True if logged successfully.
        """
        if not self.db:
            logger.warning(f"AUDIT SKIPPED: {operation} - User: {user_id} (DB not available)")
            return False
        
        try:
            # Ensure audit_logs collection exists
            if "audit_logs" not in self.db.list_collection_names():
                self.db.create_collection("audit_logs")
            
            # Prepare audit log entry
            audit_log = {
                "timestamp": datetime.utcnow(),
                "operation": operation,
                "user_id": str(user_id),  # Store as string
                "performed_by": performed_by,
                "details": details[:500],  # Limit details length
                "ip_address": ip_address,
                "metadata": metadata or {},
                "server_timestamp": datetime.utcnow().isoformat()
            }
            
            # Insert into audit logs
            result = self.db.audit_logs.insert_one(audit_log)
            
            # Log sensitive operations to console for immediate visibility
            sensitive_operations = [
                "USER_DELETED", "USER_SOFT_DELETED", "LOGIN_FAILED", 
                "PASSWORD_RESET", "MFA_DISABLED", "ACCOUNT_LOCKED",
                "USER_CREATED", "USER_MODIFIED"
            ]
            
            if operation in sensitive_operations:
                logger.info(f"🔍 AUDIT: {operation} - User: {user_id} - By: {performed_by}")
            
            return result.inserted_id is not None
            
        except Exception as e:
            # Don't crash the application if audit logging fails
            logger.error(f"⚠️  Audit logging failed: {e}")
            return False
    
    # -------------------- Specific Event Loggers --------------------
    
    def log_user_login(self, user_id: str, email: str, success: bool, 
                      ip_address: str = None, details: str = "") -> bool:
        """Log user login attempts"""
        operation = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
        
        return self.log_event(
            operation=operation,
            user_id=user_id,
            performed_by="auth_system",
            details=f"Email: {email} - {details}",
            ip_address=ip_address,
            metadata={"email": email, "success": success}
        )
    
    def log_user_registration(self, user_id: str, email: str, 
                             ip_address: str = None) -> bool:
        """Log new user registration"""
        return self.log_event(
            operation="USER_REGISTERED",
            user_id=user_id,
            performed_by="registration_system",
            details=f"New user registered: {email}",
            ip_address=ip_address,
            metadata={"email": email}
        )
    
    def log_user_deletion_attempt(self, user_id: str, attempted_by: str, 
                                 reason: str = "", ip_address: str = None) -> bool:
        """Log any attempt to delete a user"""
        return self.log_event(
            operation="USER_DELETION_ATTEMPT",
            user_id=user_id,
            performed_by=attempted_by,
            details=f"Deletion attempt - Reason: {reason}",
            ip_address=ip_address,
            metadata={"reason": reason}
        )
    
    def log_user_soft_deleted(self, user_id: str, deleted_by: str, 
                             reason: str = "", ip_address: str = None) -> bool:
        """Log when a user is soft deleted"""
        return self.log_event(
            operation="USER_SOFT_DELETED",
            user_id=user_id,
            performed_by=deleted_by,
            details=f"User soft deleted - Reason: {reason}",
            ip_address=ip_address,
            metadata={"reason": reason, "soft_delete": True}
        )
    
    def log_mfa_operation(self, user_id: str, operation: str, 
                         details: str = "", ip_address: str = None) -> bool:
        """Log MFA-related operations"""
        return self.log_event(
            operation=f"MFA_{operation}",
            user_id=user_id,
            performed_by="mfa_system",
            details=details,
            ip_address=ip_address,
            metadata={"mfa_operation": operation}
        )
    
    def log_password_reset(self, user_id: str, operation: str, 
                          details: str = "", ip_address: str = None) -> bool:
        """Log password reset operations"""
        return self.log_event(
            operation=f"PASSWORD_{operation}",
            user_id=user_id,
            performed_by="password_system",
            details=details,
            ip_address=ip_address,
            metadata={"password_operation": operation}
        )
    
    def log_page_operation(self, user_id: str, operation: str, page_id: str = None,
                          details: str = "", ip_address: str = None) -> bool:
        """Log page tracking operations"""
        metadata = {"page_operation": operation}
        if page_id:
            metadata["page_id"] = page_id
            
        return self.log_event(
            operation=f"PAGE_{operation}",
            user_id=user_id,
            performed_by="page_system",
            details=details,
            ip_address=ip_address,
            metadata=metadata
        )
    
    # -------------------- Query Methods --------------------
    
    def get_audit_logs(self, user_id: str = None, operation: str = None, 
                      start_date: datetime = None, end_date: datetime = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with filtering options.
        Useful for admin dashboard or debugging.
        """
        if not self.db:
            logger.error("Database connection not available")
            return []
        
        try:
            query = {}
            
            # Apply filters
            if user_id:
                query["user_id"] = user_id
            if operation:
                query["operation"] = operation
            if start_date:
                query["timestamp"] = {"$gte": start_date}
            if end_date:
                if "timestamp" in query:
                    query["timestamp"]["$lte"] = end_date
                else:
                    query["timestamp"] = {"$lte": end_date}
            
            # Execute query
            logs = self.db.audit_logs.find(query).sort("timestamp", -1).limit(limit)
            logs_list = list(logs)
            
            # Convert ObjectId to string and format dates
            for log in logs_list:
                if "_id" in log:
                    log["id"] = str(log["_id"])
                    del log["_id"]
                if "timestamp" in log and isinstance(log["timestamp"], datetime):
                    log["timestamp_iso"] = log["timestamp"].isoformat()
            
            return logs_list
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get summary of user activity for a specific user.
        Useful for user profile or admin review.
        """
        if not self.db:
            return {"error": "Database not available"}
        
        try:
            from datetime import timedelta
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get logs for user in date range
            logs = self.db.audit_logs.find({
                "user_id": user_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            logs_list = list(logs)
            
            # Count operations by type
            operation_counts = {}
            for log in logs_list:
                op = log.get("operation", "UNKNOWN")
                operation_counts[op] = operation_counts.get(op, 0) + 1
            
            # Get unique days with activity
            active_days = set()
            for log in logs_list:
                if "timestamp" in log:
                    day = log["timestamp"].strftime("%Y-%m-%d")
                    active_days.add(day)
            
            return {
                "user_id": user_id,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_events": len(logs_list),
                "active_days": len(active_days),
                "operation_counts": operation_counts,
                "recent_operations": [
                    {
                        "timestamp": log.get("timestamp").isoformat() if log.get("timestamp") else None,
                        "operation": log.get("operation"),
                        "details": log.get("details", "")[:100]
                    }
                    for log in logs_list[:10]  # Last 10 operations
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {"error": str(e)}
    
    def get_system_health_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate a system health report from audit logs.
        Useful for monitoring and alerts.
        """
        if not self.db:
            return {"error": "Database not available"}
        
        try:
            from datetime import timedelta
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get failed login attempts
            failed_logins = self.db.audit_logs.count_documents({
                "operation": "LOGIN_FAILED",
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            # Get successful logins
            successful_logins = self.db.audit_logs.count_documents({
                "operation": "LOGIN_SUCCESS",
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            # Get user registrations
            new_registrations = self.db.audit_logs.count_documents({
                "operation": "USER_REGISTERED",
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            # Get security events
            security_events = self.db.audit_logs.count_documents({
                "operation": {"$in": ["USER_DELETION_ATTEMPT", "USER_SOFT_DELETED"]},
                "timestamp": {"$gte": start_date, "$lte": end_date}
            })
            
            # Calculate login success rate
            total_logins = failed_logins + successful_logins
            login_success_rate = 0
            if total_logins > 0:
                login_success_rate = round((successful_logins / total_logins) * 100, 1)
            
            return {
                "report_period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "generated_at": datetime.utcnow().isoformat(),
                "metrics": {
                    "failed_login_attempts": failed_logins,
                    "successful_logins": successful_logins,
                    "new_user_registrations": new_registrations,
                    "security_events": security_events,
                    "total_login_attempts": total_logins,
                    "login_success_rate_percent": login_success_rate
                },
                "recommendations": self._generate_recommendations(
                    failed_logins, login_success_rate, security_events
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating system health report: {e}")
            return {"error": str(e)}
    
    def _generate_recommendations(self, failed_logins: int, 
                                 login_success_rate: float, 
                                 security_events: int) -> List[str]:
        """Generate recommendations based on audit data"""
        recommendations = []
        
        if failed_logins > 50:
            recommendations.append("High number of failed login attempts. Consider implementing account lockout.")
        
        if login_success_rate < 80:
            recommendations.append("Low login success rate. Review authentication flow.")
        
        if security_events > 0:
            recommendations.append("Security events detected. Review audit logs.")
        
        if not recommendations:
            recommendations.append("System health appears normal. Continue monitoring.")
        
        return recommendations
    
    def cleanup_old_audit_logs(self, days_to_keep: int = 90) -> int:
        """
        Clean up audit logs older than specified days.
        Returns number of logs deleted.
        """
        if not self.db:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = self.db.audit_logs.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned {deleted_count} old audit logs (older than {days_to_keep} days)")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old audit logs: {e}")
            return 0

# Singleton instance for easy import
audit_service = AuditService()