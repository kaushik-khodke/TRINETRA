import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ImageViewer from './components/ImageViewer';
import ResultCard from './components/ResultCard';
import TraceViewer from './components/TraceViewer';

export default function App() {
  const [inputMode, setInputMode] = useState('single');
  const [files, setFiles] = useState([]);
  const [query, setQuery] = useState('What are the predominant land-cover types and is there any water body present?');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [backendStatus, setBackendStatus] = useState(false);
  const [llmStatus, setLlmStatus] = useState(null);
  const [presets, setPresets] = useState([]);

  const refreshSystemStatus = () => {
    // Health & LLM Status
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus(true);
        if (data.llm_status) setLlmStatus(data.llm_status);
      })
      .catch(() => setBackendStatus(false));

    fetch('/api/v1/llm-status')
      .then((res) => res.json())
      .then((data) => setLlmStatus(data))
      .catch((err) => console.warn('Could not fetch LLM status:', err));

    fetch('/api/v1/samples')
      .then((res) => res.json())
      .then((data) => setPresets(data))
      .catch((err) => console.warn('Could not fetch presets:', err));
  };

  useEffect(() => {
    refreshSystemStatus();
    const timer = setInterval(refreshSystemStatus, 15000); // Heartbeat check every 15s
    return () => clearInterval(timer);
  }, []);

  const handleFilesChange = (newFiles) => {
    setFiles(newFiles);
    // Reset previous result so old analysis and old imagery are never displayed with new files
    setResult(null);
  };

  const handleAnalyze = async () => {
    if (files.length === 0 || !query.trim()) return;
    setLoading(true);

    try {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      formData.append('query', query);
      formData.append('input_mode', inputMode);

      const res = await fetch('/api/v1/analyze', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.error || `Analysis error (HTTP ${res.status})`);
      }
      setResult(data);
    } catch (err) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunPreset = async (sampleId) => {
    setLoading(true);
    setFiles([]); // Clear local staged files
    setResult(null); // Clear previous result

    const targetPreset = presets.find((p) => p.id === sampleId);
    if (targetPreset) {
      setInputMode(targetPreset.mode);
      setQuery(targetPreset.query);
    }

    try {
      const formData = new FormData();
      formData.append('sample_id', sampleId);

      const res = await fetch('/api/v1/analyze-preset', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.error || `Preset error (HTTP ${res.status})`);
      }
      setResult(data);
    } catch (err) {
      alert(`Preset analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Header backendStatus={backendStatus} llmStatus={llmStatus} />

      <main className="main-layout">
        <UploadZone
          inputMode={inputMode}
          setInputMode={(mode) => {
            setInputMode(mode);
            setFiles([]);
            setResult(null);
          }}
          files={files}
          setFiles={handleFilesChange}
          query={query}
          setQuery={setQuery}
          onAnalyze={handleAnalyze}
          loading={loading}
          presets={presets}
          onRunPreset={handleRunPreset}
        />

        <div className="canvas-panel">
          <ImageViewer result={result} loading={loading} stagedFiles={files} />
          <ResultCard result={result} />
        </div>

        <TraceViewer trace={result?.execution_trace} />
      </main>
    </div>
  );
}
