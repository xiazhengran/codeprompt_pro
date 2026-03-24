'use client';

import { AgentChat } from '@/components/AgentChat';

const AGENTS = [
  { id: 'code', name: '代码助手', icon: '💻', description: '生成、编辑和优化代码' },
  { id: 'review', name: '代码审查', icon: '🔍', description: '审查代码质量和安全性' },
  { id: 'test', name: '测试生成', icon: '🧪', description: '生成单元测试和集成测试' },
  { id: 'debug', name: '调试助手', icon: '🐛', description: '定位和修复代码问题' },
  { id: 'design', name: '架构设计', icon: '🏗️', description: '系统架构和设计方案' },
  { id: 'doc', name: '文档生成', icon: '📝', description: '生成代码文档和注释' },
];

export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-2">CodePrompt Pro</h1>
        <p className="text-gray-400 text-center mb-8">AI 驱动的编程助手</p>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          {AGENTS.map((agent) => (
            <div key={agent.id} className="agent-card">
              <div className="text-3xl mb-2">{agent.icon}</div>
              <h2 className="text-lg font-semibold">{agent.name}</h2>
              <p className="text-sm text-gray-400">{agent.description}</p>
            </div>
          ))}
        </div>
        
        <AgentChat agents={AGENTS} />
      </div>
    </main>
  );
}
