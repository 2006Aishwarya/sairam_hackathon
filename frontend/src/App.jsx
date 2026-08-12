import React, { useState, useRef, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import SettingsModal from './components/SettingsModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'dashboard'
  const [messages, setMessages] = useState([]);
  const abortControllersRef = useRef({});
  const [pinnedCharts, setPinnedCharts] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isReseeding, setIsReseeding] = useState(false);
  const [isDark, setIsDark] = useState(() => localStorage.getItem('theme') === 'dark');

  const [currentSessionId, setCurrentSessionId] = useState(() => {
    return localStorage.getItem('current_session_id') || `session_${Date.now()}`;
  });
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  const fetchHistorySessions = async () => {
    try {
      const res = await fetch('/api/history');
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error("Failed to load history sessions from API:", err);
      const localMap = JSON.parse(localStorage.getItem('chat_messages_map') || '{}');
      const localSessions = Object.keys(localMap).map(id => ({
        session_id: id,
        title: localMap[id].find(m => m.role === 'user')?.content.slice(0, 30) || 'Chat Session',
        updated_at: 'Local',
        message_count: localMap[id].length
      }));
      setSessions(localSessions);
    }
  };

  // Fetch all saved history sessions on mount
  useEffect(() => {
    fetchHistorySessions();
  }, []);

  // Load active session messages whenever currentSessionId changes
  useEffect(() => {
    if (!currentSessionId) return;
    localStorage.setItem('current_session_id', currentSessionId);
    
    const loadSessionMessages = async () => {
      try {
        const res = await fetch(`/api/history/${currentSessionId}`);
        if (res.ok) {
          const data = await res.json();
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages);
            return;
          }
        }
      } catch (err) {
        console.error("Error loading session from API:", err);
      }
      const localMap = JSON.parse(localStorage.getItem('chat_messages_map') || '{}');
      if (localMap[currentSessionId]) {
        setMessages(localMap[currentSessionId]);
      } else {
        setMessages([]);
      }
    };

    loadSessionMessages();
  }, [currentSessionId]);

  // Save current messages to active session whenever messages change
  useEffect(() => {
    if (!currentSessionId || messages.length === 0) return;

    const localMap = JSON.parse(localStorage.getItem('chat_messages_map') || '{}');
    localMap[currentSessionId] = messages;
    localStorage.setItem('chat_messages_map', JSON.stringify(localMap));

    const firstUserMsg = messages.find(m => m.role === 'user');
    const title = firstUserMsg ? (firstUserMsg.content.length > 35 ? firstUserMsg.content.slice(0, 35) + '...' : firstUserMsg.content) : 'New Chat';

    const saveToApi = async () => {
      try {
        await fetch('/api/history', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: currentSessionId,
            title: title,
            messages: messages.filter(m => !m.isPending)
          })
        });
        fetchHistorySessions();
      } catch (err) {
        console.error("Error saving session to API:", err);
      }
    };

    const timer = setTimeout(saveToApi, 1000);
    return () => clearTimeout(timer);
  }, [messages, currentSessionId]);

  const handleToggleTheme = () => {
    setIsDark(prev => !prev);
  };

  const handleStopRequest = (requestId) => {
    const controller = abortControllersRef.current[requestId];
    if (controller) {
      controller.abort();
      delete abortControllersRef.current[requestId];
    }
    setMessages(prev => prev.map(m => {
      if (m.requestId === requestId && m.role === 'assistant') {
        return {
          ...m,
          isPending: false,
          isStopped: true,
          processingStatus: '',
          content: m.content || 'Request stopped.'
        };
      }
      return m;
    }));
  };

  const handleSendMessage = async (text, attachedFile = null) => {
    if (!text || !text.trim()) return;

    const reqId = `req_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMsg = {
      id: `${reqId}_user`,
      requestId: reqId,
      role: 'user',
      content: text,
      attached_file_name: attachedFile ? attachedFile.filename : null,
      timestamp: timeStr
    };

    const assistantMsgPlaceholder = {
      id: `${reqId}_assistant`,
      requestId: reqId,
      role: 'assistant',
      isPending: true,
      processingStatus: 'Connecting to AI Data Analyst Engine...',
      content: '',
      model_badge: null,
      data_source: null,
      tools_called: [],
      sql_info: null,
      chart: null,
      flowchart: null,
      insights: null,
      timestamp: timeStr
    };

    // Prepare history snapshot of prior completed turns for context
    const historySnapshot = messages
      .filter(m => !m.isPending && !m.isStopped)
      .map(m => ({ role: m.role, content: m.content, sql_info: m.sql_info }));

    setMessages(prev => [...prev, userMsg, assistantMsgPlaceholder]);

    const controller = new AbortController();
    abortControllersRef.current[reqId] = controller;

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          request_id: reqId,
          message: text,
          history: historySnapshot,
          attached_table: attachedFile ? attachedFile.table_name : null,
          attached_file_name: attachedFile ? attachedFile.filename : null
        })
      });

      if (!response.ok || !response.body) {
        // Fallback REST endpoint
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
          body: JSON.stringify({
            request_id: reqId,
            message: text,
            history: historySnapshot,
            attached_table: attachedFile ? attachedFile.table_name : null,
            attached_file_name: attachedFile ? attachedFile.filename : null
          })
        });
        const data = await res.json();
        setMessages(prev => prev.map(m => {
          if (m.requestId === reqId && m.role === 'assistant') {
            return {
              ...m,
              ...data,
              isPending: false,
              processingStatus: ''
            };
          }
          return m;
        }));
        return;
      }

      // Read real Server-Sent Events (SSE) stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed = JSON.parse(line.replace('data: ', ''));
              const targetReqId = parsed.request_id || reqId;

              if (parsed.event === 'stage') {
                setMessages(prev => prev.map(m => {
                  if (m.requestId === targetReqId && m.role === 'assistant') {
                    return { ...m, processingStatus: parsed.label || 'Processing...' };
                  }
                  return m;
                }));
              } else if (parsed.event === 'complete' && parsed.data) {
                setMessages(prev => prev.map(m => {
                  if (m.requestId === targetReqId && m.role === 'assistant') {
                    return {
                      ...m,
                      ...parsed.data,
                      isPending: false,
                      processingStatus: ''
                    };
                  }
                  return m;
                }));
              }
            } catch (err) {
              console.error("SSE parse error:", err);
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setMessages(prev => prev.map(m => {
          if (m.requestId === reqId && m.role === 'assistant') {
            return {
              ...m,
              isPending: false,
              isStopped: true,
              processingStatus: '',
              content: m.content || 'Request stopped.'
            };
          }
          return m;
        }));
      } else {
        console.error("Chat API streaming error:", err);
        setMessages(prev => prev.map(m => {
          if (m.requestId === reqId && m.role === 'assistant') {
            return {
              ...m,
              isPending: false,
              processingStatus: '',
              content: 'An error occurred while communicating with the analyst backend. Please make sure the backend server is running.'
            };
          }
          return m;
        }));
      }
    } finally {
      delete abortControllersRef.current[reqId];
    }
  };

  const handlePinChart = (spec) => {
    setPinnedCharts(prev => {
      if (prev.some(c => c.title === spec.title)) return prev;
      return [...prev, spec];
    });
  };

  const handleUnpinChart = (index) => {
    setPinnedCharts(prev => prev.filter((_, i) => i !== index));
  };

  const handleNewChat = () => {
    Object.values(abortControllersRef.current).forEach(ctrl => ctrl.abort());
    abortControllersRef.current = {};
    const newId = `session_${Date.now()}`;
    setCurrentSessionId(newId);
    setMessages([]);
  };

  const handleSelectSession = (sessionId) => {
    if (sessionId === currentSessionId) return;
    Object.values(abortControllersRef.current).forEach(ctrl => ctrl.abort());
    abortControllersRef.current = {};
    setCurrentSessionId(sessionId);
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await fetch(`/api/history/${sessionId}`, { method: 'DELETE' });
    } catch (err) {
      console.error("Error deleting session:", err);
    }
    const localMap = JSON.parse(localStorage.getItem('chat_messages_map') || '{}');
    delete localMap[sessionId];
    localStorage.setItem('chat_messages_map', JSON.stringify(localMap));

    setSessions(prev => prev.filter(s => s.session_id !== sessionId));

    if (currentSessionId === sessionId) {
      handleNewChat();
    }
  };

  const handleReseedDb = async () => {
    setIsReseeding(true);
    try {
      await fetch('/api/seed', { method: 'POST' });
      alert("Database successfully re-seeded with fresh sample data!");
    } catch (err) {
      console.error("Reseed failed:", err);
    } finally {
      setIsReseeding(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 text-slate-900 antialiased">
      {/* Navigation Sidebar */}
      <Sidebar 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onSampleClick={(q) => {
          setActiveTab('chat');
          handleSendMessage(q);
        }}
        onNewChat={handleNewChat}
        currentSessionId={currentSessionId}
        sessions={sessions}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        pinnedCount={pinnedCharts.length}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Header 
          onReseedDb={handleReseedDb}
          isReseeding={isReseeding}
          isDark={isDark}
          onToggleTheme={handleToggleTheme}
        />

        {activeTab === 'chat' ? (
          <ChatInterface 
            messages={messages}
            onSendMessage={handleSendMessage}
            onStopRequest={handleStopRequest}
            onPinChart={handlePinChart}
            onSampleClick={handleSendMessage}
          />
        ) : (
          <Dashboard 
            pinnedCharts={pinnedCharts}
            onUnpin={handleUnpinChart}
            onSwitchToChat={() => setActiveTab('chat')}
          />
        )}
      </div>

      {/* Settings Drawer */}
      <SettingsModal 
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}
