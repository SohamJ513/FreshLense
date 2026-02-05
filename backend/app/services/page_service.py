from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
from ..models import TrackedPage, TrackedPageUpdate
from ..database import (
    pages_collection, 
    get_tracked_page, 
    update_tracked_page,
    get_tracked_pages,
    delete_tracked_page,
    get_tracked_page_by_url
)

class PageService:
    def get_page_by_id(self, page_id: str, user_id: str) -> Optional[TrackedPage]:
        """Get a page by ID and user ID"""
        try:
            # Convert string IDs to ObjectId
            page_obj_id = ObjectId(page_id)
            user_obj_id = ObjectId(user_id)
            
            # Get the page from database
            page_doc = pages_collection.find_one({
                "_id": page_obj_id,
                "user_id": user_obj_id
            })
            
            if page_doc:
                # Convert MongoDB document to TrackedPage model
                return TrackedPage(**page_doc)
            return None
        except Exception as e:
            print(f"Error getting page by ID: {e}")
            return None
    
    def update_page(self, page_id: str, page_update: TrackedPageUpdate, user_id: str) -> Optional[Dict[str, Any]]:
        """Update page details (display_name and check_interval_hours)"""
        try:
            # Validate user owns the page
            page = self.get_page_by_id(page_id, user_id)
            if not page:
                return None
            
            # Prepare update data
            update_data = {}
            
            # Convert check_interval_hours to check_interval_minutes if provided
            if page_update.display_name is not None:
                update_data["display_name"] = page_update.display_name
            
            if page_update.check_interval_hours is not None:
                update_data["check_interval_minutes"] = page_update.check_interval_hours * 60
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            if not update_data:
                # No changes to update
                return self._convert_page_to_response(page)
            
            # Perform the update
            result = pages_collection.find_one_and_update(
                {
                    "_id": ObjectId(page_id),
                    "user_id": ObjectId(user_id)
                },
                {
                    "$set": update_data
                },
                return_document=True  # Return the updated document
            )
            
            if result:
                # Convert to TrackedPage model and then to response format
                updated_page = TrackedPage(**result)
                return self._convert_page_to_response(updated_page)
            return None
            
        except Exception as e:
            print(f"Error updating page: {e}")
            return None
    
    def get_user_pages(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all pages for a user and convert to frontend format"""
        try:
            # Use your existing database function
            page_docs = get_tracked_pages(ObjectId(user_id), active_only=False)
            
            pages = []
            for page_doc in page_docs:
                try:
                    page_model = TrackedPage(**page_doc)
                    pages.append(self._convert_page_to_response(page_model))
                except Exception as e:
                    print(f"Error converting page document: {e}")
                    continue
            
            return pages
        except Exception as e:
            print(f"Error getting user pages: {e}")
            return []
    
    def delete_page(self, page_id: str, user_id: str) -> bool:
        """Delete a page"""
        try:
            # First verify the page belongs to the user
            page = self.get_page_by_id(page_id, user_id)
            if not page:
                return False
            
            # Use your existing delete function
            return delete_tracked_page(page_id)
        except Exception as e:
            print(f"Error deleting page: {e}")
            return False
    
    def _convert_page_to_response(self, page: TrackedPage) -> Dict[str, Any]:
        """Convert TrackedPage model to frontend response format"""
        return {
            "id": str(page.id) if page.id else None,
            "url": page.url,
            "display_name": page.display_name or page.url,
            "check_interval_hours": page.check_interval_minutes // 60 if page.check_interval_minutes else 24,
            "status": "active" if page.is_active else "inactive",
            "last_checked": page.last_checked,
            "created_at": page.created_at,
            "last_change_detected": page.last_change_detected,
            "current_version_id": str(page.current_version_id) if page.current_version_id else None
        }

# Create a global instance
page_service = PageService()

