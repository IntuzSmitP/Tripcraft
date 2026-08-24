"use client"

import { motion } from "framer-motion"
import { Plane, Hotel, CloudSun, IndianRupee, AlertTriangle, CheckCircle } from "lucide-react"

export function PlanResult({ plan }: { plan: any }) {
  if (!plan) return null

  const isFeasible = plan.status === "feasible"
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="w-full max-w-4xl mx-auto mt-12 space-y-6"
    >
      {/* Header / Status */}
      <div className={`glass-card p-6 flex items-center gap-4 border-l-4 ${isFeasible ? 'border-l-emerald-500' : 'border-l-red-500'}`}>
        <div className={`p-3 rounded-full ${isFeasible ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
          {isFeasible ? <CheckCircle className="w-8 h-8" /> : <AlertTriangle className="w-8 h-8" />}
        </div>
        <div>
          <h2 className="text-2xl font-bold">
            {isFeasible ? `${plan.trip.duration_days}-Day Trip to ${plan.trip.destination}` : 'Trip Plan Infeasible'}
          </h2>
          <p className="text-slate-400 mt-1">
            {isFeasible 
              ? `Estimated total: ₹${plan.budget.estimated?.toLocaleString() || 0} / Budget: ₹${plan.budget.requested?.toLocaleString() || 0}`
              : plan.reason}
          </p>
        </div>
      </div>

      {/* Assumptions Changed */}
      {plan.assumptions_changed && plan.assumptions_changed.length > 0 && (
        <div className="glass-card p-4 border border-orange-500/30 bg-orange-500/5">
          <h3 className="text-sm font-bold text-orange-400 flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4" /> Agent Self-Correction Triggered
          </h3>
          <ul className="list-disc list-inside text-sm text-slate-300 space-y-1">
            {plan.assumptions_changed.map((a: string, i: number) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {isFeasible && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Transport */}
          {plan.transport?.price && (
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center gap-3 text-brand-400">
                <Plane className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Transport</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-end">
                  <span className="text-2xl font-bold">{plan.transport.airline}</span>
                  <span className="text-xl text-emerald-400">₹{plan.transport.price.toLocaleString()}</span>
                </div>
                <div className="text-slate-400 text-sm">
                  {plan.transport.origin} → {plan.trip.destination} • {plan.transport.duration_hours}h • {plan.transport.date}
                </div>
              </div>
            </div>
          )}

          {/* Hotel */}
          {plan.hotel?.name && (
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center gap-3 text-accent-400">
                <Hotel className="w-6 h-6" />
                <h3 className="text-lg font-semibold">Accommodation</h3>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-end">
                  <span className="text-2xl font-bold truncate max-w-[200px]" title={plan.hotel.name}>
                    {plan.hotel.name}
                  </span>
                  <span className="text-xl text-emerald-400">₹{plan.hotel.total_price.toLocaleString()}</span>
                </div>
                <div className="text-slate-400 text-sm">
                  {plan.hotel.nights} nights @ ₹{plan.hotel.price_per_night.toLocaleString()}/night • {plan.hotel.rating}★ • {plan.hotel.type}
                </div>
              </div>
            </div>
          )}

          {/* Weather */}
          {plan.weather?.condition && (
            <div className="glass-card p-6 space-y-4 md:col-span-2 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="p-4 rounded-full bg-gradient-to-br from-amber-200 to-orange-400 text-white">
                  <CloudSun className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-slate-200">{plan.weather.condition}</h3>
                  <div className="text-3xl font-bold">
                    {plan.weather.temperature_high}°<span className="text-slate-500 text-xl"> / {plan.weather.temperature_low}°</span>
                  </div>
                </div>
              </div>
              <div className="flex-grow max-w-md">
                <p className="text-slate-300 text-sm bg-white/5 p-4 rounded-xl border border-white/10">
                  {plan.weather.recommendation}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}
