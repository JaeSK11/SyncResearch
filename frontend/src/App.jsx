import { useState, useEffect, useRef } from 'react';
import { Upload, Send, FileText, CheckCircle, XCircle, Loader } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE

export default function ResearchRAG() {
  const [papers, setPapers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState({ minio: 'unknown', chromadb: 'unknown', vllm: 'unknown' });
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    checkHealth();
    loadPapers();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setApiStatus(data.services || {});
    } catch (err) {
      console.error('Health check failed:', err);
    }
  };

  const loadPapers = async () => {
    try {
      const res = await fetch(`${API_BASE}/papers`);
      const data = await res.json();
      setPapers(data.papers || []);
    } catch (err) {
      console.error('Failed to load papers:', err);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/papers/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (res.ok) {
        await loadPapers();
        setMessages(prev => [...prev, {
          type: 'system',
          content: `Successfully uploaded "${file.name}"`,
          timestamp: new Date()
        }]);
      } else {
        throw new Error('Upload failed');
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: `Failed to upload "${file.name}": ${err.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleQuery = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { type: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    const question = input;
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/query/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, n_results: 5 }),
      });

      const data = await res.json();
      
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        confidence: data.confidence,
        timestamp: new Date()
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: `Query failed: ${err.message}`,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuery();
    }
  };

  const StatusIndicator = ({ status }) => {
    if (status === 'connected') return <CheckCircle className="icon icon-sm icon-green" />;
    if (status === 'disconnected') return <XCircle className="icon icon-sm icon-red" />;
    return <div className="status-dot" />;
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-content">
          <div className="header-title">
            <h1>Research RAG</h1>
            <p>Multi-paper analysis system</p>
          </div>
          <div className="status-indicators">
            <div className="status-item">
              <StatusIndicator status={apiStatus.minio} />
              <span>Storage</span>
            </div>
            <div className="status-item">
              <StatusIndicator status={apiStatus.chromadb} />
              <span>VectorDB</span>
            </div>
            <div className="status-item">
              <StatusIndicator status={apiStatus.vllm} />
              <span>LLM</span>
            </div>
          </div>
        </div>
      </header>

      <div className="main-layout">
        <aside className="sidebar">
          <div className="sidebar-header">
            <h2>Research Papers</h2>
            <label className="upload-button">
              {uploading ? (
                <>
                  <Loader className="icon spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <Upload className="icon" />
                  <span>Upload PDF</span>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleUpload}
                className="hidden"
                disabled={uploading}
              />
            </label>
          </div>

          <div className="papers-list">
            {papers.length === 0 ? (
              <p className="no-papers">No papers uploaded yet</p>
            ) : (
              papers.map((paper) => (
                <div key={paper.paper_id} className="paper-item">
                  <div className="paper-content">
                    <FileText className="icon icon-blue" />
                    <div className="paper-info">
                      <p className="paper-title">
                        {paper.title !== "Unknown" ? paper.title : paper.paper_id}
                      </p>
                      {paper.num_chunks > 0 && (
                        <p className="paper-chunks">{paper.num_chunks} chunks</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        <main className="chat-container">
          <div className="messages-area">
            {messages.length === 0 ? (
              <div className="empty-state">
                <h3>Ask questions about your research papers</h3>
                <p>Upload PDFs and start querying across multiple papers</p>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} className={`message-wrapper ${msg.type}`}>
                  <div className={`message ${msg.type}`}>
                    <p className="message-text">{msg.content}</p>
                    
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="message-sources">
                        <p className="sources-title">Sources:</p>
                        <div>
                          {msg.sources.map((source, i) => (
                            <p key={i} className="source-item">
                              • {source.paper_id || 'Unknown'} - {source.section || 'General'}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}

                    {msg.confidence !== undefined && (
                      <p className="message-confidence">
                        Confidence: {(msg.confidence * 100).toFixed(0)}%
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <div className="input-container">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your papers..."
                className="input-field"
                disabled={loading}
              />
              <button
                onClick={handleQuery}
                disabled={loading || !input.trim()}
                className="send-button"
              >
                {loading ? (
                  <Loader className="icon spin" />
                ) : (
                  <Send className="icon" />
                )}
                <span>Send</span>
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}