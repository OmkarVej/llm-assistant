import React, { useState, useRef, useEffect } from 'react'
import './App.css'
import a2zLogo from './assets/a2Z-lime-logo.webp'

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your A2Z Assistant. How can I help you today?' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [useLocal, setUseLocal] = useState(false)
  const [useRag, setUseRag] = useState(true)
  const [showSettings, setShowSettings] = useState(false)
  const [maxTokens, setMaxTokens] = useState(2000)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function sendMessage(e) {
    e?.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: userMessage,
          use_local: useLocal,
          use_rag: useRag,
          save_to_db: true,
          max_new_tokens: maxTokens
        })
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      
      // Add assistant response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || 'Sorry, I couldn\'t generate a response.',
        sources: data.sources
      }])
    } catch (error) {
      console.error('Error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${error.message}. Please make sure the backend is running.`,
        isError: true
      }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  function clearChat() {
    setMessages([
      { role: 'assistant', content: 'Chat cleared. How can I help you?' }
    ])
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-title">
            <span className="logo">
              <img src={a2zLogo} alt="A2Z Logo" className="logo-img" />
            </span>
            AI Assistant
          </h1>
          <button className="new-chat-btn" onClick={clearChat} title="New Chat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            <span>New Chat</span>
          </button>
        </div>

        <div className="sidebar-content">
          <div className="chat-history">
            <div className="history-item active">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span>Current Chat</span>
            </div>
          </div>
        </div>

        <div className="sidebar-footer">
          <button 
            className="settings-btn"
            onClick={() => setShowSettings(!showSettings)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v6m0 6v6M6 12H1m6 0h6m6 0h5"/>
            </svg>
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="main">
        {/* Settings Panel */}
        {showSettings && (
          <div className="settings-panel">
            <div className="settings-header">
              <h3>Settings</h3>
              <button className="close-btn" onClick={() => setShowSettings(false)}>×</button>
            </div>
            <div className="settings-content">
              <div className="setting-item">
                <label>
                  <input
                    type="checkbox"
                    checked={useLocal}
                    onChange={e => setUseLocal(e.target.checked)}
                  />
                  <span>Use Local Model</span>
                </label>
                <p className="setting-desc">Run inference locally instead of using external API</p>
              </div>
              <div className="setting-item">
                <label>
                  <input
                    type="checkbox"
                    checked={useRag}
                    onChange={e => setUseRag(e.target.checked)}
                  />
                  <span>Use RAG Search</span>
                </label>
                <p className="setting-desc">Search knowledge base (Confluence, Jira, docs) for context</p>
              </div>
              <div className="setting-item">
                <label htmlFor="maxTokens">
                  <span>Response Length (Max Tokens)</span>
                </label>
                <input
                  id="maxTokens"
                  type="range"
                  min="500"
                  max="4000"
                  step="100"
                  value={maxTokens}
                  onChange={e => setMaxTokens(parseInt(e.target.value))}
                  className="slider"
                />
                <div className="slider-value">{maxTokens} tokens</div>
                <p className="setting-desc">Controls how long the AI response can be. Higher = longer responses.</p>
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">
                <div className="message-avatar">
                  {msg.role === 'user' ? (
                    <div className="avatar-user">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
                      </svg>
                    </div>
                  ) : (
                    <div className="avatar-assistant">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                      </svg>
                    </div>
                  )}
                </div>
                <div className="message-text">
                  <div className="message-role">
                    {msg.role === 'user' ? 'You' : 'A2Z Assistant'}
                  </div>
                  <div className={`message-body ${msg.isError ? 'error' : ''}`}>
                    {msg.content}
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="message-sources">
                      <div className="sources-title">📚 Sources:</div>
                      {msg.sources.map((source, i) => (
                        <div key={i} className="source-item">
                          {source}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="message-avatar">
                  <div className="avatar-assistant">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                  </div>
                </div>
                <div className="message-text">
                  <div className="message-role">A2Z Assistant</div>
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <form onSubmit={sendMessage} className="input-form">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message A2Z Assistant..."
              rows={1}
              disabled={loading}
              className="input-field"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="send-btn"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
            </button>
          </form>
          <div className="input-footer">
            <span className="model-indicator">
              {useLocal ? '🖥️ Local' : '☁️ Cloud'} · {useRag ? '📚 RAG Enabled' : '📝 No RAG'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
