import { useEffect, useRef, useState, useCallback } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  Compass,
  Layers,
  MapPin,
  Maximize2,
  Minimize2,
  Navigation,
  RotateCcw,
  Search,
  Sparkles,
  Eye,
  EyeOff,
  Building2,
  Route,
  Droplets,
  ShieldCheck,
  AlertTriangle,
  Info,
  CheckCircle2,
  Sliders,
  X,
  Upload,
} from "lucide-react";
import type {
  LandParcel,
  MapSearchLocality,
  GeospatialFeatureCollection,
  GeospatialInfrastructureResponse,
} from "../../lib/api";
import {
  getGeospatialBoundaries,
  getGeospatialInfrastructure,
  getMapBuildings,
  searchMapLocalities,
  importUserGeoJSON,
} from "../../lib/api";

export interface SelectedFeatureInfo {
  feature_id: string;
  name: string;
  type: string;
  coordinates: [number, number]; // [lng, lat]
  properties: Record<string, any>;
  is_parcel: boolean;
  parcel_data?: LandParcel;
}

interface RealWorldMapLibreProps {
  parcels: LandParcel[];
  selectedParcelId: string | number | null;
  onSelectParcel?: (parcel: LandParcel) => void;
  onSelectFeature?: (feature: SelectedFeatureInfo) => void;
  winningParcels?: string[];
  onUserParcelImported?: (newParcel: LandParcel) => void;
  className?: string;
}

// Porcelain Light Carto Positron Raster Style Specification
const CARTO_POSITRON_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    "carto-positron": {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        "https://d.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>',
      maxzoom: 19,
    },
  },
  layers: [
    {
      id: "carto-tiles",
      type: "raster",
      source: "carto-positron",
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

const OSM_STANDARD_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    "osm-standard": {
      type: "raster",
      tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors (ODbL 1.0)',
      maxzoom: 19,
    },
  },
  layers: [
    {
      id: "osm-tiles",
      type: "raster",
      source: "osm-standard",
      minzoom: 0,
      maxzoom: 19,
    },
  ],
};

