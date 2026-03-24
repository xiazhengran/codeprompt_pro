"""Code Generation Templates"""
from typing import Optional
from enum import Enum
from dataclasses import dataclass


class CodeLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    CSHARP = "csharp"


class CodeTask(Enum):
    GENERATION = "generation"
    REFACTORING = "refactoring"
    OPTIMIZATION = "optimization"
    COMPLETION = "completion"
    EXPLANATION = "explanation"


@dataclass
class CodeGenerationTemplate:
    """Code Generation Template"""

    system_prompt = """You are an expert {language} software engineer with deep knowledge of:
- Clean Code principles and best practices
- Design Patterns (GoF and Enterprise)
- {framework} framework conventions
- Test-Driven Development
- Security best practices

Your task is to generate high-quality, production-ready code following these principles:

## Quality Requirements
1. **Correctness**: Code must be functionally correct and handle edge cases
2. **Readability**: Clear naming, appropriate comments, logical structure
3. **Maintainability**: Low coupling, high cohesion, SOLID principles
4. **Performance**: Efficient algorithms and data structures
5. **Security**: Input validation, secure defaults, no vulnerabilities

## Output Format
Always provide:
1. Brief explanation of the approach
2. The complete, working code
3. Unit tests (if applicable)
4. Usage examples

## Code Style
- Follow {language} idiomatic patterns
- Use type hints where appropriate
- Include docstrings for public APIs
- Keep functions focused and small"""

    user_prompt_template = """## Task Description
{task_description}

## Context Information
### Project Type
{project_type}

### Existing Code
```{language}
{existing_code}
```

### Related Files
{related_files}

### Technical Constraints
{constraints}

## Requirements
{requirements}

## Output
Please generate the solution following the specified requirements and best practices."""

    @classmethod
    def build(
        cls,
        language: CodeLanguage,
        task: CodeTask,
        task_description: str,
        existing_code: str = "",
        related_files: list[str] = None,
        constraints: str = "",
        requirements: str = "",
        project_type: str = "General Application",
        framework: str = "Standard Library"
    ) -> tuple[str, str]:
        """Build complete prompt"""

        system_prompt = cls.system_prompt.format(
            language=language.value.title(),
            framework=framework
        )

        user_prompt = cls.user_prompt_template.format(
            language=language.value,
            task_description=task_description,
            project_type=project_type,
            existing_code=existing_code,
            related_files="\n".join(related_files or []),
            constraints=constraints,
            requirements=requirements
        )

        return system_prompt, user_prompt
