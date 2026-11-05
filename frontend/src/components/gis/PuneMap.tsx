import { useEffect, useRef } from "react";
import L from "leaflet";
import type { Parcel } from "../../lib/api";

interface PuneMapProps {
  parcels: Parcel[];
  selectedParcelId: string | number | null;
  onSelectParcel: (parcel: Parcel) => void;
  winningParcels?: string[];
}

// Coordinates mapping for Pune PMRDA micro-markets
const PARCEL_COORDS: Record<string, [number, number]> = {
  "Hinjewadi Phase III": [18.5913, 73.7389],
  "Hinjawadi Phase 3": [18.5913, 73.7389],
  "Wakad Central": [18.5987, 73.7707],
  "Baner Hilltop": [18.5590, 73.7868],
  "Kharadi IT Park": [18.5515, 73.9348],
  "Wagholi East": [18.5810, 73.9810],
  "Hadapsar Growth Zone": [18.5089, 73.9259],
  "Hadapsar Extension": [18.5089, 73.9259],
  "Viman Nagar Premium": [18.5679, 73.9143],
  "Undri Greenfield": [18.4485, 73.9125],
  "Chakan Industrial": [18.7565, 73.8580],
  "Talegaon Dabhade": [18.7350, 73.6750],
  "Mamurdi PCMC": [18.6675, 73.7125],
  "Pirangut Corridor": [18.5120, 73.6810],
};

export default function PuneMap({
  parcels,
  selectedParcelId,
  onSelectParcel,
  winningParcels = [],
}: PuneMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize map centered at Pune
      const map = L.map(mapContainerRef.current, {
        center: [18.57, 73.84],
        zoom: 11,
        zoomControl: true,
      });

      // OpenStreetMap clean tile layer without watermark
      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | PMRDA Cadastral Data',
          maxZoom: 19,
          subdomains: ["a", "b", "c"],
        }
      ).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear previous markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Add parcel markers
    parcels.forEach((parcel) => {
      const coords = PARCEL_COORDS[parcel.name] || [18.5204, 73.8567];
      const isSelected = selectedParcelId !== null && String(selectedParcelId) === String(parcel.id);
      const isWinner = winningParcels.includes(parcel.name);

      const color = isWinner ? "#22d3ee" : isSelected ? "#10b981" : "#64748b";
      const radius = isWinner ? 12 : isSelected ? 10 : 8;

      const marker = L.circleMarker(coords, {
        radius,
        fillColor: color,
        color: isWinner ? "#ffffff" : color,
        weight: isWinner ? 2.5 : 1.5,
        opacity: 1,
        fillOpacity: isWinner ? 0.9 : 0.7,
      }).addTo(map);

      // Popup Content
      const popupHtml = `
        <div style="min-width: 190px; padding: 4px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-weight: 700; font-size: 13px; color: #ffffff;">${parcel.name}</span>
            <span style="font-size: 10px; padding: 2px 6px; border-radius: 9999px; background: ${
              isWinner ? "rgba(34, 211, 238, 0.2)" : "rgba(16, 185, 129, 0.2)"
            }; color: ${isWinner ? "#22d3ee" : "#34d399"}; font-weight: 600;">
              ${isWinner ? "QAOA PICK" : "₹" + parcel.price_cr + " Cr"}
            </span>
          </div>
          <div style="font-size: 11px; color: #94a3b8; margin-bottom: 8px;">
            Area: <b style="color: #f1f5f9;">${parcel.area_acres} Acres</b> | Return: <b style="color: #34d399;">+${parcel.return_pct}%</b>
          </div>
          <div style="background: rgba(2, 6, 23, 0.6); padding: 6px; border-radius: 6px; font-size: 10px; margin-bottom: 6px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span style="color: #64748b;">Water Supply:</span>
              <span style="color: #38bdf8; font-weight: 600;">${Math.round(parcel.infra_scores.water * 100)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
              <span style="color: #64748b;">Power Grid:</span>
              <span style="color: #fbbf24; font-weight: 600;">${Math.round(parcel.infra_scores.power * 100)}%</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: #64748b;">Road Connectivity:</span>
              <span style="color: #a78bfa; font-weight: 600;">${Math.round(parcel.infra_scores.road * 100)}%</span>
            </div>
          </div>
          <div style="font-size: 9px; color: #64748b; text-align: right; font-family: monospace;">
            PMRDA · Cadastral Verified
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.on("click", () => {
        onSelectParcel(parcel);
      });

      markersRef.current.push(marker);
    });

    return () => {
      // Map cleanup if needed
    };
  }, [parcels, selectedParcelId, winningParcels, onSelectParcel]);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
      <div ref={mapContainerRef} className="h-full w-full" style={{ minHeight: "360px" }} />

      {/* Map Telemetry HUD Overlay */}
      <div className="pointer-events-none absolute left-3 top-3 z-[400] flex flex-col gap-1.5 rounded-lg border border-slate-800/80 bg-slate-950/80 p-2.5 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="font-mono text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
            Pune PMRDA Geospatial GIS
          </span>
        </div>
        <div className="flex items-center gap-3 font-mono text-[10px] text-slate-400">
          <span>Lat: 18.5204° N</span>
          <span>Lng: 73.8567° E</span>
          <span className="text-cyan-400">{parcels.length} Active Parcels</span>
        </div>
      </div>

      {/* Legend Badge */}
      <div className="pointer-events-none absolute bottom-3 right-3 z-[400] flex items-center gap-3 rounded-lg border border-slate-800/80 bg-slate-950/80 px-3 py-1.5 text-[10px] font-mono text-slate-300 backdrop-blur-md">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
          <span>QAOA Selection</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
          <span>Active Focus</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-500" />
          <span>Candidate</span>
        </div>
      </div>
    </div>
  );
}
