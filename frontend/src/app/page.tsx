"use client"

import { useState, useEffect } from "react"
import { GoalInput } from "@/components/GoalInput"
import { ExecutionLog, type LogEntry } from "@/components/ExecutionLog"
import { PlanResult } from "@/components/PlanResult"
import { BudgetGauge } from "@/components/BudgetGauge"
import { ChatPanel } from "@/components/ChatPanel"
import { startPlanningSession, subscribeToExecutionLog, fetchAgentState, provideUserInput } from "@/lib/api"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, ChevronUp, Terminal } from "lucide-react"

export interface ChatMessage {
  role: "user" | "agent"
  text: string
  timestamp: string
}

export default function Home() {
  const [isPlanning, setIsPlanning] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [planResult, setPlanResult] = useState<any>(null)
  const [agentState, setAgentState] = useState<any>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [isWaiting, setIsWaiting] = useState(false)
  const [currentGoal, setCurrentGoal] = useState<string>("")
  const [showReasoning, setShowReasoning] = useState(false)

  // Fetch state periodically while planning
  useEffect(() => {
    if (!sessionId || !isPlanning) return
    const interval = setInterval(async () => {
      try {
        const state = await fetchAgentState(sessionId)
        setAgentState(state)
      } catch (e) {}
    }, 2000)
    return () => clearInterval(interval)
  }, [sessionId, isPlanning])

  // Detect WAITING log and extract question for chat
  useEffect(() => {
    if (logs.length === 0) return
    const last = logs[logs.length - 1]
    if (last.action === "WAITING") {
      setIsWaiting(true)
      setChatMessages((prev) => {
        const alreadyAdded = prev.some((m) => m.role === "agent" && m.text === last.detail)
        if (alreadyAdded) return prev
        return [...prev, { role: "agent", text: last.detail, timestamp: last.timestamp }]
      })
    } else {
      setIsWaiting(false)
    }
  }, [logs])

  const handleStartPlan = async (goal: string) => {
    try {
      setIsPlanning(true)
      setLogs([])
      setPlanResult(null)
      setAgentState(null)
      setError(null)
      setIsWaiting(false)
      setCurrentGoal(goal)
      setShowReasoning(false)
      setChatMessages([
        { role: "user", text: goal, timestamp: new Date().toISOString() }
      ])

      const { session_id } = await startPlanningSession(goal)
      setSessionId(session_id)

      const unsubscribe = subscribeToExecutionLog(
        session_id,
        (entry) => {
          setLogs((prev) => [...prev, entry])
        },
        (result) => {
          setPlanResult(result)
        },
        async (status) => {
          setIsPlanning(false)
          setIsWaiting(false)
          if (status === "error") {
            setError("Planning failed. Please check the activity log for details.")
          }
          try {
            const state = await fetchAgentState(session_id)
            setAgentState(state)
          } catch (e) {}
        },
        (err) => {
          console.error("Stream error", err)
          setError("Connection to agent lost.")
          setIsPlanning(false)
          setIsWaiting(false)
        }
      )
    } catch (err: any) {
      setError(err.message || "Failed to start planning")
      setIsPlanning(false)
    }
  }

  const handleUserReply = async (input: string) => {
    if (!sessionId) return
    setChatMessages((prev) => [
      ...prev,
      { role: "user", text: input, timestamp: new Date().toISOString() }
    ])
    setIsWaiting(false)
    await provideUserInput(sessionId, input)
  }

  const hasContent = logs.length > 0 || isPlanning

  return (
    <main className="min-h-screen py-10 px-4 md:px-8 flex flex-col items-center relative">

      {/* Navbar */}
      <header className="w-full max-w-7xl mx-auto flex justify-between items-center mb-16 relative z-10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: "var(--color-teal-500)" }}>
            <span className="font-bold text-sm leading-none" style={{ color: "var(--color-text-primary)" }}>T</span>
          </div>
          <span className="text-lg font-semibold tracking-tight" style={{ color: "var(--color-text-primary)" }}>TripCraft</span>
        </div>
      </header>

      <div className="w-full max-w-7xl mx-auto flex-grow flex flex-col items-center z-10">

        {/* Goal input */}
        <motion.div
          animate={{
            y: hasContent ? -20 : 80,
            scale: hasContent ? 0.9 : 1,
          }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="w-full"
        >
          <GoalInput onSubmit={handleStartPlan} isLoading={isPlanning} />
        </motion.div>

        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4 p-4 rounded-xl max-w-2xl mx-auto w-full flex items-center gap-3 text-sm"
              style={{ backgroundColor: "rgba(224, 164, 88, 0.1)", border: "1px solid rgba(224, 164, 88, 0.2)", color: "var(--color-warn-500)" }}
            >
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: "var(--color-warn-500)" }} />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main content */}
        <AnimatePresence>
          {hasContent && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="w-full mt-8 pb-24"
            >
              {/* Chat panel — full width, primary focus */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">

                {/* Chat — takes more visual weight */}
                <div className="lg:col-span-3 flex flex-col">
                  <h3 className="text-xs font-medium uppercase tracking-widest mb-3 flex items-center gap-2"
                    style={{ color: "var(--color-text-muted)" }}>
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: "var(--color-accent-500)" }} />
                    Conversation
                  </h3>
                  <ChatPanel
                    messages={chatMessages}
                    isWaiting={isWaiting}
                    isPlanning={isPlanning}
                    onSend={handleUserReply}
                  />
                </div>

                {/* Agent reasoning — collapsed by default, visually secondary */}
                <div className="lg:col-span-2 flex flex-col">
                  <button
                    onClick={() => setShowReasoning(!showReasoning)}
                    className="text-xs font-medium uppercase tracking-widest mb-3 flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
                    style={{ color: "var(--color-text-muted)" }}
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    Agent reasoning
                    <span className="text-[10px] font-normal normal-case tracking-normal" style={{ color: "var(--color-text-muted)" }}>
                      ({logs.length} steps)
                    </span>
                    {showReasoning
                      ? <ChevronUp className="w-3.5 h-3.5 ml-auto" />
                      : <ChevronDown className="w-3.5 h-3.5 ml-auto" />
                    }
                    {isPlanning && <span className="w-1.5 h-1.5 rounded-full animate-pulse ml-1" style={{ backgroundColor: "var(--color-accent-500)" }} />}
                  </button>

                  <AnimatePresence>
                    {showReasoning && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                      >
                        <div className="surface-raised rounded-xl overflow-hidden">
                          <div className="h-[440px] overflow-y-auto custom-scrollbar p-4">
                            <ExecutionLog logs={logs} />
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

              </div>

              {/* Plan Result */}
              <AnimatePresence>
                {planResult && (
                  <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className="mt-10 space-y-6"
                  >
                    <PlanResult 
                      plan={planResult} 
                      sessionId={sessionId}
                      onPlanUpdate={(updated) => setPlanResult(updated)}
                    />
                    {planResult.budget && (
                      <div className="max-w-sm">
                        <BudgetGauge budget={planResult.budget} />
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  )
}
