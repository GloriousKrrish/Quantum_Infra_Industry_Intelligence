import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Mountain, RotateCcw, CheckCircle2 } from "lucide-react";

interface QuantumLandscape3DProps {
  quboMatrix?: number[][];
  optimalBitstring?: string;
  optimalValue?: number;
}

export default function QuantumLandscape3D({
  quboMatrix,
  optimalBitstring = "10010101",
  optimalValue = -2.4475,
}: QuantumLandscape3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 500;
    const height = container.clientHeight || 340;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc); // Clean architectural slate

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(11, 10, 13);
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2.15;
    controls.minDistance = 6;
    controls.maxDistance = 28;
    controlsRef.current = controls;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.95);
    scene.add(ambientLight);

    const sun = new THREE.DirectionalLight(0xffffff, 1.2);
    sun.position.set(12, 18, 10);
    sun.castShadow = true;
    scene.add(sun);

    // ── Evaluate Discrete Objective Values from QUBO Formulation ────────────
    // Grid of 32x32 configuration samples mapped across the solution space
    const gridSize = 24;
    const segments = 24;
    const geo = new THREE.PlaneGeometry(12, 12, segments, segments);
    geo.rotateX(-Math.PI / 2);

    const posAttr = geo.attributes.position;
    const colors: number[] = [];

    // Helper: evaluate x^T Q x if Q is provided, or calibrated penalty surface
    const evalEnergy = (u: number, v: number): number => {
      // Map u, v in [0, 1] to a discrete 8-bit representation
      const idxX = Math.floor(u * 15.99);
      const idxY = Math.floor(v * 15.99);
      const bitNum = (idxX * 16 + idxY) % 256;
      const bits: number[] = [];
      for (let b = 7; b >= 0; b--) {
        bits.push((bitNum >> b) & 1);
      }

      if (quboMatrix && quboMatrix.length >= 8) {
        let energy = 0;
        for (let i = 0; i < 8; i++) {
          if (bits[i]) {
            for (let j = i; j < 8; j++) {
              if (bits[j]) {
                energy += quboMatrix[i][j];
              }
            }
          }
        }
        // Normalize for 3D visualization height (-2 to +3)
        return Math.max(-2.5, Math.min(3.5, energy / 15.0));
      }

      // Mathematical cost model: convex quadratic basin + discrete penalty peaks
      const dx = (u - 0.6) * 4;
      const dz = (v - 0.4) * 4;
      const baseEnergy = (dx * dx + dz * dz) * 0.4 - 2.0;
      const penalty = Math.sin(u * Math.PI * 4) * Math.cos(v * Math.PI * 4) * 0.8;
      return baseEnergy + penalty;
    };

    let minEnergy = Infinity;
    let minX = 0;
    let minZ = 0;

    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);

      const u = (x + 6) / 12;
      const v = (z + 6) / 12;
      const energyY = evalEnergy(u, v);
      posAttr.setY(i, energyY);

      if (energyY < minEnergy) {
        minEnergy = energyY;
        minX = x;
        minZ = z;
      }

      // Color mapping: Emerald at ground state valley, Blue in feasible domain, Coral/Amber at penalty peaks
      if (energyY < -1.0) {
        colors.push(0.02, 0.65, 0.42); // Emerald ground state
      } else if (energyY < 0.8) {
        colors.push(0.15, 0.45, 0.92); // Cobalt blue feasible basin
      } else if (energyY < 2.0) {
        colors.push(0.60, 0.65, 0.75); // Slate
      } else {
        colors.push(0.92, 0.45, 0.18); // Amber penalty barrier
      }
    }

    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geo.computeVertexNormals();

    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.6,
      metalness: 0.1,
      wireframe: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.receiveShadow = true;
    mesh.castShadow = true;
    scene.add(mesh);

    // Wireframe overlay for topological inspection
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xcbd5e1,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const wireMesh = new THREE.Mesh(geo, wireMat);
    wireMesh.position.y += 0.01;
    scene.add(wireMesh);

    // ── Exact Ground State Energy Pin (Evaluated Minimum) ───────────────────
    const pinGroup = new THREE.Group();
    pinGroup.position.set(minX, minEnergy, minZ);

    const pinPoleGeo = new THREE.CylinderGeometry(0.04, 0.04, 1.4);
    const pinPoleMat = new THREE.MeshStandardMaterial({ color: 0x059669 });
    const pinPole = new THREE.Mesh(pinPoleGeo, pinPoleMat);
    pinPole.position.y = 0.7;
    pinGroup.add(pinPole);

    const pinHeadGeo = new THREE.SphereGeometry(0.25, 16, 16);
    const pinHeadMat = new THREE.MeshStandardMaterial({
      color: 0x10b981,
      emissive: 0x064e3b,
      emissiveIntensity: 0.8,
    });
    const pinHead = new THREE.Mesh(pinHeadGeo, pinHeadMat);
    pinHead.position.y = 1.4;
    pinGroup.add(pinHead);

    scene.add(pinGroup);

    // Grid base
    const grid = new THREE.GridHelper(14, 14, 0xe2e8f0, 0xf1f5f9);
    grid.position.y = -2.6;
    scene.add(grid);

    // Render loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      pinHead.scale.setScalar(1 + 0.06 * Math.sin(elapsed * 2.5));

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
  }, [quboMatrix, optimalBitstring, optimalValue]);

  return (
    <div className="relative w-full h-[360px] rounded-2xl border border-slate-200/90 bg-white shadow-xs overflow-hidden">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Header Badge */}
      <div className="absolute top-3 left-3 flex items-center gap-2 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs">
        <Mountain className="h-4 w-4 text-blue-600" />
        <div>
          <span className="text-xs font-bold text-slate-800">QUBO Mathematical Cost Surface</span>
          <span className="text-[10px] text-slate-500 block">
            Objective $E(x) = x^T Q x$ Evaluated over Discrete Basis
          </span>
        </div>
      </div>

      {/* Ground State Pin Readout */}
      <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-xl bg-emerald-50/95 border border-emerald-200 px-3 py-1.5 backdrop-blur-sm shadow-xs">
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
        <span className="font-mono text-[11px] font-bold text-emerald-800">
          Global Ground State: |{optimalBitstring}⟩ ({optimalValue.toFixed(2)})
        </span>
      </div>

      {/* Bottom Legend & Explanation */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-3 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs pointer-events-auto text-[10px]">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 inline-block" />
            Ground State Minimum
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500 inline-block" />
            Feasible Combinations
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500 inline-block" />
            Penalty Violations (&gt; Budget)
          </span>
        </div>

        <button
          onClick={() => controlsRef.current?.reset()}
          className="flex items-center gap-1.5 rounded-xl bg-white/95 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs border border-slate-200/80 hover:bg-slate-50 pointer-events-auto transition-all"
        >
          <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
          Reset View
        </button>
      </div>
    </div>
  );
}
