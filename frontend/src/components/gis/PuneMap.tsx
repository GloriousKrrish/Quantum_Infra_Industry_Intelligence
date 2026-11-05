import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { Parcel } from "../../lib/api";
import { Layers, MapPin, Navigation, Eye, EyeOff } from "lucide-react";

interface PuneMapProps {
  parcels: Parcel[];
  selectedParcelId: string | number | null;
  onSelectParcel: (parcel: Parcel) => void;
  onOpenProfile?: (parcel: Parcel) => void;
  winningParcels?: string[];
}

// Canonical OpenStreetMap coordinates for the 8 PMRDA micro-markets
const PARCEL_COORDS: Record<string, [number, number]> = {
  "Wagholi East": [18.5788, 73.9787],
  "Chakan Industrial": [18.7609, 73.8639],
  "Hinjawadi Phase 3": [18.5912, 73.7380],
  "Hinjewadi Phase III": [18.5912, 73.7380],
  "Talegaon Dabhade": [18.7335, 73.6757],
  "Hadapsar Extension": [18.5089, 73.9260],
  "Hadapsar Growth Zone": [18.5089, 73.9260],
  "Pirangut Corridor": [18.5164, 73.6863],
  "Kharadi IT Hub": [18.5535, 73.9455],
  "Kharadi IT Park": [18.5535, 73.9455],
  "Mamurdi PCMC": [18.6571, 73.7889],
};

// Verified Key Regional Infrastructure Anchors
const REGIONAL_INFRA_ANCHORS = [
  { name: "Mumbai-Pune Expressway (Urse)", type: "Highway", coords: [18.7180, 73.6930] as [number, number], color: "#2563eb" },
  { name: "NH-48 Bypass (Warje)", type: "Highway", coords: [18.4850, 73.8050] as [number, number], color: "#2563eb" },
  { name: "Pune-Nashik Highway (Bhosari)", type: "Highway", coords: [18.6300, 73.8450] as [number, number], color: "#2563eb" },
  { name: "Pune-Nagar Road SH-27", type: "Highway", coords: [18.5800, 73.9800] as [number, number], color: "#2563eb" },
  { name: "Aditya Birla Hospital (Chinchwad)", type: "Hospital", coords: [18.6294, 73.7801] as [number, number], color: "#f43f5e" },
  { name: "Ruby Hall Clinic (Sasoon Rd)", type: "Hospital", coords: [18.5323, 73.8770] as [number, number], color: "#f43f5e" },
  { name: "COEP Technological University", type: "Education", coords: [18.5284, 73.8567] as [number, number], color: "#6366f1" },
  { name: "Pune Junction Railway Station", type: "Railway", coords: [18.5289, 73.8744] as [number, number], color: "#d97706" },
  { name: "Talegaon Suburban Station", type: "Railway", coords: [18.7305, 73.6730] as [number, number], color: "#d97706" },
  { name: "Pune International Airport (PNQ)", type: "Airport", coords: [18.5822, 73.9197] as [number, number], color: "#7c3aed" },
  { name: "Rajiv Gandhi IT Park (Hinjawadi)", type: "Commercial", coords: [18.5910, 73.7380] as [number, number], color: "#0d9488" },
  { name: "EON Free Zone / WTC (Kharadi)", type: "Commercial", coords: [18.5510, 73.9510] as [number, number], color: "#0d9488" },
];

