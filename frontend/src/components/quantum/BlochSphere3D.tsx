import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Atom } from "lucide-react";

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
  const [internalTheta, setInternalTheta] = useState(externalTheta ?? Math.PI / 3);
  const [internalPhi, setInternalPhi] = useState(externalPhi ?? Math.PI / 4);

  const theta = externalTheta ?? internalTheta;
  const phi = externalPhi ?? internalPhi;

  const arrowRef = useRef<THREE.ArrowHelper | null>(null);
  const pointMeshRef = useRef<THREE.Mesh | null>(null);

  // Quick state presets
  const applyPreset = (presetTheta: number, presetPhi: number) => {
    setInternalTheta(presetTheta);
    setInternalPhi(presetPhi);
    onAngleChange?.(presetTheta, presetPhi);
  };

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 320;
    const height = 300;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(2.4, 1.8, 3.2);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Ambient & Directional Light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x22d3ee, 1.5);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // 1. Transparent Inner Sphere
    const sphereGeo = new THREE.SphereGeometry(1, 32, 16);
    const sphereMat = new THREE.MeshPhongMaterial({
      color: 0x0f172a,
      emissive: 0x082f49,
      transparent: true,
      opacity: 0.35,
      wireframe: true,
    });
    const sphere = new THREE.Mesh(sphereGeo, sphereMat);
    scene.add(sphere);

    // 2. Equatorial and Meridian Rings
    const ringMat = new THREE.LineBasicMaterial({ color: 0x334155, linewidth: 1 });

    const equatorGeo = new THREE.BufferGeometry();
    const equatorPoints: THREE.Vector3[] = [];
    for (let i = 0; i <= 64; i++) {
      const angle = (i / 64) * Math.PI * 2;
      equatorPoints.push(new THREE.Vector3(Math.cos(angle), 0, Math.sin(angle)));
    }
    equatorGeo.setFromPoints(equatorPoints);
    const equatorLine = new THREE.Line(equatorGeo, ringMat);
    scene.add(equatorLine);

    // 3. Coordinate Axes (X: Red/Amber, Y: Green/Cyan, Z: Blue/Violet)
    // In physics: Z is vertical. In Three.js: Y is vertical.
    // We map physics Z -> Three.js Y, physics X -> Three.js X, physics Y -> Three.js Z
    const axisMat = new THREE.LineBasicMaterial({ color: 0x475569 });

    // Vertical Z Axis (Three.js Y)
    const zPoints = [new THREE.Vector3(0, -1.3, 0), new THREE.Vector3(0, 1.3, 0)];
    const zGeo = new THREE.BufferGeometry().setFromPoints(zPoints);
    scene.add(new THREE.Line(zGeo, axisMat));

    // X Axis
    const xPoints = [new THREE.Vector3(-1.3, 0, 0), new THREE.Vector3(1.3, 0, 0)];
    const xGeo = new THREE.BufferGeometry().setFromPoints(xPoints);
    scene.add(new THREE.Line(xGeo, axisMat));

    // Y Axis (Three.js Z)
    const yPoints = [new THREE.Vector3(0, 0, -1.3), new THREE.Vector3(0, 0, 1.3)];
    const yGeo = new THREE.BufferGeometry().setFromPoints(yPoints);
    scene.add(new THREE.Line(yGeo, axisMat));

    // 4. State Vector Arrow
    // Initial coordinates
    const dir = new THREE.Vector3(
      Math.sin(theta) * Math.cos(phi),
      Math.cos(theta),
      Math.sin(theta) * Math.sin(phi)
    ).normalize();

    const arrow = new THREE.ArrowHelper(dir, new THREE.Vector3(0, 0, 0), 1, 0x22d3ee, 0.15, 0.08);
    scene.add(arrow);
    arrowRef.current = arrow;

    // Point on sphere surface
    const pointGeo = new THREE.SphereGeometry(0.05, 16, 16);
    const pointMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
    const pointMesh = new THREE.Mesh(pointGeo, pointMat);
    pointMesh.position.copy(dir);
    scene.add(pointMesh);
    pointMeshRef.current = pointMesh;

    // Mouse drag interaction
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;

      scene.rotation.y += deltaX * 0.01;
      scene.rotation.x += deltaY * 0.01;

      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      container.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  // Update Arrow when theta/phi changes
  useEffect(() => {
    if (!arrowRef.current || !pointMeshRef.current) return;
    const dir = new THREE.Vector3(
      Math.sin(theta) * Math.cos(phi),
      Math.cos(theta),
      Math.sin(theta) * Math.sin(phi)
    ).normalize();

    arrowRef.current.setDirection(dir);
    pointMeshRef.current.position.copy(dir);
  }, [theta, phi]);

  const prob0 = Math.cos(theta / 2) ** 2;
  const prob1 = Math.sin(theta / 2) ** 2;

  return (
    <div className="flex flex-col rounded-xl border border-slate-800 bg-slate-950/80 p-4 backdrop-blur-md">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Atom className="h-4 w-4 text-cyan-400" />
          <h3 className="font-display text-sm font-semibold text-white">
            3D WebGL Bloch Sphere
          </h3>
        </div>
        <span className="font-mono text-[10px] text-slate-400">
          Click & Drag to Rotate Orbit
        </span>
      </div>

      {/* 3D Canvas Container */}
      <div className="relative flex items-center justify-center overflow-hidden py-1">
        <div ref={mountRef} className="cursor-grab active:cursor-grabbing" />
        
        {/* Orthogonal Pole Labels */}
        <div className="pointer-events-none absolute top-4 font-mono text-[11px] font-bold text-cyan-400">
          |0⟩ (+Z)
        </div>
        <div className="pointer-events-none absolute bottom-4 font-mono text-[11px] font-bold text-rose-400">
          |1⟩ (-Z)
        </div>
      </div>

      {/* State Mathematical Equation */}
      <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2 text-center font-mono text-[11px] text-slate-300">
        |&psi;&rang; = {(Math.cos(theta / 2)).toFixed(3)}|0&rang; + {(Math.sin(theta / 2)).toFixed(3)}e<sup>i{(phi / Math.PI).toFixed(2)}&pi;</sup>|1&rang;
      </div>

      {/* Sliders */}
      <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>&theta; (Polar):</span>
            <span className="font-mono text-cyan-400">{((theta * 180) / Math.PI).toFixed(0)}&deg;</span>
          </div>
          <input
            type="range"
            min="0"
            max={Math.PI}
            step="0.02"
            value={theta}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setInternalTheta(val);
              onAngleChange?.(val, phi);
            }}
            className="w-full accent-cyan-400 cursor-pointer"
          />
        </div>

        <div>
          <div className="flex justify-between text-slate-400 mb-1">
            <span>&phi; (Azimuth):</span>
            <span className="font-mono text-cyan-400">{((phi * 180) / Math.PI).toFixed(0)}&deg;</span>
          </div>
          <input
            type="range"
            min="0"
            max={2 * Math.PI}
            step="0.02"
            value={phi}
            onChange={(e) => {
              const val = parseFloat(e.target.value);
              setInternalPhi(val);
              onAngleChange?.(theta, val);
            }}
            className="w-full accent-cyan-400 cursor-pointer"
          />
        </div>
      </div>

      {/* Preset Buttons */}
      <div className="mt-3 flex items-center justify-between gap-1.5 border-t border-slate-800/80 pt-3">
        <span className="text-[10px] uppercase font-mono text-slate-500">Presets:</span>
        <div className="flex gap-1.5">
          <button
            onClick={() => applyPreset(0, 0)}
            className="rounded px-2 py-1 font-mono text-[10px] text-slate-300 hover:bg-slate-800 border border-slate-800"
          >
            |0⟩ Ground
          </button>
          <button
            onClick={() => applyPreset(Math.PI, 0)}
            className="rounded px-2 py-1 font-mono text-[10px] text-slate-300 hover:bg-slate-800 border border-slate-800"
          >
            |1⟩ Excited
          </button>
          <button
            onClick={() => applyPreset(Math.PI / 2, 0)}
            className="rounded px-2 py-1 font-mono text-[10px] text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30"
          >
            |+⟩ Superposition
          </button>
        </div>
      </div>

      {/* Probabilities */}
      <div className="mt-2.5 grid grid-cols-2 gap-2 font-mono text-[11px]">
        <div className="rounded bg-slate-900/80 p-2 text-center border border-slate-800">
          <span className="text-slate-400">P(|0⟩): </span>
          <span className="text-cyan-400 font-bold">{(prob0 * 100).toFixed(1)}%</span>
        </div>
        <div className="rounded bg-slate-900/80 p-2 text-center border border-slate-800">
          <span className="text-slate-400">P(|1⟩): </span>
          <span className="text-rose-400 font-bold">{(prob1 * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}
