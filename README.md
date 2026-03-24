# CodePrompt Pro

企业级 Vibe Coding Prompt Agent 系统

## 项目概述

CodePrompt Pro 是一个企业级 AI 编程助手系统，通过多个专业化的 AI Agent 协同工作，帮助开发者提升编程效率。系统采用模块化架构设计，支持多种 LLM 提供商，提供完整的工具集成和内存管理能力。

## 核心特性

### 🤖 多 Agent 协作系统

系统内置多种专业化 Agent，每个 Agent 针对特定任务进行了优化：

- **Code Agent** - 代码生成与重构专家
- **Review Agent** - 代码审查与质量分析
- **Test Agent** - 自动化测试生成
- **Debug Agent** - 智能问题诊断与修复
- **Design Agent** - 架构设计与模式建议
- **Doc Agent** - 文档生成与维护

### 🏗️ 系统架构

```
codeprompt_pro/
├── src/
│   ├── agents/              # Agent 模块
│   │   ├── base/           # 基础 Agent 类
│   │   ├── code_agent.py   # 代码生成 Agent
│   │   └── factory.py      # Agent 工厂
│   ├── api/                 # API 层
│   │   ├── main.py         # FastAPI 应用入口
│   │   └── routes/         # API 路由
│   ├── llm/                 # LLM 网关
│   │   ├── llm_gateway.py  # LLM 统一接口
│   │   └── providers/      # LLM 提供商实现
│   ├── memory/              # 内存管理
│   │   └── memory_manager.py
│   ├── prompts/             # Prompt 模板
│   │   └── templates/       # 模板实现
│   └── tools/               # 工具注册表
│       └── registry.py
├── frontend/                # Next.js 前端
│   ├── src/
│   │   ├── app/            # 应用页面
│   │   └── components/      # React 组件
│   ├── package.json
│   └── tailwind.config.js
├── backend/                 # 后端配置
├── Dockerfile              # 容器镜像
├── docker-compose.yml       # 容器编排
└── pyproject.toml          # Python 项目配置
```

### 🔌 LLM 提供商支持

通过统一的 LLM 网关，系统支持多种 LLM 提供商：

- OpenAI (GPT-4, GPT-3.5-turbo)
- Anthropic Claude
- 本地模型 (Ollama, LM Studio)
- 自定义 API 端点

### 🛠️ 工具集成

Agent 可以调用多种工具完成任务：

- **代码执行** - 安全地运行代码片段
- **文件系统** - 读取、写入、搜索代码文件
- **Git 操作** - 版本控制操作
- **Web 搜索** - 获取外部信息
- **终端命令** - 执行系统命令

### 💾 内存管理

智能对话上下文管理：

- **短期记忆** - 当前会话上下文
- **长期记忆** - 跨会话知识持久化
- **向量存储** - 语义检索能力
- **对话摘要** - 自动压缩历史记录

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (可选)

### 安装

#### 1. 克隆项目

```bash
git clone https://github.com/xiazhengran/codeprompt_pro.git
cd codeprompt_pro
```

#### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件配置 LLM API：

```env
# OpenAI 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# 或 Anthropic 配置
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
```

#### 3. 安装后端依赖

```bash
pip install -e .
```

或使用 uv：

```bash
uv sync
```

#### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 运行

#### 开发模式

**后端：**

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**

```bash
cd frontend
npm run dev
```

访问 http://localhost:3000 查看前端界面。

#### Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## API 文档

启动后端服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口

#### Agent 对话

```http
POST /api/agents/chat
Content-Type: application/json

{
  "agent_type": "code",
  "message": "帮我创建一个用户认证模块",
  "context": {}
}
```

#### 获取 Agent 列表

```http
GET /api/agents
```

#### 切换 Agent

```http
POST /api/agents/switch
Content-Type: application/json

{
  "agent_type": "review"
}
```

#### 健康检查

```http
GET /health
```

## 配置说明

### Agent 配置

在 `src/agents/` 目录下可以配置各 Agent 的行为：

- `temperature` - 生成温度
- `max_tokens` - 最大输出 token 数
- `system_prompt` - 系统提示词

### LLM 配置

在 `src/llm/providers/` 下添加新的 LLM 提供商：

```python
class CustomProvider(BaseLLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # 实现自定义逻辑
        pass
```

### 工具配置

在 `src/tools/registry.py` 中注册新工具：

```python
@tool_registry.register
def custom_tool(param1: str) -> str:
    """自定义工具描述"""
    return result
```

## 开发指南

### 项目结构

```
src/
├── agents/          # Agent 核心逻辑
├── api/            # REST API
├── llm/            # LLM 集成
├── memory/         # 内存管理
├── prompts/        # Prompt 模板
└── tools/          # 工具集
```

### 添加新 Agent

1. 继承 `BaseAgent` 类
2. 实现核心方法
3. 在 `factory.py` 中注册

```python
from src.agents.base.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    name = "custom"
    description = "自定义 Agent"
    
    async def process(self, input_text: str) -> str:
        # 实现处理逻辑
        pass
```

### 添加新工具

1. 在 `src/tools/registry.py` 中定义工具
2. 使用 `@tool_registry.register` 装饰器
3. 在 Agent 中调用

### 测试

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=src tests/
```

## 技术栈

### 后端

- **FastAPI** - 高性能 Web 框架
- **Pydantic** - 数据验证
- **httpx** - 异步 HTTP 客户端
- **langchain** - LLM 应用框架
- **chromadb** - 向量数据库

### 前端

- **Next.js 14** - React 框架
- **React 18** - UI 库
- **Tailwind CSS 3** - 样式框架
- **TypeScript** - 类型安全

### 基础设施

- **Docker** - 容器化
- **Docker Compose** - 服务编排
- **uv** - Python 包管理

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

## 联系方式

- GitHub Issues: https://github.com/xiazhengran/codeprompt_pro/issues
- 邮箱: xiazhengran@example.com

## 致谢

感谢所有为该项目做出贡献的开发者！
