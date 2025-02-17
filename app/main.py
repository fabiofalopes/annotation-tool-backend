from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="Chat Disentanglement Annotation API",
    description="API for annotating chat message threads in the chat disentanglement task",
    version="1.0.0"
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Annotation Tool API"} 