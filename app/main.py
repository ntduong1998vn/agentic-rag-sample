from fastapi import FastAPI

app = FastAPI(
    title="Agentic RAG API",
    description="Retrieval-augmented generation system with agentic capabilities",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Agentic RAG API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)