export default function PuneMap({
  parcels,
  selectedParcelId,
  onSelectParcel,
  onOpenProfile,
  winningParcels = [],
}: PuneMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<L.CircleMarker[]>([]);
  const infraMarkersRef = useRef<L.CircleMarker[]>([]);

  const [showInfraAnchors, setShowInfraAnchors] = useState<boolean>(true);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [18.58, 73.84],
        zoom: 11,
        zoomControl: false, // Custom controls
      });

      // Standard OpenStreetMap Tiles
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | PMRDA GIS',
        maxZoom: 18,
        subdomains: ["a", "b", "c"],
      }).addTo(map);

      mapInstanceRef.current = map;
    }
  }, []);

  // Update Markers when parcels or selection changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear previous parcel markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Add parcel markers
    parcels.forEach((parcel) => {
      const coords = PARCEL_COORDS[parcel.name] || [parcel.location_lat || 18.5204, parcel.location_lng || 73.8567];
      const isSelected = selectedParcelId !== null && String(selectedParcelId) === String(parcel.id);
      const isWinner = winningParcels.includes(parcel.name);

      const color = isWinner ? "#2563eb" : isSelected ? "#059669" : "#475569";
      const fillColor = isWinner ? "#3b82f6" : isSelected ? "#10b981" : "#64748b";
      const radius = isSelected ? 12 : isWinner ? 10 : 8;

      const marker = L.circleMarker(coords, {
        radius,
        fillColor,
        color: isSelected ? "#ffffff" : color,
        weight: isSelected ? 3 : 2,
        opacity: 1,
        fillOpacity: isSelected ? 0.95 : 0.8,
      }).addTo(map);

      // Popup content
      const popupDiv = document.createElement("div");
      popupDiv.className = "p-1 min-w-[200px] text-slate-800 font-sans";
      popupDiv.innerHTML = `
        <div style="margin-bottom: 6px;">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: 700; font-size: 13px; color: #0f172a;">${parcel.name}</span>
            <span style="font-size: 10px; font-weight: 700; color: #2563eb; background: #eff6ff; padding: 2px 6px; border-radius: 6px;">
              ₹${parcel.price_crore.toFixed(1)} Cr
            </span>
          </div>
          <span style="font-size: 10px; color: #64748b; font-family: monospace;">${parcel.id} • ${parcel.zone_type.toUpperCase()}</span>
        </div>
        <div style="font-size: 11px; margin-bottom: 8px; color: #334155;">
          <span>Area: <b>${parcel.area_acres} Acres</b></span> | 
          <span>Return: <b style="color: #059669;">+${parcel.projected_return_pct}%</b></span>
        </div>
        <button id="btn-inspect-${parcel.id}" style="width: 100%; background: #2563eb; color: #ffffff; border: none; padding: 6px 10px; font-size: 11px; font-weight: 600; border-radius: 6px; cursor: pointer;">
          Open Detailed Profile
        </button>
      `;

      // Attach button listener after popup opens
      marker.bindPopup(popupDiv);
      marker.on("popupopen", () => {
        const btn = document.getElementById(`btn-inspect-${parcel.id}`);
        if (btn) {
          btn.onclick = () => {
            onSelectParcel(parcel);
            if (onOpenProfile) onOpenProfile(parcel);
          };
        }
      });

      marker.on("click", () => {
        onSelectParcel(parcel);
      });

      markersRef.current.push(marker);
    });
  }, [parcels, selectedParcelId, winningParcels, onSelectParcel, onOpenProfile]);

  // Update Infrastructure Anchors
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    infraMarkersRef.current.forEach((m) => m.remove());
    infraMarkersRef.current = [];

    if (showInfraAnchors) {
      REGIONAL_INFRA_ANCHORS.forEach((anchor) => {
        const marker = L.circleMarker(anchor.coords, {
          radius: 5,
          fillColor: anchor.color,
          color: "#ffffff",
          weight: 1.5,
          opacity: 0.9,
          fillOpacity: 0.85,
        }).addTo(map);

        marker.bindTooltip(
          `<div style="font-size: 10px; font-weight: 600;">${anchor.name} (${anchor.type})</div>`,
          { direction: "top", offset: [0, -5] }
        );

        infraMarkersRef.current.push(marker);
      });
    }
  }, [showInfraAnchors]);

  // Map controls
  function handleZoomIn() {
    mapInstanceRef.current?.zoomIn();
  }

  function handleZoomOut() {
    mapInstanceRef.current?.zoomOut();
  }

  function handleResetView() {
    mapInstanceRef.current?.setView([18.58, 73.84], 11);
  }

  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-xs">
      <div ref={mapContainerRef} className="h-full w-full" style={{ minHeight: "420px" }} />

      {/* Top Left: GIS HUD */}
      <div className="pointer-events-none absolute left-4 top-4 z-[400] flex flex-col gap-1 rounded-xl border border-slate-200 bg-white/95 p-3 shadow-sm backdrop-blur-xs">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
          <span className="font-display text-xs font-bold text-slate-900 tracking-tight">
            PMRDA Geospatial GIS Layer
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[10px] text-slate-500">
          <span>Pune Metro (18.58° N, 73.84° E)</span>
          <span>•</span>
          <span className="text-blue-700 font-semibold">{parcels.length} Cadastral Plots</span>
        </div>
      </div>

      {/* Top Right: Layer & Zoom Controls */}
      <div className="absolute right-4 top-4 z-[400] flex flex-col gap-2">
        <div className="flex flex-col rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <button
            onClick={handleZoomIn}
            className="p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors font-bold text-sm"
            title="Zoom In"
          >
            +
          </button>
          <div className="h-px bg-slate-200" />
          <button
            onClick={handleZoomOut}
            className="p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors font-bold text-sm"
            title="Zoom Out"
          >
            -
          </button>
          <div className="h-px bg-slate-200" />
          <button
            onClick={handleResetView}
            className="p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            title="Reset to Pune Extent"
          >
            <Navigation className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Toggle Infrastructure Anchors */}
        <button
          onClick={() => setShowInfraAnchors(!showInfraAnchors)}
          className={`flex items-center gap-1.5 rounded-xl border px-2.5 py-1.5 text-[11px] font-semibold shadow-sm transition-all ${
            showInfraAnchors
              ? "border-blue-200 bg-blue-50 text-blue-700"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
          }`}
          title="Toggle Regional Infrastructure Anchors"
        >
          <Layers className="h-3.5 w-3.5" />
          <span>Infra Points</span>
          {showInfraAnchors ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
        </button>
      </div>

      {/* Bottom Right: GIS Legend */}
      <div className="pointer-events-none absolute bottom-4 right-4 z-[400] flex items-center gap-3 rounded-xl border border-slate-200 bg-white/95 px-3 py-1.5 text-[10px] font-medium text-slate-600 shadow-sm backdrop-blur-xs">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
          <span>QAOA Selection</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
          <span>Active Plot</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-slate-500" />
          <span>Candidate</span>
        </div>
        {showInfraAnchors && (
          <div className="flex items-center gap-1.5 pl-1 border-l border-slate-200">
            <span className="h-2 w-2 rounded-full bg-indigo-500" />
            <span>Infra Anchor</span>
          </div>
        )}
      </div>
    </div>
  );
}
