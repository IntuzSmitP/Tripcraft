"use client"

import { useState, useEffect } from "react"
import { GoalInput } from "@/components/GoalInput"
import { ExecutionLog, type LogEntry } from "@/components/ExecutionLog"
import { PlanResult } from "@/components/PlanResult"
import { StateInspector } from "@/components/StateInspector"
import { BudgetGauge } from "@/components/BudgetGauge"
import { UserInputForm } from "@/components/UserInputForm"
import { startPlanningSession, subscribeToExecutionLog, fetchAgentState, provideUserInput } from "@/lib/api"
import { motion, AnimatePresence } from "framer-motion"

export default function Home() {
  const [isPlanning, setIsPlanning] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [planResult, setPlanResult] = useState<any>(null)
  const [agentState, setAgentState] = useState<any>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch state periodically while planning
  useEffect(() => {
    if (!sessionId || !isPlanning) return

    const interval = setInterval(async () => {
      try {
        const state = await fetchAgentState(sessionId)
        setAgentState(state)
      } catch (e) {
        // Ignore fetch errors during polling
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [sessionId, isPlanning])

  const handleStartPlan = async (goal: string) => {
    try {
      setIsPlanning(true)
      setLogs([])
      setPlanResult(null)
      setAgentState(null)
      setError(null)

      // Start the session
      const { session_id } = await startPlanningSession(goal)
      setSessionId(session_id)

      // Subscribe to SSE
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
          if (status === "error") {
            setError("Planning failed. Please check the log below for details.")
          }
          // Final state fetch
          try {
            const state = await fetchAgentState(session_id)
            setAgentState(state)
          } catch(e) {}
        },
        (err) => {
          console.error("Stream error", err)
          setError("Connection to agent lost.")
          setIsPlanning(false)
        }
      )
      
      // We don't automatically unsubscribe on unmount for this simple demo
      // so the stream can complete
    } catch (err: any) {
      setError(err.message || "Failed to start planning")
      setIsPlanning(false)
    }
  }

  return (
    <main className="min-h-screen py-12 px-4 md:px-8 flex flex-col items-center relative overflow-hidden">
      
      {/* Background glow effects */}
      <div className="fixed top-[-10%] right-[-5%] w-[40vw] h-[40vw] bg-brand-600/20 rounded-full blur-[120px] pointer-events-none -z-10"></div>
      <div className="fixed bottom-[-10%] left-[-5%] w-[40vw] h-[40vw] bg-accent-600/10 rounded-full blur-[120px] pointer-events-none -z-10"></div>

      {/* Top Navbar */}
      <header className="w-full max-w-6xl mx-auto flex justify-between items-center mb-16 relative z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-400 to-accent-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
            <span className="text-white font-bold text-lg leading-none">T</span>
          </div>
          <span className="text-xl font-bold tracking-tight">TripCraft</span>
        </div>
      </header>

      <div className="w-full max-w-6xl mx-auto flex-grow flex flex-col items-center z-10">
        
        {/* Animate Input up when results start */}
        <motion.div 
          animate={{ 
            y: (logs.length > 0 || isPlanning) ? -20 : 100,
            scale: (logs.length > 0 || isPlanning) ? 0.9 : 1
          }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="w-full"
        >
          <GoalInput onSubmit={handleStartPlan} isLoading={isPlanning} />
        </motion.div>

        {error && (
          <div className="mt-8 p-4 glass-card border-red-500/30 bg-red-500/10 text-red-400">
            {error}
          </div>
        )}

        {/* Content area: splits into logs and results when available */}
        <div className="w-full mt-12 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start pb-24">
          
          <AnimatePresence>
            {(logs.length > 0 || isPlanning) && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={
                  planResult
                    ? "col-span-1 lg:col-span-4 transition-all duration-700"
                    : "col-span-1 lg:col-span-8 lg:col-start-3 transition-all duration-700"
                }
              >
                <div className="sticky top-8">
                  <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse"></span>
                    Agent Activity
                  </h3>
                  <div className="max-h-[70vh] overflow-y-auto custom-scrollbar pr-2 pb-4">
                    <ExecutionLog logs={logs} />
                    
                    {logs.length > 0 && logs[logs.length - 1].action === "WAITING" && sessionId && (
                      <UserInputForm 
                        onSubmit={async (input) => {
                          await provideUserInput(sessionId, input)
                        }} 
                      />
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {planResult && (
              <motion.div 
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="col-span-1 lg:col-span-8 space-y-6"
              >
                <PlanResult plan={planResult} />
                
                {planResult.budget && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl mx-auto">
                    <BudgetGauge budget={planResult.budget} />
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
          
        </div>
      </div>

      {agentState && <StateInspector stateData={agentState} />}
    </main>
  )
}
