"use client"

import { motion } from "framer-motion"
import { BrainCircuit, Wrench, FileCheck, ArrowLeftRight, CheckCircle2, MessageCircleQuestion, AlertCircle } from "lucide-react"

export interface LogEntry {
  step: number
  action: "PLAN" | "TOOL" | "RESULT" | "RE-EVALUATE" | "FINAL" | "ERROR" | "WAITING"
  detail: string
  timestamp: string
}

const ACTION_CONFIG: Record<string, any> = {
  "PLAN":        { icon: BrainCircuit },
  "TOOL":        { icon: Wrench },
  "RESULT":      { icon: FileCheck },
  "RE-EVALUATE": { icon: ArrowLeftRight },
  "FINAL":       { icon: CheckCircle2 },
  "ERROR":       { icon: AlertCircle },
  "WAITING":     { icon: MessageCircleQuestion },
}

export function ExecutionLog({ logs }: { logs: LogEntry[] }) {
  if (logs.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-sm font-mono" style={{ color: "var(--color-text-secondary)" }}>
        Agent execution log empty.
      </div>
    )
  }

  return (
    <div className="w-full space-y-4 relative font-mono">
      {/* Vertical timeline line */}
      <div className="absolute left-[20px] top-4 bottom-4 w-px -z-10" style={{ backgroundColor: "var(--color-border-subtle)" }} />

      {logs.map((log, index) => {
        const config = ACTION_CONFIG[log.action] || ACTION_CONFIG["PLAN"]
        const Icon = config.icon

        // Highlight errors in warning color, final success in green, others in muted primary text
        let iconColor = "var(--color-text-secondary)"
        if (log.action === "ERROR") iconColor = "var(--color-warn-500)"
        else if (log.action === "FINAL") iconColor = "var(--color-success-500)"
        else if (log.action === "WAITING") iconColor = "var(--color-accent-500)"

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className="flex gap-4 items-start"
          >
            {/* Icon node */}
            <div className="shrink-0 mt-1">
              <div 
                className="w-10 h-10 flex items-center justify-center rounded-lg"
                style={{ 
                  backgroundColor: "var(--color-bg-raised)",
                  border: "1px solid var(--color-border)",
                  color: iconColor
                }}
              >
                <Icon className="w-4 h-4" />
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0 pt-1">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-xs tracking-wider" style={{ color: iconColor }}>
                  {log.action}
                </span>
                <span className="text-[10px]" style={{ color: "var(--color-text-secondary)" }}>
                  STEP {log.step}
                </span>
              </div>
              <div
                className="text-[11px] leading-relaxed break-words whitespace-pre-wrap"
                style={{ color: "var(--color-text-primary)" }}
              >
                {log.detail}
              </div>
            </div>
          </motion.div>
        )
      })}

      {/* Pulsing dot when still running */}
      {logs.length > 0 && !["FINAL", "ERROR"].includes(logs[logs.length - 1].action) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex gap-4 items-center"
        >
          <div className="shrink-0 w-10 flex justify-center">
            <div className="w-1.5 h-1.5 rounded-full animate-ping" style={{ backgroundColor: "var(--color-accent-500)" }} />
          </div>
          <span className="text-[11px] italic" style={{ color: "var(--color-text-secondary)" }}>Processing…</span>
        </motion.div>
      )}
    </div>
  )
}
