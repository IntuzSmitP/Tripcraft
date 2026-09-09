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
            className="mb-4 surface-card p-0 overflow-hidden w-[500px] max-w-[90vw] shadow-2xl"
          >
            <div className="p-3 border-b flex justify-between items-center" style={{ backgroundColor: "var(--color-bg-raised)", borderColor: "var(--color-border)" }}>
              <span className="text-sm font-semibold flex items-center gap-2" style={{ color: "var(--color-text-primary)" }}>
                <Code className="w-4 h-4" style={{ color: "var(--color-accent-500)" }} />
                Agent State
              </span>
              <span className="text-xs px-2 py-1 rounded-full" style={{ backgroundColor: "var(--color-bg-base)", color: "var(--color-text-secondary)" }}>
                {stateData.status}
              </span>
            </div>
            <div className="p-4 max-h-[60vh] overflow-y-auto custom-scrollbar" style={{ backgroundColor: "var(--color-bg-base)" }}>
              <pre className="text-xs font-mono whitespace-pre-wrap" style={{ color: "var(--color-success-500)" }}>
                {JSON.stringify(stateData, null, 2)}
              </pre>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-secondary rounded-full flex items-center gap-2 shadow-lg"
      >
        <Code className="w-4 h-4" />
        <span className="text-sm font-medium">Inspect State</span>
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
      </button>
    </div>
  )
}
