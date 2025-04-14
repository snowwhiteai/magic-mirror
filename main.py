"""
Magic Mirror: Configuration sync service for Snow White AI.
Main entry point for the application.
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, UUID8
from typing import List, Dict, Optional
import uuid
import json
from datetime import datetime

app = FastAPI(
    title="Magic Mirror: Configuration Service",
    description="API for managing agent configuration and syncing with Pipecat Cloud",
    version="0.1.0",
)

# cors middleware
app.add_middleware(
    CORSMiddleware,
    # For development only, in production restrict to specific ip
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# in-memory storage for development.
agents_db = {}
configuration_db = {}


class AgentBase(BaseModel):
    name: str


class AgentCreate(AgentBase):
    pass


class Agent(AgentBase):
    id: UUID8
    pipecat_cloud_instance_id: Optional[str] = None
    status: str = "CREATED"
    last_sync_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ConfigurationBase(BaseModel):
    confid_data: Dict


class ConfigurationCreate(ConfigurationBase):
    pass


class Configuration(ConfigurationBase):
    id: UUID8
    agent_id: UUID8
    version: int
    is_active: bool = True
    created_at: datetime
    activated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class UpdateMessage(BaseModel):
    agent_id: UUID8
    version: Optional[int] = None
    change_type: str  # "CONTEXT_UPDATE", "FULL_SYNC", "PROVISION", "DEPROVISION"

# Routes


@app.get("/")
async def root():
    return {"message": "Magic Mirror configuration service"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
