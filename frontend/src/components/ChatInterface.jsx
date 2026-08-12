import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Loader2, TrendingUp, Users, Package, PieChart, ArrowUp, Paperclip, X, FileSpreadsheet, Mic, Square } from 'lucide-react';
import MessageItem from './MessageItem';

export default function ChatInterface({ 
  messages, 
  onSendMessage,
  onStopRequest,
  onPinChart,
  onSampleClick
}) {
  const [input, setInput] = useState('');
  const [attachedFile, setAttachedFile] = useState(null); // { filename, table_name, status }
  const [isUploading, setIsUploading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleToggleVoice = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech Recognition is not supported by your browser. Please try Chrome or Edge.');
      return;
    }

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
        if (event.error === 'not-allowed') {
          alert('Microphone permission denied. Please allow microphone access in your browser settings.');
        }
      };

      recognition.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          setInput(prev => (prev ? `${prev} ${finalTranscript.trim()}` : finalTranscript.trim()));
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Speech recognition initialization error:", err);
      setIsListening(false);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (res.ok && data.status === 'success') {
        setAttachedFile({
          filename: file.filename || file.name,
          table_name: data.primary_table,
          rows: data.rows_imported
        });
      } else {
        alert(`Failed to attach file: ${data.detail || data.message || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Upload error:", err);
      alert("Error attaching file. Please make sure the backend server is running.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if ((!input.trim() && !attachedFile) || isUploading) return;
    
    // Stop active voice listening if submitting
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    const text = input.trim() || `Analyze the attached file '${attachedFile?.filename}'`;
    onSendMessage(text, attachedFile);
    
    setInput('');
    setAttachedFile(null);
  };

  const simplePromptCards = [
    {
      title: "Sales Trends",
      query: "Show me the monthly sales revenue trend over the last year",
      description: "Analyze monthly revenue momentum & order count",
      icon: <TrendingUp size={18} className="text-indigo-600" />,
      bg: "bg-indigo-50/70 border-indigo-100 hover:border-indigo-300"
    },
    {
      title: "Top Customers",
      query: "Show me our top customers by total amount spent",
      description: "Identify high-value client tiers and spending",
      icon: <Users size={18} className="text-emerald-600" />,
      bg: "bg-emerald-50/70 border-emerald-100 hover:border-emerald-300"
    },
    {
      title: "Inventory Health",
      query: "Show me low inventory stock items and restock levels",
      description: "Spot stock bottlenecks before they impact sales",
      icon: <Package size={18} className="text-amber-600" />,
      bg: "bg-amber-50/70 border-amber-100 hover:border-amber-300"
    },
    {
      title: "Category Breakdown",
      query: "What is the revenue breakdown across product categories?",
      description: "Market share distribution per category",
      icon: <PieChart size={18} className="text-purple-600" />,
      bg: "bg-purple-50/70 border-purple-100 hover:border-purple-300"
    }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-3xl mx-auto space-y-6">
            <div className="p-4 rounded-3xl bg-indigo-50 border border-indigo-100 text-indigo-600 shadow-sm">
              <Sparkles size={44} className="animate-bounce" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-slate-800">
                Welcome back! I'm your AI Data Analyst companion.
              </h2>
              <p className="text-sm text-slate-600 max-w-lg mx-auto leading-relaxed">
                What insights are we exploring today? Choose a prompt card, ask a question, or attach your own dataset files below!
              </p>
            </div>

            {/* Simple Prompt Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full pt-2">
              {simplePromptCards.map((card, idx) => (
                <button
                  key={idx}
                  onClick={() => onSampleClick(card.query)}
                  className={`p-5 rounded-3xl border ${card.bg} text-left transition-all group shadow-sm hover:shadow-md flex items-start space-x-3.5`}
                >
                  <div className="p-2.5 rounded-2xl bg-white shadow-sm shrink-0 mt-0.5">
                    {card.icon}
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-slate-800 group-hover:text-indigo-600 transition-colors">
                      {card.title}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1 leading-snug">
                      {card.description}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {messages.map((msg, idx) => (
              <MessageItem 
                key={msg.id || idx} 
                message={msg} 
                onPinChart={onPinChart}
                onFollowupClick={(q) => onSendMessage(q)}
                onStopRequest={onStopRequest}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input & Attachment Composer Bar */}
      <div className="p-4 border-t border-slate-200/80 bg-white shadow-lg shadow-slate-200/50 space-y-2">
        {/* Attachment Badge */}
        {attachedFile && (
          <div className="max-w-4xl mx-auto flex items-center justify-between px-3.5 py-1.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-medium">
            <div className="flex items-center space-x-2">
              <FileSpreadsheet size={15} className="text-indigo-600" />
              <span className="font-bold">{attachedFile.filename}</span>
              <span className="text-indigo-600 text-[11px]">({attachedFile.rows} rows imported)</span>
            </div>
            <button
              type="button"
              onClick={() => setAttachedFile(null)}
              aria-label="Remove attachment"
              title="Remove attachment"
              className="p-1 rounded-lg hover:bg-indigo-100 text-indigo-600"
            >
              <X size={14} />
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-center space-x-2">
          {/* File Attachment Hidden Input */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".xlsx,.xls,.csv,.json,.md,.txt,.log,.pdf,.docx,.doc"
            className="hidden"
          />

          {/* LEFT: Paperclip Attachment Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            aria-label="Attach file"
            title="Attach Excel (.xlsx), CSV, JSON, Markdown, PDF, or Word data file"
            className="p-3.5 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-indigo-600 border border-slate-200 transition-all flex items-center justify-center shrink-0 disabled:opacity-50"
          >
            {isUploading ? <Loader2 size={18} className="animate-spin text-indigo-600" /> : <Paperclip size={18} />}
          </button>

          {/* CENTER: Textarea / Input Text */}
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                isListening
                  ? "Listening... speak now"
                  : attachedFile
                  ? `Ask a question about '${attachedFile.filename}'...`
                  : "Ask your data analyst companion or attach Excel, CSV, JSON, PDF, or Word file..."
              }
              aria-label="Chat query input"
              className={`w-full px-5 py-3.5 rounded-2xl bg-slate-50 border text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:bg-white transition-all shadow-inner ${
                isListening ? 'border-rose-300 ring-2 ring-rose-100 bg-rose-50/30' : 'border-slate-200 focus:border-indigo-500'
              }`}
            />
          </div>

          {/* RIGHT: Voice Button & Send Button */}
          <button
            type="button"
            onClick={handleToggleVoice}
            aria-label={isListening ? "Stop voice input" : "Start voice input"}
            title={isListening ? "Stop voice input" : "Start voice input"}
            className={`p-3.5 rounded-2xl transition-all flex items-center justify-center shrink-0 border ${
              isListening
                ? 'bg-rose-500 hover:bg-rose-600 text-white border-rose-600 animate-pulse shadow-md shadow-rose-500/30'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600 hover:text-indigo-600 border-slate-200'
            }`}
          >
            {isListening ? <Square size={18} className="fill-white stroke-none" /> : <Mic size={18} />}
          </button>

          <button
            type="submit"
            disabled={(!input.trim() && !attachedFile) || isUploading}
            aria-label="Send message"
            title="Send message"
            className="p-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white shadow-md shadow-indigo-500/30 transition-all flex items-center justify-center shrink-0"
          >
            <ArrowUp size={18} className="stroke-[2.5]" />
          </button>
        </form>
      </div>
    </div>
  );
}
