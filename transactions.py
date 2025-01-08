from supabase import create_client
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uvicorn
from auth import get_current_user
import re

# Initialize Router
router = APIRouter(prefix="/transactions", tags=["transactions"])

# Supabase configuration
SUPABASE_URL = "https://zvmseqpsgsgnzwxvvkak.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp2bXNlcXBzZ3Nnbnp3eHZ2a2FrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NTI3MzgsImV4cCI6MjA1MTQyODczOH0.pBP5G8Igj4MtItR8Zz7EobAL_2rCSYzTGcSvek7yvIs"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Pydantic models for transactions
class TransactionCreate(BaseModel):
    category: str
    sub_category: str
    date_of_transaction: str  # Format: "MM-DD"
    amount_incurred: str
    transaction_name: str

class TransactionUpdate(BaseModel):
    transaction_name: Optional[str] = None
    amount_incurred: Optional[str] = None
    date_of_transaction: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None

# CRUD Endpoints
@router.post("/{user_id}")
async def create_transaction(
    user_id: str,
    transaction: TransactionCreate, 
    current_user: str = Depends(get_current_user)
):
    print(f"\n=== Create Transaction ===")
    print(f"User: {user_id}")
    print(f"Data: {transaction.model_dump()}")
    
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only create transactions for yourself")
    
    try:
        # Validate date format (MM-DD)
        if not re.match(r'^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$', transaction.date_of_transaction):
            raise HTTPException(
                status_code=400,
                detail="Invalid date format. Use MM-DD (e.g., 03-20)"
            )

        # First find the subcategory_id from subcategories table
        subcategory_check = supabase.from_('subcategories').select('subcategory_id').eq(
            'category', transaction.category
        ).eq(
            'subcategory_name', transaction.sub_category
        ).execute()

        # If no subcategory found, return error
        if not subcategory_check.data:
            raise HTTPException(
                status_code=400,
                detail=f"No subcategory found for category '{transaction.category}' and subcategory '{transaction.sub_category}'"
            )

        subcategory_id = subcategory_check.data[0]['subcategory_id']

        # Insert into transaction_details table
        transaction_data = {
            "transaction_name": transaction.transaction_name,
            "amount_incurred": transaction.amount_incurred,
            "date_of_transaction": transaction.date_of_transaction,
            "subcategory_id": subcategory_id,
            "user_id": user_id
        }
        
        response = supabase.from_('transaction_details').insert(
            transaction_data
        ).execute()
        
        print(f"Created transaction: {response.data}")
        return response.data[0]

    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}")
async def read_user_transactions(
    user_id: str, 
    current_user: str = Depends(get_current_user)
):
    print("\n=== Transaction Request ===")
    print(f"Requested user_id: {user_id}")
    print(f"Authenticated user: {current_user}")
    
    try:
        # First get all transactions
        response = supabase.from_('transaction_details').select('*').eq(
            'user_id', user_id
        ).execute()

        # Format response
        formatted_transactions = []
        for transaction in response.data:
            # Get subcategory data for each transaction
            subcategory_data = supabase.from_('subcategories').select(
                'category, subcategory_name'
            ).eq(
                'subcategory_id', transaction['subcategory_id']
            ).single().execute()

            formatted_transaction = {
                "transaction_id": transaction["transaction_id"],
                "date_of_transaction": transaction["date_of_transaction"],
                "amount_incurred": transaction["amount_incurred"],
                "transaction_name": transaction["transaction_name"],
                "user_id": transaction["user_id"],
                "subcategory_id": transaction["subcategory_id"],
                "category": subcategory_data.data["category"],
                "subcategory_name": subcategory_data.data["subcategory_name"]
            }
            formatted_transactions.append(formatted_transaction)

        return formatted_transactions

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to fetch transactions: {str(e)}"
        )

