/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useRef, useEffect } from "react";
import { useAppStore } from "../state/store";
import { 
  Sparkles, Send, Brain, ArrowDownCircle, RefreshCw, Layers, Terminal 
} from "lucide-react";

export default function AIAssistantTab() {
  const { chatMessages, addChatMessage } = useAppStore();
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const activeChat = chatMessages.global || [
    { id: "msg-0", role: "assistant", content: "Hello! I am your TriVerse ML expert Native AI Copilot. Let's inspect model latency curves, tune learning rates, or explore loss convergence natively!", timestamp: new Date().toISOString() }
  ];

  const suggestedQueries = [
    "How do I reduce my deep model's inference latency?",
    "Analyze the correlation score between applicant debt and delinquencies.",
    "Recommend tuning rates for Optuna ADAMW training runs."
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeChat]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || loading) return;
    
    // Add user message locally
    addChatMessage("global", "user", textToSend);
    setInputValue("");
    setLoading(true);

    try {
      const token = localStorage.getItem("token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      // Connect to native fullstack post proxy
      const response = await fetch("/api/chat", {
        method: "POST",
        headers,
        body: JSON.stringify({ 
          message: textToSend
        })
      });

      if (response.ok) {
        const data = await response.json();
        addChatMessage("global", "assistant", data.text);
      } else {
        const errData = await response.json();
        addChatMessage("global", "assistant", `Failed to compile response: ${errData.details || "Error communicating with local server"}`);
      }
    } catch (err) {
      console.error("AI Assistant error:", err);
      addChatMessage("global", "assistant", "An error occurred connecting to the native backend environment loop. Please check container stats.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-12 h-[calc(100vh-12rem)] animate-fade-in">
      {/* Sidebar helper shortcuts */}
      <div className="glass-panel p-5 lg:col-span-4 flex flex-col justify-between shadow-lg">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Brain className="h-5 w-5 text-cyan-400" />
            <span className="text-xs font-semibold text-white font-sans uppercase">Companion Shortcuts</span>
          </div>
          <p className="text-[11px] text-slate-400 mb-4 leading-relaxed">Click any quick-start directive on the list to launch a native exploratory ML audit query.</p>

          <div className="space-y-2.5">
            {suggestedQueries.map((query, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(query)}
                disabled={loading}
                className="w-full text-left p-3 rounded-lg border border-white/5 hover:bg-white/10 hover:border-white/20 text-slate-400 hover:text-white transition-all font-mono text-[10.5px] leading-relaxed block cursor-pointer"
              >
                &ldquo;{query}&rdquo;
              </button>
            ))}
          </div>
        </div>

        {/* Console details */}
        <div className="p-3 bg-black/20 rounded-lg border border-white/5 flex items-center gap-2 text-[10px] text-slate-400 font-mono">
          <Terminal className="h-4 w-4 text-cyan-400 shrink-0" />
          <span>Active: Native Local Model Intelligence Optimizer</span>
        </div>
      </div>

      {/* Primary chat workspace console */}
      <div className="glass-panel p-5 lg:col-span-8 flex flex-col h-full justify-between shadow-lg">
        {/* Chat Logs scroll zone */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto space-y-4 pr-2 max-h-[calc(100vh-25rem)] mb-4"
        >
          {activeChat.map((msg, idx) => {
            const isAI = msg.role === "assistant";
            return (
              <div 
                key={idx} 
                className={`flex gap-3 max-w-[85%] text-xs ${isAI ? "self-start" : "ml-auto flex-row-reverse"}`}
              >
                {/* avatar marker */}
                <div className={`h-8 w-8 rounded-lg shrink-0 flex items-center justify-center font-bold ${
                  isAI ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" : "bg-white text-black"
                }`}>
                  {isAI ? "C" : "U"}
                </div>

                <div className={`p-3.5 rounded-xl leading-relaxed text-slate-200 font-sans border ${
                  isAI ? "bg-white/5 border-white/5" : "bg-cyan-500/10 border-cyan-500/15"
                }`}>
                  {/* format rendering with simple line breaks */}
                  <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-2 items-center text-xs text-slate-400 font-mono italic animate-pulse">
              <RefreshCw className="h-3.5 w-3.5 animate-spin text-cyan-400" />
              <span>Optimizing local telemetry query...</span>
            </div>
          )}
        </div>

        {/* Input Text Form */}
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(inputValue); }} 
          className="relative mt-auto pt-3 border-t border-white/5 flex gap-2.5 items-center"
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask AI Copilot about latency tuning, SHAP values, Optuna parameters..."
            className="flex-1 h-10 px-4 rounded-lg bg-black/15 border border-white/10 hover:border-white/25 focus:border-cyan-500/50 text-xs text-slate-200 outline-none transition-all"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || loading}
            className="h-10 px-4 rounded-lg bg-gradient-to-br from-cyan-400 to-indigo-600 hover:from-cyan-350 hover:to-indigo-550 text-white font-bold text-xs transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Submit</span>
          </button>
        </form>
      </div>
    </div>
  );
}
