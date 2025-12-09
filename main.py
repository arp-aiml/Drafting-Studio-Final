from fastapi import FastAPI
from app.routers import drafting
import uvicorn

app = FastAPI(title="LexFlow AI Backend")

# Include the router. The prefix "/draft" is handled inside drafting.py
app.include_router(drafting.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)