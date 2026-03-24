"""LLM Gateway - Unified LLM Interface"""
from typing import Optional, Protocol
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
import logging
from datetime import datetime
import hashlib
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"


@dataclass
class LLMRequest:
    prompt: str
    system_prompt: Optional[str] = None
    model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    tools: Optional[list[dict]] = None
    stream: bool = False


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict = field(default_factory=dict)
    finish_reason: str = "stop"
    cached: bool = False
    latency_ms: float = 0.0


class LLMProvider(Protocol):
    """LLM Provider Protocol"""
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response"""
        ...
    
    async def health_check(self) -> bool:
        """Health check"""
        ...


class RateLimiter:
    """Rate Limiter"""
    
    def __init__(self, rpm: int = 60, tpm: int = 100000):
        self.rpm = rpm
        self.tpm = tpm
        self.request_timestamps: list[datetime] = []
        self.token_usage: list[tuple[datetime, int]] = []
    
    async def acquire(self, estimated_tokens: int) -> bool:
        """Acquire permit"""
        now = datetime.now()
        
        # Clean expired records
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if (now - ts).total_seconds() < 60
        ]
        self.token_usage = [
            (ts, tokens) for ts, tokens in self.token_usage
            if (now - ts).total_seconds() < 60
        ]
        
        # Check RPM
        if len(self.request_timestamps) >= self.rpm:
            return False
        
        # Check TPM
        total_tokens = sum(tokens for _, tokens in self.token_usage)
        if total_tokens + estimated_tokens > self.tpm:
            return False
        
        self.request_timestamps.append(now)
        self.token_usage.append((now, estimated_tokens))
        return True
    
    async def wait_and_acquire(self, estimated_tokens: int, timeout: int = 60):
        """Wait and acquire permit"""
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            if await self.acquire(estimated_tokens):
                return True
            await asyncio.sleep(1)
        
        raise TimeoutError("Rate limit wait timeout")


class CostTracker:
    """Cost Tracker"""
    
    def __init__(self):
        self.usage_by_model: dict[str, dict] = {}
        self.cost_by_user: dict[str, float] = {}
    
    def record_usage(
        self,
        user_id: str,
        model: str,
        tokens: dict,
        cost: float
    ) -> None:
        """Record usage"""
        if model not in self.usage_by_model:
            self.usage_by_model[model] = {
                "total_requests": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_cost": 0.0
            }
        
        self.usage_by_model[model]["total_requests"] += 1
        self.usage_by_model[model]["prompt_tokens"] += tokens.get("prompt_tokens", 0)
        self.usage_by_model[model]["completion_tokens"] += tokens.get("completion_tokens", 0)
        self.usage_by_model[model]["total_cost"] += cost
        
        if user_id not in self.cost_by_user:
            self.cost_by_user[user_id] = 0.0
        self.cost_by_user[user_id] += cost
    
    def get_cost_summary(self) -> dict:
        """Get cost summary"""
        return {
            "by_model": self.usage_by_model,
            "by_user": self.cost_by_user,
            "total_cost": sum(m["total_cost"] for m in self.usage_by_model.values())
        }


class LLMCache:
    """LLM Response Cache"""
    
    def __init__(self):
        self.cache: dict[str, LLMResponse] = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, request: LLMRequest) -> str:
        """Generate cache key"""
        content = f"{request.prompt}:{request.system_prompt}:{request.model}:{request.temperature}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def get(self, request: LLMRequest) -> Optional[LLMResponse]:
        """Get cached response"""
        key = self._generate_key(request)
        
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        
        self.miss_count += 1
        return None
    
    async def set(self, request: LLMRequest, response: LLMResponse) -> None:
        """Set cache"""
        key = self._generate_key(request)
        self.cache[key] = response
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total if total > 0 else 0
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache)
        }


class LLMGateway:
    """LLM Gateway - Unified Entry Point"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.providers: dict[str, LLMProvider] = {}
        self.rate_limiter = RateLimiter(
            rpm=self.config.get("rate_limit_rpm", 60),
            tpm=self.config.get("rate_limit_tpm", 100000)
        )
        self.cost_tracker = CostTracker()
        self.cache = LLMCache()
        self.fallback_chains: dict[str, list[str]] = self.config.get("fallback_chains", {})
    
    def register_provider(self, name: str, provider: LLMProvider) -> None:
        """Register Provider"""
        self.providers[name] = provider
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4-turbo",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[list[dict]] = None,
        user_id: str = "default",
        use_cache: bool = True
    ) -> dict:
        """Generate Response"""
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools
        )
        
        # Check cache
        if use_cache:
            cached = await self.cache.get(request)
            if cached:
                logger.info(f"Cache hit for model {model}")
                return cached.__dict__
        
        # Wait for rate limit
        await self.rate_limiter.wait_and_acquire(max_tokens)
        
        # Determine Provider
        provider_name = self._get_provider_name(model)
        chain = [provider_name] + self.fallback_chains.get(provider_name, [])
        
        # Try each provider
        last_error = None
        for prov_name in chain:
            if prov_name not in self.providers:
                continue
            
            try:
                start = datetime.now()
                response = await self.providers[prov_name].generate(request)
                response.latency_ms = (datetime.now() - start).total_seconds() * 1000
                
                # Record cost
                cost = self._calculate_cost(model, response.usage)
                self.cost_tracker.record_usage(user_id, model, response.usage, cost)
                
                # Cache
                if use_cache:
                    await self.cache.set(request, response)
                
                return response.__dict__
            
            except Exception as e:
                logger.warning(f"Provider {prov_name} failed: {e}")
                last_error = e
                continue
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")
    
    def _get_provider_name(self, model: str) -> str:
        """Get Provider Name"""
        if model.startswith("gpt-") or model.startswith("text-"):
            return "openai"
        elif model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("azure-"):
            return "azure"
        else:
            return "local"
    
    def _calculate_cost(self, model: str, usage: dict) -> float:
        """Calculate Cost"""
        pricing = {
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        }
        
        rates = pricing.get(model, {"prompt": 0.001, "completion": 0.002})
        
        prompt_cost = usage.get("prompt_tokens", 0) / 1000 * rates["prompt"]
        completion_cost = usage.get("completion_tokens", 0) / 1000 * rates["completion"]
        
        return prompt_cost + completion_cost
    
    def get_stats(self) -> dict:
        """Get Statistics"""
        return {
            "cache": self.cache.get_stats(),
            "cost": self.cost_tracker.get_cost_summary()
        }
