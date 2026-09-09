"use client"

import { useRef, useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Send, Bot, User, Loader2 } from "lucide-react"
import type { ChatMessage } from "@/app/page"

interface ChatPanelProps {
  messages: ChatMessage[]
  isWaiting: boolean
  isPlanning: boolean
  onSend: (input: string) => Promise<void>
}

export function ChatPanel({ messages, isWaiting, isPlanning, onSend }: ChatPanelProps) {
  const [input, setInput] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to the latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isWaiting])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSubmitting || !isWaiting) return
    setIsSubmitting(true)
    try {
      await onSend(input.trim())
      setInput("")
    } catch (err) {
      console.error(err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="surface-card rounded-2xl flex flex-col overflow-hidden" style={{ height: "500px" }}>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-5">
        {messages.length === 0 && (
          <div className="h-full flex items-center justify-center text-sm" style={{ color: "var(--color-text-muted)" }}>
            Your conversation with TripCraft will appear here.
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              {/* Avatar */}
              <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center border`}
                style={{
                  backgroundColor: msg.role === "agent" ? "var(--color-bg-raised)" : "var(--color-accent-500)",
                  borderColor: msg.role === "agent" ? "var(--color-border)" : "var(--color-accent-600)",
                  color: msg.role === "agent" ? "var(--color-text-secondary)" : "var(--color-text-primary)"
                }}
              >
                {msg.role === "agent" ? <Bot className="w-4 h-4" /> : <User className="w-4 h-4" />}
              </div>

              {/* Bubble */}
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed break-words`}
                style={{
                  backgroundColor: msg.role === "agent" ? "var(--color-bg-raised)" : "var(--color-accent-500)",
                  color: msg.role === "agent" ? "var(--color-text-primary)" : "var(--color-text-primary)",
                  borderTopLeftRadius: msg.role === "agent" ? "0.25rem" : "1rem",
                  borderTopRightRadius: msg.role === "user" ? "0.25rem" : "1rem",
                }}
              >
                {msg.text}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator when agent is processing */}
        {isPlanning && !isWaiting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center border"
              style={{
                backgroundColor: "var(--color-bg-raised)",
                borderColor: "var(--color-border)",
                color: "var(--color-text-secondary)"
              }}
            >
              <Bot className="w-4 h-4" />
            </div>
            <div className="rounded-2xl px-4 py-3 flex items-center gap-1.5"
              style={{
                backgroundColor: "var(--color-bg-raised)",
                borderTopLeftRadius: "0.25rem"
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: "var(--color-text-muted)", animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: "var(--color-text-muted)", animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ backgroundColor: "var(--color-text-muted)", animationDelay: "300ms" }} />
            </div>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Divider */}
      <div className="h-px w-full" style={{ backgroundColor: "var(--color-border-subtle)" }} />

      {/* Input bar */}
      <form onSubmit={handleSubmit} className="p-3 flex gap-2 items-center" style={{ backgroundColor: "var(--color-bg-card)" }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isWaiting ? "Type your answer…" : "Waiting for agent…"}
          disabled={!isWaiting || isSubmitting}
          className="flex-1 rounded-xl px-4 py-2.5 text-sm outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed glass-input"
          style={{
            color: "var(--color-text-primary)",
          }}
        />
        <button
          type="submit"
          disabled={!input.trim() || !isWaiting || isSubmitting}
          className="p-2.5 rounded-xl flex items-center justify-center shrink-0 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          style={{ backgroundColor: "var(--color-accent-500)", color: "var(--color-text-primary)" }}
        >
          {isSubmitting
            ? <Loader2 className="w-4 h-4 animate-spin" />
            : <Send className="w-4 h-4" />
          }
        </button>
      </form>
    </div>
  )
}
