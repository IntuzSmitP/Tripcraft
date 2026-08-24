"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Send } from "lucide-react"

export function UserInputForm({ 
  onSubmit 
}: { 
  onSubmit: (input: string) => Promise<void> 
}) {
  const [input, setInput] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    try {
      await onSubmit(input)
      setInput("")
    } catch (err) {
      console.error(err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <motion.form 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      onSubmit={handleSubmit}
      className="mt-4 ml-16 flex gap-2 w-full max-w-2xl bg-slate-900/50 p-2 rounded-xl border border-brand-500/30"
    >
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type your answer here..."
        className="flex-grow bg-transparent text-white px-4 py-2 outline-none"
        autoFocus
      />
      <button
        type="submit"
        disabled={!input.trim() || isSubmitting}
        className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white p-3 rounded-lg transition-colors flex items-center justify-center"
      >
        {isSubmitting ? (
          <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <Send className="w-5 h-5" />
        )}
      </button>
    </motion.form>
  )
}
