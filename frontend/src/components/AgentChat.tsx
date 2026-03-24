'use client';

import { useState } from 'react';

interface Agent {
  id: string;
  name: string;
  icon: string;
  description: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface AgentChatProps {
  agents: Agent[];
}

export function AgentChat({ agents }: AgentChatProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>('code');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/agents/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_type: selectedAgent,
          prompt: input,
          context: {},
        }),
      });

      const data = await response.json();
      const assistantMessage: Message = { 
        role: 'assistant', 
        content: data.result?.content || data.error || '发生错误' 
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', content: '请求失败，请检查后端服务' }]);
    } finally {
      setLoading(false);
    }
  };

  const currentAgent = agents.find((a) => a.id === selectedAgent);

  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden">
      <div className="bg-gray-900 p-4 border-b border-gray-800">
        <div className="flex gap-2 overflow-x-auto">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => setSelectedAgent(agent.id)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap ${
                selectedAgent === agent.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {agent.icon} {agent.name}
            </button>
          ))}
        </div>
      </div>

      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xl px-4 py-2 rounded-lg ${
                msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-800'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 px-4 py-2 rounded-lg animate-pulse">
              {currentAgent?.icon} 思考中...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={`向 ${currentAgent?.name} 提问...`}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}
