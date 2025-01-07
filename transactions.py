from supabase import create_client
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uvicorn
from auth import get_current_user

# Initialize Router
router = APIRouter(prefix="/transactions", tags=["transactions"])

# Supabase configuration
SUPABASE_URL = "https://zvmseqpsgsgnzwxvvkak.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2bXNlcXBzZ3Nnbnp3eHZ2a2FrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NTI3MzgsImV4cCI6MjA1MTQyODczOH0.pBP5G8Igj4MtItR8Zz7EobAL_2rCSYzTGcSvek7yvIs"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic model for transactions
class TransactionBase(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    date_of_transaction: Optional[str] = None
    amount_incurred: Optional[str] = None
    transaction_name: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionUpdate(TransactionBase):
    pass

# CRUD Endpoints
@router.post("/{user_id}")
async def create_transaction(
    user_id: str,
    transaction: TransactionCreate, 
    current_user: str = Depends(get_current_user)
):
    # Verify the user is creating their own transaction
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only create transactions for yourself")
    
    try:
        # Verify subcategory exists
        subcategory_check = supabase.table("subcategories").select("*").eq(
            "category", transaction.category
        ).eq(
            "subcategory_name", transaction.sub_category
        ).or_(
            f"is_standard.eq.true,user_id.eq.{user_id}"
        ).execute()

        if not subcategory_check.data:
            raise HTTPException(
                status_code=400,
                detail="Invalid category-subcategory combination"
            )

        transaction_data = transaction.model_dump()
        transaction_data["user_id"] = user_id
        
        response = supabase.table("transaction_details").insert(transaction_data).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}")
async def read_user_transactions(
    user_id: str, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only view your own transactions")
    
    try:
        response = supabase.table("transaction_details").select("*").eq("user_id", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}/{transaction_id}")
async def read_transaction(
    user_id: str,
    transaction_id: int, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only view your own transactions")
    
    try:
        response = supabase.table("transaction_details").select("*").eq(
            "transaction_id", transaction_id
        ).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/{transaction_id}")
async def update_transaction(
    user_id: str,
    transaction_id: int, 
    transaction: TransactionUpdate, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only update your own transactions")
    
    try:
        check_response = supabase.table("transaction_details").select("*").eq(
            "transaction_id", transaction_id
        ).eq("user_id", user_id).execute()
        
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")

        if transaction.category is not None or transaction.sub_category is not None:
            current_category = transaction.category or check_response.data[0]["category"]
            current_subcategory = transaction.sub_category or check_response.data[0]["sub_category"]
            
            subcategory_check = supabase.table("subcategories").select("*").eq(
                "category", current_category
            ).eq(
                "subcategory_name", current_subcategory
            ).or_(
                f"is_standard.eq.true,user_id.eq.{user_id}"
            ).execute()

            if not subcategory_check.data:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid category-subcategory combination"
                )

        update_data = {k: v for k, v in transaction.model_dump().items() if v is not None}
        response = supabase.table("transaction_details").update(
            update_data
        ).eq("transaction_id", transaction_id).eq("user_id", user_id).execute()
        
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}/{transaction_id}")
async def delete_transaction(
    user_id: str,
    transaction_id: int, 
    current_user: str = Depends(get_current_user)
):
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only delete your own transactions")
    
    try:
        response = supabase.table("transaction_details").delete().eq(
            "transaction_id", transaction_id
        ).eq("user_id", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return {"message": "Transaction deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 