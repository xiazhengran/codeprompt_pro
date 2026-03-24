"""Agent API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, list
from datetime import datetime
import uuid

from src.agents.base.base_agent import AgentContext, AgentResult, AgentConfig, AgentStatus
from src.agents.code_agent import CodeAgent

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class AgentRequest(BaseModel):
    """Agent Request"""
    agent_type: str = Field(..., description="Agent type: code, review, test, debug, design, doc")
    task: str = Field(..., description="Task description")
    context: Optional[dict] = Field(default_factory=dict, description="Additional context")
    files_to_modify: Optional[list[str]] = Field(default=None, description="Files to modify")
    options: Optional[dict] = Field(default_factory=dict, description="Agent options")


class AgentResponse(BaseModel):
    """Agent Response"""
    session_id: str
    status: str
    message: str
    result: Optional[dict]
    artifacts: list[dict]
    execution_time: float
    token_usage: dict


# Store for agent factory (will be initialized in main.py)
_agent_factory = None


def set_agent_factory(factory):
    """Set agent factory"""
    global _agent_factory
    _agent_factory = factory


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest):
    """Execute Agent Task"""
    
    session_id = str(uuid.uuid4())
    
    # Create context
    context = AgentContext(
        session_id=session_id,
        user_id=request.context.get("user_id", "demo_user"),
        project_path=request.context.get("project_path", "/tmp/project"),
        task_description=request.task,
        files_to_modify=request.files_to_modify or [],
        additional_context=request.context
    )
    
    try:
        # Get Agent from factory
        if _agent_factory is None:
            raise HTTPException(status_code=500, detail="Agent factory not initialized")
        
        agent = _agent_factory.create(
            request.agent_type,
            config=request.options
        )
        
        result = await agent.execute(context)
        
        return AgentResponse(
            session_id=session_id,
            status=result.status.value,
            message=result.message,
            result=result.data,
            artifacts=result.artifacts,
            execution_time=result.execution_time,
            token_usage=result.token_usage
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools():
    """Get available tools"""
    if _agent_factory is None:
        return {"tools": []}
    return {"tools": _agent_factory.tool_registry.get_all_definitions()}


@router.get("/stats")
async def get_stats():
    """Get agent statistics"""
    if _agent_factory is None:
        return {"stats": {}}
    return {
        "stats": _agent_factory.llm.get_stats()
    }