@router.put("/{user_id}/{transaction_id}")
async def update_transaction(
    user_id: str,
    transaction_id: int, 
    transaction: TransactionUpdate, 
    current_user: str = Depends(get_current_user)
):
    print(f"\n=== Update Transaction ===")
    print(f"User: {user_id}")
    print(f"Transaction ID: {transaction_id}")
    print(f"Update data: {transaction.model_dump()}")

    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only update your own transactions")
    
    try:
        # First verify transaction exists and belongs to user
        check_response = supabase.from_('transaction_details').select('*').eq(
            'transaction_id', transaction_id
        ).eq('user_id', user_id).execute()
        
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Transaction not found")

        # Prepare update data
        update_data = {k: v for k, v in transaction.model_dump().items() if v is not None}
        
        # If both category and sub_category are provided, find the subcategory_id
        if transaction.category is not None and transaction.sub_category is not None:
            subcategory_check = supabase.from_('subcategories').select('subcategory_id').eq(
                'category', transaction.category
            ).eq(
                'subcategory_name', transaction.sub_category
            ).execute()

            if not subcategory_check.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"No subcategory found for category '{transaction.category}' and subcategory '{transaction.sub_category}'"
                )
            
            # Remove category and sub_category from update data
            update_data.pop('category', None)
            update_data.pop('sub_category', None)
            # Add the found subcategory_id
            update_data['subcategory_id'] = subcategory_check.data[0]['subcategory_id']
        elif transaction.category is not None or transaction.sub_category is not None:
            # If only one of category or sub_category is provided, that's an error
            raise HTTPException(
                status_code=400,
                detail="Both category and sub_category must be provided together"
            )

        # Update transaction
        response = supabase.from_('transaction_details').update(
            update_data
        ).eq('transaction_id', transaction_id).eq('user_id', user_id).execute()

        # First get the updated transaction
        updated_transaction = supabase.from_('transaction_details').select('*').eq(
            'transaction_id', transaction_id
        ).single().execute()

        transaction_data = updated_transaction.data

        # Then get the subcategory data
        subcategory_data = supabase.from_('subcategories').select(
            'category, subcategory_name'
        ).eq(
            'subcategory_id', transaction_data['subcategory_id']
        ).single().execute()

        # Add debug logging
        print(f"Raw transaction data: {transaction_data}")
        print(f"Subcategory data: {subcategory_data.data}")
        
        formatted_response = {
            "transaction_id": transaction_data["transaction_id"],
            "date_of_transaction": transaction_data["date_of_transaction"],
            "amount_incurred": transaction_data["amount_incurred"],
            "transaction_name": transaction_data["transaction_name"],
            "user_id": transaction_data["user_id"],
            "category": subcategory_data.data["category"],
            "subcategory_name": subcategory_data.data["subcategory_name"]
        }
        
        print(f"Updated transaction: {formatted_response}")
        return formatted_response

    except Exception as e:
        print(f"Error updating transaction: {str(e)}")
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

@router.get("/{user_id}/expenses/{year}/{month}")
async def get_expenses_by_month(
    user_id: str,
    year: str,
    month: str,
    current_user: str = Depends(get_current_user)
):
    print(f"\n=== Fetch Monthly Expenses ===")
    print(f"User ID: {user_id}")
    print(f"Year: {year}")
    print(f"Month: {month}")
    
    if user_id != current_user:
        raise HTTPException(status_code=403, detail="Can only view your own expenses")
    
    try:
        # Format month to ensure two digits
        month = month.zfill(2)  # e.g., "3" becomes "03"
        
        # Get transactions for the month
        response = supabase.from_('transaction_details').select('*').eq(
            'user_id', user_id
        ).like(
            'date_of_transaction', f'{year}-{month}-%'
        ).execute()

        print(f"Query: date_of_transaction LIKE '{year}-{month}-%'")
        print(f"Found transactions: {response.data}")

        if not response.data:
            return []

        # Group and sum by subcategory_id
        expenses_by_subcategory = {}
        for transaction in response.data:
            subcategory_id = transaction['subcategory_id']
            amount = float(transaction['amount_incurred'])
            
            if subcategory_id in expenses_by_subcategory:
                expenses_by_subcategory[subcategory_id] += amount
            else:
                expenses_by_subcategory[subcategory_id] = amount

        print(f"\nGrouped by subcategory: {expenses_by_subcategory}")

        # Get subcategory names and format response
        expenses = []
        for subcategory_id, total_amount in expenses_by_subcategory.items():
            subcategory = supabase.from_('subcategories').select(
                'subcategory_name, category'
            ).eq('subcategory_id', subcategory_id).single().execute()

            print(f"\nSubcategory details for ID {subcategory_id}: {subcategory.data}")

            expenses.append({
                "subcategory_id": subcategory_id,
                "subcategory_name": subcategory.data['subcategory_name'],
                "total_amount": round(total_amount, 2)
            })

        # Sort by subcategory_name
        expenses.sort(key=lambda x: x['subcategory_name'])
        return expenses

    except Exception as e:
        print(f"Error fetching expenses: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch expenses: {str(e)}"
        )