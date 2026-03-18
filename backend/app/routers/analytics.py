# backend/app/routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import logging

# ✅ FIXED: Import get_current_user from utils.security
from ..utils.security import get_current_user
from ..database import get_db  # This is a synchronous function
from ..models import User

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

# 🔴🔴🔴 TEST ENDPOINT - Add this to verify router is working 🔴🔴🔴
@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify router is working"""
    return {
        "success": True,
        "message": "Analytics router is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/api/analytics/test",
            "/api/analytics/page-health",
            "/api/analytics/change-frequency",
            "/api/analytics/fact-alerts",
            "/api/analytics/failed-crawls",
            "/api/analytics/alerts/{alert_id}/read"
        ]
    }

@router.get("/page-health")
async def get_page_health(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)  # Synchronous db client
):
    """Get health scores for all pages using your existing data"""
    try:
        user_id = str(current_user.id)
        logger.info("=" * 60)
        logger.info("PAGE-HEALTH DEBUG START")
        logger.info("=" * 60)
        logger.info(f"User ID from current_user: {user_id}")
        logger.info(f"User ID type: {type(user_id)}")
        
        # Check all collections
        collections = db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        # Find pages in tracked_pages collection
        logger.info("Trying to find pages in tracked_pages...")
        pages = list(db.tracked_pages.find({"user_id": ObjectId(user_id)}))
        logger.info(f"Pages found: {len(pages)}")
        
        if not pages:
            logger.info("No pages found for this user - returning empty array")
            logger.info("=" * 60)
            return {"success": True, "data": []}
        
        # Log all pages found
        logger.info(f"Pages found: {len(pages)}")
        for i, page in enumerate(pages):
            logger.info(f"Page {i+1}: ID={page['_id']}, URL={page.get('url')}, Title={page.get('display_name')}")
        
        result = []
        for page in pages:
            page_id = page["_id"]
            logger.info(f"Processing page: {page.get('url')} (ID: {page_id})")
            
            # Get versions for this page from page_versions collection
            versions = list(db.page_versions.find(
                {"page_id": page_id}
            ).sort("timestamp", -1).limit(50))
            logger.info(f"  - Versions found: {len(versions)}")
            
            # Get fact checks for this page
            fact_checks = []
            try:
                if 'fact_checks' in collections:
                    fact_checks = list(db.fact_checks.find(
                        {"page_id": str(page_id)}
                    ))
                    logger.info(f"  - Fact checks found: {len(fact_checks)}")
            except Exception as e:
                logger.warning(f"  - Fact checks error: {e}")
                fact_checks = []
            
            # Calculate metrics
            total_versions = len(versions)
            significant_changes = sum(1 for v in versions if v.get("change_significance_score", 0) > 0.3)
            
            # Calculate average change significance
            avg_significance = 0
            if versions:
                significance_scores = [v.get("change_significance_score", 0) for v in versions if v.get("change_significance_score") is not None]
                avg_significance = sum(significance_scores) / len(significance_scores) if significance_scores else 0
            
            # Fact check metrics
            verified = sum(1 for f in fact_checks if f.get("status") == "verified")
            debunked = sum(1 for f in fact_checks if f.get("status") == "debunked")
            total_checks = len(fact_checks)
            
            # Calculate health score (0-100)
            version_health = max(0, 100 - (avg_significance * 100))  # Lower change = healthier
            fact_health = (verified / max(total_checks, 1)) * 100 if total_checks > 0 else 100
            crawl_health = 100 if page.get("last_checked") else 50
            
            health_score = int((version_health + fact_health + crawl_health) / 3)
            
            # Determine status
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "warning"
            else:
                status = "critical"
            
            # Format last_checked as string if it exists
            last_checked = page.get("last_checked")
            if last_checked and isinstance(last_checked, datetime):
                last_checked = last_checked.isoformat()
            
            page_result = {
                "pageId": str(page_id),
                "pageUrl": page.get("url", ""),
                "pageTitle": page.get("display_name") or page.get("url", ""),
                "avgConfidence": round((verified / max(total_checks, 1)) * 100, 1) if total_checks > 0 else 100,
                "totalVersions": total_versions,
                "significantChanges": significant_changes,
                "lastChecked": last_checked or "",
                "healthScore": health_score,
                "healthStatus": status,
                "metrics": {
                    "avgChangeSignificance": round(avg_significance, 2),
                    "totalFactChecks": total_checks,
                    "verifiedCount": verified,
                    "debunkedCount": debunked
                }
            }
            logger.info(f"  - Result: healthScore={health_score}, status={status}, versions={total_versions}")
            result.append(page_result)
        
        # Sort by health score (worst first)
        result.sort(key=lambda x: x["healthScore"])
        
        logger.info(f"Returning {len(result)} page health records")
        logger.info("=" * 60)
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"Page health error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/change-frequency")
async def get_change_frequency(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)  # Synchronous db client
):
    """Get change frequency from version history"""
    try:
        user_id = str(current_user.id)
        start_date = datetime.utcnow() - timedelta(days=days)
        logger.info("=" * 60)
        logger.info("CHANGE-FREQUENCY DEBUG START")
        logger.info("=" * 60)
        logger.info(f"User ID: {user_id}, Days: {days}, Start Date: {start_date}")
        
        # Get all pages for user from tracked_pages
        pages = list(db.tracked_pages.find({"user_id": ObjectId(user_id)}))
        logger.info(f"Total pages found: {len(pages)}")
        
        if not pages:
            logger.info("No pages found - returning empty array")
            logger.info("=" * 60)
            return {"success": True, "data": []}
            
        page_map = {str(p["_id"]): p for p in pages}
        page_ids = [ObjectId(pid) for pid in page_map.keys()]
        logger.info(f"Page IDs: {[str(pid) for pid in page_ids]}")
        
        # Check if page_versions collection exists
        collections = db.list_collection_names()
        if 'page_versions' not in collections:
            logger.info("page_versions collection not found - returning empty array")
            logger.info("=" * 60)
            return {"success": True, "data": []}
        
        # Check total versions in database
        total_versions = db.page_versions.count_documents({})
        logger.info(f"Total versions in database: {total_versions}")
        
        # Check versions for these pages
        versions_count = db.page_versions.count_documents({"page_id": {"$in": page_ids}})
        logger.info(f"Versions for user's pages: {versions_count}")
        
        # Aggregate versions by date
        pipeline = [
            {
                "$match": {
                    "page_id": {"$in": page_ids},
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                        "page_id": "$page_id"
                    },
                    "count": {"$sum": 1},
                    "max_significance": {"$max": "$change_significance_score"},
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "totalChanges": {"$sum": 1},
                    "significantChanges": {
                        "$sum": {
                            "$cond": [{"$gte": ["$max_significance", 0.3]}, 1, 0]
                        }
                    },
                    "pages": {
                        "$push": {
                            "pageId": {"$toString": "$_id.page_id"},
                            "changeCount": "$count",
                            "significanceScore": "$max_significance"
                        }
                    }
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        # Synchronous aggregation
        results = list(db.page_versions.aggregate(pipeline))
        logger.info(f"Aggregation results count: {len(results)}")
        
        # Format results
        formatted = []
        for r in results:
            logger.info(f"Date {r['_id']}: {r['totalChanges']} changes, {r['significantChanges']} significant")
            page_details = []
            for p in r["pages"]:
                page = page_map.get(p["pageId"])
                if page:
                    page_details.append({
                        "pageId": p["pageId"],
                        "pageTitle": page.get("display_name") or page.get("url", ""),
                        "changeCount": p["changeCount"],
                        "significanceScore": p["significanceScore"] or 0
                    })
            
            formatted.append({
                "date": r["_id"],
                "count": r["totalChanges"],
                "significantCount": r["significantChanges"],
                "pages": page_details
            })
        
        logger.info(f"Returning {len(formatted)} change frequency records")
        logger.info("=" * 60)
        return {"success": True, "data": formatted}
        
    except Exception as e:
        logger.error(f"Change frequency error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fact-alerts")
async def get_fact_alerts(
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)  # Synchronous db client
):
    """Get fact-check alerts from change logs"""
    try:
        user_id = str(current_user.id)
        logger.info("=" * 60)
        logger.info("FACT-ALERTS DEBUG START")
        logger.info("=" * 60)
        logger.info(f"User ID: {user_id}, Limit: {limit}")
        
        # Check if change_logs collection exists
        collections = db.list_collection_names()
        if 'change_logs' not in collections:
            logger.info("change_logs collection not found - returning empty array")
            logger.info("=" * 60)
            return {"success": True, "data": []}
        
        # Count total change logs
        total_logs = db.change_logs.count_documents({})
        logger.info(f"Total change logs in database: {total_logs}")
        
        # Count for this user
        user_logs = db.change_logs.count_documents({"user_id": ObjectId(user_id)})
        logger.info(f"Change logs for this user: {user_logs}")
        
        # Get recent change logs with significant changes
        change_logs = list(db.change_logs.find(
            {
                "user_id": ObjectId(user_id),
                "change_significance_score": {"$gte": 0.3}
            }
        ).sort("timestamp", -1).limit(limit))
        
        logger.info(f"Significant change logs found: {len(change_logs)}")
        
        alerts = []
        for log in change_logs:
            logger.info(f"Processing log: {log['_id']}, significance: {log.get('change_significance_score')}")
            
            # Get page details from tracked_pages
            page = db.tracked_pages.find_one({"_id": log["page_id"]})
            if not page:
                logger.warning(f"Page not found for log: {log['_id']}")
                continue
            
            # Determine alert type based on significance
            significance = log.get("change_significance_score", 0) or 0
            if significance >= 0.7:
                alert_type = "critical"
            elif significance >= 0.4:
                alert_type = "warning"
            else:
                alert_type = "info"
            
            # Build message
            page_title = page.get("display_name") or page.get("url", "")
            message = f"Content changed on {page_title}"
            
            # Add specific change info if available
            diff = log.get("diff", {})
            if diff and diff.get("significant_changes"):
                significant_changes = diff.get("significant_changes", [])
                if significant_changes:
                    message += f" - {significant_changes[0]}"
            
            # Format timestamp
            timestamp = log.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            
            alerts.append({
                "id": str(log["_id"]),
                "pageId": str(log["page_id"]),
                "pageTitle": page_title,
                "pageUrl": page.get("url", ""),
                "type": alert_type,
                "message": message,
                "timestamp": timestamp,
                "confidence": max(0, 100 - (significance * 100)),
                "changeSignificanceScore": significance,
                "read": log.get("user_viewed", False) or log.get("viewed_by_user", False)
            })
        
        # Sort by timestamp (newest first) and limit
        alerts.sort(key=lambda x: x["timestamp"], reverse=True)
        alerts = alerts[:limit]
        
        logger.info(f"Returning {len(alerts)} fact alerts")
        logger.info("=" * 60)
        return {"success": True, "data": alerts}
        
    except Exception as e:
        logger.error(f"Fact alerts error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/failed-crawls")
async def get_failed_crawls(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)  # Synchronous db client
):
    """Get pages with failed crawls"""
    try:
        user_id = str(current_user.id)
        logger.info("=" * 60)
        logger.info("FAILED-CRAWLS DEBUG START")
        logger.info("=" * 60)
        logger.info(f"User ID: {user_id}")
        
        # Find pages with crawl issues
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Look for pages that either:
        # 1. Have crawl_status = 'failed'
        # 2. Haven't been checked in 7 days
        # 3. Have never been checked
        query = {
            "user_id": ObjectId(user_id),
            "$or": [
                {"crawl_status": "failed"},
                {"last_checked": {"$lt": seven_days_ago}},
                {"last_checked": None}
            ]
        }
        logger.info(f"Query: {query}")
        
        pages = list(db.tracked_pages.find(query))
        logger.info(f"Pages with crawl issues: {len(pages)}")
        
        failures = []
        for page in pages:
            logger.info(f"Failed page: {page.get('url')}, last_checked: {page.get('last_checked')}, status: {page.get('crawl_status')}")
            
            # Format last_attempt
            last_attempt = page.get("last_checked")
            if isinstance(last_attempt, datetime):
                last_attempt = last_attempt.isoformat()
            
            failures.append({
                "pageId": str(page["_id"]),
                "pageUrl": page.get("url", ""),
                "pageTitle": page.get("display_name") or page.get("url", ""),
                "failedAttempts": page.get("crawl_failures", 1),
                "lastAttempt": last_attempt or "",
                "errorMessage": page.get("last_error", "Crawl failed or never attempted")
            })
        
        logger.info(f"Returning {len(failures)} failed crawls")
        logger.info("=" * 60)
        return {"success": True, "data": failures}
        
    except Exception as e:
        logger.error(f"Failed crawls error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/alerts/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db)  # Synchronous db client
):
    """Mark a change log as viewed"""
    try:
        user_id = str(current_user.id)
        logger.info(f"Marking alert {alert_id} as read for user {user_id}")
        
        # Check if change_logs collection exists
        collections = db.list_collection_names()
        if 'change_logs' not in collections:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Try both possible field names (user_viewed or viewed_by_user)
        result = db.change_logs.update_one(
            {
                "_id": ObjectId(alert_id),
                "user_id": ObjectId(user_id)
            },
            {
                "$set": {
                    "user_viewed": True,
                    "viewed_by_user": True
                }
            }
        )
        
        if result.modified_count == 0:
            # Check if alert exists but doesn't belong to user
            alert = db.change_logs.find_one({"_id": ObjectId(alert_id)})
            if alert:
                logger.warning(f"Alert {alert_id} found but doesn't belong to user {user_id}")
                raise HTTPException(status_code=403, detail="Not authorized to modify this alert")
            else:
                logger.warning(f"Alert {alert_id} not found")
                raise HTTPException(status_code=404, detail="Alert not found")
        
        logger.info(f"Successfully marked alert {alert_id} as read")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Mark alert read error: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))