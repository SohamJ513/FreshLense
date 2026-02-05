from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from bson import ObjectId
from bson.errors import InvalidId

from ..models import TrackedPageUpdate
from ..schemas.diff import PageUpdate  # For backward compatibility
from ..services.page_service import page_service
# Remove this import - it's causing the type mismatch
# from ..schemas.auth import User
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/pages", tags=["pages"])

@router.put("/{page_id}")
async def update_page_details(
    page_id: str,
    page_update: PageUpdate,  # Using your existing PageUpdate schema
    current_user = Depends(get_current_user)  # Remove type hint for now
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
    
    # DEBUG: Check what current_user actually is
    print(f"DEBUG - current_user type: {type(current_user)}")
    print(f"DEBUG - current_user attributes: {dir(current_user) if hasattr(current_user, '__dict__') else 'dict-like'}")
    
    # Extract user ID safely - handles both dict and User object
    user_id = None
    
    # Case 1: If current_user is a dictionary (from MongoDB)
    if isinstance(current_user, dict):
        if '_id' in current_user:
            user_id = str(current_user['_id'])
            print(f"DEBUG - Got user_id from dict['_id']: {user_id}")
        elif 'id' in current_user:
            user_id = str(current_user['id'])
            print(f"DEBUG - Got user_id from dict['id']: {user_id}")
    
    # Case 2: If current_user is a User model object
    elif hasattr(current_user, 'id') and current_user.id is not None:
        user_id = str(current_user.id)
        print(f"DEBUG - Got user_id from model.id: {user_id}")
    elif hasattr(current_user, '_id') and current_user._id is not None:
        user_id = str(current_user._id)
        print(f"DEBUG - Got user_id from model._id: {user_id}")
    
    # Case 3: If nothing worked
    if not user_id:
        print(f"DEBUG - current_user content: {current_user}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract user ID from current_user. Type: {type(current_user)}"
        )
    
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
    current_user = Depends(get_current_user)  # Remove type hint
):
    """
    Get all pages for the current user
    
    Returns:
    - List of page objects
    """
    # Extract user ID safely - handles both dict and User object
    user_id = None
    
    # Case 1: If current_user is a dictionary (from MongoDB)
    if isinstance(current_user, dict):
        if '_id' in current_user:
            user_id = str(current_user['_id'])
        elif 'id' in current_user:
            user_id = str(current_user['id'])
    
    # Case 2: If current_user is a User model object
    elif hasattr(current_user, 'id') and current_user.id is not None:
        user_id = str(current_user.id)
    elif hasattr(current_user, '_id') and current_user._id is not None:
        user_id = str(current_user._id)
    
    # Case 3: If nothing worked
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract user ID from current_user. Type: {type(current_user)}"
        )
    
    pages = page_service.get_user_pages(
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    
    return pages