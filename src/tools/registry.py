"""Tool Registry - Unified Tool Management"""
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import asyncio
import re

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Tool Definition"""
    name: str
    description: str
    parameters: dict
    handler: Callable
    enabled: bool = True
    timeout: int = 30
    retry_count: int = 0


class BaseTool(ABC):
    """Base Tool Class"""
    
    def __init__(self, name: str, config: dict = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute Tool"""
        pass
    
    def get_definition(self) -> dict:
        """Get Tool Definition"""
        return {
            "name": self.name,
            "description": self.__doc__ or "",
            "parameters": self.get_schema()
        }
    
    @abstractmethod
    def get_schema(self) -> dict:
        """Get Parameters Schema"""
        pass


class FileTool(BaseTool):
    """File Operation Tool"""
    
    def __init__(self, base_path: str = "."):
        super().__init__("file")
        self.base_path = Path(base_path)
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute File Operation"""
        
        if operation == "read":
            return await self._read_file(kwargs["path"])
        elif operation == "write":
            return await self._write_file(kwargs["path"], kwargs["content"])
        elif operation == "tree":
            return await self._list_tree(kwargs.get("path", "."))
        elif operation == "search":
            return await self._search(kwargs.get("path", "."), kwargs["pattern"])
        elif operation == "exists":
            return await self._check_exists(kwargs["path"])
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    async def _read_file(self, path: str) -> str:
        """Read File"""
        full_path = self.base_path / path
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
    
    async def _write_file(self, path: str, content: str) -> dict:
        """Write File"""
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"path": path, "written": True}
    
    async def _list_tree(self, path: str, max_depth: int = 3) -> dict:
        """List Directory Tree"""
        
        def build_tree(dir_path: Path, current_depth: int) -> dict:
            if current_depth >= max_depth:
                return {"type": "truncated"}
            
            tree = {"type": "directory", "children": {}}
            
            try:
                for item in sorted(dir_path.iterdir()):
                    if item.name.startswith("."):
                        continue
                    
                    if item.is_file():
                        tree["children"][item.name] = {"type": "file"}
                    else:
                        tree["children"][item.name] = build_tree(item, current_depth + 1)
            except PermissionError:
                return {"type": "permission_denied"}
            
            return tree
        
        full_path = self.base_path / path
        return build_tree(full_path, 0)
    
    async def _search(self, path: str, pattern: str) -> list[dict]:
        """Search Files"""
        results = []
        full_path = self.base_path / path
        
        for match in full_path.rglob("*"):
            if match.is_file() and re.search(pattern, str(match)):
                results.append({"path": str(match.relative_to(self.base_path))})
        
        return results
    
    async def _check_exists(self, path: str) -> bool:
        """Check if file exists"""
        return (self.base_path / path).exists()
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "tree", "search", "exists"]
                },
                "path": {"type": "string"},
                "content": {"type": "string"},
                "pattern": {"type": "string"}
            },
            "required": ["operation", "path"]
        }


class ShellTool(BaseTool):
    """Shell Execution Tool"""
    
    def __init__(self, working_dir: str = "."):
        super().__init__("shell")
        self.working_dir = working_dir
    
    async def execute(self, command: str, timeout: int = 30) -> dict:
        """Execute Shell Command"""
        
        self.logger.info(f"Executing command: {command}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8") if stdout else "",
                "stderr": stderr.decode("utf-8") if stderr else ""
            }
        
        except asyncio.TimeoutError:
            raise TimeoutError(f"Command timed out after {timeout}s")
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["command"]
        }


class GitTool(BaseTool):
    """Git Operation Tool"""
    
    def __init__(self, repo_path: str = "."):
        super().__init__("git")
        self.repo_path = repo_path
    
    async def execute(self, operation: str, **kwargs) -> Any:
        """Execute Git Operation"""
        
        operations = {
            "status": f"git -C {self.repo_path} status --porcelain",
            "diff": f"git -C {self.repo_path} diff --no-color",
            "log": f"git -C {self.repo_path} log --oneline -n {kwargs.get('limit', 10)}",
            "branch": f"git -C {self.repo_path} branch -a",
            "commit": f"git -C {self.repo_path} commit -m '{kwargs.get('message', '')}'",
            "push": f"git -C {self.repo_path} push {kwargs.get('remote', 'origin')} {kwargs.get('branch', 'main')}",
            "pull": f"git -C {self.repo_path} pull --rebase",
        }
        
        if operation not in operations:
            raise ValueError(f"Unknown operation: {operation}")
        
        command = operations[operation]
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "returncode": process.returncode,
            "stdout": stdout.decode("utf-8") if stdout else "",
            "stderr": stderr.decode("utf-8") if stderr else ""
        }
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["status", "diff", "log", "branch", "commit", "push", "pull"]
                },
                "message": {"type": "string"},
                "remote": {"type": "string"},
                "branch": {"type": "string"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["operation"]
        }


class ToolRegistry:
    """Tool Registry"""
    
    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}
        self._executors: dict[str, Callable] = {}
    
    def register(
        self,
        name: str,
        handler: Any,
        description: str = "",
        parameters: dict = None,
        enabled: bool = True
    ) -> None:
        """Register Tool"""
        
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or {},
            handler=handler,
            enabled=enabled
        )
        self._setup_executor(name, handler)
    
    def _setup_executor(self, name: str, handler: Any) -> None:
        """Setup Dynamic Executor"""
        
        async def executor(**kwargs):
            if hasattr(handler, "execute"):
                return await handler.execute(**kwargs)
            return await handler(**kwargs)
        
        self._executors[name] = executor
    
    def get(self, name: str) -> Optional[Callable]:
        """Get Tool"""
        
        tool = self.tools.get(name)
        if tool and tool.enabled:
            return self._executors.get(name)
        return None
    
    def get_all_definitions(self) -> list[dict]:
        """Get All Tool Definitions"""
        return [
            {
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters,
                "enabled": tool.enabled
            }
            for name, tool in self.tools.items()
        ]
    
    def enable(self, name: str) -> None:
        """Enable Tool"""
        if name in self.tools:
            self.tools[name].enabled = True
    
    def disable(self, name: str) -> None:
        """Disable Tool"""
        if name in self.tools:
            self.tools[name].enabled = False


def create_default_registry(working_dir: str = ".") -> ToolRegistry:
    """Create Default Tool Registry"""
    
    registry = ToolRegistry()
    
    # Register File Tool
    file_tool = FileTool(base_path=working_dir)
    registry.register(
        "file",
        file_tool,
        "File operations (read, write, tree, search)",
        file_tool.get_schema()
    )
    
    # Register Shell Tool
    shell_tool = ShellTool(working_dir=working_dir)
    registry.register(
        "shell",
        shell_tool,
        "Execute shell commands",
        shell_tool.get_schema()
    )
    
    # Register Git Tool
    git_tool = GitTool(repo_path=working_dir)
    registry.register(
        "git",
        git_tool,
        "Git operations (status, diff, log, commit, push, pull)",
        git_tool.get_schema()
    )
    
    return registry
