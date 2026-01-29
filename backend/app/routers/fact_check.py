from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from ..database import (
    versions_collection, 
    pages_collection, 
    get_page_versions,
    get_tracked_page,
    get_tracked_pages,
    doc_to_dict
)
from ..services.fact_check_service import FactCheckService
from ..services.diff_service import DiffService
from ..schemas.fact_check import FactCheckRequest, FactCheckResponse, FactCheckItem, ClaimType, Verdict
from ..schemas.diff import DiffRequest, DiffResponse, ContentChange, VersionInfo
import resend
import os

router = APIRouter(prefix="/api/fact-check", tags=["fact-check"])

# Service instance for diff operations
diff_service = DiffService()

# ✅ EMAIL FUNCTION (keep existing)
def send_fact_check_email(to_email: str, page_title: str, page_url: str, results_summary: dict):
    """Send fact-check results email via Resend"""
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        if not resend.api_key:
            print("⚠️ RESEND_API_KEY not found in environment")
            return False
        
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        
        total = results_summary.get("total_claims", 0)
        verified = results_summary.get("verified_claims", 0)
        credibility_score = int((verified / total * 100)) if total > 0 else 0
        
        params = {
            "from": f"FreshLense <{from_email}>",
            "to": [to_email],
            "subject": f"📋 FreshLense Fact-Check Results: {page_title[:50]}{'...' if len(page_title) > 50 else ''}",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; color: white; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">📋 Fact-Check Results</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Your content analysis is ready</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 25px; border-radius: 0 0 10px 10px;">
                    <!-- Content Info -->
                    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #333;">{page_title}</h3>
                        <p style="color: #666; margin-bottom: 5px;"><strong>URL:</strong> {page_url}</p>
                        <p style="color: #666; margin: 0;"><strong>Analyzed:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>
                    </div>
                    
                    <!-- Credibility Score -->
                    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;">
                        <h3 style="margin-top: 0; color: #333;">Credibility Score</h3>
                        <div style="font-size: 48px; font-weight: bold; color: {"#51cf66" if credibility_score >= 80 else "#ff922b" if credibility_score >= 60 else "#ff6b6b"};">
                            {credibility_score}%
                        </div>
                        <p style="color: #666; margin-top: 10px;">
                            Based on {total} claims analyzed
                        </p>
                    </div>
                    
                    <!-- Results Breakdown -->
                    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #333;">Results Breakdown</h3>
                        
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-top: 15px;">
                            <!-- Verified -->
                            <div style="text-align: center; padding: 15px; background: #f0f9ff; border-radius: 8px;">
                                <div style="font-size: 24px; font-weight: bold; color: #51cf66;">
                                    {results_summary.get('verified_claims', 0)}
                                </div>
                                <div style="color: #666; font-size: 14px;">Verified Claims</div>
                            </div>
                            
                            <!-- Unverified -->
                            <div style="text-align: center; padding: 15px; background: #fff7ed; border-radius: 8px;">
                                <div style="font-size: 24px; font-weight: bold; color: #ff922b;">
                                    {results_summary.get('unverified_claims', 0)}
                                </div>
                                <div style="color: #666; font-size: 14px;">Unverified Claims</div>
                            </div>
                            
                            <!-- False -->
                            <div style="text-align: center; padding: 15px; background: #fef2f2; border-radius: 8px;">
                                <div style="font-size: 24px; font-weight: bold; color: #ff6b6b;">
                                    {results_summary.get('inconclusive_claims', 0)}
                                </div>
                                <div style="color: #666; font-size: 14px;">False Claims</div>
                            </div>
                            
                            <!-- Total -->
                            <div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
                                <div style="font-size: 24px; font-weight: bold; color: #667eea;">
                                    {total}
                                </div>
                                <div style="color: #666; font-size: 14px;">Total Claims</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Action Button -->
                    <div style="text-align: center; margin-top: 25px;">
                        <a href="{page_url}" 
                           style="display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;"
                           target="_blank">
                            View Original Content
                        </a>
                    </div>
                    
                    <!-- Footer -->
                    <div style="margin-top: 25px; padding-top: 20px; border-top: 1px solid #e9ecef; text-align: center;">
                        <p style="color: #666; font-size: 12px; margin: 0;">
                            This is an automated email from FreshLense Web Content Monitoring System.<br>
                            <a href="#" style="color: #667eea; text-decoration: none;">Unsubscribe from these emails</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "text": f"""FreshLense Fact-Check Results

Content: {page_title}
URL: {page_url}
Analyzed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

Results Summary:
✅ Verified Claims: {results_summary.get('verified_claims', 0)}
❓ Unverified Claims: {results_summary.get('unverified_claims', 0)}
❌ False Claims: {results_summary.get('inconclusive_claims', 0)}
📊 Total Claims: {total}
🎯 Credibility Score: {credibility_score}%

View original content: {page_url}

This is an automated message from FreshLense Web Content Monitoring System."""
        }
        
        email = resend.Emails.send(params)
        print(f"✅ Fact-check email sent to {to_email}, ID: {email['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

# ✅ NEW ENDPOINT: Get all tracked pages for the user
@router.get("/pages", response_model=List[Dict[str, Any]])
async def get_user_pages(current_user: dict = Depends(lambda: None)):
    """Get all tracked pages for the user"""
    try:
        # In a real app, you would filter by current_user.id
        # For now, return all pages (or implement authentication later)
        pages = get_tracked_pages(None)  # Pass None for now, or user_id when auth is implemented
        
        page_list = []
        for page in pages:
            # Get version count for each page
            version_count = versions_collection.count_documents({"page_id": page["_id"]})
            
            page_list.append({
                "id": str(page["_id"]),
                "url": page["url"],
                "title": page.get("display_name", page["url"]),
                "last_checked": page.get("last_checked"),
                "version_count": version_count,
                "is_active": page.get("is_active", True)
            })
        
        return page_list
        
    except Exception as e:
        print(f"💥 Error fetching pages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pages: {str(e)}")

# ✅ UPDATED ENDPOINT: Get all versions for a specific page WITH PAGE INFO
@router.get("/pages/{page_id}/versions", response_model=Dict[str, Any])
async def get_page_versions_endpoint(page_id: str, current_user: dict = Depends(lambda: None)):
    """Get all versions for a specific page WITH PAGE INFO"""
    try:
        # Verify page exists
        page = get_tracked_page(page_id)
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        # Get versions for this page using database function
        versions = get_page_versions(page_id, limit=100)
        
        # Convert to proper format
        version_list = []
        for i, version in enumerate(versions):
            content = version.get("text_content", "")
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            version_list.append({
                "id": str(version["_id"]),
                "page_id": str(version["page_id"]),
                "version_number": i + 1,
                "captured_at": version["timestamp"],
                "content_preview": content_preview,
                "title": f"Version {i+1} - {version['timestamp'].strftime('%Y-%m-%d %H:%M')}",
                "has_content": bool(content.strip())
            })
        
        # Reverse to show newest first (most recent at top)
        version_list.reverse()
        
        # Re-number after reversing
        for i, version in enumerate(version_list):
            version["version_number"] = i + 1
        
        # ✅ FIXED: Return page info AND versions in the structure frontend expects
        return {
            "page_info": {
                "page_id": str(page["_id"]),
                "url": page.get("url", ""),  # <-- This is what you need!
                "display_name": page.get("display_name", page.get("url", "Untitled Page")),
                "last_checked": page.get("last_checked"),
                "version_count": len(version_list)
            },
            "versions": version_list
        }
        
    except Exception as e:
        print(f"💥 Error fetching versions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch versions: {str(e)}")

# ✅ NEW ENDPOINT: Get specific version by ID
@router.get("/versions/{version_id}")
async def get_version_by_id(version_id: str, current_user: dict = Depends(lambda: None)):
    """Get a specific page version by ID"""
    try:
        version = versions_collection.find_one({"_id": ObjectId(version_id)})
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Get page info
        page = get_tracked_page(str(version["page_id"]))
        
        return {
            "id": str(version["_id"]),
            "page_id": str(version["page_id"]),
            "timestamp": version["timestamp"],
            "text_content": version.get("text_content", ""),
            "html_content": version.get("html_content", ""),
            "page_title": page.get("display_name", "Unknown") if page else "Unknown",
            "page_url": page.get("url", "") if page else ""
        }
        
    except Exception as e:
        print(f"💥 Error fetching version: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch version: {str(e)}")

# ✅ EXISTING ENDPOINTS (keep these as they are)
@router.post("/check", response_model=FactCheckResponse)
async def fact_check_page(request: FactCheckRequest, current_user: dict = Depends(lambda: None)):
    """Perform fact checking on a page version"""
    try:
        fact_check_service = FactCheckService()
        print("🔄 DEBUG: Created fresh FactCheckService instance")
        
        version = versions_collection.find_one({"_id": ObjectId(request.version_id)})
        if not version:
            raise HTTPException(status_code=404, detail="Page version not found")
        
        page = get_tracked_page(str(version["page_id"]))
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        text_content = version.get("text_content", "")
        print(f"🔍 DEBUG: Starting fact check on {len(text_content)} chars of content")
        fact_check_results = await fact_check_service.check_content(text_content)
        
        response = FactCheckResponse(
            page_id=str(version["page_id"]),
            version_id=request.version_id,
            page_url=page.get("url", ""),
            page_title=page.get("display_name", ""),
            checked_at=datetime.utcnow(),
            results=fact_check_results,
            total_claims=len(fact_check_results),
            verified_claims=len([r for r in fact_check_results if r.verdict == Verdict.TRUE]),
            unverified_claims=len([r for r in fact_check_results if r.verdict == Verdict.FALSE]),
            inconclusive_claims=len([r for r in fact_check_results if r.verdict == Verdict.UNVERIFIED])
        )
        
        return response
        
    except Exception as e:
        print(f"💥 Fact checking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fact checking failed: {str(e)}")

@router.post("/check-direct", response_model=FactCheckResponse)
async def fact_check_direct_content(request: dict, current_user: dict = Depends(lambda: None)):
    """Perform fact checking on directly provided text content"""
    try:
        fact_check_service = FactCheckService()
        print("🔄 DEBUG: Created fresh FactCheckService instance for direct check")
        
        text_content = request.get("content", "")
        page_url = request.get("page_url", "Direct input")
        page_title = request.get("page_title", "User provided content")
        user_email = request.get("user_email")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        if len(text_content) > 15000:
            text_content = text_content[:15000] + "... [content truncated]"
        
        print(f"🔍 DEBUG: Starting direct fact check on {len(text_content)} chars of content")
        fact_check_results = await fact_check_service.check_content(text_content)
        
        response = FactCheckResponse(
            page_id="direct_input",
            version_id="direct_input",
            page_url=page_url,
            page_title=page_title,
            checked_at=datetime.utcnow(),
            results=fact_check_results,
            total_claims=len(fact_check_results),
            verified_claims=len([r for r in fact_check_results if r.verdict == Verdict.TRUE]),
            unverified_claims=len([r for r in fact_check_results if r.verdict == Verdict.FALSE]),
            inconclusive_claims=len([r for r in fact_check_results if r.verdict == Verdict.UNVERIFIED])
        )
        
        # Send email if requested
        if user_email and os.getenv("EMAIL_ENABLED", "true").lower() == "true":
            try:
                results_summary = {
                    "total_claims": len(fact_check_results),
                    "verified_claims": len([r for r in fact_check_results if r.verdict == Verdict.TRUE]),
                    "unverified_claims": len([r for r in fact_check_results if r.verdict == Verdict.FALSE]),
                    "inconclusive_claims": len([r for r in fact_check_results if r.verdict == Verdict.UNVERIFIED])
                }
                
                email_sent = send_fact_check_email(
                    to_email=user_email,
                    page_title=page_title,
                    page_url=page_url,
                    results_summary=results_summary
                )
                
                if email_sent:
                    print(f"📧 Email notification sent to {user_email}")
                else:
                    print(f"⚠️ Email notification failed for {user_email}")
                
            except Exception as email_error:
                print(f"⚠️ Email sending error (but fact-check succeeded): {email_error}")
        
        return response
        
    except Exception as e:
        print(f"💥 Direct fact checking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Direct fact checking failed: {str(e)}")

@router.post("/compare", response_model=DiffResponse)
async def compare_versions(request: DiffRequest, current_user: dict = Depends(lambda: None)):
    """Compare two page versions and show differences WITH ENHANCED HIGHLIGHTING"""
    try:
        old_version = versions_collection.find_one({"_id": ObjectId(request.old_version_id)})
        new_version = versions_collection.find_one({"_id": ObjectId(request.new_version_id)})
        
        if not old_version or not new_version:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        
        if str(old_version["page_id"]) != str(new_version["page_id"]):
            raise HTTPException(status_code=400, detail="Versions must be from the same page")
        
        old_text = old_version.get("text_content", "")
        new_text = new_version.get("text_content", "")
        
        diff_result = diff_service.compare_text(old_text, new_text)
        metrics = diff_service.calculate_change_metrics(old_text, new_text)
        html_diff = diff_service.generate_html_diff(old_text, new_text)
        side_by_side = diff_service.get_side_by_side_diff(old_text, new_text)
        
        page = get_tracked_page(str(old_version["page_id"]))
        
        return DiffResponse(
            page_id=str(old_version["page_id"]),
            old_version_id=request.old_version_id,
            new_version_id=request.new_version_id,
            old_timestamp=old_version["timestamp"],
            new_timestamp=new_version["timestamp"],
            changes=diff_result,
            total_changes=len(diff_result),
            change_metrics=metrics,
            html_diff=html_diff,
            side_by_side_diff=side_by_side,
            has_changes=len(diff_result) > 0
        )
        
    except Exception as e:
        print(f"💥 Comparison failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/debug-serb")
async def debug_serp_integration():
    """Debug SERP API integration"""
    try:
        fact_check_service = FactCheckService()
        print("🔄 DEBUG: Created fresh FactCheckService instance for debug")
        
        config_status = fact_check_service.check_serp_status()
        
        test_claim = {
            "text": "Python 3.6 offers 50% better performance than Python 2.7",
            "type": ClaimType.PERFORMANCE,
            "technical_indicators": {
                "technologies": ["python"],
                "versions": ["3.6", "2.7"],
                "numbers": ["50%"]
            }
        }
        
        result = await fact_check_service.verify_claim_enhanced(test_claim)
        
        return {
            "config_status": config_status,
            "test_claim": test_claim["text"],
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug endpoint failed: {str(e)}")