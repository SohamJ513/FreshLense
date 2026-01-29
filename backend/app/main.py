from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from bson import ObjectId
import asyncio
import logging
from contextlib import asynccontextmanager

# ✅ Load environment variables
from dotenv import load_dotenv
import os
load_dotenv()

# ================================================
# Configure logging
# ================================================

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

# ✅ Import database functions (for pages only)
from .database import (
    get_tracked_pages, get_tracked_page, create_tracked_page, update_tracked_page,
    get_page_versions, create_change_log, get_change_logs_for_user, create_page_version,
    get_tracked_page_by_url, get_user_page_count, delete_tracked_page
)
from .scheduler import MonitoringScheduler
from .crawler import ContentFetcher

# ✅ Import routers
from .routers import fact_check, auth

# ✅ Import security utilities
from .utils.security import get_current_user

# -------------------- Email Configuration Check --------------------
def check_email_configuration():
    """Check and log email configuration status"""
    email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    resend_api_key = os.getenv("RESEND_API_KEY")
    resend_from_email = os.getenv("RESEND_FROM_EMAIL")
    
    if email_enabled:
        if resend_api_key:
            print("✅ Email notifications: ENABLED with Resend")
            print(f"   From email: {resend_from_email or 'onboarding@resend.dev'}")
            return True
        else:
            print("❌ EMAIL_ENABLED=true but RESEND_API_KEY missing!")
            print("   Add RESEND_API_KEY to your .env file")
            return False
    else:
        print("ℹ️  Email notifications: DISABLED (EMAIL_ENABLED=false)")
        return False

# Instantiate scheduler and crawler
monitoring_scheduler = MonitoringScheduler()
crawler = ContentFetcher()

# -------------------- Page Models --------------------
class TrackedPageCreate(BaseModel):
    url: str
    display_name: Optional[str] = None
    check_interval_minutes: int = 1440

class TrackedPageResponse(BaseModel):
    id: str
    user_id: str
    url: str
    display_name: Optional[str]
    check_interval_minutes: int
    is_active: bool
    created_at: datetime
    last_checked: Optional[datetime] = None
    last_change_detected: Optional[datetime] = None
    current_version_id: Optional[str] = None

class PageVersionResponse(BaseModel):
    id: str
    page_id: str
    timestamp: datetime
    text_content: str
    metadata: dict

class ChangeLogResponse(BaseModel):
    id: str
    page_id: str
    user_id: str
    type: str
    timestamp: datetime
    description: Optional[str] = None
    semantic_similarity_score: Optional[float] = None

def normalize_doc(doc: dict) -> dict:
    """Convert MongoDB _id -> id (string) for API responses"""
    if not doc:
        return None
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    if "user_id" in doc:
        doc["user_id"] = str(doc["user_id"])
    if "page_id" in doc:
        doc["page_id"] = str(doc["page_id"])
    if "current_version_id" in doc and doc["current_version_id"]:
        doc["current_version_id"] = str(doc["current_version_id"])
    return doc

def generate_sequential_name(user_id: str) -> str:
    """Generate sequential names like test1, test2, test3 for extension requests"""
    page_count = get_user_page_count(user_id)
    next_number = page_count + 1
    return f"test{next_number}"

# -------------------- Lifespan (startup/shutdown) --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    print("=" * 60)
    print("🚀 Starting FreshLense API...")
    print("=" * 60)
    
    # Silence scheduler and crawler logs
    logging.getLogger("app.scheduler").setLevel(logging.WARNING)
    logging.getLogger("app.crawler").setLevel(logging.WARNING)
    logging.getLogger("app.services").setLevel(logging.WARNING)
    
    # Check SERP API configuration
    serp_api_key = os.getenv("SERPAPI_API_KEY")
    if serp_api_key:
        print(f"✅ SERP API Key loaded: {serp_api_key[:10]}...")
    else:
        print("❌ SERP API Key NOT found in environment")
        print("💡 Make sure you have a .env file with SERPAPI_API_KEY=your_key")
    
    # Check email configuration
    email_configured = check_email_configuration()
    
    # Check database connection
    from .database import is_db_available
    if is_db_available():
        print("✅ Database connection: ACTIVE")
    else:
        print("❌ Database connection: FAILED")
    
    # Start monitoring scheduler
    try:
        print("\n🔄 Starting monitoring scheduler...")
        if asyncio.iscoroutinefunction(monitoring_scheduler.start):
            await monitoring_scheduler.start()
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, monitoring_scheduler.start)
        print("✅ Monitoring scheduler started successfully")
        
        if hasattr(monitoring_scheduler, 'email_enabled'):
            if monitoring_scheduler.email_enabled:
                print("✅ Scheduler email notifications: ENABLED")
            else:
                print("❌ Scheduler email notifications: DISABLED")
    except Exception as e:
        print(f"❌ Error starting monitoring scheduler: {e}")
        raise

    print("\n" + "=" * 60)
    print("✅ FreshLense API is ready!")
    print("=" * 60)
    
    try:
        yield
    finally:
        # SHUTDOWN
        print("\n" + "=" * 60)
        print("🛑 Shutting down FreshLense API...")
        try:
            if asyncio.iscoroutinefunction(monitoring_scheduler.shutdown):
                await monitoring_scheduler.shutdown()
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, monitoring_scheduler.shutdown)
            print("✅ Monitoring scheduler stopped")
        except Exception as e:
            print(f"❌ Error during monitoring_scheduler.shutdown(): {e}")
        print("=" * 60)

