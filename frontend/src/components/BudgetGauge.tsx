"use client"

import { motion } from "framer-motion"

export function BudgetGauge({ budget }: { budget: any }) {
  if (!budget || !budget.requested) return null

  const requested = budget.requested
  const estimated = budget.estimated
  const percentage = Math.min(100, Math.max(0, (estimated / requested) * 100))
  
  const isOverBudget = estimated > requested
  const strokeColor = isOverBudget ? "#ef4444" : "#10b981" // red-500 or emerald-500

  // SVG parameters
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (percentage / 100) * circumference

  return (
    <div className="glass-card p-6 flex flex-col items-center relative overflow-hidden">
      {/* Background glow */}
      <div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 blur-3xl opacity-20 rounded-full"
        style={{ backgroundColor: strokeColor }}
      />
      
      <h3 className="text-sm font-semibold text-slate-400 mb-6 uppercase tracking-wider">Budget Utilization</h3>
      
      <div className="relative w-40 h-40 flex items-center justify-center">
        {/* Background Circle */}
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="12"
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
            strokeWidth="12"
            fill="transparent"
            strokeLinecap="round"
            style={{ strokeDasharray: circumference }}
          />
        </svg>
        
        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold">{Math.round(percentage)}%</span>
        </div>
      </div>
      
      <div className="w-full mt-6 pt-6 border-t border-white/10 space-y-3 text-sm">
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Total Budget</span>
          <span className="font-semibold">₹{requested.toLocaleString()}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-slate-400">Estimated Cost</span>
          <span className={`font-semibold ${isOverBudget ? 'text-red-400' : 'text-emerald-400'}`}>
            ₹{estimated.toLocaleString()}
          </span>
        </div>
        
        {budget.breakdown && Object.keys(budget.breakdown).length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/5 space-y-2">
            {Object.entries(budget.breakdown).map(([category, amount]: [string, any]) => (
              <div key={category} className="flex justify-between items-center text-xs">
                <span className="text-slate-500 capitalize">{category.replace('_', ' ')}</span>
                <span className="text-slate-300">₹{amount.toLocaleString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
