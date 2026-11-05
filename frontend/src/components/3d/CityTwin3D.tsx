import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  RotateCcw,
  Sparkles,
  Droplets,
  Zap,
  Layers,
  Sun,
  Moon,
  Compass,
} from "lucide-react";
import type { Parcel } from "../../lib/api";

interface CityTwin3DProps {
  parcels: Parcel[];
  selectedParcelId: string | number | null;
  onSelectParcel: (parcel: Parcel) => void;
  winningParcels?: string[];
  showInfrastructure?: boolean;
}

// 3D Grid Positions & Spatial layout across Pune Metropolitan Region
const PUNE_3D_LAYOUT: Record<
  string,
  {
    x: number;
    z: number;
    height: number;
    type: "tech" | "commercial" | "residential" | "industrial";
    color: number;
  }
> = {
  "Hinjewadi Phase III": { x: -6.5, z: -3.0, height: 4.2, type: "tech", color: 0x2563eb },
  "Hinjawadi Phase 3": { x: -6.5, z: -3.0, height: 4.2, type: "tech", color: 0x2563eb },
  "Wakad Central": { x: -3.2, z: -1.2, height: 3.5, type: "residential", color: 0x0284c7 },
  "Baner Hilltop": { x: -2.0, z: 2.2, height: 3.0, type: "residential", color: 0x4f46e5 },
  "Kharadi IT Park": { x: 5.8, z: -1.5, height: 4.6, type: "tech", color: 0x1d4ed8 },
  "Kharadi IT Hub": { x: 5.8, z: -1.5, height: 4.6, type: "tech", color: 0x1d4ed8 },
  "Wagholi East": { x: 7.2, z: 2.4, height: 2.4, type: "residential", color: 0x059669 },
  "Hadapsar Growth Zone": { x: 4.2, z: 4.8, height: 2.8, type: "industrial", color: 0x0d9488 },
  "Hadapsar Extension": { x: 4.2, z: 4.8, height: 2.8, type: "industrial", color: 0x0d9488 },
  "Talegaon Dabhade": { x: -7.5, z: -6.0, height: 2.6, type: "residential", color: 0x10b981 },
  "Pirangut Corridor": { x: -6.0, z: 4.5, height: 2.4, type: "residential", color: 0x6366f1 },
  "Mamurdi PCMC": { x: -4.5, z: -5.2, height: 3.0, type: "commercial", color: 0x0284c7 },
  "Viman Nagar Premium": { x: 3.4, z: -3.6, height: 3.8, type: "commercial", color: 0x7c3aed },
  "Undri Greenfield": { x: 1.8, z: 6.5, height: 2.0, type: "residential", color: 0x16a34a },
  "Chakan Industrial": { x: -0.5, z: -7.5, height: 2.6, type: "industrial", color: 0xd97706 },
};

