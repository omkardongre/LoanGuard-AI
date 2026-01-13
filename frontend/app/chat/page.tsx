"use client";

import { useState, useRef, useEffect } from "react";
import { Sidebar } from "@/components/sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Loader2,
  RefreshCw,
  ExternalLink,
  AlertCircle,
} from "lucide-react";
import { chatWithAgent, fetchLoans, type Loan } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  suggestions?: string[];
  error?: boolean;
}

const initialSuggestions = [
  "Show me loans at risk of covenant breach",
  "What is the ESG status of LOAN-0001?",
  "Which covenants are closest to their thresholds?",
  "Explain the breach prediction for LOAN-0003",
  "Generate a portfolio risk summary",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm LoanGuard AI, your covenant and ESG compliance assistant powered by Gemini. How can I help you today?",
      timestamp: new Date(),
      suggestions: initialSuggestions,
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loans, setLoans] = useState<Loan[]>([]);
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load loans for context selector
  useEffect(() => {
    async function loadLoans() {
      try {
        const response = await fetchLoans({ limit: 50 });
        setLoans(response.loans || []);
      } catch (err) {
        console.error("Failed to load loans:", err);
      }
    }
    loadLoans();
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      // Build conversation history for context (exclude initial greeting, limit to recent messages)
      const historyForContext = messages
        .slice(1) // Skip initial greeting
        .concat(userMessage) // Include current message
        .slice(-10) // Keep last 10 messages
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const response = await chatWithAgent(
        currentInput,
        selectedLoan || undefined,
        historyForContext
      );

      const assistantMessage: Message = {
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
        suggestions: response.suggestions?.length > 0 ? response.suggestions : undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error("Chat error:", err);
      const errorMessage: Message = {
        role: "assistant",
        content:
          "I apologize, but I couldn't process your request. Please check if the API Gateway is running or try again later.",
        timestamp: new Date(),
        error: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSuggestion(suggestion: string) {
    setInput(suggestion);
  }

  function handleClearChat() {
    setMessages([
      {
        role: "assistant",
        content:
          "Hello! I'm LoanGuard AI, your covenant and ESG compliance assistant. How can I help you today?",
        timestamp: new Date(),
        suggestions: initialSuggestions,
      },
    ]);
  }

  // Get latest suggestions from messages
  const latestSuggestions =
    messages.length > 0 && messages[messages.length - 1].role === "assistant"
      ? messages[messages.length - 1].suggestions
      : undefined;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-white to-slate-50 border-b p-4 shadow-sm">
          <div className="flex items-center justify-between max-w-4xl mx-auto">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-slate-900 gradient-text">
                  LoanGuard AI Assistant
                </h1>
                <p className="text-xs text-slate-500">
                  Powered by Gemini • Ask about covenants, ESG, and compliance
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Loan Context Selector */}
              <select
                value={selectedLoan || ""}
                onChange={(e) => setSelectedLoan(e.target.value || null)}
                className="px-3 py-1.5 text-sm border-2 rounded-xl focus:outline-none focus:ring-0 focus:border-purple-500 transition-colors"
              >
                <option value="">All Loans (Portfolio)</option>
                {loans.map((loan) => (
                  <option key={loan.loan_id} value={loan.loan_id}>
                    {loan.loan_id} - {loan.borrower_name}
                  </option>
                ))}
              </select>
              <Button variant="outline" size="sm" onClick={handleClearChat} className="rounded-xl hover:bg-slate-50">
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-4xl mx-auto w-full">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${message.role === "user" ? "justify-end" : ""}`}
            >
              {message.role === "assistant" && (
                <div
                  className={`p-2 rounded-full h-fit ${message.error ? "bg-red-100" : "bg-emerald-100"
                    }`}
                >
                  {message.error ? (
                    <AlertCircle className="h-4 w-4 text-red-600" />
                  ) : (
                    <Bot className="h-4 w-4 text-emerald-600" />
                  )}
                </div>
              )}

              <div
                className={`max-w-2xl p-4 rounded-xl ${message.role === "user"
                  ? "bg-emerald-600 text-white"
                  : message.error
                    ? "bg-red-50 border border-red-200 shadow-sm"
                    : "bg-white border shadow-sm"
                  }`}
              >
                <div className={`prose prose-sm max-w-none ${message.role === "user"
                  ? "prose-invert"
                  : "prose-slate prose-headings:text-slate-800 prose-headings:font-semibold prose-headings:text-base prose-p:text-slate-700 prose-strong:text-slate-900 prose-li:text-slate-700"
                  }`}>
                  <ReactMarkdown
                    components={{
                      // Custom heading styles
                      h1: ({ children }) => <h1 className="text-lg font-bold mt-3 mb-2">{children}</h1>,
                      h2: ({ children }) => <h2 className="text-base font-bold mt-3 mb-2">{children}</h2>,
                      h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 text-slate-800">{children}</h3>,
                      // Bold text
                      strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
                      // Lists
                      ul: ({ children }) => <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>,
                      li: ({ children }) => <li className="text-sm">{children}</li>,
                      // Paragraphs
                      p: ({ children }) => <p className="mb-2 last:mb-0 text-sm leading-relaxed">{children}</p>,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
                <p
                  className={`text-xs mt-2 ${message.role === "user" ? "text-emerald-200" : "text-slate-400"
                    }`}
                >
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>

              {message.role === "user" && (
                <div className="p-2 bg-slate-200 rounded-full h-fit">
                  <User className="h-4 w-4 text-slate-600" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3">
              <div className="p-2 bg-emerald-100 rounded-full h-fit">
                <Bot className="h-4 w-4 text-emerald-600" />
              </div>
              <div className="bg-white border shadow-sm p-4 rounded-xl">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
                  <span className="text-sm text-slate-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {latestSuggestions && latestSuggestions.length > 0 && !isLoading && (
          <div className="px-4 pb-2 max-w-4xl mx-auto w-full">
            <p className="text-xs text-slate-500 mb-2">Suggested questions:</p>
            <div className="flex flex-wrap gap-2">
              {latestSuggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestion(suggestion)}
                  className="text-sm px-3 py-1.5 bg-white border rounded-full hover:bg-slate-50 text-slate-700 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Selected Loan Context */}
        {selectedLoan && (
          <div className="px-4 pb-2 max-w-4xl mx-auto w-full">
            <div className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg border border-emerald-200">
              <Badge variant="outline" className="text-emerald-700">
                Context: {selectedLoan}
              </Badge>
              <span className="text-sm text-emerald-700">
                {loans.find((l) => l.loan_id === selectedLoan)?.borrower_name}
              </span>
              <a
                href={`/loans/${selectedLoan}`}
                className="text-xs text-emerald-600 hover:underline flex items-center gap-1 ml-auto"
              >
                View Loan <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="bg-white border-t p-4">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder={
                selectedLoan
                  ? `Ask about ${selectedLoan}...`
                  : "Ask about covenants, ESG compliance, or loan status..."
              }
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              disabled={isLoading}
            />
            <Button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-slate-400 text-center mt-2">
            LoanGuard AI may make mistakes. Verify important information.
          </p>
        </div>
      </main>
    </div>
  );
}
