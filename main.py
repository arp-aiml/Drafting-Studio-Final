#main.py
from fastapi import FastAPI
from app.routers.drafting import router as drafting_router

app = FastAPI(title="Drafting Studio API")

app.include_router(drafting_router)
app.include_router(drafting_router, prefix="/draft")  


@app.get("/")
def health_check():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
