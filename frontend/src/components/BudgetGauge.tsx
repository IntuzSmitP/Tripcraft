"use client"

import { motion } from "framer-motion"

export function BudgetGauge({ budget }: { budget: any }) {
  if (!budget || !budget.requested) return null

  const requested = budget.requested
  const estimated = budget.estimated
  const percentage = Math.min(100, Math.max(0, (estimated / requested) * 100))
  
  const isOverBudget = estimated > requested
  // Use warning amber for over budget, and the primary terracotta accent for normal
  const strokeColor = isOverBudget ? "var(--color-warn-500)" : "var(--color-accent-500)" 

  // SVG parameters
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="surface-card p-6 flex flex-col items-center relative overflow-hidden" style={{ backgroundColor: "var(--color-bg-card)" }}>
      <h3 className="text-sm font-medium uppercase tracking-widest mb-6 w-full text-left" style={{ color: "var(--color-text-muted)" }}>Budget Utilization</h3>
      
      <div className="relative w-40 h-40 flex items-center justify-center">
        {/* Background Circle */}
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="var(--color-border-subtle)"
            strokeWidth="8"
            fill="transparent"
          />
          {/* Progress Circle */}
          <motion.circle
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            cx="80"
            cy="80"
            r={radius}
            stroke={strokeColor}
            strokeWidth="8"
            fill="transparent"
            strokeLinecap="round"
            style={{ strokeDasharray: circumference }}
          />
        </svg>
        
        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold" style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>{Math.round(percentage)}%</span>
        </div>
      </div>
      
      <div className="w-full mt-6 space-y-3 text-sm">
        <div className="flex justify-between items-center pb-2 border-b" style={{ borderColor: "var(--color-border-subtle)" }}>
          <span style={{ color: "var(--color-text-secondary)" }}>Total Budget</span>
          <span className="font-medium" style={{ color: "var(--color-text-primary)" }}>₹{requested.toLocaleString()}</span>
        </div>
        <div className="flex justify-between items-center">
          <span style={{ color: "var(--color-text-secondary)" }}>Estimated Cost</span>
          <span className="font-medium" style={{ color: isOverBudget ? "var(--color-warn-500)" : "var(--color-text-primary)" }}>
            ₹{estimated.toLocaleString()}
          </span>
        </div>
        
        {budget.breakdown && Object.keys(budget.breakdown).length > 0 && (
          <div className="mt-3 pt-3 border-t space-y-2" style={{ borderColor: "var(--color-border-subtle)" }}>
            {Object.entries(budget.breakdown).map(([category, amount]: [string, any]) => (
              <div key={category} className="flex justify-between items-center text-xs">
                <span className="capitalize" style={{ color: "var(--color-text-muted)" }}>{category.replace('_', ' ')}</span>
                <span style={{ color: "var(--color-text-secondary)" }}>₹{amount.toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
