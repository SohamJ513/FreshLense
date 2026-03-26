# backend/app/main.py
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
# Configure logging - REDUCED VERBOSITY
# ================================================

logging.basicConfig(
    level=logging.WARNING,  # Only show WARNING and above in console
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('app.log', mode='a')  # File handler for detailed logs
    ]
)

# Set specific loggers to appropriate levels
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.ERROR)  # Hide passlib warnings

# Your application loggers - set to WARNING to reduce noise
logging.getLogger("app").setLevel(logging.INFO)
logging.getLogger("app.scheduler").setLevel(logging.WARNING)
logging.getLogger("app.crawler").setLevel(logging.WARNING)
logging.getLogger("app.services").setLevel(logging.WARNING)
logging.getLogger("app.ai_service").setLevel(logging.INFO)  # AI service logging
logging.getLogger("app.auth").setLevel(logging.WARNING)  # Reduce auth logs
logging.getLogger("app.database").setLevel(logging.WARNING)
logging.getLogger("app.utils").setLevel(logging.WARNING)

# File handler for detailed logs (DEBUG level in file only)
file_handler = logging.FileHandler('detailed.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add file handler to specific loggers for detailed debugging
logging.getLogger("app").addHandler(file_handler)
logging.getLogger("app.scheduler").addHandler(file_handler)
logging.getLogger("app.ai_service").addHandler(file_handler)

# Create logger for this module
logger = logging.getLogger(__name__)

# ✅ Import database functions
from .database import (
    get_tracked_pages, get_tracked_page, create_tracked_page, update_tracked_page,
    get_page_versions, create_change_log, get_change_logs_for_user, create_page_version,
    get_tracked_page_by_url, get_user_page_count, delete_tracked_page,
    get_db, versions_collection, pages_collection, change_logs_collection
)
from .scheduler import MonitoringScheduler
from .crawler import ContentFetcher

# ✅ Import routers
from .routers import fact_check, auth, pages, analytics

# ✅ Import services
from .services.ai_service import ai_service
from .services.versioning_service import VersioningService

# ✅ Import security utilities
from .utils.security import get_current_user
from .models import User as UserModel

# -------------------- Helper function to get user ID --------------------
def get_user_id_from_current_user(current_user) -> str:
    """Extract user ID from current_user (handles both dict and User object)"""
    if isinstance(current_user, dict):
        # Dictionary format (fallback)
        if '_id' in current_user:
            return str(current_user['_id'])
        elif 'id' in current_user:
            return str(current_user['id'])
    elif hasattr(current_user, '_id') and current_user._id is not None:
        # User model with _id attribute
        return str(current_user._id)
    elif hasattr(current_user, 'id') and current_user.id is not None:
        # User model with id attribute
        return str(current_user.id)
    else:
        raise ValueError(f"Cannot extract user ID from current_user. Type: {type(current_user)}")

def get_user_email_from_current_user(current_user) -> str:
    """Extract email from current_user (handles both dict and User object)"""
    if isinstance(current_user, dict):
        # Dictionary format (fallback)
        return current_user.get('email', 'unknown@email.com')
    elif hasattr(current_user, 'email'):
        # User model with email attribute
        return current_user.email
    else:
        return 'unknown@email.com'

# -------------------- Email Configuration Check --------------------
def check_email_configuration():
    """Check and log email configuration status"""
    email_enabled = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    resend_api_key = os.getenv("RESEND_API_KEY")
    resend_from_email = os.getenv("RESEND_FROM_EMAIL")
    
    if email_enabled:
        if resend_api_key:
            logger.info("Email notifications: ENABLED with Resend")
            logger.info(f"   From email: {resend_from_email or 'onboarding@resend.dev'}")
            return True
        else:
            logger.warning("EMAIL_ENABLED=true but RESEND_API_KEY missing!")
            logger.warning("   Add RESEND_API_KEY to your .env file")
            return False
    else:
        logger.info("Email notifications: DISABLED (EMAIL_ENABLED=false)")
        return False

# -------------------- AI Configuration Check --------------------
def check_ai_configuration():
    """Check and log AI service configuration status"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    ai_enabled = os.getenv("AI_SUMMARIES_ENABLED", "true").lower() == "true"
    
    if ai_enabled:
        if openai_api_key:
            logger.info("AI summaries: ENABLED with Groq")
            logger.info(f"   Model: {os.getenv('OPENAI_MODEL', 'gpt-5-nano')}")
            return True
        else:
            logger.warning("AI_SUMMARIES_ENABLED=true but OPENAI_API_KEY missing!")
            logger.warning("   Add OPENAI_API_KEY to your .env file")
            return False
    else:
        logger.info("AI summaries: DISABLED (AI_SUMMARIES_ENABLED=false)")
        return False

# Instantiate services
monitoring_scheduler = MonitoringScheduler()
crawler = ContentFetcher()
versioning_service = VersioningService()

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
    version_count: Optional[int] = 0

class PageVersionResponse(BaseModel):
    id: str
    page_id: str
    timestamp: datetime
    text_content: str
    metadata: dict
    change_significance_score: Optional[float] = 0
    has_ai_summary: Optional[bool] = False

class ChangeLogResponse(BaseModel):
    id: str
    page_id: str
    user_id: str
    type: str
    timestamp: datetime
    description: Optional[str] = None
    semantic_similarity_score: Optional[float] = None
    change_significance_score: Optional[float] = 0

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
    print("Starting FreshLense API...")
    print("=" * 60)
    
    # Check SERP API configuration
    serp_api_key = os.getenv("SERPAPI_API_KEY")
    if serp_api_key:
        print(f"SERP API Key loaded: {serp_api_key[:10]}...")
    else:
        print("SERP API Key NOT found in environment")
        print("Make sure you have a .env file with SERPAPI_API_KEY=your_key")
    
    # Check email configuration
    email_configured = check_email_configuration()
    
    # Check AI configuration
    ai_configured = check_ai_configuration()
    
    # Check database connection
    from .database import is_db_available
    if is_db_available():
        print("Database connection: ACTIVE")
        
        # Set up versioning service collections
        db = get_db()
        versioning_service.set_collections(
            versions_coll=db.page_versions,
            pages_coll=db.tracked_pages,
            change_logs_coll=db.change_logs
        )
        print("✅ Versioning service initialized with database collections")
    else:
        print("Database connection: FAILED")
    
    # Start monitoring scheduler
    try:
        print("\nStarting monitoring scheduler...")
        if asyncio.iscoroutinefunction(monitoring_scheduler.start):
            await monitoring_scheduler.start()
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, monitoring_scheduler.start)
        print("Monitoring scheduler started successfully")
        
        if hasattr(monitoring_scheduler, 'email_enabled'):
            if monitoring_scheduler.email_enabled:
                print("Scheduler email notifications: ENABLED")
            else:
                print("Scheduler email notifications: DISABLED")
    except Exception as e:
        logger.error(f"Error starting monitoring scheduler: {e}")
        raise

    print("\n" + "=" * 60)
    print("FreshLense API is ready!")
    print("=" * 60)
    
    try:
        yield
    finally:
        # SHUTDOWN
        print("\n" + "=" * 60)
        print("Shutting down FreshLense API...")
        print("=" * 60)
        try:
            if asyncio.iscoroutinefunction(monitoring_scheduler.shutdown):
                await monitoring_scheduler.shutdown()
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, monitoring_scheduler.shutdown)
            print("Monitoring scheduler stopped")
        except Exception as e:
            logger.error(f"Error during monitoring_scheduler.shutdown(): {e}")
        print("=" * 60)

# -------------------- Create FastAPI app --------------------
app = FastAPI(
    title="FreshLense API",
    description="API for web content monitoring platform with AI-powered summaries",
    version="1.1.0",  # Updated version
    lifespan=lifespan
)

# ================================================
# CORS middleware with explicit OPTIONS handling
# ================================================

# Get allowed origins from environment variable
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
origins = [origin.strip() for origin in allowed_origins_str.split(",")]

# Always include chrome-extension for extension support
if "chrome-extension://*" not in origins:
    origins.append("chrome-extension://*")

# Log the CORS configuration
print(f"🔧 CORS configured with origins: {origins}")
logger.info(f"CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return None

# -------------------- Include Routers --------------------
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(analytics.router)
app.include_router(fact_check.router, dependencies=[Depends(get_current_user)])

# -------------------- Tracked Pages Routes --------------------
@app.get("/api/pages", response_model=List[TrackedPageResponse])
async def get_my_pages(current_user = Depends(get_current_user)):
    """Get all tracked pages for the current user"""
    user_id = get_user_id_from_current_user(current_user)
    user_email = get_user_email_from_current_user(current_user)
    
    logger.debug(f"Fetching pages for user: {user_email}")
    pages_list = get_tracked_pages(user_id)
    
    # Add version count to each page
    db = get_db()
    for page in pages_list:
        page['version_count'] = db.page_versions.count_documents(
            {"page_id": ObjectId(page['_id'])}
        )
    
    logger.debug(f"Found {len(pages_list)} pages for {user_email}")
    return [normalize_doc(p) for p in pages_list]

@app.post("/api/pages", response_model=TrackedPageResponse)
async def create_page(
    page: TrackedPageCreate, 
    request: Request,
    current_user = Depends(get_current_user)
):
    user_id = get_user_id_from_current_user(current_user)
    
    # Check if request is from Chrome extension
    is_extension = request.headers.get("x-request-source") == "chrome-extension"
    
    # Generate sequential name for extension requests without display name
    if is_extension and (not page.display_name or page.display_name.strip() == ""):
        display_name = generate_sequential_name(user_id)
    else:
        display_name = page.display_name or page.url
    
    page_data = {
        "url": page.url, 
        "display_name": display_name,
        "check_interval_minutes": page.check_interval_minutes
    }
    
    new_page = create_tracked_page(page_data, user_id)
    
    # Schedule page
    try:
        if asyncio.iscoroutinefunction(monitoring_scheduler.schedule_page):
            await monitoring_scheduler.schedule_page(new_page)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, monitoring_scheduler.schedule_page, new_page)
    except Exception as e:
        logger.error(f"Failed to schedule page immediately after creation: {e}")

    return normalize_doc(new_page)

@app.delete("/api/pages/{page_id}")
async def delete_page(page_id: str, current_user = Depends(get_current_user)):
    """Delete a tracked page"""
    user_id = get_user_id_from_current_user(current_user)
    
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")
    
    page = get_tracked_page(page_id)
    if not page or str(page["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Delete all versions first
    db = get_db()
    db.page_versions.delete_many({"page_id": ObjectId(page_id)})
    
    # Then delete the page
    success = delete_tracked_page(page_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete page")
    
    return {"status": "success", "message": "Page and all versions deleted successfully"}

@app.get("/api/pages/by-url", response_model=TrackedPageResponse)
async def get_page_by_url(
    url: str = Query(..., description="URL to check"),
    current_user = Depends(get_current_user)
):
    """Check if a page is already tracked by its URL"""
    user_id = get_user_id_from_current_user(current_user)
    page = get_tracked_page_by_url(url, user_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found for this user at this URL"
        )
    return normalize_doc(page)

@app.get("/api/pages/{page_id}", response_model=TrackedPageResponse)
async def get_page(page_id: str, current_user = Depends(get_current_user)):
    user_id = get_user_id_from_current_user(current_user)
    
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")
    page = get_tracked_page(page_id)
    if not page or str(page["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Add version count
    db = get_db()
    page['version_count'] = db.page_versions.count_documents(
        {"page_id": ObjectId(page_id)}
    )
    
    return normalize_doc(page)

# Note: The versions endpoint is now handled by the pages router
# This endpoint is kept for backward compatibility
@app.get("/api/pages/{page_id}/versions", response_model=List[PageVersionResponse])
async def get_versions(page_id: str, current_user = Depends(get_current_user)):
    user_id = get_user_id_from_current_user(current_user)
    
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")
    page = get_tracked_page(page_id)
    if not page or str(page["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Page not found")
    versions = get_page_versions(page_id)
    
    # Add AI summary info
    for v in versions:
        v['has_ai_summary'] = 'ai_summary' in v
    
    return [normalize_doc(v) for v in versions]

# -------------------- Change Logs Routes --------------------
@app.get("/api/changes", response_model=List[ChangeLogResponse])
async def get_my_changes(current_user = Depends(get_current_user)):
    user_id = get_user_id_from_current_user(current_user)
    changes = get_change_logs_for_user(user_id)
    return [normalize_doc(c) for c in changes]

# -------------------- Crawl Routes with AI Integration --------------------
@app.post("/api/crawl/{page_id}")
async def crawl_page_by_id(
    page_id: str, 
    generate_ai_summary: bool = Query(True, description="Generate AI summary for significant changes"),
    current_user = Depends(get_current_user)
):
    """Trigger a manual crawl for a tracked page by its ID and store results with AI summary"""
    user_id = get_user_id_from_current_user(current_user)
    
    try:
        ObjectId(page_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid page ID")

    page = get_tracked_page(page_id)
    if not page or str(page["user_id"]) != user_id:
        raise HTTPException(status_code=404, detail="Page not found")

    try:
        html_content, text_content = crawler.fetch_and_extract(page["url"])
        if not html_content:
            raise HTTPException(status_code=400, detail="Failed to fetch content from URL")

        # Use versioning service with AI
        version_id = await versioning_service.save_version_if_significant(
            page_id=page_id,
            new_content=text_content,
            html_content=html_content,
            url=page["url"],
            user_id=user_id,
            generate_ai_summary=generate_ai_summary
        )

        if not version_id:
            return {
                "status": "no_changes",
                "page_id": page_id,
                "url": page["url"],
                "message": "No significant changes detected"
            }

        return {
            "status": "success",
            "page_id": page_id,
            "url": page["url"],
            "version_id": version_id,
            "change_detected": True,
            "ai_summary_generated": generate_ai_summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- AI Status Endpoint --------------------
@app.get("/api/ai/status")
async def get_ai_status(current_user = Depends(get_current_user)):
    """Get AI service status and configuration"""
    return {
        "enabled": ai_service.enabled,
        "model": os.getenv("OPENAI_MODEL", "gpt-5-nano"),
        "summaries_enabled": os.getenv("AI_SUMMARIES_ENABLED", "true").lower() == "true",
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

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
            "subject": "FreshLense Email Test",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>FreshLense Email System Test</h2>
                <p>If you receive this email, your FreshLense email system is working correctly!</p>
                <div style="background: #f0f9ff; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p><strong>System Status:</strong> Operational</p>
                    <p><strong>Test Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
                </div>
                <p>You will now receive:</p>
                <ul>
                    <li>Direct fact-check results</li>
                    <li>Page change notifications</li>
                    <li>AI-powered change summaries</li>
                </ul>
            </body>
            </html>
            """,
            "text": f"""FreshLense Email Test

If you receive this email, your FreshLense email system is working correctly!

System Status: Operational
Test Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

You will now receive:
- Direct fact-check results
- Page change notifications
- AI-powered change summaries

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
        "ai_enabled": ai_service.enabled,
        "version": "1.1.0"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FreshLense API is running!",
        "version": "1.1.0",
        "features": {
            "email_notifications": getattr(monitoring_scheduler, 'email_enabled', False),
            "scheduler_active": monitoring_scheduler.is_running,
            "ai_summaries": ai_service.enabled
        },
        "endpoints": {
            "documentation": "/docs",
            "health": "/api/health",
            "ai_status": "/api/ai/status",
            "email_config": "/api/debug/email-config",
            "test_email": "POST /api/test/email"
        }
    }