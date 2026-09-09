"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Star, MapPin, CheckCircle, Loader2, Building2 } from "lucide-react"
import { fetchHotelOptions, selectHotel } from "@/lib/api"

interface HotelPickerModalProps {
  isOpen: boolean
  onClose: () => void
  sessionId: string
  currentHotelName: string
  currentHotels?: any[]
  initialCity?: string | null
  onPlanUpdate: (updatedPlan: any) => void
}

export function HotelPickerModal({
  isOpen,
  onClose,
  sessionId,
  currentHotelName,
  currentHotels = [],
  initialCity = null,
  onPlanUpdate
}: HotelPickerModalProps) {
  const [hotels, setHotels] = useState<any[]>([])
  const [byCity, setByCity] = useState<Record<string, any[]>>({})
  const [cities, setCities] = useState<string[]>([])
  const [selectedCityTab, setSelectedCityTab] = useState<string>("ALL")
  const [isLoading, setIsLoading] = useState(false)
  const [isUpdating, setIsUpdating] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && sessionId) {
      loadHotels()
    }
  }, [isOpen, sessionId])

  const loadHotels = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await fetchHotelOptions(sessionId)
      const allHotelsList = data.hotels || []
      const citiesList = data.cities || []
      const byCityMap = data.by_city || {}

      setHotels(allHotelsList)
      setCities(citiesList)
      setByCity(byCityMap)
      
      if (initialCity && citiesList.includes(initialCity)) {
        setSelectedCityTab(initialCity)
      } else {
        setSelectedCityTab("ALL")
      }
    } catch (err: any) {
      setError(err.message || "Failed to load hotels")
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelect = async (hotel: any) => {
    try {
      setIsUpdating(hotel.name)
      setError(null)
      const updatedPlan = await selectHotel(sessionId, hotel.name, hotel.city)
      onPlanUpdate(updatedPlan)
      onClose()
    } catch (err: any) {
      setError(err.message || "Failed to update hotel selection")
    } finally {
      setIsUpdating(null)
    }
  }

  const isHotelSelected = (hotel: any) => {
    if (currentHotels && currentHotels.length > 0) {
      return currentHotels.some((ch: any) => {
        const nameMatch = ch.name && hotel.name && (
          ch.name.toLowerCase() === hotel.name.toLowerCase() ||
          ch.name.toLowerCase().includes(hotel.name.toLowerCase()) ||
          hotel.name.toLowerCase().includes(ch.name.toLowerCase())
        )
        if (!nameMatch) return false
        if (ch.city && hotel.city) {
          return ch.city.toLowerCase() === hotel.city.toLowerCase()
        }
        return true
      })
    }
    return Boolean(
      currentHotelName && hotel.name && (
        currentHotelName.toLowerCase() === hotel.name.toLowerCase() ||
        currentHotelName.toLowerCase().includes(hotel.name.toLowerCase())
      )
    )
  }

  const filteredHotels = selectedCityTab === "ALL" 
    ? hotels 
    : (byCity[selectedCityTab] || hotels.filter(h => h.city === selectedCityTab))

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md"
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.98 }}
            transition={{ type: "spring", bounce: 0, duration: 0.3 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 pointer-events-none"
          >
            <div 
              className="w-full max-w-4xl max-h-[85vh] flex flex-col surface-card overflow-hidden shadow-2xl pointer-events-auto rounded-2xl border"
              style={{ 
                backgroundColor: "var(--color-bg-raised)",
                borderColor: "rgba(255, 255, 255, 0.1)"
              }}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-5 border-b" style={{ borderColor: "rgba(255, 255, 255, 0.08)" }}>
                <div>
                  <h2 className="text-xl font-semibold flex items-center gap-2.5" style={{ fontFamily: "var(--font-display)", color: "var(--color-text-primary)" }}>
                    <Building2 className="w-5 h-5" style={{ color: "var(--color-accent-500)" }} />
                    Accommodation Options
                  </h2>
                  <p className="text-xs mt-1" style={{ color: "var(--color-text-secondary)" }}>
                    Select a hotel for any city to update your stay independently
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-full hover:bg-white/10 transition-colors cursor-pointer text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* City Filter Pills (Sleek Segmented Control UI) */}
              {cities.length > 1 && (
                <div className="px-6 py-3 border-b flex items-center gap-2 overflow-x-auto custom-scrollbar" style={{ borderColor: "rgba(255, 255, 255, 0.08)", backgroundColor: "rgba(0, 0, 0, 0.25)" }}>
                  <button
                    onClick={() => setSelectedCityTab("ALL")}
                    className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 flex items-center gap-1.5 cursor-pointer ${
                      selectedCityTab === "ALL"
                        ? "bg-[var(--color-accent-500)] text-black shadow-md font-bold"
                        : "bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white border border-white/5"
                    }`}
                  >
                    <span>All Cities</span>
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${selectedCityTab === "ALL" ? "bg-black/20 text-black font-bold" : "bg-black/40 text-slate-300"}`}>
                      {hotels.length}
                    </span>
                  </button>
                  {cities.map((city) => {
                    const count = (byCity[city] || []).length
                    const isSelected = selectedCityTab === city
                    return (
                      <button
                        key={city}
                        onClick={() => setSelectedCityTab(city)}
                        className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0 flex items-center gap-1.5 cursor-pointer ${
                          isSelected
                            ? "bg-[var(--color-accent-500)] text-black shadow-md font-bold"
                            : "bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white border border-white/5"
                        }`}
                      >
                        <MapPin className={`w-3 h-3 ${isSelected ? "text-black" : "text-[var(--color-accent-500)]"}`} />
                        <span>{city}</span>
                        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${isSelected ? "bg-black/20 text-black font-bold" : "bg-black/40 text-slate-300"}`}>
                          {count}
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Error Banner */}
              {error && (
                <div className="p-4 mx-6 mt-6 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  {error}
                </div>
              )}

              {/* Grid Content */}
              <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-20 space-y-3">
                    <Loader2 className="w-8 h-8 animate-spin text-[var(--color-accent-500)]" />
                    <p className="text-sm text-slate-400">Loading scraped hotel options...</p>
                  </div>
                ) : filteredHotels.length === 0 ? (
                  <div className="text-center py-20 text-sm text-slate-400">
                    No hotel options available for this selection.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {filteredHotels.map((hotel, idx) => {
                      const isSelected = isHotelSelected(hotel)
                      const isCurrentlyUpdating = isUpdating === hotel.name

                      return (
                        <div
                          key={idx}
                          onClick={() => !isUpdating && handleSelect(hotel)}
                          className={`
                            relative p-5 rounded-xl border-2 transition-all duration-200 cursor-pointer flex flex-col justify-between
                            ${isSelected ? 'border-[var(--color-accent-500)] bg-[var(--color-accent-500)]/10 shadow-lg' : 'border-white/10 hover:border-white/20 bg-white/[0.02] hover:bg-white/[0.04]'}
                            ${isUpdating && !isCurrentlyUpdating ? 'opacity-40 pointer-events-none' : ''}
                          `}
                        >
                          <div>
                            {/* Selection Badge */}
                            {isSelected && (
                              <div className="absolute top-0 right-0 transform translate-x-2 -translate-y-2 z-10">
                                <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold shadow-md bg-[var(--color-accent-500)] text-black">
                                  <CheckCircle className="w-3 h-3" />
                                  <span>Selected</span>
                                </div>
                              </div>
                            )}

                            {/* City Tag Badge */}
                            {hotel.city && (
                              <div className="mb-2">
                                <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-[var(--color-accent-500)]/15 border border-[var(--color-accent-500)]/30 text-[var(--color-accent-500)]">
                                  <MapPin className="w-3 h-3" />
                                  <span>{hotel.city}</span>
                                </span>
                              </div>
                            )}
                            
                            <div className="flex justify-between items-start gap-4 mb-3">
                              <h3 className="font-semibold text-base leading-snug text-white">
                                {hotel.name}
                              </h3>
                              <div className="shrink-0 text-right">
                                <div className="font-semibold text-lg text-white">
                                  ₹{hotel.price_per_night?.toLocaleString()}
                                </div>
                                <div className="text-[11px] text-slate-400">
                                  / night
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          <div className="space-y-2 pt-2 text-xs border-t border-white/5 text-slate-300">
                            <div className="flex items-center gap-1.5">
                              <Star className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
                              <span className="font-medium text-white">{hotel.rating} Stars</span>
                              {hotel.type && (
                                <>
                                  <span className="opacity-30">•</span>
                                  <span className="capitalize text-slate-400">{hotel.type}</span>
                                </>
                              )}
                            </div>
                            
                            {hotel.location && (
                              <div className="flex items-start gap-1.5 line-clamp-2 text-slate-400">
                                <MapPin className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500" />
                                <span>{hotel.location}</span>
                              </div>
                            )}
                          </div>

                          {/* Selection Spinner Overlay */}
                          {isCurrentlyUpdating && (
                            <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-black/60 backdrop-blur-[2px]">
                              <Loader2 className="w-6 h-6 animate-spin text-[var(--color-accent-500)]" />
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
