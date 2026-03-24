"""OpenAI Provider Implementation"""
import os
import aiohttp
from typing import Optional
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()

from src.llm.llm_gateway import LLMRequest, LLMResponse, LLMProvider

logger = __import__("logging").getLogger(__name__)


class OpenAIProvider:
    """OpenAI Provider Implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate Response"""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p
        }
        
        if request.tools:
            payload["tools"] = request.tools
        
        try:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                data = await resp.json()
                
                if "error" in data:
                    raise Exception(data["error"])
                
                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data["model"],
                    usage=data.get("usage", {}),
                    finish_reason=data["choices"][0].get("finish_reason", "stop")
                )
        except aiohttp.ClientError as e:
            logger.error(f"OpenAI API request failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Health Check"""
        try:
            session = await self._get_session()
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with session.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def close(self) -> None:
        """Close session"""
        if self._session and not self._session.closed:
            await self._session.close()
