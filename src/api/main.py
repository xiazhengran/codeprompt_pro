"""Main FastAPI Application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.llm.llm_gateway import LLMGateway
from src.llm.providers.openai_provider import OpenAIProvider
from src.agents.factory import AgentFactory
from src.api.routes.agents import router as agents_router, set_agent_factory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
llm_gateway: LLMGateway = None
agent_factory: AgentFactory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global llm_gateway, agent_factory
    
    logger.info("Initializing Vibe Coding Agent System...")
    
    # Initialize LLM Gateway
    llm_gateway = LLMGateway(config={
        "rate_limit_rpm": 60,
        "rate_limit_tpm": 100000,
        "fallback_chains": {
            "gpt-4-turbo": ["openai"],
            "gpt-3.5-turbo": ["openai"]
        }
    })
    
    # Register OpenAI Provider
    openai_provider = OpenAIProvider()
    llm_gateway.register_provider("openai", openai_provider)
    
    # Initialize Agent Factory
    agent_factory = AgentFactory(
        llm_gateway=llm_gateway,
        memory_manager=None
    )
    
    # Set factory for routes
    set_agent_factory(agent_factory)
    
    logger.info("System initialized successfully")
    
    yield
    
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Vibe Coding Prompt Agent",
    description="Enterprise-grade AI coding assistant",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(agents_router)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Vibe Coding Prompt Agent",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