# -------------------- Create FastAPI app --------------------
app = FastAPI(
    title="FreshLense API",
    description="API for web content monitoring platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
origins = [
    "http://localhost:3000",
    "chrome-extension://*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Include Routers --------------------
# ✅ All auth endpoints are in auth.router
app.include_router(auth.router)

# -------------------- Tracked Pages Routes --------------------
@app.get("/api/pages", response_model=List[TrackedPageResponse])
async def get_my_pages(current_user: dict = Depends(get_current_user)):
    """Get all tracked pages for the current user"""
    print(f"📄 [MAIN] Fetching pages for user: {current_user['email']}")
    pages = get_tracked_pages(current_user["_id"])
    print(f"✅ [MAIN] Found {len(pages)} pages for {current_user['email']}")
    return [normalize_doc(p) for p in pages]

@app.post("/api/pages", response_model=TrackedPageResponse)
async def create_page(
    page: TrackedPageCreate, 
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    # Check if request is from Chrome extension
    is_extension = request.headers.get("x-request-source") == "chrome-extension"
    
    # Generate sequential name for extension requests without display name
    if is_extension and (not page.display_name or page.display_name.strip() == ""):
        display_name = generate_sequential_name(current_user["_id"])
    else:
        display_name = page.display_name or page.url
    
    page_data = {
        "url": page.url, 
        "display_name": display_name,
        "check_interval_minutes": page.check_interval_minutes
    }
    
    new_page = create_tracked_page(page_data, current_user["_id"])
    
    # Schedule page
    try:
        if asyncio.iscoroutinefunction(monitoring_scheduler.schedule_page):
            await monitoring_scheduler.schedule_page(new_page)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, monitoring_scheduler.schedule_page, new_page)
    except Exception as e:
        print(f"Failed to schedule page immediately after creation: {e}")

    return normalize_doc(new_page)

@app.delete("/api/pages/{page_id}")
async def delete_page(page_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a tracked page"""
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")
    
    page = get_tracked_page(page_id)
    if not page or page["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Page not found")
    
    success = delete_tracked_page(page_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete page")
    
    return {"status": "success", "message": "Page deleted successfully"}

@app.get("/api/pages/by-url", response_model=TrackedPageResponse)
async def get_page_by_url(
    url: str = Query(..., description="URL to check"),
    current_user: dict = Depends(get_current_user)
):
    """Check if a page is already tracked by its URL"""
    page = get_tracked_page_by_url(url, current_user["_id"])
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found for this user at this URL"
        )
    return normalize_doc(page)

@app.get("/api/pages/{page_id}", response_model=TrackedPageResponse)
async def get_page(page_id: str, current_user: dict = Depends(get_current_user)):
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")
    page = get_tracked_page(page_id)
    if not page or page["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Page not found")
    return normalize_doc(page)

@app.get("/api/pages/{page_id}/versions", response_model=List[PageVersionResponse])
async def get_versions(page_id: str, current_user: dict = Depends(get_current_user)):
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")
    page = get_tracked_page(page_id)
    if not page or page["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Page not found")
    versions = get_page_versions(page_id)
    return [normalize_doc(v) for v in versions]

# -------------------- Change Logs Routes --------------------
@app.get("/api/changes", response_model=List[ChangeLogResponse])
async def get_my_changes(current_user: dict = Depends(get_current_user)):
    changes = get_change_logs_for_user(current_user["_id"])
    return [normalize_doc(c) for c in changes]

# -------------------- Fact Check Routes --------------------
# ✅ Include fact check router with authentication
app.include_router(fact_check.router, dependencies=[Depends(get_current_user)])

# -------------------- Crawl Routes --------------------
@app.post("/api/crawl")
async def crawl_url(
    url: str = Query(..., description="URL to crawl"),
    current_user: dict = Depends(get_current_user)
):
    """Trigger a manual crawl for a given URL (no DB save)"""
    try:
        html_content, text_content = crawler.fetch_and_extract(url)
        if not html_content:
            raise HTTPException(status_code=400, detail="Failed to fetch content from URL")

        return {
            "status": "success",
            "url": url,
            "html_content_length": len(html_content) if html_content else 0,
            "text_content_length": len(text_content) if text_content else 0,
            "text_content_preview": text_content[:300] if text_content else None,
            "full_text_content": text_content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawl/{page_id}")
async def crawl_page_by_id(page_id: str, current_user: dict = Depends(get_current_user)):
    """Trigger a manual crawl for a tracked page by its ID and store results"""
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")

    page = get_tracked_page(page_id)
    if not page or page["user_id"] != current_user["_id"]:
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        html_content, text_content = crawler.fetch_and_extract(page["url"])
        if not html_content:
            raise HTTPException(status_code=400, detail="Failed to fetch content from URL")

        new_version = create_page_version(
            page_id=page_id,
            html_content=html_content,
            text_content=text_content,
            url=page["url"]
        )
        
        if not new_version:
            raise HTTPException(status_code=500, detail="Failed to save page version")

        update_data = {
            "last_checked": datetime.utcnow(),
            "current_version_id": str(new_version["_id"])
        }

        versions = get_page_versions(page_id)
        if len(versions) > 1 and versions[-2]["text_content"] != text_content:
            update_data["last_change_detected"] = datetime.utcnow()
            create_change_log({
                "page_id": ObjectId(page_id),
                "user_id": page["user_id"],
                "type": "manual_crawl",
                "timestamp": datetime.utcnow(),
                "description": "Content changed on manual crawl"
            })

        update_tracked_page(page_id, update_data)

        return {
            "status": "success",
            "page_id": page_id,
            "url": page["url"],
            "version_id": str(new_version["_id"]),
            "change_detected": "last_change_detected" in update_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- Debug & Test Routes --------------------
@app.get("/api/debug/email-config")
async def debug_email_config():
    """Debug endpoint to check email configuration"""
    email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    resend_api_key = os.getenv("RESEND_API_KEY")
    
    return {
        "email_enabled": email_enabled,
        "resend_api_key_configured": bool(resend_api_key),
        "resend_api_key_length": len(resend_api_key) if resend_api_key else 0,
        "resend_from_email": os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
        "scheduler_email_enabled": getattr(monitoring_scheduler, 'email_enabled', 'Unknown'),
        "scheduler_running": monitoring_scheduler.is_running,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/test/email")
async def test_email_send(request: Request):
    """Test email sending manually"""
    try:
        import resend
        resend_api_key = os.getenv("RESEND_API_KEY")
        
        if not resend_api_key:
            return {
                "success": False,
                "error": "RESEND_API_KEY not configured",
                "message": "Add RESEND_API_KEY to your .env file"
            }
        
        resend.api_key = resend_api_key
        
        data = await request.json()
        test_email = data.get("email", "test@example.com")
        
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        
        params = {
            "from": f"FreshLense Test <{from_email}>",
            "to": [test_email],
            "subject": "🧪 FreshLense Email Test",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>🧪 FreshLense Email System Test</h2>
                <p>If you receive this email, your FreshLense email system is working correctly!</p>
                <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p><strong>System Status:</strong> ✅ Operational</p>
                    <p><strong>Test Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
                </div>
                <p>You will now receive:</p>
                <ul>
                    <li>Direct fact-check results</li>
                    <li>Page change notifications</li>
                    <li>Monitoring alerts</li>
                </ul>
            </body>
            </html>
            """,
            "text": f"""FreshLense Email Test

If you receive this email, your FreshLense email system is working correctly!

System Status: ✅ Operational
Test Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

You will now receive:
- Direct fact-check results
- Page change notifications
- Monitoring alerts

This is a test email from FreshLense."""
        }
        
        response = resend.Emails.send(params)
        return {
            "success": True,
            "email_id": response['id'],
            "recipient": test_email,
            "message": f"Test email sent to {test_email}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to send test email. Check RESEND_API_KEY configuration."
        }

# -------------------- Health Check --------------------
@app.get("/api/health")
async def health_check():
    """Health check endpoint with detailed status"""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(), 
        "scheduler_running": monitoring_scheduler.is_running,
        "email_enabled": getattr(monitoring_scheduler, 'email_enabled', False),
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FreshLense API is running!",
        "version": "1.0.0",
        "endpoints": {
            "documentation": "/docs",
            "health": "/api/health",
            "email_config": "/api/debug/email-config",
            "test_email": "POST /api/test/email",
            "token_debug": "POST /api/auth/debug-token?token=YOUR_TOKEN"
        },
        "features": {
            "email_notifications": getattr(monitoring_scheduler, 'email_enabled', False),
            "scheduler_active": monitoring_scheduler.is_running
        }
    }