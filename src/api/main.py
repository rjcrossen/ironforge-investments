"""
Ironforge Investments API

This module provides the FastAPI application for accessing World of Warcraft
auction house data and analytics.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import items, commodities, token

app = FastAPI(
    title="Ironforge Investments API",
    description="API for accessing World of Warcraft auction house data and analytics",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(items.router)
app.include_router(commodities.router)
app.include_router(token.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}