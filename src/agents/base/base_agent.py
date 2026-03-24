"""Base Agent Abstract Class"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING
from enum import Enum
import logging
from datetime import datetime

if TYPE_CHECKING:
    from src.llm.llm_gateway import LLMGateway
    from src.tools.registry import ToolRegistry
    from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentConfig:
    """Agent Configuration"""
    name: str
    description: str
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    retry_count: int = 3
    system_prompt_version: str = "v1.0.0"
    tools_enabled: list[str] = field(default_factory=list)


@dataclass
class AgentContext:
    """Agent Execution Context"""
    session_id: str
    user_id: str
    project_path: str
    task_description: str
    files_to_modify: list[str] = field(default_factory=list)
    additional_context: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict] = field(default_factory=list)


@dataclass
class AgentResult:
    """Agent Execution Result"""
    status: AgentStatus
    message: str
    data: Optional[dict] = None
    artifacts: list[dict] = field(default_factory=list)
    execution_time: float = 0.0
    token_usage: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "artifacts": self.artifacts,
            "execution_time": self.execution_time,
            "token_usage": self.token_usage,
            "errors": self.errors
        }


@dataclass
class ToolCall:
    """Tool Call Record"""
    tool_name: str
    arguments: dict
    result: Any
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base Agent Class"""

    def __init__(
        self,
        config: AgentConfig,
        llm_gateway: "LLMGateway",
        tool_registry: "ToolRegistry",
        memory_manager: "MemoryManager"
    ):
        self.config = config
        self.llm = llm_gateway
        self.tools = tool_registry
        self.memory = memory_manager
        self.logger = logging.getLogger(f"{__name__}.{config.name}")
        self.status = AgentStatus.IDLE
        self.tool_calls: list[ToolCall] = []

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute Agent Task"""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get System Prompt"""
        pass

    async def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        tools: Optional[list[dict]] = None
    ) -> dict:
        """Call LLM"""
        return await self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt or self.get_system_prompt(),
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            tools=tools
        )

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute Tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        try:
            result = await tool.execute(**kwargs)
            self.tool_calls.append(ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=result,
                success=True
            ))
            return result
        except Exception as e:
            self.tool_calls.append(ToolCall(
                tool_name=tool_name,
                arguments=kwargs,
                result=None,
                success=False,
                error=str(e)
            ))
            raise

    def get_tool_calls_history(self) -> list[dict]:
        """Get Tool Call History"""
        return [
            {
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "result": tc.result,
                "timestamp": tc.timestamp.isoformat(),
                "success": tc.success
            }
            for tc in self.tool_calls
        ]
