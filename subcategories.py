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

class SubcategoryUpdate(BaseModel):
    category: str
    subcategory_name: str

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
    print(f"\n=== Update Subcategory ===")
    print(f"User ID: {user_id}")
    print(f"Subcategory ID: {subcategory_id}")
    print(f"Update data: {subcategory.model_dump()}")
    
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only update your own subcategories")
    
    try:
        # First verify subcategory exists and belongs to user
        existing = supabase.from_('subcategories').select('*').eq(
            'subcategory_id', subcategory_id
        ).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Subcategory not found")
            
        if existing.data[0]['is_standard']:
            raise HTTPException(status_code=403, detail="Cannot modify standard subcategories")
            
        if existing.data[0]['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Can only update your own subcategories")

        # Update subcategory
        response = supabase.from_('subcategories').update({
            'category': subcategory.category,
            'subcategory_name': subcategory.subcategory_name
        }).eq('subcategory_id', subcategory_id).eq('user_id', user_id).execute()
        
        # Format response
        formatted_response = {
            "category": response.data[0]["category"],
            "subcategory_name": response.data[0]["subcategory_name"],
            "subcategory_id": response.data[0]["subcategory_id"]
        }
        
        print(f"Updated subcategory: {formatted_response}")
        return formatted_response

    except Exception as e:
        print(f"Error updating subcategory: {str(e)}")
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
