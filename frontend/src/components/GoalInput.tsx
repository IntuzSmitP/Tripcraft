"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Search, ArrowRight } from "lucide-react"

export function GoalInput({ onSubmit, isLoading }: { onSubmit: (goal: string) => void, isLoading: boolean }) {
  const [goal, setGoal] = useState("")
  const [isFocused, setIsFocused] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-full max-w-3xl mx-auto space-y-8"
    >
      <div className="text-center space-y-4">
        <h1 className="text-4xl md:text-[3.25rem] font-semibold leading-tight tracking-tight"
          style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>
          Craft your perfect <span style={{
            backgroundImage: "linear-gradient(to right, var(--color-accent-500), var(--color-warn-500))",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text"
          }}>journey.</span>
        </h1>
        <p className="text-base md:text-lg max-w-xl mx-auto" style={{ color: "var(--color-text-secondary)" }}>
          TripCraft breaks down your travel goals, checks real-time prices, and builds a realistic budget plan.
        </p>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (goal.trim() && !isLoading) onSubmit(goal)
        }}
        className="relative flex items-center surface-card p-2 rounded-xl transition-shadow duration-300"
        style={{
          border: "1px solid var(--color-border-subtle)",
          boxShadow: isFocused
            ? "0 8px 24px rgba(0, 0, 0, 0.45), 0 0 0 3px color-mix(in srgb, var(--color-accent-500) 25%, transparent)"
            : "0 6px 16px rgba(0, 0, 0, 0.35), 0 2px 4px rgba(0, 0, 0, 0.25)",
        }}
      >
        <Search className="w-5 h-5 ml-4 absolute left-2 pointer-events-none" style={{ color: "var(--color-text-muted)" }} />
        <input
          type="text"
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          disabled={isLoading}
          placeholder="Plan a trip to..."
          className="w-full bg-transparent border-none focus:ring-0 text-base md:text-lg py-3.5 pl-14 pr-32 outline-none"
          style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-sans)" }}
        />
        <button
          type="submit"
          disabled={goal.trim().length < 5 || isLoading}
          className="absolute right-2 py-2.5 px-5 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-shadow"
          style={{
            backgroundColor: "var(--color-accent-500)",
            color: "var(--color-text-primary)",
            boxShadow: "0 4px 10px color-mix(in srgb, var(--color-accent-500) 50%, transparent)",
          }}
        >
          {isLoading ? (
            <span className="w-4 h-4 border-2 border-current/20 border-t-current rounded-full animate-spin" />
          ) : (
            <ArrowRight className="w-4 h-4" />
          )}
          <span className="text-sm font-medium">Plan</span>
        </button>
      </form>
    </motion.div>
  )
}