export default function RealWorldMapLibre({
  parcels,
  selectedParcelId,
  onSelectParcel,
  onSelectFeature,
  winningParcels = [],
  onUserParcelImported,
  className = "h-[540px] w-full",
}: RealWorldMapLibreProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  // View & Mode States
  const [is3DMode, setIs3DMode] = useState<boolean>(true);
  const [basemapStyle, setBasemapStyle] = useState<"carto" | "osm">("carto");
  const [heightMode, setHeightMode] = useState<"verified" | "2d" | "illustrative">("verified");

  // Layer Visibility
  const [showBuildings, setShowBuildings] = useState<boolean>(true);
  const [showBoundaries, setShowBoundaries] = useState<boolean>(true);
  const [showCorridors, setShowCorridors] = useState<boolean>(true);
  const [showWater, setShowWater] = useState<boolean>(true);
  const [showZones, setShowZones] = useState<boolean>(false);
  const [showParcels, setShowParcels] = useState<boolean>(true);
  const [showLayersDropdown, setShowLayersDropdown] = useState<boolean>(false);

  // Search & Geocoding
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<MapSearchLocality[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);

  // Client GeoJSON Import Modal
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [importText, setImportText] = useState<string>("");
  const [importName, setImportName] = useState<string>("");
  const [importError, setImportError] = useState<string | null>(null);
  const [importLoading, setImportLoading] = useState<boolean>(false);

  // Selection Highlight
  const [selectedFeature, setSelectedFeature] = useState<SelectedFeatureInfo | null>(null);

  // ─────────────────────────────────────────────────────────────────────────
  // 1. MAP INITIALIZATION LIFECYCLE
  // ─────────────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapRef.current) return; // Prevent duplicate initialization

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: CARTO_POSITRON_STYLE,
      center: [73.805, 18.56], // Centered between Hinjewadi and Central Pune
      zoom: 11.4,
      pitch: 52, // Initial 3D tilt
      bearing: -15,
      maxPitch: 70,
      attributionControl: false, // Custom attribution rendered cleanly
    });

    // Add Navigation and Scale controls
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");
    map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-left");

    map.on("load", async () => {
      // 1. Load Real Buildings GeoJSON Source
      try {
        const buildingsData = await getMapBuildings();
        if (map.getSource("pune-buildings")) {
          (map.getSource("pune-buildings") as maplibregl.GeoJSONSource).setData(buildingsData as any);
        } else {
          map.addSource("pune-buildings", {
            type: "geojson",
            data: buildingsData as any,
            generateId: true,
          });

          // 3D Extrusion Layer
          map.addLayer({
            id: "pune-buildings-extrusion",
            type: "fill-extrusion",
            source: "pune-buildings",
            layout: { visibility: "visible" },
            paint: {
              "fill-extrusion-color": [
                "case",
                ["==", ["get", "building"], "commercial"],
                "#2563eb", // Tech & Commercial: Royal Cobalt
                ["==", ["get", "building"], "industrial"],
                "#d97706", // Industrial: Amber
                ["==", ["get", "building"], "hospital"],
                "#e11d48", // Hospital: Crimson
                ["==", ["get", "building"], "university"],
                "#7c3aed", // Academic: Violet
                "#64748b", // Default: Slate
              ],
              "fill-extrusion-height": [
                "case",
                ["!=", ["get", "height_m"], null],
                ["get", "height_m"],
                ["!=", ["get", "levels"], null],
                ["*", ["get", "levels"], 3.5],
                12, // fallback
              ],
              "fill-extrusion-base": 0,
              "fill-extrusion-opacity": 0.88,
            },
          });

          // 2D Footprint Fill Layer (Used when 3D pitch is 0 or flat mode)
          map.addLayer({
            id: "pune-buildings-2d",
            type: "fill",
            source: "pune-buildings",
            layout: { visibility: "none" },
            paint: {
              "fill-color": "#3b82f6",
              "fill-opacity": 0.4,
            },
          });

          // Building Outlines
          map.addLayer({
            id: "pune-buildings-lines",
            type: "line",
            source: "pune-buildings",
            paint: {
              "line-color": "#1e40af",
              "line-width": 1.2,
            },
          });
        }
      } catch (err) {
        console.warn("Failed to load building footprints layer:", err);
      }

      // 2. Load Administrative Boundaries
      try {
        const boundsData = await getGeospatialBoundaries();
        if (!map.getSource("admin-boundaries")) {
          map.addSource("admin-boundaries", {
            type: "geojson",
            data: boundsData as any,
          });

          map.addLayer({
            id: "admin-boundaries-fill",
            type: "fill",
            source: "admin-boundaries",
            paint: {
              "fill-color": "#3b82f6",
              "fill-opacity": 0.05,
            },
          });

          map.addLayer({
            id: "admin-boundaries-line",
            type: "line",
            source: "admin-boundaries",
            paint: {
              "line-color": "#2563eb",
              "line-width": 2,
              "line-dasharray": [3, 2],
            },
          });
        }
      } catch (err) {
        console.warn("Failed to load boundary layers:", err);
      }

      // 3. Load Corridors, Water, and Planning Zones
      try {
        const infraData = await getGeospatialInfrastructure();

        // Corridors
        if (!map.getSource("infra-corridors")) {
          map.addSource("infra-corridors", {
            type: "geojson",
            data: infraData.corridors as any,
          });

          map.addLayer({
            id: "infra-corridors-line",
            type: "line",
            source: "infra-corridors",
            paint: {
              "line-color": "#dc2626",
              "line-width": 3,
            },
          });
        }

        // Water Bodies & Rivers
        if (!map.getSource("water-rivers")) {
          map.addSource("water-rivers", {
            type: "geojson",
            data: infraData.water_bodies as any,
          });

          map.addLayer({
            id: "water-rivers-line",
            type: "line",
            source: "water-rivers",
            paint: {
              "line-color": "#0284c7",
              "line-width": 3.5,
            },
          });
        }

        // Planning Zones
        if (!map.getSource("planning-zones")) {
          map.addSource("planning-zones", {
            type: "geojson",
            data: infraData.planning_zones as any,
          });

          map.addLayer({
            id: "planning-zones-fill",
            type: "fill",
            source: "planning-zones",
            layout: { visibility: "none" },
            paint: {
              "fill-color": "#f59e0b",
              "fill-opacity": 0.15,
            },
          });

          map.addLayer({
            id: "planning-zones-line",
            type: "line",
            source: "planning-zones",
            layout: { visibility: "none" },
            paint: {
              "line-color": "#d97706",
              "line-width": 1.5,
              "line-dasharray": [2, 1],
            },
          });
        }
      } catch (err) {
        console.warn("Failed to load infrastructure layers:", err);
      }

      // 4. Load Real Estate Candidate Parcels Source
      renderParcelFeatures(map, parcels, winningParcels, selectedParcelId);
    });

    // ───────────────────────────────────────────────────────────────────────
    // CLICK INTERACTION & RAYCASTING
    // ───────────────────────────────────────────────────────────────────────
    map.on("click", (e: any) => {
      const clickLngLat = [e.lngLat.lng, e.lngLat.lat] as [number, number];
      const bbox: [maplibregl.PointLike, maplibregl.PointLike] = [
        [e.point.x - 4, e.point.y - 4],
        [e.point.x + 4, e.point.y + 4],
      ];

      // Query features across buildings, parcels, corridors, boundaries
      const features = map.queryRenderedFeatures(bbox, {
        layers: [
          "pune-buildings-extrusion",
          "pune-buildings-2d",
          "candidate-parcels-fill",
          "candidate-parcels-line",
          "infra-corridors-line",
          "admin-boundaries-fill",
        ].filter((id) => map.getLayer(id)),
      });

      if (features.length > 0) {
        const topFeature = features[0];
        const props = topFeature.properties || {};

        let featureName = props.name || "Mapped Feature";
        let featureType = props.building_type || props.building || topFeature.layer.id;
        let isParcel = false;
        let matchedParcel: LandParcel | undefined;

        // Check if clicked feature is one of our land parcels
        if (props.parcel_id || props.id) {
          const pid = props.parcel_id || props.id;
          matchedParcel = parcels.find((p) => String(p.id) === String(pid) || p.name === props.name);
          if (matchedParcel) {
            isParcel = true;
            featureName = matchedParcel.name;
            featureType = `${matchedParcel.zone_type} Zone Parcel`;
            if (onSelectParcel) onSelectParcel(matchedParcel);
          }
        }

        const featureInfo: SelectedFeatureInfo = {
          feature_id: String(props.osm_id || props.id || topFeature.id || `FEAT_${Date.now()}`),
          name: featureName,
          type: featureType,
          coordinates: clickLngLat,
          properties: props,
          is_parcel: isParcel,
          parcel_data: matchedParcel,
        };

        setSelectedFeature(featureInfo);
        if (onSelectFeature) onSelectFeature(featureInfo);

        // Highlight with popup or camera centering
        const heightNotice = props?.height_m
          ? `<br/><span class="text-amber-700 text-[10px] font-mono">Height: ${props.height_m}m (Modeled: ${props.levels || 4} levels)</span>`
          : "";
        new maplibregl.Popup({ closeButton: false, offset: 15, className: "text-xs font-sans" })
          .setLngLat(e.lngLat)
          .setHTML(
            `<div class="p-1.5"><b class="text-slate-900">${featureName}</b><br/><span class="text-slate-500 font-mono text-[10px]">${featureType}</span>${heightNotice}</div>`
          )
          .addTo(map);
      } else {
        // Clicked bare land or unmapped point
        const featureInfo: SelectedFeatureInfo = {
          feature_id: `POINT_${clickLngLat[1].toFixed(4)}_${clickLngLat[0].toFixed(4)}`,
          name: "Inspected Geographic Coordinate",
          type: "Survey Centroid Point",
          coordinates: clickLngLat,
          properties: {},
          is_parcel: false,
        };
        setSelectedFeature(featureInfo);
        if (onSelectFeature) onSelectFeature(featureInfo);
      }
    });

    // Pointer cursor when hovering interactive layers
    const interactiveLayers = ["pune-buildings-extrusion", "pune-buildings-2d", "candidate-parcels-fill"];
    interactiveLayers.forEach((lId) => {
      map.on("mouseenter", lId, () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", lId, () => (map.getCanvas().style.cursor = ""));
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  // 2. HELPER: RENDER REAL ESTATE PARCELS
  // ─────────────────────────────────────────────────────────────────────────
  const renderParcelFeatures = (
    map: maplibregl.Map,
    currentParcels: LandParcel[],
    winners: string[],
    selectedId: string | number | null
  ) => {
    // Convert parcels to GeoJSON Features
    const parcelFeatures = currentParcels.map((p) => {
      const isWinner = winners.includes(p.name);
      const isSelected = selectedId !== null && (String(selectedId) === String(p.id) || selectedId === p.name);

      // Approximate 500m bounding polygon if exact boundary_polygon missing
      let geom = p.geojson_geometry;
      if (!geom) {
        const offset = 0.0025; // ~250m box
        geom = {
          type: "Polygon",
          coordinates: [[
            [p.location_lng - offset, p.location_lat - offset],
            [p.location_lng + offset, p.location_lat - offset],
            [p.location_lng + offset, p.location_lat + offset],
            [p.location_lng - offset, p.location_lat + offset],
            [p.location_lng - offset, p.location_lat - offset],
          ]],
        };
      }

      return {
        type: "Feature",
        id: p.id,
        geometry: geom,
        properties: {
          parcel_id: p.id,
          name: p.name,
          price_crore: p.price_crore,
          area_acres: p.area_acres,
          zone_type: p.zone_type,
          is_winner: isWinner,
          is_selected: isSelected,
          color: isWinner ? "#10b981" : isSelected ? "#2563eb" : "#6366f1",
        },
      };
    });

    const parcelsGeoJSON = {
      type: "FeatureCollection",
      features: parcelFeatures,
    };

    if (map.getSource("candidate-parcels")) {
      (map.getSource("candidate-parcels") as maplibregl.GeoJSONSource).setData(parcelsGeoJSON as any);
    } else {
      map.addSource("candidate-parcels", {
        type: "geojson",
        data: parcelsGeoJSON as any,
      });

      // Extruded Parcel Height / Lot Fill
      map.addLayer({
        id: "candidate-parcels-fill",
        type: "fill-extrusion",
        source: "candidate-parcels",
        paint: {
          "fill-extrusion-color": ["get", "color"],
          "fill-extrusion-height": [
            "case",
            ["==", ["get", "is_winner"], true],
            30, // Winning parcel stands out higher
            ["==", ["get", "is_selected"], true],
            25,
            15,
          ],
          "fill-extrusion-base": 0,
          "fill-extrusion-opacity": 0.85,
        },
      });

      map.addLayer({
        id: "candidate-parcels-line",
        type: "line",
        source: "candidate-parcels",
        paint: {
          "line-color": [
            "case",
            ["==", ["get", "is_winner"], true],
            "#059669",
            ["==", ["get", "is_selected"], true],
            "#1d4ed8",
            "#4338ca",
          ],
          "line-width": 3,
        },
      });
    }
  };

  // Update parcels when props change
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    renderParcelFeatures(map, parcels, winningParcels, selectedParcelId);
  }, [parcels, winningParcels, selectedParcelId]);

  // ─────────────────────────────────────────────────────────────────────────
  // 3. 2D / 3D CAMERA & HEIGHT MODE SWITCHING
  // ─────────────────────────────────────────────────────────────────────────
  const toggle2D3D = () => {
    const map = mapRef.current;
    if (!map) return;

    if (is3DMode) {
      // Switch to 2D
      map.easeTo({ pitch: 0, bearing: 0, duration: 1200 });
      setIs3DMode(false);
      if (map.getLayer("pune-buildings-extrusion")) {
        map.setLayoutProperty("pune-buildings-extrusion", "visibility", "none");
      }
      if (map.getLayer("pune-buildings-2d")) {
        map.setLayoutProperty("pune-buildings-2d", "visibility", "visible");
      }
    } else {
      // Switch to 3D
      map.easeTo({ pitch: 55, bearing: -15, duration: 1200 });
      setIs3DMode(true);
      if (map.getLayer("pune-buildings-extrusion")) {
        map.setLayoutProperty("pune-buildings-extrusion", "visibility", "visible");
      }
      if (map.getLayer("pune-buildings-2d")) {
        map.setLayoutProperty("pune-buildings-2d", "visibility", "none");
      }
    }
  };

  // ─────────────────────────────────────────────────────────────────────────
  // 4. LAYER TOGGLES
  // ─────────────────────────────────────────────────────────────────────────
  const toggleLayer = (layerName: string, visible: boolean, setVisible: (v: boolean) => void) => {
    const map = mapRef.current;
    if (!map) return;
    const nextVal = !visible;
    setVisible(nextVal);

    const layerMap: Record<string, string[]> = {
      buildings: ["pune-buildings-extrusion", "pune-buildings-2d", "pune-buildings-lines"],
      boundaries: ["admin-boundaries-fill", "admin-boundaries-line"],
      corridors: ["infra-corridors-line"],
      water: ["water-rivers-line"],
      zones: ["planning-zones-fill", "planning-zones-line"],
      parcels: ["candidate-parcels-fill", "candidate-parcels-line"],
    };

    const targetLayerIds = layerMap[layerName] || [];
    targetLayerIds.forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", nextVal ? "visible" : "none");
      }
    });
  };

  // ─────────────────────────────────────────────────────────────────────────
  // 5. GEOCODING SEARCH & FLY-TO
  // ─────────────────────────────────────────────────────────────────────────
  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchMapLocalities(query);
      setSearchResults(results);
      setIsSearchOpen(true);
    } catch (err) {
      console.warn("Geocoding search failed:", err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectLocality = (loc: MapSearchLocality) => {
    const map = mapRef.current;
    if (!map) return;

    map.flyTo({
      center: loc.coordinates, // [lng, lat]
      zoom: loc.suggested_zoom || 14,
      pitch: is3DMode ? 52 : 0,
      bearing: -10,
      duration: 2200,
    });

    setSearchQuery(loc.name);
    setIsSearchOpen(false);

    // Identify as selected feature
    const featureInfo: SelectedFeatureInfo = {
      feature_id: `GEO_${loc.name.replace(/\s+/g, "_")}`,
      name: loc.name,
      type: loc.type,
      coordinates: loc.coordinates,
      properties: {
        jurisdiction: loc.jurisdiction,
        source: loc.source,
      },
      is_parcel: false,
    };
    setSelectedFeature(featureInfo);
    if (onSelectFeature) onSelectFeature(featureInfo);
  };

  // ─────────────────────────────────────────────────────────────────────────
  // 6. CLIENT GEOJSON PARCEL IMPORT
  // ─────────────────────────────────────────────────────────────────────────
  const handleImportGeoJSON = async () => {
    if (!importText.trim()) {
      setImportError("Please paste valid RFC 7946 GeoJSON data.");
      return;
    }

    setImportLoading(true);
    setImportError(null);

    try {
      const parsed = JSON.parse(importText);
      const res = await importUserGeoJSON({
        geojson_data: parsed,
        parcel_name: importName || "Client Uploaded Parcel",
        check_pmrda_boundary: true,
      });

      if (res.is_valid) {
        // Fly camera to imported parcel
        const map = mapRef.current;
        if (map) {
          map.flyTo({
            center: [res.centroid[0], res.centroid[1]],
            zoom: 14.5,
            pitch: 50,
            duration: 2000,
          });
        }

        // Create standard parcel record
        const newParcel: LandParcel = {
          id: res.parcel_id,
          name: res.parcel_name,
          location_lat: res.centroid[1],
          location_lng: res.centroid[0],
          area_acres: res.area_acres,
          price_crore: Math.max(12.0, Number((res.area_acres * 2.8).toFixed(1))),
          price_cr: Math.max(12.0, Number((res.area_acres * 2.8).toFixed(1))),
          price_per_acre_crore: 2.8,
          zone_type: "commercial",
          water_score: 0.85,
          electricity_score: 0.90,
          sewage_score: 0.80,
          road_score: 0.90,
          infrastructure_index: 0.86,
          utility_score: 0.86,
          projected_return_pct: 18.5,
          expected_roi_pct: 18.5,
          return_pct: 18.5,
          infra_scores: { water: 0.85, power: 0.90, sewage: 0.80, road: 0.90 },
          water_supply_score: 0.85,
          location: "Pune PMRDA Client Parcel",
          status: "Available",
          data_provenance: "USER_PROVIDED (Client GeoJSON Submission)",
          geojson_geometry: res.normalized_geojson,
        };

        if (onUserParcelImported) onUserParcelImported(newParcel);
        setIsImportModalOpen(false);
        setImportText("");
        setImportName("");
      } else {
        setImportError("Invalid GeoJSON geometry. Exterior linear rings must be closed polygons.");
      }
    } catch (err: any) {
      setImportError(err.response?.data?.detail || err.message || "Failed to parse GeoJSON.");
    } finally {
      setImportLoading(false);
    }
  };

  return (
    <div className={`relative overflow-hidden rounded-2xl border border-slate-200/90 bg-slate-900 shadow-md ${className}`}>
      {/* ── Top Floating Overlay Bar ──────────────────────────────────── */}
      <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Left: Geocoding Search Bar */}
        <div className="relative w-72 sm:w-80 pointer-events-auto">
          <div className="relative flex items-center">
            <Search className="absolute left-3 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search Hinjewadi, Wakad, Baner, Kharadi..."
              className="w-full rounded-xl border border-slate-200/90 bg-white/95 pl-9 pr-8 py-2 text-xs font-medium text-slate-800 shadow-md backdrop-blur-md outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery("");
                  setSearchResults([]);
                  setIsSearchOpen(false);
                }}
                className="absolute right-2.5 text-slate-400 hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {/* Autocomplete Search Dropdown */}
          {isSearchOpen && searchResults.length > 0 && (
            <div className="absolute mt-1.5 w-full rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl backdrop-blur-md z-30 max-h-60 overflow-y-auto">
              <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                Pune Micro-Markets & Economic Hubs
              </span>
              {searchResults.map((loc, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectLocality(loc)}
                  className="flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left hover:bg-slate-50 transition-colors"
                >
                  <MapPin className="h-4 w-4 shrink-0 text-blue-600 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-slate-900">{loc.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      {loc.type} • {loc.jurisdiction}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Map Controls & Mode Toggles */}
        <div className="flex items-center gap-1.5 pointer-events-auto">
          {/* 2D / 3D Mode Toggle Button */}
          <button
            onClick={toggle2D3D}
            className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold shadow-md transition-all backdrop-blur-md border ${
              is3DMode
                ? "bg-blue-600 text-white border-blue-500 hover:bg-blue-700"
                : "bg-white/95 text-slate-800 border-slate-200 hover:bg-slate-100"
            }`}
            title="Toggle between 2D Top-Down View and 3D Angled Extrusions"
          >
            <Compass className="h-3.5 w-3.5" />
            <span>{is3DMode ? "3D Mode" : "2D Mode"}</span>
          </button>

          {/* Layer Visibility Dropdown Trigger */}
          <div className="relative">
            <button
              onClick={() => setShowLayersDropdown(!showLayersDropdown)}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold shadow-md transition-all backdrop-blur-md border ${
                showLayersDropdown
                  ? "bg-slate-800 text-white border-slate-700"
                  : "bg-white/95 text-slate-800 border-slate-200 hover:bg-slate-100"
              }`}
            >
              <Layers className="h-3.5 w-3.5" />
              <span>Layers</span>
            </button>

            {/* Layer Control Menu */}
            {showLayersDropdown && (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-slate-200 bg-white/98 p-3 shadow-xl backdrop-blur-md z-30 space-y-2 text-xs">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="font-bold text-slate-800 flex items-center gap-1.5">
                    <Sliders className="h-3.5 w-3.5 text-blue-600" />
                    Spatial Layer Overlays
                  </span>
                  <button
                    onClick={() => setShowLayersDropdown(false)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Building Footprints Toggle */}
                <label className="flex items-center justify-between py-1 cursor-pointer hover:bg-slate-50 px-2 rounded-lg">
                  <span className="flex items-center gap-2 text-slate-700 font-medium">
                    <Building2 className="h-3.5 w-3.5 text-blue-600" />
                    3D Building Footprints
                  </span>
                  <input
                    type="checkbox"
                    checked={showBuildings}
                    onChange={() => toggleLayer("buildings", showBuildings, setShowBuildings)}
                    className="accent-blue-600 cursor-pointer"
                  />
                </label>

                {/* Boundaries Toggle */}
                <label className="flex items-center justify-between py-1 cursor-pointer hover:bg-slate-50 px-2 rounded-lg">
                  <span className="flex items-center gap-2 text-slate-700 font-medium">
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                    PMRDA / PMC Boundaries
                  </span>
                  <input
                    type="checkbox"
                    checked={showBoundaries}
                    onChange={() => toggleLayer("boundaries", showBoundaries, setShowBoundaries)}
                    className="accent-blue-600 cursor-pointer"
                  />
                </label>

                {/* Transport Corridors Toggle */}
                <label className="flex items-center justify-between py-1 cursor-pointer hover:bg-slate-50 px-2 rounded-lg">
                  <span className="flex items-center gap-2 text-slate-700 font-medium">
                    <Route className="h-3.5 w-3.5 text-red-600" />
                    Expressways & Metro Lines
                  </span>
                  <input
                    type="checkbox"
                    checked={showCorridors}
                    onChange={() => toggleLayer("corridors", showCorridors, setShowCorridors)}
                    className="accent-blue-600 cursor-pointer"
                  />
                </label>

                {/* Hydrological Rivers Toggle */}
                <label className="flex items-center justify-between py-1 cursor-pointer hover:bg-slate-50 px-2 rounded-lg">
                  <span className="flex items-center gap-2 text-slate-700 font-medium">
                    <Droplets className="h-3.5 w-3.5 text-sky-600" />
                    Mula-Mutha River Network
                  </span>
                  <input
                    type="checkbox"
                    checked={showWater}
                    onChange={() => toggleLayer("water", showWater, setShowWater)}
                    className="accent-blue-600 cursor-pointer"
                  />
                </label>

                {/* Planning Zones Toggle */}
                <label className="flex items-center justify-between py-1 cursor-pointer hover:bg-slate-50 px-2 rounded-lg">
                  <span className="flex items-center gap-2 text-slate-700 font-medium">
                    <MapPin className="h-3.5 w-3.5 text-amber-600" />
                    SEZ / Industrial MIDC Zones
                  </span>
                  <input
                    type="checkbox"
                    checked={showZones}
                    onChange={() => toggleLayer("zones", showZones, setShowZones)}
                    className="accent-blue-600 cursor-pointer"
                  />
                </label>

                {/* Candidate Parcels Toggle */}
                <label className="flex items-center justify-between py-1 cursor-pointer hover:bg-slate-50 px-2 rounded-lg">
                  <span className="flex items-center gap-2 text-slate-700 font-medium">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
                    Real Estate Parcels
                  </span>
                  <input
                    type="checkbox"
                    checked={showParcels}
                    onChange={() => toggleLayer("parcels", showParcels, setShowParcels)}
                    className="accent-blue-600 cursor-pointer"
                  />
                </label>
              </div>
            )}
          </div>

          {/* Import GeoJSON Button */}
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center gap-1.5 rounded-xl bg-white/95 px-3 py-1.5 text-xs font-bold text-slate-800 shadow-md border border-slate-200 hover:bg-slate-100 transition-all backdrop-blur-md"
            title="Import user GeoJSON parcel polygon"
          >
            <Upload className="h-3.5 w-3.5 text-indigo-600" />
            <span className="hidden sm:inline">Import GeoJSON</span>
          </button>
        </div>
      </div>

      {/* ── Main MapLibre WebGL Canvas Container ───────────────────────── */}
      <div ref={mapContainerRef} className="h-full w-full" />

      {/* ── Bottom Floating Attribution & Provenance Bar ────────────────── */}
      <div className="absolute bottom-2 left-2 z-10 hidden sm:flex items-center gap-2 rounded-lg bg-white/90 px-2.5 py-1 text-[10px] text-slate-600 shadow-xs border border-slate-200 backdrop-blur-xs">
        <span className="font-semibold text-slate-800">MapLibre GL</span>
        <span>•</span>
        <span>© OpenStreetMap contributors</span>
        <span>•</span>
        <span>PMRDA DP 2021-2041</span>
        <span>•</span>
        <span className="text-emerald-700 font-semibold flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          EPSG:4326 / EPSG:32643
        </span>
      </div>

      {/* ── Client GeoJSON Import Modal ───────────────────────────────── */}
      {isImportModalOpen && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Upload className="h-4 w-4 text-blue-600" />
                <h4 className="font-display text-sm font-bold text-slate-900">
                  Import Client GeoJSON Parcel
                </h4>
              </div>
              <button
                onClick={() => setIsImportModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Paste standard RFC 7946 GeoJSON geometry (Feature or Polygon). The platform will validate linear ring closure, orient counter-clockwise per right-hand rule, and project metric surface acreage.
            </p>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                Parcel / Site Name:
              </label>
              <input
                type="text"
                value={importName}
                onChange={(e) => setImportName(e.target.value)}
                placeholder="e.g. Hinjewadi Phase 4 Expansion Plot"
                className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-800 outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">
                GeoJSON Polygon Data:
              </label>
              <textarea
                rows={5}
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder='{"type": "Polygon", "coordinates": [[[73.72, 18.58], [73.74, 18.58], [73.74, 18.60], [73.72, 18.60], [73.72, 18.58]]]}'
                className="w-full rounded-lg border border-slate-200 p-2.5 font-mono text-[11px] text-slate-800 outline-none focus:border-blue-500 bg-slate-50"
              />
            </div>

            {importError && (
              <div className="rounded-lg bg-red-50 p-2.5 border border-red-200 text-xs text-red-700 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{importError}</span>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setIsImportModalOpen(false)}
                className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                onClick={handleImportGeoJSON}
                disabled={importLoading}
                className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 shadow-xs flex items-center gap-1.5"
              >
                {importLoading ? "Validating Geometry..." : "Validate & Render on Map"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

