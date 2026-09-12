import React, { useState, useEffect } from 'react';
import { Satellite, Radio, ShieldCheck, Cpu, Bot } from 'lucide-react';

export default function Header({ backendStatus, llmStatus }) {
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentTime(now.toUTCString().replace('GMT', 'UTC'));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const getLlmBadge = () => {
    if (!llmStatus) return { label: 'LLM: CHECKING...', color: '#64748B', title: 'Connecting to reasoning engine' };
    if (llmStatus.ollama?.available && llmStatus.ollama?.selected_model) {
      return {
        label: `LLM: OLLAMA (${llmStatus.ollama.selected_model.toUpperCase()})`,
        color: '#10B981',
        title: `Connected to local Ollama at ${llmStatus.ollama.url}`
      };
    }
    if (llmStatus.gemini_configured) {
      return {
        label: 'LLM: GEMINI 1.5 FLASH',
        color: '#10B981',
        title: 'Cloud Google Gemini vision-language reasoning active'
      };
    }
    return {
      label: 'LLM: LOCAL PHYSICS',
      color: '#F59E0B',
      title: "Grounded remote-sensing radiometric reasoning active. To enable local LLM, start Ollama ('ollama run llama3')."
    };
  };

  const llmInfo = getLlmBadge();

  return (
    <header className="top-nav">
      <div className="nav-brand">
        <div className="nav-logo-icon">
          <Satellite size={20} />
        </div>
        <div>
          <div className="nav-title">SATQUERY AI</div>
          <div className="nav-subtitle">ISRO PS-26167 • Multimodal Vision-Language Assistant</div>
        </div>
      </div>

      <div className="telemetry-badges">
        <div className="telemetry-badge">
          <span className="radar-pulse"></span>
          <span style={{ color: '#10B981' }}>AGENT ONLINE</span>
        </div>

        <div className="telemetry-badge" title={llmInfo.title}>
          <Bot size={14} style={{ color: llmInfo.color }} />
          <span style={{ color: llmInfo.color }}>{llmInfo.label}</span>
        </div>

        <div className="telemetry-badge mono" style={{ color: '#94A3B8' }}>
          <Radio size={14} style={{ color: '#10B981' }} />
          <span>{currentTime || 'SYNCHRONIZING...'}</span>
        </div>

        <div className="telemetry-badge">
          <Cpu size={14} style={{ color: '#F59E0B' }} />
          <span>PIPELINE: {backendStatus ? 'ACTIVE' : 'CONNECTING...'}</span>
        </div>
      </div>
    </header>
  );
}
