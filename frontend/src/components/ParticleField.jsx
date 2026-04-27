import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function Particles({ count = 200 }) {
  const mesh = useRef();
  
  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const velocities = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 30;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 15;
      
      velocities[i * 3] = (Math.random() - 0.5) * 0.005;
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.005;
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.005;
    }
    return { positions, velocities };
  }, [count]);

  useFrame(() => {
    if (!mesh.current) return;
    const pos = mesh.current.geometry.attributes.position.array;
    
    for (let i = 0; i < count; i++) {
      pos[i * 3] += particles.velocities[i * 3];
      pos[i * 3 + 1] += particles.velocities[i * 3 + 1];
      pos[i * 3 + 2] += particles.velocities[i * 3 + 2];
      
      // Wrap around boundaries
      if (Math.abs(pos[i * 3]) > 15) particles.velocities[i * 3] *= -1;
      if (Math.abs(pos[i * 3 + 1]) > 10) particles.velocities[i * 3 + 1] *= -1;
      if (Math.abs(pos[i * 3 + 2]) > 7.5) particles.velocities[i * 3 + 2] *= -1;
    }
    
    mesh.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={particles.positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color="#4a5568"
        transparent
        opacity={0.6}
        sizeAttenuation
        depthWrite={false}
      />
    </points>
  );
}

export default function ParticleField() {
  return (
    <div className="particle-canvas">
      <Canvas camera={{ position: [0, 0, 8], fov: 50 }} dpr={[1, 1.5]}>
        <Particles />
      </Canvas>
    </div>
  );
}
