import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { Mountain, RotateCcw, Play, CheckCircle2 } from "lucide-react";

interface QuantumLandscape3DProps {
  optimalBitstring?: string;
  onSelectState?: (state: string) => void;
}

export default function QuantumLandscape3D({
  optimalBitstring = "11010010",
}: QuantumLandscape3DProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const [isTunneling, setIsTunneling] = useState<boolean>(false);
  const particleRef = useRef<THREE.Mesh | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;
    const container = mountRef.current;
    const width = container.clientWidth || 500;
    const height = container.clientHeight || 340;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc); // Crisp light slate

    // Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(10, 9, 12);
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
    controls.maxPolarAngle = Math.PI / 2.1;
    controls.minDistance = 6;
    controls.maxDistance = 28;
    controlsRef.current = controls;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const sun = new THREE.DirectionalLight(0xffffff, 1.2);
    sun.position.set(12, 18, 10);
    sun.castShadow = true;
    scene.add(sun);

    // ── Create 3D Energy Landscape Mesh ──────────────────────────────────────
    const size = 14;
    const segments = 48;
    const geo = new THREE.PlaneGeometry(size, size, segments, segments);
    geo.rotateX(-Math.PI / 2);

    const posAttr = geo.attributes.position;
    const colors: number[] = [];

    // Global minimum valley located at (x: 2.2, z: 1.8)
    const valleyX = 2.2;
    const valleyZ = 1.8;

    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);

      // Distance to global minimum
      const distToValley = Math.hypot(x - valleyX, z - valleyZ);

      // Energy surface: combinatorial hills + penalty barriers - deep valley
      const hills = Math.sin(x * 0.7) * Math.cos(z * 0.7) * 1.2;
      const barriers = Math.cos(x * 1.4) * 0.5 + Math.sin(z * 1.4) * 0.5;
      const valley = -3.2 * Math.exp(-distToValley * 0.7);

      const y = hills + barriers + valley + 0.8;
      posAttr.setY(i, y);

      // Colormap based on energy height y:
      // Lowest (valley / ground state): Emerald / Deep Royal Blue
      // Mid: Slate / Porcelain
      // Highest (violations / penalties): Coral / Amber
      if (y < -0.8) {
        colors.push(0.02, 0.65, 0.42); // Emerald (#059669) - Optimal ground state
      } else if (y < 0.5) {
        colors.push(0.15, 0.45, 0.92); // Cobalt (#2563eb) - Feasible space
      } else if (y < 1.6) {
        colors.push(0.60, 0.65, 0.75); // Slate (#94a3b8) - Saddle points
      } else {
        colors.push(0.92, 0.45, 0.18); // Amber/Coral - Constraint violation peaks
      }
    }

    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geo.computeVertexNormals();

    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      roughness: 0.65,
      metalness: 0.1,
      wireframe: false,
      flatShading: false,
    });

    const mesh = new THREE.Mesh(geo, mat);
    mesh.receiveShadow = true;
    mesh.castShadow = true;
    scene.add(mesh);

    // Wireframe overlay for crisp topological grid lines
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xcbd5e1,
      wireframe: true,
      transparent: true,
      opacity: 0.45,
    });
    const wireMesh = new THREE.Mesh(geo, wireMat);
    wireMesh.position.y += 0.01;
    scene.add(wireMesh);

    // ── Minimum Energy Pin Indicator (Optimal State) ─────────────────────────
    const pinGroup = new THREE.Group();
    pinGroup.position.set(valleyX, -1.8, valleyZ);

    const pinPoleGeo = new THREE.CylinderGeometry(0.04, 0.04, 1.6);
    const pinPoleMat = new THREE.MeshStandardMaterial({ color: 0x059669 });
    const pinPole = new THREE.Mesh(pinPoleGeo, pinPoleMat);
    pinPole.position.y = 0.8;
    pinGroup.add(pinPole);

    const pinHeadGeo = new THREE.SphereGeometry(0.24, 16, 16);
    const pinHeadMat = new THREE.MeshStandardMaterial({
      color: 0x10b981,
      emissive: 0x064e3b,
      emissiveIntensity: 0.6,
    });
    const pinHead = new THREE.Mesh(pinHeadGeo, pinHeadMat);
    pinHead.position.y = 1.6;
    pinGroup.add(pinHead);

    scene.add(pinGroup);

    // ── Quantum Tunneling Wavepacket (Particle) ──────────────────────────────
    const pGeo = new THREE.SphereGeometry(0.3, 24, 24);
    const pMat = new THREE.MeshStandardMaterial({
      color: 0x3b82f6,
      emissive: 0x1d4ed8,
      emissiveIntensity: 0.8,
    });
    const particle = new THREE.Mesh(pGeo, pMat);
    particle.position.set(-3.5, 1.8, -3.0);
    scene.add(particle);
    particleRef.current = particle;

    // Grid base
    const grid = new THREE.GridHelper(16, 16, 0xe2e8f0, 0xf1f5f9);
    grid.position.y = -2.5;
    scene.add(grid);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Gentle floating animation of pin
      pinHead.scale.setScalar(1 + 0.08 * Math.sin(elapsedTime * 3));

      // Quantum Wavepacket trajectory animation
      const t = (Math.sin(elapsedTime * 0.8) + 1) / 2; // 0 to 1
      // Lerp from local minimum (-3.5, 1.8, -3.0) directly into global valley (valleyX, -1.8, valleyZ)
      particle.position.x = -3.5 + t * (valleyX - (-3.5));
      particle.position.z = -3.0 + t * (valleyZ - (-3.0));
      // Tunnels *through* the energy barrier
      particle.position.y = 1.8 - t * (1.8 - (-1.8)) + Math.sin(t * Math.PI) * 0.3;

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

  const resetView = () => {
    controlsRef.current?.reset();
  };

  return (
    <div className="relative w-full h-[360px] rounded-2xl border border-slate-200/90 bg-white shadow-xs overflow-hidden">
      {/* 3D WebGL Canvas */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Top Overlay Badge */}
      <div className="absolute top-3 left-3 flex items-center gap-2 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs">
        <Mountain className="h-4 w-4 text-blue-600" />
        <div>
          <span className="text-xs font-bold text-slate-800">3D QUBO Energy Landscape</span>
          <span className="text-[10px] text-slate-500 block">Hamiltonian $H_C(z)$ Combinatorial Valley</span>
        </div>
      </div>

      {/* Ground State Indicator */}
      <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-xl bg-emerald-50/95 border border-emerald-200 px-3 py-1.5 backdrop-blur-sm shadow-xs">
        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
        <span className="font-mono text-[11px] font-bold text-emerald-800">
          Global Min: |{optimalBitstring}⟩
        </span>
      </div>

      {/* Legend & Controls Overlay */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
        <div className="flex items-center gap-3 rounded-xl bg-white/95 px-3 py-1.5 backdrop-blur-sm border border-slate-200/80 shadow-xs pointer-events-auto text-[10px]">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 inline-block" />
            Global Ground State (₹14.6 Cr)
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-blue-500 inline-block" />
            QAOA Quantum Tunneling
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500 inline-block" />
            Penalty Mountains (&gt; ₹15 Cr)
          </span>
        </div>

        <button
          onClick={resetView}
          className="flex items-center gap-1.5 rounded-xl bg-white/95 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs border border-slate-200/80 hover:bg-slate-50 pointer-events-auto transition-all"
        >
          <RotateCcw className="h-3.5 w-3.5 text-slate-500" />
          Reset Camera
        </button>
      </div>
    </div>
  );
}

