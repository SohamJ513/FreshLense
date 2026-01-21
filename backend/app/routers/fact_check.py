from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..database import (
    versions_collection, 
    pages_collection, 
    get_page_versions,
    get_tracked_page,
    doc_to_dict
)
from ..services.fact_check_service import FactCheckService
from ..services.diff_service import DiffService
from ..schemas.fact_check import FactCheckRequest, FactCheckResponse, FactCheckItem, ClaimType, Verdict
from ..schemas.diff import DiffRequest, DiffResponse, ContentChange
import resend  # ✅ ADD THIS IMPORT
import os  # ✅ ADD THIS IMPORT

router = APIRouter(prefix="/api/fact-check", tags=["fact-check"])

# 🚨 CRITICAL FIX: Create service instance inside functions to avoid caching issues
# Don't create at module level - create fresh instances when needed

diff_service = DiffService()

# ✅ ADD THIS FUNCTION
def send_fact_check_email(to_email: str, page_title: str, page_url: str, results_summary: dict):
    """Send fact-check results email via Resend"""
    try:
        # Configure Resend
        resend.api_key = os.getenv("RESEND_API_KEY")
        if not resend.api_key:
            print("⚠️ RESEND_API_KEY not found in environment")
            return False
        
        # Get your from email from environment
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        
        # Calculate credibility score
        total = results_summary.get("total_claims", 0)
        verified = results_summary.get("verified_claims", 0)
        credibility_score = int((verified / total * 100)) if total > 0 else 0
        
        # Prepare email
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

@router.post("/check", response_model=FactCheckResponse)
async def fact_check_page(request: FactCheckRequest, current_user: dict = Depends(lambda: None)):
    """Perform fact checking on a page version"""
    try:
        # 🚨 CRITICAL FIX: Create fresh FactCheckService instance
        fact_check_service = FactCheckService()
        print("🔄 DEBUG: Created fresh FactCheckService instance")
        
        # Get the specific page version
        version = versions_collection.find_one({"_id": ObjectId(request.version_id)})
        if not version:
            raise HTTPException(status_code=404, detail="Page version not found")
        
        # Get page info and verify ownership
        page = get_tracked_page(str(version["page_id"]))
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        # Perform fact checking on text content
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
        
        # ✅ OPTIONAL: Add email sending for regular fact-check too
        # You can enable this later if you want
        
        return response
        
    except Exception as e:
        print(f"💥 Fact checking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fact checking failed: {str(e)}")

@router.post("/check-direct", response_model=FactCheckResponse)
async def fact_check_direct_content(request: dict, current_user: dict = Depends(lambda: None)):
    """Perform fact checking on directly provided text content"""
    try:
        # 🚨 CRITICAL FIX: Create fresh FactCheckService instance
        fact_check_service = FactCheckService()
        print("🔄 DEBUG: Created fresh FactCheckService instance for direct check")
        
        text_content = request.get("content", "")
        page_url = request.get("page_url", "Direct input")
        page_title = request.get("page_title", "User provided content")
        user_email = request.get("user_email")  # ✅ Get email from request
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Limit content length to prevent abuse
        if len(text_content) > 15000:
            text_content = text_content[:15000] + "... [content truncated]"
        
        print(f"🔍 DEBUG: Starting direct fact check on {len(text_content)} chars of content")
        # Perform fact checking on direct text content
        fact_check_results = await fact_check_service.check_content(text_content)
        
        # Prepare response
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
        
        # ✅ SEND EMAIL IF USER PROVIDED EMAIL
        if user_email and os.getenv("EMAIL_ENABLED", "true").lower() == "true":
            try:
                # Prepare results summary
                results_summary = {
                    "total_claims": len(fact_check_results),
                    "verified_claims": len([r for r in fact_check_results if r.verdict == Verdict.TRUE]),
                    "unverified_claims": len([r for r in fact_check_results if r.verdict == Verdict.FALSE]),
                    "inconclusive_claims": len([r for r in fact_check_results if r.verdict == Verdict.UNVERIFIED])
                }
                
                # Send email
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
                # Don't fail the request if email fails
        
        return response
        
    except Exception as e:
        print(f"💥 Direct fact checking failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Direct fact checking failed: {str(e)}")

@router.post("/compare", response_model=DiffResponse)
async def compare_versions(request: DiffRequest, current_user: dict = Depends(lambda: None)):
    """Compare two page versions and show differences"""
    try:
        # Get both versions
        old_version = versions_collection.find_one({"_id": ObjectId(request.old_version_id)})
        new_version = versions_collection.find_one({"_id": ObjectId(request.new_version_id)})
        
        if not old_version or not new_version:
            raise HTTPException(status_code=404, detail="One or both versions not found")
        
        if str(old_version["page_id"]) != str(new_version["page_id"]):
            raise HTTPException(status_code=400, detail="Versions must be from the same page")
        
        # Perform diff comparison
        old_text = old_version.get("text_content", "")
        new_text = new_version.get("text_content", "")
        
        diff_result = diff_service.compare_text(old_text, new_text)
        
        return DiffResponse(
            page_id=str(old_version["page_id"]),
            old_version_id=request.old_version_id,
            new_version_id=request.new_version_id,
            old_timestamp=old_version["timestamp"],
            new_timestamp=new_version["timestamp"],
            changes=diff_result,
            total_changes=len(diff_result)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.get("/page/{page_id}/versions")
async def get_page_versions_for_factcheck(page_id: str, limit: int = 20, current_user: dict = Depends(lambda: None)):
    """Get page versions with basic info for fact check UI"""
    try:
        versions = get_page_versions(page_id, limit)
        page = get_tracked_page(page_id)
        
        version_list = []
        for version in versions:
            version_list.append({
                "version_id": str(version["_id"]),
                "timestamp": version["timestamp"],
                "content_preview": version.get("text_content", "")[:200] + "..." if len(version.get("text_content", "")) > 200 else version.get("text_content", ""),
                "word_count": version.get("metadata", {}).get("word_count", 0),
                "content_length": version.get("metadata", {}).get("content_length", 0)
            })
        
        return {
            "page_info": {
                "page_id": page_id,
                "url": page.get("url", "") if page else "",
                "display_name": page.get("display_name", "") if page else ""
            },
            "versions": version_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")

@router.get("/debug-serb")
async def debug_serp_integration():
    """Debug SERP API integration"""
    try:
        # 🚨 CRITICAL FIX: Create fresh FactCheckService instance
        fact_check_service = FactCheckService()
        print("🔄 DEBUG: Created fresh FactCheckService instance for debug")
        
        # Check configuration
        config_status = fact_check_service.check_serp_status()
        
        # Test a claim that should trigger SERP API
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