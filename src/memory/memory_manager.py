"""Memory Manager for Agent System"""
from typing import Any, Optional, Protocol
from dataclasses import dataclass, field
import logging
from datetime import datetime
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryStore(Protocol):
    """Memory Store Protocol"""
    async def save(self, key: str, value: Any) -> None: ...
    async def get(self, key: str) -> Optional[Any]: ...
    async def delete(self, key: str) -> None: ...


class InMemoryStore:
    """In-Memory Implementation of MemoryStore"""
    
    def __init__(self):
        self._store: dict[str, Any] = {}
    
    async def save(self, key: str, value: Any) -> None:
        self._store[key] = value
    
    async def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)
    
    async def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]


@dataclass
class MemoryEntry:
    """Memory Entry"""
    content: Any
    memory_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class MemoryManager:
    """Memory Manager for managing different types of memory"""

    def __init__(self, store: Optional[MemoryStore] = None):
        self.store = store or InMemoryStore()
        self.session_memories: dict[str, list[MemoryEntry]] = defaultdict(list)
        self.project_memories: dict[str, list[MemoryEntry]] = defaultdict(list)

    async def add(
        self,
        session_id: str,
        content: Any,
        memory_type: str = "general",
        metadata: dict = None
    ) -> None:
        """Add a memory entry"""
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            metadata=metadata or {}
        )
        self.session_memories[session_id].append(entry)
        
        key = f"session:{session_id}:{len(self.session_memories[session_id])}"
        await self.store.save(key, entry.__dict__)

    async def get_session_memory(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[dict]:
        """Get session memory"""
        entries = self.session_memories.get(session_id, [])
        return [
            {
                "content": e.content,
                "memory_type": e.memory_type,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata
            }
            for e in entries[-limit:]
        ]

    async def add_project_memory(
        self,
        project_id: str,
        content: Any,
        memory_type: str = "general",
        metadata: dict = None
    ) -> None:
        """Add a project memory entry"""
        entry = MemoryEntry(
            content=content,
            memory_type=memory_type,
            metadata=metadata or {}
        )
        self.project_memories[project_id].append(entry)

    async def get_project_memory(
        self,
        project_id: str,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> list[dict]:
        """Get project memory"""
        entries = self.project_memories.get(project_id, [])
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        return [
            {
                "content": e.content,
                "memory_type": e.memory_type,
                "timestamp": e.timestamp.isoformat(),
                "metadata": e.metadata
            }
            for e in entries[-limit:]
        ]

    async def search_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> list[dict]:
        """Search memory for relevant entries"""
        results = []
        query_lower = query.lower()
        
        memories = []
        if session_id:
            memories.extend(self.session_memories.get(session_id, []))
        if project_id:
            memories.extend(self.project_memories.get(project_id, []))
        
        for entry in memories:
            content_str = str(entry.content).lower()
            if query_lower in content_str:
                results.append({
                    "content": entry.content,
                    "memory_type": entry.memory_type,
                    "timestamp": entry.timestamp.isoformat(),
                    "relevance": content_str.count(query_lower)
                })
        
        return sorted(results, key=lambda x: x["relevance"], reverse=True)

    async def clear_session(self, session_id: str) -> None:
        """Clear session memory"""
        if session_id in self.session_memories:
            del self.session_memories[session_id]

    async def save_workflow_memory(
        self,
        workflow_id: str,
        summary: dict
    ) -> None:
        """Save workflow execution summary"""
        key = f"workflow:{workflow_id}"
        await self.store.save(key, {
            "summary": summary,
            "completed_at": datetime.now().isoformat()
        })
