import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Atom, RotateCcw, Compass } from "lucide-react";

interface BlochSphere3DProps {
  theta?: number;
  phi?: number;
  onAngleChange?: (theta: number, phi: number) => void;
}

export default function BlochSphere3D({
  theta: externalTheta,
  phi: externalPhi,
  onAngleChange,
}: BlochSphere3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const [internalTheta, setInternalTheta] = useState(externalTheta ?? Math.PI / 3);
  const [internalPhi, setInternalPhi] = useState(externalPhi ?? Math.PI / 4);

  const theta = externalTheta ?? internalTheta;
  const phi = externalPhi ?? internalPhi;

  const arrowRef = useRef<THREE.ArrowHelper | null>(null);
  const pointMeshRef = useRef<THREE.Mesh | null>(null);

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

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc); // Crisp light porcelain background

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(2.8, 2.2, 3.2);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Orbit Controls for smooth 3D rotation
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 2.0;
    controls.maxDistance = 8.0;
    controlsRef.current = controls;

    // Soft architectural lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x2563eb, 0.6);
    dirLight.position.set(4, 8, 5);
    scene.add(dirLight);

    // 1. Transparent Sphere Wireframe
    const sphereGeo = new THREE.SphereGeometry(1, 28, 16);
    const sphereMat = new THREE.MeshBasicMaterial({
      color: 0xcbd5e1,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const sphere = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(sphere);

    // Subtle inner frosted sphere
    const innerGeo = new THREE.SphereGeometry(0.98, 32, 32);
    const innerMat = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.15,
      roughness: 0.2,
    });
    scene.add(new THREE.Mesh(innerGeo, innerMat));

    // 2. Equatorial Ring
    const ringMat = new THREE.LineBasicMaterial({ color: 0x94a3b8, linewidth: 2 });
    const equatorGeo = new THREE.BufferGeometry();
    const equatorPoints: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      equatorPoints.push(new THREE.Vector3(Math.cos(angle), 0, Math.sin(angle)));
    }
    equatorGeo.setFromPoints(equatorPoints);
    const equatorLine = new THREE.Line(equatorGeo, ringMat);
    scene.add(equatorLine);

    // 3. Coordinate Axes with Clean Colors
    // Z Axis (Vertical: |0> at top, |1> at bottom)
    const zAxisMat = new THREE.LineBasicMaterial({ color: 0x2563eb, linewidth: 2 });
    const zGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, -1.35, 0),
      new THREE.Vector3(0, 1.35, 0),
    ]);
    scene.add(new THREE.Line(zGeo, zAxisMat));

    // X Axis
    const xAxisMat = new THREE.LineBasicMaterial({ color: 0x64748b, linewidth: 1.5 });
    const xGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-1.3, 0, 0),
      new THREE.Vector3(1.3, 0, 0),
    ]);
    scene.add(new THREE.Line(xGeo, xAxisMat));

    // Y Axis
    const yAxisMat = new THREE.LineBasicMaterial({ color: 0x64748b, linewidth: 1.5 });
    const yGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, -1.3),
      new THREE.Vector3(0, 0, 1.3),
    ]);
    scene.add(new THREE.Line(yGeo, yAxisMat));

    // 4. State Vector Arrow (Royal Blue)
    const dir = new THREE.Vector3(
      Math.sin(theta) * Math.cos(phi),
      Math.cos(theta),
      Math.sin(theta) * Math.sin(phi)
    ).normalize();

    const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(0, 0, 0), 1.0, 0x1d4ed8, 0.18, 0.1);
    scene.add(arrow);
    arrowRef.current = arrow;

    // Glowing tip sphere on statevector
    const pointGeo = new THREE.SphereGeometry(0.06, 16, 16);
    const pointMat = new THREE.MeshStandardMaterial({
      color: 0x2563eb,
      emissive: 0x1d4ed8,
      emissiveIntensity: 0.8,
    });
    const pointMesh = new THREE.Mesh(pointGeo, pointMat);
    pointMesh.position.copy(dir);
    scene.add(pointMesh);
    pointMeshRef.current = pointMesh;

    // Subtle projection line to equator
    const projMat = new THREE.LineDashedMaterial({
      color: 0x94a3b8,
      dashSize: 0.05,
      gapSize: 0.03,
    });
    const projGeo = new THREE.BufferGeometry().setFromPoints([
      dir,
      new THREE.Vector3(dir.x, 0, dir.z),
      new THREE.Vector3(0, 0, 0),
    ]);
    const projLine = new THREE.Line(projGeo, projMat);
    projLine.computeLineDistances();
    scene.add(projLine);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
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
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Update arrow on angle change
  useEffect(() => {
    if (!arrowRef.current || !pointMeshRef.current) return;
    const dir = new THREE.Vector3(
      Math.sin(theta) * Math.cos(phi),
      Math.cos(theta),
      Math.sin(theta) * Math.sin(phi)
    ).normalize();

    arrowRef.current.setDirection(dir);
    arrowRef.current.setLength(1.0, 0.18, 0.1);
    pointMeshRef.current.position.copy(dir);
  }, [theta, phi]);

  // Derived quantum amplitudes
  const alphaVal = Math.cos(theta / 2);
  const betaVal = Math.sin(theta / 2);
  const prob0 = (alphaVal * alphaVal * 100).toFixed(1);
  const prob1 = (betaVal * betaVal * 100).toFixed(1);

  return (
    <div className="relative w-full h-[360px] rounded-2xl border border-slate-200/90 bg-white shadow-xs overflow-hidden">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Header Badge */}
      <div className="absolute top-3 left-3 flex items-center gap-2 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs">
        <Atom className="h-4 w-4 text-blue-600" />
        <div>
          <span className="text-xs font-bold text-slate-800">1-Qubit Bloch Sphere</span>
          <span className="text-[10px] text-slate-500 block">Single-Qubit Model (SU(2)) • Educational Subsystem</span>
        </div>
      </div>

      {/* State Amplitude Readout */}
      <div className="absolute top-3 right-3 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs text-right font-mono text-[11px]">
        <div className="text-blue-700 font-bold">
          P(|0⟩) = {prob0}% &nbsp;|&nbsp; P(|1⟩) = {prob1}%
        </div>
        <div className="text-slate-400 text-[9px] mt-0.5">
          θ = {(theta / Math.PI).toFixed(2)}π, φ = {(phi / Math.PI).toFixed(2)}π
        </div>
      </div>

      {/* Interactive Presets Bar */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-1.5 rounded-xl bg-white/95 p-1 backdrop-blur-sm border border-slate-200/80 shadow-xs pointer-events-auto">
          <button
            onClick={() => applyPreset(0, 0)}
            className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all"
          >
            |0⟩ Ground
          </button>
          <button
            onClick={() => applyPreset(Math.PI, 0)}
            className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all"
          >
            |1⟩ Excited
          </button>
          <button
            onClick={() => applyPreset(Math.PI / 2, 0)}
            className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 transition-all"
          >
            |+⟩ Superposition (H)
          </button>
          <button
            onClick={() => applyPreset(Math.PI / 2, Math.PI / 2)}
            className="rounded-lg px-2.5 py-1 text-[11px] font-mono font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-all"
          >
            |i⟩ Phase (S)
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
    </div>
  );
}
