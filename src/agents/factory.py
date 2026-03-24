"""Agent Factory for creating agent instances"""
from typing import Optional
import logging

from src.agents.base.base_agent import BaseAgent, AgentConfig
from src.agents.code_agent import CodeAgent
from src.llm.llm_gateway import LLMGateway
from src.tools.registry import ToolRegistry, create_default_registry
from src.memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory for creating agent instances"""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        tool_registry: Optional[ToolRegistry] = None,
        memory_manager: Optional[MemoryManager] = None
    ):
        self.llm = llm_gateway
        self.tool_registry = tool_registry or create_default_registry()
        self.memory = memory_manager or MemoryManager()
        
        # Register default agents
        self._agent_classes = {
            "code": CodeAgent,
            # Can add more agents here
        }

    def create(self, agent_type: str, config: dict = None) -> BaseAgent:
        """Create agent instance"""
        
        if agent_type not in self._agent_classes:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = self._agent_classes[agent_type]
        
        # Create agent config
        agent_config = AgentConfig(
            name=agent_type,
            description=f"{agent_type} agent",
            model=config.get("model", "gpt-4-turbo"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4096),
            timeout=config.get("timeout", 120),
            tools_enabled=config.get("tools", [])
        )
        
        return agent_class(
            config=agent_config,
            llm_gateway=self.llm,
            tool_registry=self.tool_registry,
            memory_manager=self.memory
        )

    def register_agent(self, name: str, agent_class: type[BaseAgent]) -> None:
        """Register new agent type"""
        self._agent_classes[name] = agent_class