export default function CityTwin3D({
  parcels,
  selectedParcelId,
  onSelectParcel,
  winningParcels = [],
  showInfrastructure = true,
}: CityTwin3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const [hoveredParcel, setHoveredParcel] = useState<Parcel | null>(null);
  const [activeLayer, setActiveLayer] = useState<"all" | "water" | "power">("all");
  const [lightingMode, setLightingMode] = useState<"day" | "sunset">("day");

  // Camera Target for smooth lerping
  const targetCamPos = useRef<THREE.Vector3>(new THREE.Vector3(14, 16, 18));
  const targetLookAt = useRef<THREE.Vector3>(new THREE.Vector3(0, 0, 0));

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 520;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(lightingMode === "day" ? 0xf8fafc : 0xf1f5f9);

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
    camera.position.copy(targetCamPos.current);
    cameraRef.current = camera;

    // 3. Renderer with soft shadow maps
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    // 4. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.15; // Don't flip below ground
    controls.minDistance = 6;
    controls.maxDistance = 50;
    controlsRef.current = controls;

    // 5. Lighting Setup (Architectural Sun & Sky)
    const ambientLight = new THREE.AmbientLight(
      lightingMode === "day" ? 0xffffff : 0xfef3c7,
      lightingMode === "day" ? 0.9 : 0.75
    );
    scene.add(ambientLight);

    const sun = new THREE.DirectionalLight(
      lightingMode === "day" ? 0xffffff : 0xf59e0b,
      lightingMode === "day" ? 1.4 : 1.1
    );
    sun.position.set(22, 34, 18);
    sun.castShadow = true;
    sun.shadow.mapSize.width = 2048;
    sun.shadow.mapSize.height = 2048;
    sun.shadow.camera.near = 0.5;
    sun.shadow.camera.far = 100;
    sun.shadow.camera.left = -25;
    sun.shadow.camera.right = 25;
    sun.shadow.camera.top = 25;
    sun.shadow.camera.bottom = -25;
    sun.shadow.bias = -0.0002;
    scene.add(sun);

    // Secondary fill light
    const fillLight = new THREE.DirectionalLight(0x93c5fd, 0.4);
    fillLight.position.set(-15, 10, -10);
    scene.add(fillLight);

    // 6. Architectural Terrain Baseplate
    const terrainGeo = new THREE.PlaneGeometry(54, 54, 32, 32);
    const terrainMat = new THREE.MeshStandardMaterial({
      color: 0xf1f5f9,
      roughness: 0.95,
      metalness: 0.02,
    });
    const terrain = new THREE.Mesh(terrainGeo, terrainMat);
    terrain.rotation.x = -Math.PI / 2;
    terrain.receiveShadow = true;
    scene.add(terrain);

    // Coordinate Grid (Architectural 1-meter & 5-meter lines)
    const gridMajor = new THREE.GridHelper(50, 10, 0x94a3b8, 0xcbd5e1);
    gridMajor.position.y = 0.01;
    scene.add(gridMajor);

    // 7. Arterial Roads (PMRDA Expressways connecting parcels)
    const roadMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      roughness: 0.8,
    });

    // East-West Spine (Mumbai-Pune Expressway to Kharadi Bypass)
    const ewRoad = new THREE.Mesh(new THREE.PlaneGeometry(48, 1.2), roadMat);
    ewRoad.rotation.x = -Math.PI / 2;
    ewRoad.position.set(0, 0.02, -1.5);
    ewRoad.receiveShadow = true;
    scene.add(ewRoad);

    // North-South Spine (Chakan to Hadapsar)
    const nsRoad = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 48), roadMat);
    nsRoad.rotation.x = -Math.PI / 2;
    nsRoad.position.set(0.5, 0.02, 0);
    nsRoad.receiveShadow = true;
    scene.add(nsRoad);

    // 8. 3D Buildings & Cadastral Parcels
    const interactiveObjects: THREE.Object3D[] = [];

    parcels.forEach((parcel, idx) => {
      const cfg = PUNE_3D_LAYOUT[parcel.name] || {
        x: (idx - 4) * 3,
        z: 0,
        height: 3.0,
        type: "tech",
        color: 0x2563eb,
      };

      const isWinner = winningParcels.includes(parcel.name);
      const isSelected = selectedParcelId !== null && (String(selectedParcelId) === String(parcel.id) || selectedParcelId === parcel.name);

      const group = new THREE.Group();
      group.position.set(cfg.x, 0, cfg.z);

      // A) Cadastral Base Lot Slab
      const plotWidth = 2.8;
      const plotDepth = 2.8;
      const slabGeo = new THREE.BoxGeometry(plotWidth, 0.16, plotDepth);
      const slabMat = new THREE.MeshStandardMaterial({
        color: isWinner ? 0xdcfce7 : isSelected ? 0xdbeafe : 0xffffff,
        roughness: 0.6,
      });
      const slab = new THREE.Mesh(slabGeo, slabMat);
      slab.position.y = 0.08;
      slab.receiveShadow = true;
      group.add(slab);

      // Cadastral boundary line
      const slabEdges = new THREE.EdgesGeometry(slabGeo);
      const boundaryMat = new THREE.LineBasicMaterial({
        color: isWinner ? 0x059669 : isSelected ? 0x2563eb : 0x94a3b8,
        linewidth: 2,
      });
      const boundaryWire = new THREE.LineSegments(slabEdges, boundaryMat);
      boundaryWire.position.y = 0.08;
      group.add(boundaryWire);

      // B) Architectural Extruded Tower Massing
      const bHeight = isWinner ? cfg.height * 1.15 : cfg.height;
      const towerWidth = 1.6;
      const towerDepth = 1.6;

      let towerMat: THREE.Material;
      if (isWinner) {
        towerMat = new THREE.MeshStandardMaterial({
          color: 0x10b981, // Emerald Winner
          emissive: 0x064e3b,
          emissiveIntensity: 0.25,
          roughness: 0.25,
          metalness: 0.15,
        });
      } else if (isSelected) {
        towerMat = new THREE.MeshStandardMaterial({
          color: 0x2563eb, // Royal Cobalt
          emissive: 0x1e3a8a,
          emissiveIntensity: 0.3,
          roughness: 0.3,
          metalness: 0.1,
        });
      } else {
        towerMat = new THREE.MeshStandardMaterial({
          color: 0xffffff,
          roughness: 0.4,
          metalness: 0.05,
        });
      }

      // Main Tower
      const towerGeo = new THREE.BoxGeometry(towerWidth, bHeight, towerDepth);
      const tower = new THREE.Mesh(towerGeo, towerMat);
      tower.position.y = bHeight / 2 + 0.16;
      tower.castShadow = true;
      tower.receiveShadow = true;
      group.add(tower);

      // Architectural crisp edges
      const towerEdges = new THREE.EdgesGeometry(towerGeo);
      const edgeLineMat = new THREE.LineBasicMaterial({
        color: isWinner ? 0x047857 : isSelected ? 0x1d4ed8 : 0xcbd5e1,
      });
      const towerWire = new THREE.LineSegments(towerEdges, edgeLineMat);
      towerWire.position.y = bHeight / 2 + 0.16;
      group.add(towerWire);

      // C) Stepped Podium / Terrace Architectural Details
      const podiumHeight = 0.6;
      const podiumGeo = new THREE.BoxGeometry(2.1, podiumHeight, 2.1);
      const podiumMat = new THREE.MeshStandardMaterial({
        color: 0xf8fafc,
        roughness: 0.7,
      });
      const podium = new THREE.Mesh(podiumGeo, podiumMat);
      podium.position.y = podiumHeight / 2 + 0.16;
      podium.castShadow = true;
      podium.receiveShadow = true;
      group.add(podium);

      // D) Rooftop Mechanical / Heli-pad Penthouse
      const roofBoxGeo = new THREE.BoxGeometry(0.7, 0.3, 0.7);
      const roofMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8 });
      const roofBox = new THREE.Mesh(roofBoxGeo, roofMat);
      roofBox.position.y = bHeight + 0.16 + 0.15;
      group.add(roofBox);

      // E) QAOA Winning Ring Halo
      if (isWinner) {
        const haloGeo = new THREE.RingGeometry(1.8, 2.0, 32);
        const haloMat = new THREE.MeshBasicMaterial({
          color: 0x10b981,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.7,
        });
        const halo = new THREE.Mesh(haloGeo, haloMat);
        halo.rotation.x = -Math.PI / 2;
        halo.position.y = 0.17;
        group.add(halo);
      }

      // Store parcel info on group for raycasting
      (group as any).parcelData = parcel;
      (tower as any).parcelData = parcel;
      interactiveObjects.push(tower);

      scene.add(group);
    });

    // 9. 3D Infrastructure Systems: Water Network & Power Grid
    const infraGroup = new THREE.Group();

    if (showInfrastructure) {
      // A) Water Pipelines (IS 1172): Blue 3D Curves connecting parcels
      const waterMat = new THREE.MeshStandardMaterial({
        color: 0x0284c7,
        emissive: 0x0369a1,
        emissiveIntensity: 0.4,
        roughness: 0.3,
      });

      const waterCurvePoints = [
        new THREE.Vector3(-6.5, 0.25, -3.0), // Hinjewadi
        new THREE.Vector3(-3.2, 0.25, -1.2), // Wakad
        new THREE.Vector3(-2.0, 0.25, 2.2),  // Baner
        new THREE.Vector3(3.4, 0.25, -3.6),  // Viman Nagar
        new THREE.Vector3(5.8, 0.25, -1.5),  // Kharadi
        new THREE.Vector3(4.2, 0.25, 4.8),   // Hadapsar
      ];

      const waterCurve = new THREE.CatmullRomCurve3(waterCurvePoints);
      const waterTubeGeo = new THREE.TubeGeometry(waterCurve, 40, 0.08, 8, false);
      const waterTube = new THREE.Mesh(waterTubeGeo, waterMat);
      infraGroup.add(waterTube);

      // B) Power Grid Transmission: Golden lines connecting to 220kV Substation
      const powerMat = new THREE.LineBasicMaterial({
        color: 0xd97706,
        linewidth: 2,
      });

      const powerPoints = [
        new THREE.Vector3(-6.5, 2.5, -3.0),
        new THREE.Vector3(-3.2, 2.5, -1.2),
        new THREE.Vector3(0.0, 3.2, 0.0), // Central Grid Hub
        new THREE.Vector3(5.8, 2.5, -1.5),
        new THREE.Vector3(4.2, 2.5, 4.8),
      ];
      const powerGeo = new THREE.BufferGeometry().setFromPoints(powerPoints);
      const powerLines = new THREE.Line(powerGeo, powerMat);
      infraGroup.add(powerLines);
    }

    scene.add(infraGroup);

    // 10. Mouse Raycasting for Interactive Selection
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const onPointerMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(interactiveObjects);

      if (hits.length > 0) {
        const hitData = (hits[0].object as any).parcelData as Parcel;
        if (hitData) {
          setHoveredParcel(hitData);
          renderer.domElement.style.cursor = "pointer";
        }
      } else {
        setHoveredParcel(null);
        renderer.domElement.style.cursor = "default";
      }
    };

    const onClick = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(interactiveObjects);

      if (hits.length > 0) {
        const hitData = (hits[0].object as any).parcelData as Parcel;
        if (hitData) {
          onSelectParcel(hitData);
          // Focus camera on clicked parcel
          const pos = PUNE_3D_LAYOUT[hitData.name];
          if (pos) {
            targetLookAt.current.set(pos.x, 1.5, pos.z);
            targetCamPos.current.set(pos.x + 6, 8, pos.z + 8);
          }
        }
      }
    };

    renderer.domElement.addEventListener("mousemove", onPointerMove);
    renderer.domElement.addEventListener("click", onClick);

    // 11. Render Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      clock.getElapsedTime();

      // Smooth camera lerp
      camera.position.lerp(targetCamPos.current, 0.04);
      controls.target.lerp(targetLookAt.current, 0.04);
      controls.update();

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      renderer.domElement.removeEventListener("mousemove", onPointerMove);
      renderer.domElement.removeEventListener("click", onClick);
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [parcels, selectedParcelId, winningParcels, showInfrastructure, lightingMode]);

  // Camera presets
  const setCameraPreset = (preset: "wide" | "winners" | "focus") => {
    if (preset === "wide") {
      targetLookAt.current.set(0, 0, 0);
      targetCamPos.current.set(14, 16, 18);
    } else if (preset === "winners") {
      // Center between Hinjewadi, Wakad, Kharadi, Hadapsar
      targetLookAt.current.set(0, 1.5, 0.5);
      targetCamPos.current.set(7, 10, 12);
    } else if (preset === "focus") {
      const activeParcel = parcels.find((p) => p.id === selectedParcelId) || parcels[0];
      const pos = PUNE_3D_LAYOUT[activeParcel.name];
      if (pos) {
        targetLookAt.current.set(pos.x, 1.5, pos.z);
        targetCamPos.current.set(pos.x + 6, 8, pos.z + 8);
      }
    }
  };

  return (
    <div className="relative w-full h-[520px] rounded-3xl border border-slate-200/90 bg-white shadow-xs overflow-hidden">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Left: Title Badge */}
      <div className="absolute top-4 left-4 flex items-center gap-3 rounded-2xl bg-white/95 px-3.5 py-2 backdrop-blur-sm border border-slate-200/80 shadow-xs">
        <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-xs shadow-xs">
          3D
        </div>
        <div>
          <span className="text-xs font-bold text-slate-900 block leading-tight">
            Pune PMRDA 3D Digital Twin
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            8 Cadastral Parcels • Illustrative Spatial Mesh
          </span>
        </div>
      </div>

      {/* Top Right: Camera Presets & Controls */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <div className="flex items-center gap-1 rounded-2xl bg-white/95 p-1 backdrop-blur-sm border border-slate-200/80 shadow-xs text-xs font-medium">
          <button
            onClick={() => setCameraPreset("wide")}
            className="rounded-xl px-2.5 py-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-[11px]"
          >
            PMRDA Wide
          </button>
          <button
            onClick={() => setCameraPreset("winners")}
            className="flex items-center gap-1 rounded-xl px-2.5 py-1 text-emerald-700 bg-emerald-50 border border-emerald-200/60 font-semibold text-[11px]"
          >
            <Sparkles className="h-3 w-3 text-emerald-600" />
            QAOA Winners
          </button>
          <button
            onClick={() => setCameraPreset("focus")}
            className="rounded-xl px-2.5 py-1 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all text-[11px]"
          >
            Selected Plot
          </button>
        </div>

        <button
          onClick={() => setLightingMode(lightingMode === "day" ? "sunset" : "day")}
          className="flex h-8 w-8 items-center justify-center rounded-2xl bg-white/95 text-slate-600 shadow-xs border border-slate-200/80 hover:bg-slate-50"
          title="Toggle Day / Sunset Lighting"
        >
          {lightingMode === "day" ? <Sun className="h-4 w-4 text-amber-500" /> : <Moon className="h-4 w-4 text-blue-600" />}
        </button>

        <button
          onClick={() => setCameraPreset("wide")}
          className="flex h-8 w-8 items-center justify-center rounded-2xl bg-white/95 text-slate-600 shadow-xs border border-slate-200/80 hover:bg-slate-50"
          title="Reset View"
        >
          <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
        </button>
      </div>

      {/* Bottom Floating Hover Card */}
      {hoveredParcel && (
        <div className="absolute bottom-16 left-4 rounded-2xl bg-white/95 p-3.5 backdrop-blur-sm border border-slate-200/90 shadow-md animate-fadeIn max-w-xs pointer-events-none">
          <div className="flex items-center justify-between gap-3 mb-1">
            <span className="font-display text-xs font-bold text-slate-900">
              {hoveredParcel.name}
            </span>
            <span className="font-mono text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-lg border border-blue-200/60">
              ₹{hoveredParcel.price_cr} Cr
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-500 mt-2 border-t border-slate-100 pt-2">
            <span>Area: {hoveredParcel.area_acres} Acres</span>
            <span className="text-emerald-600 font-semibold text-right">
              Return: +{hoveredParcel.expected_roi_pct ?? hoveredParcel.return_pct}%
            </span>
            <span>Water: {((hoveredParcel.water_supply_score ?? hoveredParcel.infra_scores.water) * 100).toFixed(0)}%</span>
            <span className="text-right">Infra: {((hoveredParcel.infrastructure_index ?? hoveredParcel.utility_score) * 100).toFixed(0)}%</span>
          </div>
          {winningParcels.includes(hoveredParcel.name) && (
            <div className="mt-2 flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-1 rounded-lg border border-emerald-200">
              <Sparkles className="h-3 w-3 text-emerald-600" />
              QAOA Optimal Selected Parcel
            </div>
          )}
        </div>
      )}

      {/* Bottom Legend & Infrastructure Layers Bar */}
      <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-3 rounded-2xl bg-white/95 px-3.5 py-2 backdrop-blur-sm border border-slate-200/80 shadow-xs pointer-events-auto text-[11px]">
          <span className="font-semibold text-slate-700 flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-slate-500" /> 3D Networks:
          </span>
          <span className="flex items-center gap-1 text-slate-600">
            <Droplets className="h-3 w-3 text-blue-500" /> Water Pipelines (IS 1172)
          </span>
          <span className="flex items-center gap-1 text-slate-600">
            <Zap className="h-3 w-3 text-amber-500" /> 220kV Power Grid
          </span>
          <span className="flex items-center gap-1 text-emerald-700 font-medium">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 inline-block" /> QAOA Winners
          </span>
        </div>

        <div className="text-[10px] text-slate-400 font-mono pointer-events-none bg-white/80 px-2.5 py-1 rounded-xl backdrop-blur-sm">
          Left Click + Drag: Rotate • Right Click: Pan • Scroll: Zoom
        </div>
      </div>
    </div>
  );
}
