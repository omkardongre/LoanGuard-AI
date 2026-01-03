"use client";

import { useState } from "react";
import { Sidebar } from "@/components/sidebar";
import { Button } from "@/components/ui/button";
import { Send, Bot, User, Sparkles } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const suggestions = [
  "Show me loans at risk of covenant breach",
  "Generate a compliance report for LOAN-0001",
  "What is the ESG status of my SLL portfolio?",
  "Which covenants are closest to their thresholds?",
  "Explain the SHAP analysis for LOAN-0003 breach prediction",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm LoanGuard AI, your covenant and ESG compliance assistant. How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate API call
    setTimeout(() => {
      const response: Message = {
        role: "assistant",
        content: getSimulatedResponse(input),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, response]);
      setIsLoading(false);
    }, 1000);
  };

  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />

      <main className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b p-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <Sparkles className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <h1 className="font-semibold text-slate-900">
                LoanGuard AI Assistant
              </h1>
              <p className="text-xs text-slate-500">
                Ask questions about covenants, ESG, and compliance
              </p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${
                message.role === "user" ? "justify-end" : ""
              }`}
            >
              {message.role === "assistant" && (
                <div className="p-2 bg-emerald-100 rounded-full h-fit">
                  <Bot className="h-4 w-4 text-emerald-600" />
                </div>
              )}

              <div
                className={`max-w-2xl p-4 rounded-xl ${
                  message.role === "user"
                    ? "bg-emerald-600 text-white"
                    : "bg-white border shadow-sm"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                <p
                  className={`text-xs mt-2 ${
                    message.role === "user"
                      ? "text-emerald-200"
                      : "text-slate-400"
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
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-slate-300 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Suggestions */}
        {messages.length === 1 && (
          <div className="px-4 pb-2">
            <p className="text-xs text-slate-500 mb-2">Suggested questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestion(suggestion)}
                  className="text-sm px-3 py-1.5 bg-white border rounded-full hover:bg-slate-50 text-slate-700"
                >
                  {suggestion}
                </button>
              ))}
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
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about covenants, ESG compliance, or loan status..."
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <Button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

function getSimulatedResponse(input: string): string {
  const lowerInput = input.toLowerCase();

  if (lowerInput.includes("risk") || lowerInput.includes("breach")) {
    return `Based on our ML breach prediction model, here are the loans at highest risk:

**High Risk (>50% probability):**
• LOAN-0003 (TechStart Inc): 72% breach probability
  - Key factors: Declining EBITDA, rising debt levels
  - Recommended action: Schedule borrower review

**Medium Risk (25-50%):**
• LOAN-0002 (Global Industries): 35% probability
• LOAN-0005 (Manufacturing Plus): 28% probability

Would you like me to generate a detailed risk report or schedule alerts for these loans?`;
  }

  if (lowerInput.includes("esg") || lowerInput.includes("sll")) {
    return `**ESG Portfolio Summary:**

📊 **SLL Loans:** 18 of 50 total loans
✅ **SPT Achievement Rate:** 78% (14/18 loans)
📈 **Average ESG Score:** 72.5

**Top Performers:**
• LOAN-0004 (Energy Solutions): -7.5 bps margin adjustment
• LOAN-0001 (Acme Corp): -5 bps margin adjustment

**Attention Needed:**
• LOAN-0003: Greenwashing risk flagged (MEDIUM)
• 3 loans have KPIs behind target

Shall I drill down into any specific loan?`;
  }

  if (lowerInput.includes("report")) {
    return `I can generate the following compliance reports:

1. **Covenant Compliance Report** - Full portfolio status
2. **ESG Performance Report** - SLL KPI tracking
3. **Risk Assessment Report** - ML predictions and trends
4. **Executive Summary** - High-level dashboard

Which report would you like me to generate? I can export to PDF or send via email.`;
  }

  return `I understand you're asking about "${input}". 

I can help you with:
• Covenant compliance monitoring
• ESG and SLL tracking
• Breach predictions with SHAP explanations
• Alert management
• Report generation

Could you please be more specific about what you'd like to know?`;
}
