"""Code Agent Implementation"""
import time
import re
from pathlib import Path
from typing import Optional

from src.agents.base.base_agent import (
    BaseAgent, 
    AgentConfig, 
    AgentContext, 
    AgentResult,
    AgentStatus
)
from src.prompts.templates.code_generation import CodeGenerationTemplate, CodeLanguage, CodeTask


class CodeAgent(BaseAgent):
    """Code Generation Agent"""
    
    def get_system_prompt(self) -> str:
        return """You are an expert code generation agent specializing in:
- Clean, maintainable code
- Production-ready implementations
- Comprehensive error handling
- Performance optimization

You have access to tools for:
- Reading files and project structure
- Creating and modifying files
- Running commands
- Searching codebase

Always prefer working code over pseudocode. Include proper imports and dependencies."""
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute Code Generation Task"""
        
        start_time = time.time()
        
        try:
            # 1. Analyze project context
            project_context = await self._analyze_project(context)
            
            # 2. Detect language
            language = self._detect_language(context)
            
            # 3. Get related code
            related_code = await self._get_related_code(context)
            
            # 4. Build prompt
            system_prompt, user_prompt = CodeGenerationTemplate.build(
                language=language,
                task=CodeTask.GENERATION,
                task_description=context.task_description,
                existing_code=related_code.get("main", ""),
                related_files=related_code.get("related", []),
                constraints=self._extract_constraints(context),
                requirements=self._extract_requirements(context),
                project_type=project_context.get("type", "General"),
                framework=project_context.get("framework", "Standard")
            )
            
            # 5. Call LLM
            response = await self.call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt
            )
            
            # 6. Extract code
            generated_code = self._extract_code(response["content"])
            
            # 7. Create files if needed
            files_created = []
            if context.files_to_modify:
                for file_path in context.files_to_modify:
                    await self.execute_tool(
                        "file",
                        operation="write",
                        path=file_path,
                        content=generated_code
                    )
                    files_created.append(file_path)
            
            # 8. Save to memory
            await self._save_to_memory(context, generated_code)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                status=AgentStatus.SUCCESS,
                message="Code generated successfully",
                data={
                    "generated_code": generated_code,
                    "language": language.value,
                    "files_created": files_created
                },
                artifacts=[
                    {
                        "type": "code",
                        "content": generated_code,
                        "language": language.value
                    }
                ],
                execution_time=execution_time,
                token_usage=response.get("usage", {})
            )
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return AgentResult(
                status=AgentStatus.FAILED,
                message=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _analyze_project(self, context: AgentContext) -> dict:
        """Analyze project structure"""
        
        try:
            structure = await self.execute_tool(
                "file",
                operation="tree",
                path=context.project_path
            )
            
            # Detect project type
            package_info = await self.execute_tool(
                "file",
                operation="read",
                path=f"{context.project_path}/package.json"
            )
            
            if package_info:
                return {"type": "Node.js/TypeScript", "framework": "Node.js"}
            
            pyproject = await self.execute_tool(
                "file",
                operation="read",
                path=f"{context.project_path}/pyproject.toml"
            )
            
            if pyproject:
                return {"type": "Python", "framework": "Python Standard"}
            
            return {"type": "General", "framework": "Standard"}
            
        except Exception:
            return {"type": "General", "framework": "Standard"}
    
    def _detect_language(self, context: AgentContext) -> CodeLanguage:
        """Detect programming language"""
        
        if context.files_to_modify:
            ext = Path(context.files_to_modify[0]).suffix
            lang_map = {
                ".py": CodeLanguage.PYTHON,
                ".ts": CodeLanguage.TYPESCRIPT,
                ".js": CodeLanguage.TYPESCRIPT,
                ".tsx": CodeLanguage.TYPESCRIPT,
                ".java": CodeLanguage.JAVA,
                ".go": CodeLanguage.GO,
                ".rs": CodeLanguage.RUST,
                ".cs": CodeLanguage.CSHARP
            }
            return lang_map.get(ext, CodeLanguage.PYTHON)
        
        return CodeLanguage.PYTHON
    
    async def _get_related_code(self, context: AgentContext) -> dict:
        """Get related code"""
        
        related = {"main": "", "related": []}
        
        try:
            search_results = await self.execute_tool(
                "file",
                operation="search",
                path=context.project_path,
                pattern=r"\.(py|ts|js|java|go)$"
            )
            
            if search_results:
                for result in search_results[:2]:
                    content = await self.execute_tool(
                        "file",
                        operation="read",
                        path=result["path"]
                    )
                    related["main"] = content
                    related["related"].append(result["path"])
                    
        except Exception as e:
            self.logger.warning(f"Could not fetch related code: {e}")
        
        return related
    
    def _extract_code(self, content: str) -> str:
        """Extract code from response"""
        
        pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            return max(matches, key=len).strip()
        
        return content.strip()
    
    def _extract_constraints(self, context: AgentContext) -> str:
        """Extract constraints"""
        
        constraints = []
        
        if "constraints" in context.additional_context:
            constraints.append(context.additional_context["constraints"])
        
        match = re.search(
            r'constraints?:\s*(.+?)(?:\n\n|$)', 
            context.task_description, 
            re.IGNORECASE
        )
        if match:
            constraints.append(match.group(1))
        
        return "\n".join(constraints) if constraints else "No specific constraints."
    
    def _extract_requirements(self, context: AgentContext) -> str:
        """Extract requirements"""
        return context.task_description
    
    async def _save_to_memory(self, context: AgentContext, code: str):
        """Save to memory system"""
        await self.memory.add(
            session_id=context.session_id,
            content={
                "task": context.task_description,
                "generated_code": code,
                "files": context.files_to_modify
            },
            memory_type="generation_history"
        )
