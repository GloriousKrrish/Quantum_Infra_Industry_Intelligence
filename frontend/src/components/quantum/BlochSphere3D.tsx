import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Atom, RotateCcw, AlertTriangle, CheckCircle2 } from "lucide-react";

interface BlochSphere3DProps {
  theta?: number;
  phi?: number;
  blochVector?: { x: number; y: number; z: number; length?: number };
  purity?: number;
  stateClassification?: "PURE" | "MIXED" | "MAXIMALLY_MIXED" | string;
  qubitLabel?: string;
  onAngleChange?: (theta: number, phi: number) => void;
}

export default function BlochSphere3D({
  theta: externalTheta,
  phi: externalPhi,
  blochVector,
  purity = 1.0,
  stateClassification = "PURE",
  qubitLabel = "Qubit q₀",
  onAngleChange,
}: BlochSphere3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  const [internalTheta, setInternalTheta] = useState(externalTheta ?? 0.0);
  const [internalPhi, setInternalPhi] = useState(externalPhi ?? 0.0);

  // Determine effective coordinates (either from external blochVector or angles)
  const isVectorMode = Boolean(blochVector);
  const vx = blochVector ? blochVector.x : Math.sin(externalTheta ?? internalTheta) * Math.cos(externalPhi ?? internalPhi);
  const vy = blochVector ? blochVector.y : Math.sin(externalTheta ?? internalTheta) * Math.sin(externalPhi ?? internalPhi);
  const vz = blochVector ? blochVector.z : Math.cos(externalTheta ?? internalTheta);
  const vLen = blochVector?.length ?? Math.sqrt(vx * vx + vy * vy + vz * vz);

  const isMixed = stateClassification === "MIXED" || stateClassification === "MAXIMALLY_MIXED" || vLen < 0.95;
  const isMaximallyMixed = stateClassification === "MAXIMALLY_MIXED" || vLen < 0.05;

  // Scene references
  const arrowRef = useRef<THREE.ArrowHelper | null>(null);
  const pointMeshRef = useRef<THREE.Mesh | null>(null);
  const originMeshRef = useRef<THREE.Mesh | null>(null);

  const applyPreset = (presetTheta: number, presetPhi: number) => {
    setInternalTheta(presetTheta);
    setInternalPhi(presetPhi);
    onAngleChange?.(presetTheta, presetPhi);
  };

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 360;
    const height = container.clientHeight || 340;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc); // Crisp architectural porcelain

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(2.8, 2.2, 3.2);
    camera.lookAt(0, 0, 0);

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // 4. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2.0;
    controls.maxDistance = 8.0;
    controlsRef.current = controls;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0x2563eb, 0.6);
    dirLight.position.set(4, 8, 5);
    scene.add(dirLight);

    // 5. Outer Bloch Sphere Wireframe
    const sphereGeo = new THREE.SphereGeometry(1, 28, 16);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0xcbd5e1,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    scene.add(new THREE.Mesh(sphereGeo, sphereMat));

    // Inner frosted shell
    const innerGeo = new THREE.SphereGeometry(0.98, 32, 32);
    const innerMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.12,
      roughness: 0.3,
    });
    scene.add(new THREE.Mesh(innerGeo, innerMat));

    // 6. Coordinate Axes (-1 to +1)
    const axesColor = 0x94a3b8;
    const makeAxis = (from: THREE.Vector3, to: THREE.Vector3, color = axesColor) => {
      const geo = new THREE.BufferGeometry().setFromPoints([from, to]);
      const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.6 });
      return new THREE.Line(geo, mat);
    };

    // Z-axis (Computational Basis |0⟩ to |1⟩)
    scene.add(makeAxis(new THREE.Vector3(0, -1.2, 0), new THREE.Vector3(0, 1.2, 0), 0x2563eb));
    // X-axis (|+⟩ to |-⟩)
    scene.add(makeAxis(new THREE.Vector3(-1.2, 0, 0), new THREE.Vector3(1.2, 0, 0), 0x059669));
    // Y-axis (|i⟩ to |-i⟩)
    scene.add(makeAxis(new THREE.Vector3(0, 0, -1.2), new THREE.Vector3(0, 0, 1.2), 0xd97706));

    // 7. Equatorial Ring
    const equatorGeo = new THREE.BufferGeometry();
    const equatorPoints: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * Math.PI * 2;
      equatorPoints.push(new THREE.Vector3(Math.cos(a), 0, Math.sin(a)));
    }
    equatorGeo.setFromPoints(equatorPoints);
    scene.add(new THREE.Line(equatorGeo, new THREE.LineBasicMaterial({ color: 0x94a3b8, opacity: 0.4 })));

    // 8. Origin Indicator (Glowing bead for mixed states)
    const originGeo = new THREE.SphereGeometry(0.045, 16, 16);
    const originMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e });
    const originMesh = new THREE.Mesh(originGeo, originMat);
    scene.add(originMesh);
    originMeshRef.current = originMesh;

    // 9. State Vector Arrow (Three.js Z is forward, Y is up)
    // Physical mapping:
    // Quantum Z (|0⟩ up) -> Three.js +Y
    // Quantum X (|+⟩ front) -> Three.js +X
    // Quantum Y (|i⟩ side)  -> Three.js +Z
    const dir = new THREE.Vector3(vx, vz, vy).normalize();
    const arrowColor = isMixed ? 0xf43f5e : 0x2563eb;
    const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(0, 0, 0), Math.max(vLen, 0.05), arrowColor, 0.16, 0.09);
    scene.add(arrow);
    arrowRef.current = arrow;

    // 10. Tip Point Mesh
    const tipGeo = new THREE.SphereGeometry(0.045, 16, 16);
    const tipMat = new THREE.MeshStandardMaterial({
      color: arrowColor,
      emissive: arrowColor,
      emissiveIntensity: 0.6,
    });
    const tipMesh = new THREE.Mesh(tipGeo, tipMat);
    tipMesh.position.set(vx, vz, vy);
    scene.add(tipMesh);
    pointMeshRef.current = tipMesh;

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, []);

  // Update Vector on state changes
  useEffect(() => {
    if (!arrowRef.current || !pointMeshRef.current) return;

    // Quantum Z -> Three.js Y, Quantum X -> Three.js X, Quantum Y -> Three.js Z
    const targetPos = new THREE.Vector3(vx, vz, vy);
    const currentLen = Math.max(vLen, 0.01);
    const dir = targetPos.clone().normalize();

    if (vLen > 0.05) {
      arrowRef.current.visible = true;
      arrowRef.current.setDirection(dir);
      arrowRef.current.setLength(currentLen, 0.14, 0.08);
      pointMeshRef.current.position.copy(targetPos);
      pointMeshRef.current.visible = true;
    } else {
      // Maximally mixed state at the origin
      arrowRef.current.visible = false;
      pointMeshRef.current.position.set(0, 0, 0);
      pointMeshRef.current.visible = true;
    }

    const arrowColor = isMixed ? 0xf43f5e : 0x2563eb;
    arrowRef.current.setColor(new THREE.Color(arrowColor));
  }, [vx, vy, vz, vLen, isMixed]);

  // Derived probabilities
  const prob0 = Math.max(0, Math.min(100, ((1.0 + vz) / 2.0) * 100)).toFixed(1);
  const prob1 = Math.max(0, Math.min(100, ((1.0 - vz) / 2.0) * 100)).toFixed(1);

  return (
    <div className="relative w-full h-[360px] rounded-2xl border border-slate-200/90 bg-white shadow-xs overflow-hidden">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Header Badge */}
      <div className="absolute top-3 left-3 flex items-center gap-2 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs">
        <Atom className="h-4 w-4 text-blue-600" />
        <div>
          <span className="text-xs font-bold text-slate-900 block leading-tight">
            {qubitLabel} Bloch Sphere
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {isMaximallyMixed ? (
              <span className="text-rose-600 font-semibold">Maximally Mixed State (|r|=0)</span>
            ) : isMixed ? (
              <span className="text-amber-600 font-semibold">Mixed State (Entangled, |r|&lt;1)</span>
            ) : (
              <span className="text-emerald-700 font-semibold">Pure State (|r|=1.00)</span>
            )}
          </span>
        </div>
      </div>

      {/* State Metrics HUD */}
      <div className="absolute top-3 right-3 rounded-xl bg-white/95 p-2 backdrop-blur-sm border border-slate-200/80 shadow-xs text-right font-mono text-[11px] space-y-0.5">
        <div className="flex items-center justify-end gap-2 text-slate-800 font-bold">
          <span>P(|0⟩): <b className="text-blue-600">{prob0}%</b></span>
          <span>•</span>
          <span>P(|1⟩): <b className="text-blue-600">{prob1}%</b></span>
        </div>
        <div className="text-[10px] text-slate-500">
          Bloch: ({vx.toFixed(2)}, {vy.toFixed(2)}, {vz.toFixed(2)}) • |r| = {vLen.toFixed(2)}
        </div>
        <div className="text-[10px] text-slate-400">
          Purity γ = {purity.toFixed(3)} {purity >= 0.99 ? "(Pure)" : purity <= 0.51 ? "(Max Mixed)" : "(Mixed)"}
        </div>
      </div>

      {/* Entanglement Alert Callout if Mixed */}
      {isMixed && (
        <div className="absolute left-3 top-16 max-w-[280px] rounded-xl border border-rose-200 bg-rose-50/95 p-2.5 text-[10px] text-rose-900 backdrop-blur-xs shadow-xs animate-fadeIn">
          <div className="flex items-center gap-1.5 font-bold mb-0.5">
            <AlertTriangle className="h-3.5 w-3.5 text-rose-600" />
            Reduced Density Matrix Notice
          </div>
          Because this qubit is entangled with other qubits in the register, its isolated state is mixed (non-pure). The Bloch vector terminates {isMaximallyMixed ? "at the origin" : "inside the unit sphere"}.
        </div>
      )}

      {/* Interactive Presets (if not in fixed vector mode) */}
      {!isVectorMode && (
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-1 rounded-xl bg-white/95 p-1 backdrop-blur-sm border border-slate-200/80 shadow-xs pointer-events-auto">
            <button
              onClick={() => applyPreset(0, 0)}
              className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-medium text-slate-600 hover:bg-slate-100 transition-all"
            >
              |0⟩ Ground
            </button>
            <button
              onClick={() => applyPreset(Math.PI, 0)}
              className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-medium text-slate-600 hover:bg-slate-100 transition-all"
            >
              |1⟩ Excited
            </button>
            <button
              onClick={() => applyPreset(Math.PI / 2, 0)}
              className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 transition-all"
            >
              |+⟩ Superposition
            </button>
            <button
              onClick={() => applyPreset(Math.PI / 2, Math.PI / 2)}
              className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-medium text-slate-600 hover:bg-slate-100 transition-all"
            >
              |i⟩ Phase
            </button>
          </div>

          <button
            onClick={() => controlsRef.current?.reset()}
            className="flex items-center gap-1 rounded-xl bg-white/95 px-2.5 py-1.5 text-[11px] font-semibold text-slate-600 shadow-xs border border-slate-200/80 hover:bg-slate-50 pointer-events-auto transition-all"
          >
            <RotateCcw className="h-3 w-3 text-slate-400" />
            Reset View
          </button>
        </div>
      )}
    </div>
  );
}
