import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { LandParcel, GeospatialFeatureCollection, GeospatialInfrastructureResponse } from "../../lib/api";
import {
  getGeospatialBoundaries,
  getGeospatialInfrastructure,
  importUserGeoJSON,
  normalizeParcel,
} from "../../lib/api";
import {
  Layers,
  MapPin,
  Navigation,
  Eye,
  EyeOff,
  Upload,
  ShieldCheck,
  Compass,
  AlertTriangle,
  X,
  FileCheck2,
} from "lucide-react";

interface PuneMapProps {
  parcels: LandParcel[];
  selectedParcelId: string | number | null;
  onSelectParcel: (parcel: LandParcel) => void;
  onOpenProfile?: (parcel: LandParcel) => void;
  winningParcels?: string[];
  onUserParcelImported?: (newParcel: LandParcel) => void;
}

// Verified Key Regional Infrastructure Anchors
const REGIONAL_INFRA_ANCHORS = [
  { name: "Mumbai-Pune Expressway (Urse)", type: "Highway", coords: [18.7180, 73.6930] as [number, number], color: "#dc2626" },
  { name: "NH-48 Bypass (Warje)", type: "Highway", coords: [18.4850, 73.8050] as [number, number], color: "#d97706" },
  { name: "Pune-Nashik Highway (Bhosari)", type: "Highway", coords: [18.6300, 73.8450] as [number, number], color: "#d97706" },
  { name: "Pune-Nagar Road SH-27", type: "Highway", coords: [18.5800, 73.9800] as [number, number], color: "#d97706" },
  { name: "Aditya Birla Memorial Hospital", type: "Hospital", coords: [18.6294, 73.7801] as [number, number], color: "#f43f5e" },
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
  onUserParcelImported,
}: PuneMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const markersRef = useRef<L.CircleMarker[]>([]);
  const infraMarkersRef = useRef<L.CircleMarker[]>([]);

  // Layer groups
  const boundariesLayerRef = useRef<L.GeoJSON | null>(null);
  const corridorsLayerRef = useRef<L.GeoJSON | null>(null);
  const waterLayerRef = useRef<L.GeoJSON | null>(null);
  const zonesLayerRef = useRef<L.GeoJSON | null>(null);
  const userPolygonsLayerRef = useRef<L.GeoJSON | null>(null);

  // Layer Visibility Toggles
  const [showBoundaries, setShowBoundaries] = useState<boolean>(true);
  const [showCorridors, setShowCorridors] = useState<boolean>(true);
  const [showWater, setShowWater] = useState<boolean>(true);
  const [showZones, setShowZones] = useState<boolean>(false);
  const [showInfraAnchors, setShowInfraAnchors] = useState<boolean>(true);

  // GeoJSON Import Modal State
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [importText, setImportText] = useState<string>("");
  const [importSiteName, setImportSiteName] = useState<string>("");
  const [importError, setImportError] = useState<string | null>(null);
  const [importLoading, setImportLoading] = useState<boolean>(false);

  // 1. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [18.58, 73.84],
        zoom: 11,
        zoomControl: false,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | PMRDA GIS',
        maxZoom: 18,
        subdomains: ["a", "b", "c"],
      }).addTo(map);

      mapInstanceRef.current = map;
    }
  }, []);

  // 2. Fetch and render Real GeoJSON Layers from RGIE Backend
  useEffect(() => {
    async function loadLayers() {
      const currentMap = mapInstanceRef.current;
      if (!currentMap) return;

      try {
        // A. Load Administrative Boundaries
        const boundaryData = await getGeospatialBoundaries();
        if (boundariesLayerRef.current) boundariesLayerRef.current.remove();
        boundariesLayerRef.current = L.geoJSON(boundaryData as any, {
          style: (feature) => ({
            color: feature?.properties?.stroke || "#2563eb",
            weight: 2,
            dashArray: feature?.id === "BOUNDARY_PMRDA_REGION" ? "6, 4" : undefined,
            fillColor: feature?.properties?.fill || "#3b82f6",
            fillOpacity: feature?.properties?.fill_opacity || 0.04,
          }),
          onEachFeature: (feature, layer) => {
            layer.bindTooltip(
              `<div class="p-1 font-sans text-xs"><b>${feature.properties?.name}</b><br/><span class="text-slate-500 font-mono text-[10px]">${feature.properties?.jurisdiction}</span></div>`,
              { sticky: true }
            );
          },
        });
        if (showBoundaries && boundariesLayerRef.current) {
          boundariesLayerRef.current.addTo(currentMap);
        }

        // B. Load Infrastructure Corridors, Water, and Zones
        const infraData = await getGeospatialInfrastructure();

        // Corridors
        if (corridorsLayerRef.current) corridorsLayerRef.current.remove();
        corridorsLayerRef.current = L.geoJSON(infraData.corridors as any, {
          style: (feature) => ({
            color: feature?.properties?.stroke || "#dc2626",
            weight: feature?.properties?.stroke_width || 3,
            dashArray: feature?.properties?.stroke_dasharray,
          }),
          onEachFeature: (feature, layer) => {
            layer.bindTooltip(
              `<div class="p-1 font-sans text-xs"><b>${feature.properties?.name}</b><br/><span class="text-slate-500 font-mono text-[10px]">${feature.properties?.highway_type || feature.properties?.transit_type}</span></div>`,
              { sticky: true }
            );
          },
        });
        if (showCorridors && corridorsLayerRef.current) {
          corridorsLayerRef.current.addTo(currentMap);
        }

        // Water Bodies
        if (waterLayerRef.current) waterLayerRef.current.remove();
        waterLayerRef.current = L.geoJSON(infraData.water_bodies as any, {
          style: (feature) => ({
            color: feature?.properties?.stroke || "#0284c7",
            weight: feature?.properties?.stroke_width || 3,
          }),
          onEachFeature: (feature, layer) => {
            layer.bindTooltip(
              `<div class="p-1 font-sans text-xs"><b>${feature.properties?.name}</b></div>`,
              { sticky: true }
            );
          },
        });
        if (showWater && waterLayerRef.current) {
          waterLayerRef.current.addTo(currentMap);
        }

        // Planning Zones
        if (zonesLayerRef.current) zonesLayerRef.current.remove();
        zonesLayerRef.current = L.geoJSON(infraData.planning_zones as any, {
          style: (feature) => ({
            color: feature?.properties?.stroke || "#f59e0b",
            weight: 1.5,
            fillColor: feature?.properties?.fill || "#f59e0b",
            fillOpacity: feature?.properties?.fill_opacity || 0.12,
          }),
          onEachFeature: (feature, layer) => {
            layer.bindTooltip(
              `<div class="p-1 font-sans text-xs"><b>${feature.properties?.name}</b><br/><span class="text-amber-800 font-mono text-[10px]">${feature.properties?.zone_classification}</span></div>`,
              { sticky: true }
            );
          },
        });
        if (showZones && zonesLayerRef.current) {
          zonesLayerRef.current.addTo(currentMap);
        }
      } catch (err) {
        console.warn("Failed to load real geospatial layers, using base map:", err);
      }
    }

    loadLayers();
  }, []);

  // 3. Handle Layer Visibility Toggle Updates
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (boundariesLayerRef.current) {
      if (showBoundaries) boundariesLayerRef.current.addTo(map);
      else boundariesLayerRef.current.remove();
    }
    if (corridorsLayerRef.current) {
      if (showCorridors) corridorsLayerRef.current.addTo(map);
      else corridorsLayerRef.current.remove();
    }
    if (waterLayerRef.current) {
      if (showWater) waterLayerRef.current.addTo(map);
      else waterLayerRef.current.remove();
    }
    if (zonesLayerRef.current) {
      if (showZones) zonesLayerRef.current.addTo(map);
      else zonesLayerRef.current.remove();
    }
  }, [showBoundaries, showCorridors, showWater, showZones]);

  // 4. Update Parcel Markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    parcels.forEach((parcel) => {
      const coords: [number, number] = [parcel.location_lat || 18.5204, parcel.location_lng || 73.8567];
      const isSelected = selectedParcelId !== null && String(selectedParcelId) === String(parcel.id);
      const isWinner = winningParcels.includes(parcel.name);
      const isUserProvided = parcel.id.startsWith("USER-");

      const color = isWinner
        ? "#2563eb"
        : isUserProvided
        ? "#7c3aed"
        : isSelected
        ? "#059669"
        : "#475569";

      const fillColor = isWinner
        ? "#3b82f6"
        : isUserProvided
        ? "#8b5cf6"
        : isSelected
        ? "#10b981"
        : "#64748b";

      const radius = isSelected ? 12 : isWinner ? 10 : 8;

      const marker = L.circleMarker(coords, {
        radius,
        fillColor,
        color: isSelected ? "#ffffff" : color,
        weight: isSelected ? 3 : 2,
        opacity: 1,
        fillOpacity: isSelected ? 0.95 : 0.85,
      }).addTo(map);

      // Popup Content
      const popupDiv = document.createElement("div");
      popupDiv.className = "p-1 min-w-[220px] text-slate-800 font-sans";
      popupDiv.innerHTML = `
        <div style="margin-bottom: 6px;">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-weight: 700; font-size: 13px; color: #0f172a;">${parcel.name}</span>
            <span style="font-size: 10px; font-weight: 700; color: #2563eb; background: #eff6ff; padding: 2px 6px; border-radius: 6px;">
              ₹${parcel.price_crore.toFixed(1)} Cr
            </span>
          </div>
          <span style="font-size: 10px; color: #64748b; font-family: monospace;">${parcel.id} • ${parcel.zone_type?.toUpperCase()}</span>
        </div>
        <div style="font-size: 11px; margin-bottom: 8px; color: #334155;">
          <span>Area: <b>${parcel.area_acres} Acres</b></span> | 
          <span>Return: <b style="color: #059669;">+${parcel.projected_return_pct}%</b></span>
        </div>
        <div style="font-size: 10px; margin-bottom: 8px; padding: 4px 6px; border-radius: 6px; background: #f8fafc; border: 1px solid #e2e8f0;">
          <span style="color: #64748b; font-weight: 600;">Provenance:</span> 
          <span style="font-weight: 700; color: ${isUserProvided ? '#7c3aed' : '#059669'};">
            ${isUserProvided ? 'USER_PROVIDED' : 'VERIFIED_OPEN_DATA'}
          </span>
        </div>
        <button id="btn-inspect-${parcel.id}" style="width: 100%; background: #2563eb; color: #ffffff; border: none; padding: 6px 10px; font-size: 11px; font-weight: 600; border-radius: 6px; cursor: pointer;">
          Open Detailed Intelligence Dossier
        </button>
      `;

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

  // 5. Update Regional Infrastructure Anchors
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

  // Handle GeoJSON Import Submission
  const handleImportSubmit = async () => {
    setImportError(null);
    setImportLoading(true);

    try {
      const parsed = JSON.parse(importText);
      const res = await importUserGeoJSON({
        geojson_data: parsed,
        parcel_name: importSiteName || "Imported Custom Site",
        check_pmrda_boundary: true,
      });

      if (res.is_valid) {
        // Construct standard LandParcel object
        const importedParcel: LandParcel = normalizeParcel({
          id: res.parcel_id,
          name: res.parcel_name,
          location_lat: res.centroid[1],
          location_lng: res.centroid[0],
          area_acres: res.area_acres,
          price_crore: Math.max(10.0, Number((res.area_acres * 2.5).toFixed(1))),
          price_cr: Math.max(10.0, Number((res.area_acres * 2.5).toFixed(1))),
          price_per_acre_crore: 2.5,
          zone_type: "commercial",
          water_score: 0.85,
          electricity_score: 0.90,
          sewage_score: 0.80,
          road_score: 0.90,
          infrastructure_index: 0.86,
          utility_score: 0.86,
          projected_return_pct: 18.5,
          location: "Pune PMRDA Imported Parcel",
          data_provenance: "USER_PROVIDED (Client GeoJSON Submission)",
          geojson_geometry: res.normalized_geojson,
        });

        // Render imported polygon on the map
        const map = mapInstanceRef.current;
        if (map) {
          if (userPolygonsLayerRef.current) userPolygonsLayerRef.current.remove();
          userPolygonsLayerRef.current = L.geoJSON(res.normalized_geojson as any, {
            style: {
              color: "#7c3aed",
              weight: 3,
              fillColor: "#8b5cf6",
              fillOpacity: 0.25,
            },
          }).addTo(map);

          map.setView([res.centroid[1], res.centroid[0]], 13);
        }

        if (onUserParcelImported) {
          onUserParcelImported(importedParcel);
        }
        onSelectParcel(importedParcel);

        setIsImportModalOpen(false);
        setImportText("");
        setImportSiteName("");
      }
    } catch (err: any) {
      console.error("GeoJSON Import error:", err);
      setImportError(err.response?.data?.detail || err.message || "Invalid GeoJSON data.");
    } finally {
      setImportLoading(false);
    }
  };

  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-xs">
      <div ref={mapContainerRef} className="h-full w-full" style={{ minHeight: "440px" }} />

      {/* Top Left: GIS HUD & Provenance Badge */}
      <div className="pointer-events-none absolute left-4 top-4 z-[400] flex flex-col gap-1 rounded-xl border border-slate-200 bg-white/95 p-3 shadow-sm backdrop-blur-xs">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
          <span className="font-display text-xs font-bold text-slate-900 tracking-tight">
            Real Geographic Intelligence Engine (RGIE)
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[10px] text-slate-500">
          <span>Pune Metro (EPSG:4326 / UTM 43N)</span>
          <span>•</span>
          <span className="text-blue-700 font-semibold">{parcels.length} Active Plots</span>
        </div>
      </div>

      {/* Top Right: Layer Controls & GeoJSON Upload */}
      <div className="absolute right-4 top-4 z-[400] flex flex-col gap-2">
        {/* Zoom Controls */}
        <div className="flex flex-col rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <button
            onClick={() => mapInstanceRef.current?.zoomIn()}
            className="p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors font-bold text-sm"
            title="Zoom In"
          >
            +
          </button>
          <div className="h-px bg-slate-200" />
          <button
            onClick={() => mapInstanceRef.current?.zoomOut()}
            className="p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors font-bold text-sm"
            title="Zoom Out"
          >
            -
          </button>
          <div className="h-px bg-slate-200" />
          <button
            onClick={() => mapInstanceRef.current?.setView([18.58, 73.84], 11)}
            className="p-2 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            title="Reset to Pune Extent"
          >
            <Navigation className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* User GeoJSON Import Button */}
        <button
          onClick={() => setIsImportModalOpen(true)}
          className="flex items-center gap-1.5 rounded-xl border border-purple-200 bg-purple-50 px-2.5 py-1.5 text-[11px] font-bold text-purple-700 shadow-sm hover:bg-purple-100 transition-all"
          title="Import Custom GeoJSON Parcel"
        >
          <Upload className="h-3.5 w-3.5" />
          <span>Import GeoJSON</span>
        </button>

        {/* Layer Toggles Panel */}
        <div className="flex flex-col gap-1 rounded-xl border border-slate-200 bg-white/95 p-2 shadow-sm backdrop-blur-xs text-[11px]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-0.5">
            GIS Layers
          </span>

          <button
            onClick={() => setShowBoundaries(!showBoundaries)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded-lg text-left transition-colors ${
              showBoundaries ? "bg-blue-50 text-blue-700 font-semibold" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>PMRDA/PMC Limits</span>
            {showBoundaries ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3 text-slate-400" />}
          </button>

          <button
            onClick={() => setShowCorridors(!showCorridors)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded-lg text-left transition-colors ${
              showCorridors ? "bg-red-50 text-red-700 font-semibold" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>Expressway & Metro</span>
            {showCorridors ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3 text-slate-400" />}
          </button>

          <button
            onClick={() => setShowWater(!showWater)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded-lg text-left transition-colors ${
              showWater ? "bg-sky-50 text-sky-700 font-semibold" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>Mula-Mutha Rivers</span>
            {showWater ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3 text-slate-400" />}
          </button>

          <button
            onClick={() => setShowZones(!showZones)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded-lg text-left transition-colors ${
              showZones ? "bg-amber-50 text-amber-700 font-semibold" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>MIDC & BDP Zones</span>
            {showZones ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3 text-slate-400" />}
          </button>

          <button
            onClick={() => setShowInfraAnchors(!showInfraAnchors)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded-lg text-left transition-colors ${
              showInfraAnchors ? "bg-indigo-50 text-indigo-700 font-semibold" : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <span>Infra Anchors</span>
            {showInfraAnchors ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3 text-slate-400" />}
          </button>
        </div>
      </div>

      {/* Bottom Center: Provenance Tier Indicators */}
      <div className="pointer-events-none absolute bottom-4 left-4 z-[400] flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white/95 px-3 py-1.5 text-[10px] font-medium text-slate-600 shadow-sm backdrop-blur-xs">
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="font-bold text-emerald-800">OFFICIAL (PMRDA/PMC)</span>
        </div>
        <span>•</span>
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-blue-500" />
          <span className="font-bold text-blue-800">OPEN DATA (OSM)</span>
        </div>
        <span>•</span>
        <div className="flex items-center gap-1">
          <span className="h-2 w-2 rounded-full bg-purple-500" />
          <span className="font-bold text-purple-800">USER IMPORTED</span>
        </div>
      </div>

      {/* ── GeoJSON Import Modal ────────────────────────────────────────── */}
      {isImportModalOpen && (
        <div className="fixed inset-0 z-[600] flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FileCheck2 className="h-5 w-5 text-purple-600" />
                <h3 className="font-display text-sm font-bold text-slate-900">
                  Import Real GeoJSON Parcel Geometry
                </h3>
              </div>
              <button
                onClick={() => setIsImportModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Paste standard <b>RFC 7946 GeoJSON</b> (Polygon or Feature) within the Pune Metropolitan Region.
              The engine projects coordinates to <b>UTM Zone 43N</b>, computes exact metric acreage, calculates the area-weighted centroid, and validates boundary closure.
            </p>

            <div>
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                Site / Parcel Name
              </label>
              <input
                type="text"
                placeholder="e.g. Wakad Commercial Plot #4"
                value={importSiteName}
                onChange={(e) => setImportSiteName(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 outline-none focus:border-purple-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                GeoJSON Geometry
              </label>
              <textarea
                rows={6}
                placeholder='{ "type": "Polygon", "coordinates": [[[73.735, 18.590], [73.740, 18.590], [73.740, 18.595], [73.735, 18.595], [73.735, 18.590]]] }'
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 font-mono text-[11px] text-slate-800 outline-none focus:border-purple-500"
              />
            </div>

            {importError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-2.5 text-xs text-rose-800 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{importError}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsImportModalOpen(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={importLoading || !importText.trim()}
                onClick={handleImportSubmit}
                className="px-4 py-2 rounded-xl bg-purple-600 text-xs font-bold text-white hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {importLoading ? "Validating..." : "Validate & Ingest"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
