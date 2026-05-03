"use client";

import type { UIMessage } from "ai";
import { useChat } from "@ai-sdk/react";
import { useState, useRef, useCallback, useEffect, FormEvent } from "react";

function getTextFromMessage(message: UIMessage): string {
  return message.parts
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("");
}

export default function Home() {
  const [viewportText, setViewportText] = useState("");
  const [selectedText, setSelectedText] = useState("");
  const [input, setInput] = useState("");
  const contentRef = useRef<HTMLDivElement>(null);

  const contextToSend = selectedText || viewportText;

  const { messages, sendMessage, status } = useChat();

  const isLoading = status === "streaming" || status === "submitted";

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const text = input;
    setInput("");
    sendMessage({ text }, { body: { context: contextToSend } });
  };

  const captureViewportText = useCallback(() => {
    if (!contentRef.current) return;
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      setSelectedText(selection.toString().trim());
      return;
    }
    setSelectedText("");

    const container = contentRef.current;
    const nodes = container.querySelectorAll("p, h1, h2, h3, h4, li, td, th");
    const visibleTexts: string[] = [];

    nodes.forEach((node) => {
      const rect = node.getBoundingClientRect();
      const inViewport = rect.top < window.innerHeight && rect.bottom > 0;
      if (inViewport && node.textContent) {
        visibleTexts.push(node.textContent.trim());
      }
    });

    setViewportText(visibleTexts.join("\n"));
  }, []);

  useEffect(() => {
    const container = contentRef.current?.closest(".overflow-y-auto");
    if (!container) return;

    const handleScroll = () => captureViewportText();
    container.addEventListener("scroll", handleScroll, { passive: true });
    document.addEventListener("selectionchange", captureViewportText);
    captureViewportText();

    return () => {
      container.removeEventListener("scroll", handleScroll);
      document.removeEventListener("selectionchange", captureViewportText);
    };
  }, [captureViewportText]);

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Reading pane */}
      <div className="flex-1 overflow-y-auto p-8">
        <div
          ref={contentRef}
          className="prose dark:prose-invert mx-auto max-w-3xl"
        >
          <h1>Welcome to AI Reader</h1>
          <p>
            Paste or load content here to start reading. As you scroll, the AI
            assistant will automatically have context about what you&apos;re
            currently viewing.
          </p>
          <p>
            You can also <strong>highlight any text</strong> to ask specific
            questions about it. The highlighted text will be sent as context to
            the AI.
          </p>
          <h2>How it works</h2>
          <p>
            The reading pane tracks which text is currently visible in your
            viewport. When you ask a question in the chat panel, the visible
            text is automatically included as context for the AI, so it knows
            exactly what you&apos;re looking at.
          </p>
          <p>
            Try scrolling through a long document and asking questions — the AI
            will always know what part you&apos;re reading.
          </p>
        </div>
      </div>

      {/* Chat sidebar */}
      <div className="w-96 border-l border-zinc-200 dark:border-zinc-800 flex flex-col bg-white dark:bg-zinc-900">
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            AI Assistant
          </h2>
          {selectedText && (
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 truncate">
              Context: &quot;{selectedText.slice(0, 80)}
              {selectedText.length > 80 ? "…" : ""}&quot;
            </p>
          )}
          {!selectedText && viewportText && (
            <p className="text-xs text-zinc-500 mt-1">
              Reading viewport context active
            </p>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <p className="text-sm text-zinc-400 text-center mt-8">
              Ask a question about what you&apos;re reading
            </p>
          )}
          {messages.map((m) => (
            <div
              key={m.id}
              className={`text-sm ${
                m.role === "user"
                  ? "text-zinc-900 dark:text-zinc-100"
                  : "text-zinc-600 dark:text-zinc-300"
              }`}
            >
              <span className="font-semibold text-xs uppercase tracking-wide text-zinc-400 block mb-1">
                {m.role === "user" ? "You" : "AI"}
              </span>
              <p className="whitespace-pre-wrap">{getTextFromMessage(m)}</p>
            </div>
          ))}
          {isLoading && (
            <p className="text-sm text-zinc-400 animate-pulse">Thinking…</p>
          )}
        </div>

        <form
          onSubmit={handleSubmit}
          className="p-4 border-t border-zinc-200 dark:border-zinc-800"
        >
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about what you're reading…"
              className="flex-1 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 px-3 py-2 text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
