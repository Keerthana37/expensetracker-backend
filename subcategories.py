from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from supabase import create_client
from auth import get_current_user

router = APIRouter(prefix="/subcategories", tags=["subcategories"])

# Supabase configuration
SUPABASE_URL = "https://zvmseqpsgsgnzwxvvkak.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2bXNlcXBzZ3Nnbnp3eHZ2a2FrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NTI3MzgsImV4cCI6MjA1MTQyODczOH0.pBP5G8Igj4MtItR8Zz7EobAL_2rCSYzTGcSvek7yvIs"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic models
class SubcategoryBase(BaseModel):
    category: str
    subcategory_name: str
    budget: Optional[float] = None

class SubcategoryCreate(SubcategoryBase):
    pass

class SubcategoryUpdate(SubcategoryBase):
    category: Optional[str] = None
    subcategory_name: Optional[str] = None
    budget: Optional[float] = None

class Subcategory(SubcategoryBase):
    subcategory_id: int
    is_standard: bool
    created_at: str
    user_id: Optional[str]
    budget: Optional[float]

# CRUD Endpoints
@router.post("/{user_id}")
async def create_subcategory(
    user_id: str,
    subcategory: SubcategoryCreate, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only create subcategories for yourself")
    
    try:
        existing = supabase.table("subcategories").select("*").eq(
            "category", subcategory.category
        ).eq("subcategory_name", subcategory.subcategory_name).eq(
            "user_id", user_id
        ).execute()

        if existing.data:
            raise HTTPException(
                status_code=400, 
                detail="This category-subcategory combination already exists"
            )

        response = supabase.table("subcategories").insert({
            "category": subcategory.category,
            "subcategory_name": subcategory.subcategory_name,
            "is_standard": False,
            "user_id": user_id
        }).execute()

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}")
async def read_subcategories(
    user_id: str, 
    current_user: str = Depends(get_current_user)
):
    print(f"\n=== Fetching Categories ===")
    print(f"User ID: {user_id}")
    print(f"Current user: {current_user}")
    
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only view your own categories")
    
    try:
        # Get both standard categories and user's custom categories
        response = supabase.from_('subcategories').select('*').or_(
            f'is_standard.eq.true,user_id.eq.{user_id}'
        ).execute()
        
        print(f"Found categories: {response.data}")
        
        # Format the response
        categories = []
        for category in response.data:
            formatted_category = {
                "subcategory_id": category["subcategory_id"],
                "category": category["category"],
                "subcategory_name": category["subcategory_name"],
                "is_standard": category["is_standard"],
                "budget": category.get("budget"),
                "user_id": category.get("user_id")
            }
            categories.append(formatted_category)
        
        return categories

    except Exception as e:
        print(f"\n=== Error Details ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch categories: {str(e)}"
        )

@router.get("/{user_id}/{subcategory_id}")
async def read_subcategory(
    user_id: str,
    subcategory_id: int, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only view your own subcategories")
    
    try:
        response = supabase.table("subcategories").select("*").eq(
            "subcategory_id", subcategory_id
        ).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Subcategory not found")
            
        subcategory = response.data[0]
        if not subcategory["is_standard"] and subcategory["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Subcategory not accessible")
            
        return subcategory
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/{subcategory_id}")
async def update_subcategory(
    user_id: str,
    subcategory_id: int,
    subcategory: SubcategoryUpdate,
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only update your own subcategories")
    
    try:
        # First verify subcategory exists
        existing = supabase.table("subcategories").select("*").eq(
            "subcategory_id", subcategory_id
        ).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Subcategory not found")

        # Handle budget update in subcategory_budgets table
        if subcategory.budget is not None:
            try:
                budget_value = float(subcategory.budget)
                print(f"Processing budget update: {budget_value}")

                # First try to update existing budget
                budget_response = supabase.table("subcategory_budgets").update({
                    "budget": budget_value
                }).eq("user_id", user_id).eq(
                    "subcategory_id", subcategory_id
                ).execute()

                # If no existing budget, create new entry
                if not budget_response.data:
                    print("Creating new budget entry")
                    budget_response = supabase.table("subcategory_budgets").insert({
                        "user_id": user_id,
                        "subcategory_id": subcategory_id,
                        "budget": budget_value
                    }).execute()

                print(f"Budget operation response: {budget_response.data}")
            except Exception as budget_error:
                print(f"Budget update error: {str(budget_error)}")
                raise HTTPException(status_code=400, detail=f"Budget update failed: {str(budget_error)}")

        # Verify the budget was stored
        budget_verification = supabase.table("subcategory_budgets").select("budget").eq(
            "user_id", user_id
        ).eq("subcategory_id", subcategory_id).execute()
        
        print(f"Budget verification: {budget_verification.data}")

        return {
            "message": "Update successful",
            "budget_stored": budget_verification.data[0] if budget_verification.data else None
        }
            
    except Exception as e:
        print(f"Update error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/{subcategory_id}")
async def delete_subcategory(
    user_id: str,
    subcategory_id: int, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only delete your own subcategories")
    
    try:
        existing = supabase.table("subcategories").select("*").eq(
            "subcategory_id", subcategory_id
        ).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Subcategory not found")
        
        if existing.data[0]["is_standard"]:
            raise HTTPException(status_code=403, detail="Cannot delete standard subcategories")
            
        if existing.data[0]["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Can only delete your own subcategories")

        response = supabase.table("subcategories").delete().eq(
            "subcategory_id", subcategory_id
        ).eq("user_id", user_id).execute()
        
        return {"message": "Subcategory deleted successfully"}
    except Exception as e:
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Cannot delete subcategory because it is being used in transactions"
            )
        raise HTTPException(status_code=400, detail=str(e))
