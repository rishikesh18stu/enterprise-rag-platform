from dotenv import load_dotenv
from fastapi import FastAPI
from auth.routes import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from api.chat_routes import router as chat_router
from api.upload_routes import router as upload_router
import os
load_dotenv()

print("LANGSMITH_TRACING:", os.getenv("LANGSMITH_TRACING"))
print("LANGSMITH_API_KEY set:", bool(os.getenv("LANGSMITH_API_KEY")))
print("LANGSMITH_PROJECT:", os.getenv("LANGSMITH_PROJECT"))
app = FastAPI(title="Enterprise RAG Platform")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(upload_router)
from auth.security import get_current_user
from fastapi import Depends

@app.get("/protected")
def protected_route(user: dict = Depends(get_current_user)):
    return {"message": f"Hello user {user['sub']}, your role is {user['role']}"}

@app.get("/")
def read_root():
    """
    Health check endpoint.
    """
    return {"status": "ok", "message": "Enterprise RAG backend is alive"}