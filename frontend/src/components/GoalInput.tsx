"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Search, Sparkles } from "lucide-react"

const EXAMPLES = [
  "Plan a 3-day trip to Goa under ₹15,000",
  "I have ₹30,000 for a 5-day trip to Jaipur",
  "Weekend getaway to Mumbai from Ahmedabad under ₹10,000"
]

export function GoalInput({ onSubmit, isLoading }: { onSubmit: (goal: string) => void, isLoading: boolean }) {
  const [goal, setGoal] = useState("")

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-full max-w-3xl mx-auto space-y-8"
    >
      <div className="text-center space-y-4">
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight">
          Craft your perfect <span className="gradient-text">journey.</span>
        </h1>
        <p className="text-slate-400 text-lg md:text-xl max-w-xl mx-auto">
          TripCraft breaks down your travel goals, checks real-time prices, and builds a realistic budget plan.
        </p>
      </div>

      <div className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-brand-500 to-accent-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
        <form 
          onSubmit={(e) => {
            e.preventDefault()
            if (goal.trim() && !isLoading) onSubmit(goal)
          }}
          className="relative flex items-center glass-card p-2"
        >
          <Search className="w-6 h-6 text-slate-400 ml-4 absolute left-2 pointer-events-none" />
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            disabled={isLoading}
            placeholder="Plan a 3-day trip to Goa under ₹15,000..."
            className="w-full bg-transparent border-none focus:ring-0 text-lg md:text-xl text-white placeholder-slate-500 py-4 pl-14 pr-32 outline-none"
          />
          <button 
            type="submit" 
            disabled={!goal.trim() || isLoading}
            className="absolute right-2 btn-primary py-2.5 px-6 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-5 h-5" />
            )}
            <span>Plan</span>
          </button>
        </form>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
        <span className="text-sm text-slate-500 mr-2">Try:</span>
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            onClick={() => {
              setGoal(ex)
            }}
            disabled={isLoading}
            className="text-xs md:text-sm px-4 py-2 glass-card hover:bg-white/10 text-slate-300 transition-colors border-white/5 rounded-full"
          >
            {ex}
          </button>
        ))}
      </div>
    </motion.div>
  )
}
