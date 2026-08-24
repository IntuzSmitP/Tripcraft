"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Code, ChevronDown, ChevronUp } from "lucide-react"

export function StateInspector({ stateData }: { stateData: any }) {
  const [isOpen, setIsOpen] = useState(false)

  if (!stateData) return null

  return (
    <div className="fixed bottom-4 left-4 z-50">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="mb-4 glass-card p-0 overflow-hidden w-[500px] max-w-[90vw] shadow-2xl border-brand-500/30"
          >
            <div className="bg-brand-950/80 p-3 border-b border-white/10 flex justify-between items-center">
              <span className="text-sm font-semibold flex items-center gap-2">
                <Code className="w-4 h-4 text-brand-400" />
                Agent State
              </span>
              <span className="text-xs px-2 py-1 bg-brand-500/20 text-brand-300 rounded-full">
                {stateData.status}
              </span>
            </div>
            <div className="p-4 max-h-[60vh] overflow-y-auto custom-scrollbar bg-[#0f111a]">
              <pre className="text-xs text-green-400 font-mono whitespace-pre-wrap">
                {JSON.stringify(stateData, null, 2)}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-secondary rounded-full flex items-center gap-2 shadow-lg backdrop-blur-xl border border-white/10"
      >
        <Code className="w-4 h-4" />
        <span className="text-sm font-medium">Inspect State</span>
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
      </button>
    </div>
  )
}
