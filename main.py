from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from transactions import router as transactions_router
from subcategories import router as subcategories_router
from auth import router as auth_router
import uvicorn

app = FastAPI(title="Transaction Management System")

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(transactions_router)
app.include_router(subcategories_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 

