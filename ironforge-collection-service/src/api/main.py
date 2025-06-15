import uvicorn
from fastapi import FastAPI

app = FastAPI(
    title="Ironforge Data Collection API",
    description="An API for collecting data from Ironforge",
    version="0.1.0",
)


# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello World! Welcome to my FastAPI app"}


@app.get("/status")
def health_check():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello World! Welcome to my FastAPI app"}

@app.get("/start")
def start_app():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello World! Welcome to my FastAPI app"}

@app.get("/stop")
def stop_app():
    """Root endpoint that returns a welcome message."""
    return {"message": "Hello World! Welcome to my FastAPI app"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
