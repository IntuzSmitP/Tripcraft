"use client"

import { motion } from "framer-motion"
import { BrainCircuit, Wrench, FileCheck, ArrowLeftRight, CheckCircle2, MessageCircleQuestion } from "lucide-react"

export interface LogEntry {
  step: number
  action: "PLAN" | "TOOL" | "RESULT" | "RE-EVALUATE" | "FINAL" | "ERROR" | "WAITING"
  detail: string
  timestamp: string
}

const ACTION_CONFIG: Record<string, any> = {
  "PLAN": { icon: BrainCircuit, color: "text-emerald-400", bg: "bg-emerald-400/10", border: "border-emerald-400/20" },
  "TOOL": { icon: Wrench, color: "text-blue-400", bg: "bg-blue-400/10", border: "border-blue-400/20" },
  "RESULT": { icon: FileCheck, color: "text-amber-400", bg: "bg-amber-400/10", border: "border-amber-400/20" },
  "RE-EVALUATE": { icon: ArrowLeftRight, color: "text-orange-400", bg: "bg-orange-400/10", border: "border-orange-400/20" },
  "FINAL": { icon: CheckCircle2, color: "text-purple-400", bg: "bg-purple-400/10", border: "border-purple-400/20" },
  "ERROR": { icon: BrainCircuit, color: "text-red-400", bg: "bg-red-400/10", border: "border-red-400/20" },
  "WAITING": { icon: MessageCircleQuestion, color: "text-pink-400", bg: "bg-pink-400/10", border: "border-pink-400/20" }
}

export function ExecutionLog({ logs }: { logs: LogEntry[] }) {
  if (logs.length === 0) return null

  return (
    <div className="w-full max-w-3xl mx-auto mt-12 space-y-4 relative">
      <div className="absolute left-8 top-4 bottom-4 w-px bg-slate-800 -z-10"></div>
      
      {logs.map((log, index) => {
        const config = ACTION_CONFIG[log.action] || ACTION_CONFIG["PLAN"]
        const Icon = config.icon

        return (
          <motion.div 
            key={index}
            initial={{ opacity: 0, x: -20, height: 0 }}
            animate={{ opacity: 1, x: 0, height: "auto" }}
            transition={{ duration: 0.4 }}
            className="flex gap-4 items-start"
          >
            <div className={`w-16 flex-shrink-0 flex justify-center py-2`}>
              <div className={`p-2 rounded-full border ${config.bg} ${config.border} ${config.color}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
            
            <div className={`flex-grow glass-card p-4 my-1`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-bold tracking-wider ${config.color}`}>
                  {log.action}
                </span>
                <span className="text-xs text-slate-500">
                  Step {log.step}
                </span>
              </div>
              <div className={`text-sm ${log.action === "TOOL" ? "font-mono text-blue-200" : "text-slate-300"}`}>
                {log.detail}
              </div>
            </div>
          </motion.div>
        )
      })}
      
      {/* Animated loading indicator if last log is not FINAL or ERROR */}
      {logs.length > 0 && !["FINAL", "ERROR"].includes(logs[logs.length - 1].action) && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex gap-4 items-start mt-4"
        >
          <div className="w-16 flex-shrink-0 flex justify-center py-2">
            <div className="w-2 h-2 rounded-full bg-brand-500 animate-ping"></div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
