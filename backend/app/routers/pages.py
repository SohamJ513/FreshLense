# backend/app/routers/pages.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

from ..models import TrackedPageUpdate
from ..schemas.diff import PageUpdate  # For backward compatibility
from ..services.page_service import page_service
from ..services.versioning_service import VersioningService
from ..utils.security import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/pages", tags=["pages"])

# Initialize versioning service
versioning_service = VersioningService()

# Helper function to extract user ID
def extract_user_id(current_user) -> str:
    """Extract user ID from current_user (handles both dict and User object)"""
    # Case 1: If current_user is a dictionary (from MongoDB)
    if isinstance(current_user, dict):
        if '_id' in current_user:
            return str(current_user['_id'])
        elif 'id' in current_user:
            return str(current_user['id'])
    
    # Case 2: If current_user is a User model object
    elif hasattr(current_user, 'id') and current_user.id is not None:
        return str(current_user.id)
    elif hasattr(current_user, '_id') and current_user._id is not None:
        return str(current_user._id)
    
    # Case 3: If nothing worked
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Could not extract user ID from current_user. Type: {type(current_user)}"
    )

@router.put("/{page_id}")
async def update_page_details(
    page_id: str,
    page_update: PageUpdate,  # Using your existing PageUpdate schema
    current_user = Depends(get_current_user)
):
    """
    Update page name and check interval
    
    Parameters:
    - page_id: The ID of the page to update
    - page_update: Object containing display_name and/or check_interval_hours
    - current_user: Automatically injected from JWT token
    
    Returns:
    - Updated page object
    """
    # Validate page_id format
    if not ObjectId.is_valid(page_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid page ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Convert PageUpdate to TrackedPageUpdate
    tracked_page_update = TrackedPageUpdate(
        display_name=page_update.display_name,
        check_interval_hours=page_update.check_interval_hours
    )
    
    # Update the page
    updated_page = page_service.update_page(
        page_id=page_id,
        page_update=tracked_page_update,
        user_id=user_id
    )
    
    if not updated_page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found or you don't have permission to update it"
        )
    
    return updated_page

