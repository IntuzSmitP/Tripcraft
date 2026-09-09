"use client"

import { motion } from "framer-motion"
import { Plane, Hotel, CloudSun, AlertTriangle, CheckCircle, MapPin, ExternalLink } from "lucide-react"
import { useState } from "react"
import { HotelPickerModal } from "./HotelPickerModal"

export function PlanResult({
  plan,
  sessionId,
  onPlanUpdate
}: {
  plan: any
  sessionId?: string | null
  onPlanUpdate?: (updatedPlan: any) => void
}) {
  if (!plan) return null

  const isFeasible = plan.status === "feasible"
  
  // States for simple hover interactions to show accent color on hover
  const [hoveredCard, setHoveredCard] = useState<string | null>(null)
  const [isHotelModalOpen, setIsHotelModalOpen] = useState(false)

  const [selectedCityForModal, setSelectedCityForModal] = useState<string | null>(null)

  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      className="w-full space-y-6"
    >
      {/* Header / Primary Summary Card - Visually heavier */}
      <div 
        className="surface-card p-8 flex items-start gap-5 relative overflow-hidden"
        style={{ backgroundColor: "var(--color-bg-raised)" }}
      >
        <div 
          className="absolute top-0 left-0 bottom-0 w-1.5"
          style={{ backgroundColor: isFeasible ? "var(--color-success-500)" : "var(--color-warn-500)" }}
        />
        <div className="shrink-0 mt-1">
          {isFeasible 
            ? <CheckCircle className="w-8 h-8" style={{ color: "var(--color-success-500)" }} /> 
            : <AlertTriangle className="w-8 h-8" style={{ color: "var(--color-warn-500)" }} />
          }
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-3xl font-semibold leading-tight break-words mb-2" style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>
            {isFeasible
              ? `${plan.trip?.duration_days}-Day Trip to ${plan.trip?.destination}`
              : "Trip Plan Infeasible"}
          </h2>
          <p className="text-base break-words flex items-center gap-2" style={{ color: "var(--color-text-secondary)" }}>
            {isFeasible
              ? (
                <>
                  <MapPin className="w-4 h-4 shrink-0" />
                  <span>From {plan.trip?.origin}</span>
                  <span className="opacity-50">•</span>
                  <span>Estimated: <strong style={{ color: "var(--color-text-primary)" }}>₹{plan.budget?.estimated?.toLocaleString() ?? 0}</strong></span>
                  <span className="opacity-50">•</span>
                  <span>Budget: <strong style={{ color: "var(--color-text-primary)" }}>{plan.budget?.requested ? `₹${plan.budget.requested.toLocaleString()}` : "No limit"}</strong></span>
                </>
              )
              : plan.reason}
          </p>
        </div>
      </div>

      {/* Self-correction notice - warning state */}
      {plan.assumptions_changed && plan.assumptions_changed.length > 0 && (
        <div className="p-5 rounded-xl border" style={{ backgroundColor: "rgba(224, 164, 88, 0.05)", borderColor: "rgba(224, 164, 88, 0.15)" }}>
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-2" style={{ color: "var(--color-warn-500)" }}>
            <AlertTriangle className="w-4 h-4 shrink-0" />
            Agent Self-Correction
          </h3>
          <ul className="list-disc list-inside text-sm space-y-1 ml-1" style={{ color: "var(--color-text-secondary)" }}>
            {plan.assumptions_changed.map((a: string, i: number) => (
              <li key={i} className="break-words">{a}</li>
            ))}
          </ul>
        </div>
      )}

      {isFeasible && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

          {/* Transport */}
          {Boolean(plan.transport?.price) && (
            <div 
              className="surface-card p-6 space-y-5 transition-colors cursor-default"
              onMouseEnter={() => setHoveredCard('transport')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div className="flex items-center gap-3 transition-colors" style={{ color: hoveredCard === 'transport' ? "var(--color-accent-500)" : "var(--color-text-muted)" }}>
                <Plane className="w-5 h-5 shrink-0" />
                <h3 className="text-sm font-medium uppercase tracking-widest">Transport</h3>
              </div>
              <div className="space-y-1">
                <div className="flex items-start justify-between gap-3">
                  <span className="text-xl font-semibold break-words min-w-0" style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>{plan.transport.airline}</span>
                  <span className="text-xl font-medium shrink-0" style={{ color: "var(--color-text-primary)" }}>₹{plan.transport.price.toLocaleString()}</span>
                </div>
                <p className="text-sm break-words" style={{ color: "var(--color-text-secondary)" }}>
                  {plan.transport.origin} → {plan.trip?.destination} <br/>
                  <span className="inline-block mt-1">{plan.transport.duration_hours}h flight • {plan.transport.date}</span>
                </p>
              </div>
            </div>
          )}

          {/* Hotel / Accommodation Section */}
          {((plan.hotels && plan.hotels.length > 0) || plan.hotel?.name) && (
            <div 
              className="surface-card p-6 space-y-4 transition-all cursor-pointer group hover:border-[var(--color-accent-500)]"
              onMouseEnter={() => setHoveredCard('hotel')}
              onMouseLeave={() => setHoveredCard(null)}
              onClick={() => {
                if (sessionId) {
                  setSelectedCityForModal(null)
                  setIsHotelModalOpen(true)
                }
              }}
            >
              <div className="flex items-center justify-between border-b pb-3" style={{ borderColor: "var(--color-border-subtle)" }}>
                <div className="flex items-center gap-3 transition-colors" style={{ color: hoveredCard === 'hotel' ? "var(--color-accent-500)" : "var(--color-text-muted)" }}>
                  <Hotel className="w-5 h-5 shrink-0" />
                  <h3 className="text-sm font-medium uppercase tracking-widest">Accommodation</h3>
                </div>
                {sessionId && (
                  <span className="text-xs flex items-center gap-1 text-[var(--color-accent-500)] opacity-80 group-hover:opacity-100 transition-opacity font-medium">
                    Change hotels <ExternalLink className="w-3 h-3" />
                  </span>
                )}
              </div>

              <div className="space-y-4 divide-y divide-[var(--color-border-subtle)]">
                {((plan.hotels && plan.hotels.length > 0) ? plan.hotels : [plan.hotel]).map((h: any, idx: number) => (
                  <div key={idx} className={idx > 0 ? "pt-3" : ""}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        {h.city && (
                          <span className="inline-block text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[var(--color-accent-500)]/10 text-[var(--color-accent-500)] mb-1">
                            {h.city}
                          </span>
                        )}
                        <h4 className="text-lg font-semibold break-words min-w-0" style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>
                          {h.name}
                        </h4>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-lg font-medium" style={{ color: "var(--color-text-primary)" }}>
                          ₹{h.total_price?.toLocaleString()}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm mt-1" style={{ color: "var(--color-text-secondary)" }}>
                      {h.nights} {h.nights === 1 ? "night" : "nights"} @ ₹{h.price_per_night?.toLocaleString()}/night
                      {h.rating && <span className="inline-block ml-2">{h.rating}★</span>}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Weather — full width, different layout weight */}
          {plan.weather?.condition && (
            <div 
              className="surface-card p-6 md:col-span-2 flex flex-col sm:flex-row sm:items-center gap-6 cursor-default transition-colors"
              style={{ backgroundColor: "var(--color-bg-raised)" }}
              onMouseEnter={() => setHoveredCard('weather')}
              onMouseLeave={() => setHoveredCard(null)}
            >
              <div className="flex items-center gap-4 shrink-0 w-48">
                <div 
                  className="p-3 rounded-full border transition-colors" 
                  style={{ 
                    color: hoveredCard === 'weather' ? "var(--color-accent-500)" : "var(--color-text-muted)",
                    borderColor: "var(--color-border)"
                  }}
                >
                  <CloudSun className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-medium text-slate-200" style={{ color: "var(--color-text-secondary)" }}>{plan.weather.condition}</h3>
                  <div className="text-2xl font-semibold" style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>
                    {plan.weather.temperature_high}°
                    <span className="text-lg ml-1" style={{ color: "var(--color-text-muted)" }}>/ {plan.weather.temperature_low}°</span>
                  </div>
                </div>
              </div>
              <div className="flex-1 min-w-0 pl-0 sm:pl-6 sm:border-l" style={{ borderColor: "var(--color-border)" }}>
                <p className="text-sm break-words leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {plan.weather.recommendation}
                </p>
              </div>
            </div>
          )}

        </div>
      )}

      {/* Infeasible suggestions */}
      {!isFeasible && plan.suggestions && plan.suggestions.length > 0 && (
        <div className="surface-card p-6">
          <h3 className="text-sm font-medium uppercase tracking-widest mb-4" style={{ color: "var(--color-text-primary)" }}>Alternatives</h3>
          <ul className="space-y-3">
            {plan.suggestions.map((s: string, i: number) => (
              <li key={i} className="text-sm flex gap-3" style={{ color: "var(--color-text-secondary)" }}>
                <span className="shrink-0 mt-0.5" style={{ color: "var(--color-accent-500)" }}>→</span>
                <span className="break-words leading-relaxed">{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Execution summary */}
      {plan.execution_summary && plan.execution_summary.length > 0 && (
        <div className="surface-card p-6 border-t" style={{ backgroundColor: "transparent", borderColor: "var(--color-border-subtle)" }}>
          <h3 className="text-sm font-medium uppercase tracking-widest mb-4" style={{ color: "var(--color-text-muted)" }}>Execution Summary</h3>
          <ul className="space-y-2">
            {plan.execution_summary.map((s: string, i: number) => (
              <li key={i} className="text-sm flex gap-3" style={{ color: "var(--color-text-secondary)" }}>
                <span className="shrink-0 font-mono font-bold" style={{ color: "var(--color-accent-500)" }}>{String(i + 1).padStart(2, '0')}</span>
                <span className="break-words" style={{ color: "var(--color-text-primary)" }}>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sessionId && onPlanUpdate && (
        <HotelPickerModal
          isOpen={isHotelModalOpen}
          onClose={() => setIsHotelModalOpen(false)}
          sessionId={sessionId}
          currentHotelName={plan.hotel?.name || ""}
          currentHotels={plan.hotels || (plan.hotel?.name ? [plan.hotel] : [])}
          initialCity={selectedCityForModal}
          onPlanUpdate={onPlanUpdate}
        />
      )}
    </motion.div>
  )
}