@router.get("/")
async def get_user_pages(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    Get all pages for the current user
    
    Returns:
    - List of page objects
    """
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    pages = page_service.get_user_pages(
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    
    return pages

@router.get("/{page_id}")
async def get_page(
    page_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get a single page by ID
    
    Returns:
    - Page object
    """
    # Validate page_id format
    if not ObjectId.is_valid(page_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid page ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Get the page
    page = page_service.get_page(page_id, user_id)
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    return page

@router.delete("/{page_id}")
async def delete_page(
    page_id: str,
    current_user = Depends(get_current_user)
):
    """
    Delete a page by ID
    
    Returns:
    - Success message
    """
    # Validate page_id format
    if not ObjectId.is_valid(page_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid page ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Delete the page
    success = page_service.delete_page(page_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found or you don't have permission to delete it"
        )
    
    return {"success": True, "message": "Page deleted successfully"}

# ================================================
# VERSION MANAGEMENT ENDPOINTS
# ================================================

@router.get("/{page_id}/versions")
async def get_page_versions(
    page_id: str,
    limit: int = Query(50, ge=1, le=100),
    include_summary: bool = Query(False, description="Include AI summary in response"),
    current_user = Depends(get_current_user)
):
    """
    Get all versions for a page
    
    Parameters:
    - page_id: The ID of the page
    - limit: Maximum number of versions to return
    - include_summary: Whether to include AI summary in response
    
    Returns:
    - List of version objects
    """
    # Validate page_id format
    if not ObjectId.is_valid(page_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid page ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Verify page ownership
    page = page_service.get_page(page_id, user_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get database connection
    db = get_db()
    
    # Get versions
    versions = list(db.page_versions.find(
        {"page_id": ObjectId(page_id)}
    ).sort("timestamp", -1).limit(limit))
    
    # Format response
    result = []
    for v in versions:
        version_data = {
            "id": str(v["_id"]),
            "page_id": str(v["page_id"]),
            "timestamp": v["timestamp"].isoformat(),
            "text_content": v["text_content"][:500] + "..." if len(v["text_content"]) > 500 else v["text_content"],
            "change_significance_score": v.get("change_significance_score", 0),
            "has_ai_summary": "ai_summary" in v,
            "metadata": v.get("metadata", {})
        }
        
        # Include full AI summary if requested
        if include_summary and v.get("ai_summary"):
            version_data["ai_summary"] = v["ai_summary"]
        
        result.append(version_data)
    
    return {
        "success": True,
        "data": result,
        "total": len(result)
    }

@router.get("/{page_id}/versions/{version_id}")
async def get_version(
    page_id: str,
    version_id: str,
    include_summary: bool = Query(True, description="Include AI summary in response"),
    current_user = Depends(get_current_user)
):
    """
    Get a specific version by ID
    
    Returns:
    - Version object with full content and AI summary
    """
    # Validate IDs
    if not ObjectId.is_valid(page_id) or not ObjectId.is_valid(version_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Verify page ownership
    page = page_service.get_page(page_id, user_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get database connection
    db = get_db()
    
    # Get the version
    version = db.page_versions.find_one({
        "_id": ObjectId(version_id),
        "page_id": ObjectId(page_id)
    })
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Format response
    result = {
        "id": str(version["_id"]),
        "page_id": str(version["page_id"]),
        "timestamp": version["timestamp"].isoformat(),
        "text_content": version["text_content"],
        "html_content": version.get("html_content"),
        "change_significance_score": version.get("change_significance_score", 0),
        "change_metrics": version.get("change_metrics", {}),
        "metadata": version.get("metadata", {}),
        "has_ai_summary": "ai_summary" in version
    }
    
    # Include AI summary if available
    if include_summary and version.get("ai_summary"):
        result["ai_summary"] = version["ai_summary"]
    
    return {
        "success": True,
        "data": result
    }

@router.get("/{page_id}/versions/{version_id}/summary")
async def get_version_summary(
    page_id: str,
    version_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get AI summary for a specific version
    
    Returns:
    - AI summary object
    """
    # Validate IDs
    if not ObjectId.is_valid(page_id) or not ObjectId.is_valid(version_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Verify page ownership
    page = page_service.get_page(page_id, user_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get database connection
    db = get_db()
    
    # Get the version
    version = db.page_versions.find_one({
        "_id": ObjectId(version_id),
        "page_id": ObjectId(page_id)
    })
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Check if AI summary exists
    if "ai_summary" not in version:
        return {
            "success": True,
            "data": {
                "has_summary": False,
                "message": "No AI summary available for this version"
            }
        }
    
    return {
        "success": True,
        "data": {
            "has_summary": True,
            "summary": version["ai_summary"],
            "generated_at": version["ai_summary"].get("generated_at"),
            "model_used": version["ai_summary"].get("model_used")
        }
    }

@router.post("/{page_id}/versions/{version_id}/regenerate-summary")
async def regenerate_version_summary(
    page_id: str,
    version_id: str,
    current_user = Depends(get_current_user)
):
    """
    Regenerate AI summary for a version
    
    Returns:
    - New AI summary
    """
    # Validate IDs
    if not ObjectId.is_valid(page_id) or not ObjectId.is_valid(version_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Verify page ownership
    page = page_service.get_page(page_id, user_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get database connection
    db = get_db()
    
    # Get the version
    version = db.page_versions.find_one({
        "_id": ObjectId(version_id),
        "page_id": ObjectId(page_id)
    })
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    # Get previous version for comparison
    prev_version = db.page_versions.find_one({
        "page_id": ObjectId(page_id),
        "timestamp": {"$lt": version["timestamp"]}
    }).sort("timestamp", -1)
    
    if not prev_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate summary for first version"
        )
    
    # Import AI service
    from ..services.ai_service import ai_service
    
    # Generate new summary
    try:
        ai_summary = await ai_service.generate_change_summary(
            old_content=prev_version.get("text_content", ""),
            new_content=version.get("text_content", ""),
            page_title=page.get("display_name") or page.get("url", ""),
            url=page.get("url", "")
        )
        
        # Update version with new summary
        db.page_versions.update_one(
            {"_id": ObjectId(version_id)},
            {"$set": {"ai_summary": ai_summary}}
        )
        
        return {
            "success": True,
            "data": {
                "summary": ai_summary,
                "message": "Summary regenerated successfully"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

@router.get("/{page_id}/versions/compare/{version1_id}/{version2_id}")
async def compare_versions(
    page_id: str,
    version1_id: str,
    version2_id: str,
    current_user = Depends(get_current_user)
):
    """
    Compare two versions and get AI summary of differences
    
    Returns:
    - Comparison result with AI summary
    """
    # Validate IDs
    if not ObjectId.is_valid(page_id) or not ObjectId.is_valid(version1_id) or not ObjectId.is_valid(version2_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid ID format"
        )
    
    # Extract user ID
    user_id = extract_user_id(current_user)
    
    # Verify page ownership
    page = page_service.get_page(page_id, user_id)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    # Get database connection
    db = get_db()
    
    # Get both versions
    version1 = db.page_versions.find_one({
        "_id": ObjectId(version1_id),
        "page_id": ObjectId(page_id)
    })
    
    version2 = db.page_versions.find_one({
        "_id": ObjectId(version2_id),
        "page_id": ObjectId(page_id)
    })
    
    if not version1 or not version2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found"
        )
    
    # Import diff service
    from ..services.diff_service import DiffService
    diff_service = DiffService()
    
    # Calculate diff
    diff_result = diff_service.calculate_diff(
        version1.get("text_content", ""),
        version2.get("text_content", "")
    )
    
    # Import AI service
    from ..services.ai_service import ai_service
    
    # Generate comparison summary
    try:
        ai_summary = await ai_service.generate_change_summary(
            old_content=version1.get("text_content", ""),
            new_content=version2.get("text_content", ""),
            page_title=page.get("display_name") or page.get("url", ""),
            url=page.get("url", "")
        )
    except Exception as e:
        ai_summary = {"error": str(e), "summary": "Could not generate AI summary"}
    
    return {
        "success": True,
        "data": {
            "version1": {
                "id": str(version1["_id"]),
                "timestamp": version1["timestamp"].isoformat()
            },
            "version2": {
                "id": str(version2["_id"]),
                "timestamp": version2["timestamp"].isoformat()
            },
            "diff": diff_result,
            "ai_summary": ai_summary,
            "change_significance": abs(
                version1.get("change_significance_score", 0) - 
                version2.get("change_significance_score", 0)
            )
        }
    }