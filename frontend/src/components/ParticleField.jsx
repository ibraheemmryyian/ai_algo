import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function ParticleField({ count = 2000 }) {
  const mesh = useRef();
  const dummy = useMemo(() => new THREE.Object3D(), []);

  // Generate random positions and velocities
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < count; i++) {
      const x = (Math.random() - 0.5) * 40;
      const y = (Math.random() - 0.5) * 40;
      const z = (Math.random() - 0.5) * 40;
      const vx = (Math.random() - 0.5) * 0.02;
      const vy = (Math.random() - 0.5) * 0.02;
      const vz = (Math.random() - 0.5) * 0.02;
      const factor = Math.random() * 0.5 + 0.5;
      temp.push({ x, y, z, vx, vy, vz, factor });
    }
    return temp;
  }, [count]);

  useFrame((state) => {
    // Mouse interaction
    const mouseX = (state.pointer.x * state.viewport.width) / 2;
    const mouseY = (state.pointer.y * state.viewport.height) / 2;

    particles.forEach((particle, i) => {
      // Basic drift
      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.z += particle.vz;

      // Mouse repulsion
      const dx = mouseX - particle.x;
      const dy = mouseY - particle.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist < 5) {
        const force = (5 - dist) * 0.02;
        particle.vx -= (dx / dist) * force;
        particle.vy -= (dy / dist) * force;
      }

      // Constrain to box (bounce)
      if (Math.abs(particle.x) > 20) particle.vx *= -1;
      if (Math.abs(particle.y) > 20) particle.vy *= -1;
      if (Math.abs(particle.z) > 20) particle.vz *= -1;

      // Apply friction
      particle.vx *= 0.99;
      particle.vy *= 0.99;
      particle.vz *= 0.99;

      // Ensure min velocity
      if (Math.abs(particle.vx) < 0.001) particle.vx += (Math.random() - 0.5) * 0.01;
      if (Math.abs(particle.vy) < 0.001) particle.vy += (Math.random() - 0.5) * 0.01;

      // Update dummy and matrix
      dummy.position.set(particle.x, particle.y, particle.z);
      dummy.rotation.x += particle.vx * 2;
      dummy.rotation.y += particle.vy * 2;
      const s = Math.max(0.1, Math.sin(state.clock.elapsedTime * particle.factor) * 0.2 + 0.8);
      dummy.scale.set(s, s, s);
      dummy.updateMatrix();
      
      mesh.current.setMatrixAt(i, dummy.matrix);
    });
    
    mesh.current.instanceMatrix.needsUpdate = true;
    
    // Slowly rotate the entire field
    mesh.current.rotation.y = state.clock.elapsedTime * 0.05;
    mesh.current.rotation.x = state.clock.elapsedTime * 0.02;
  });

  return (
    <instancedMesh ref={mesh} args={[null, null, count]}>
      <octahedronGeometry args={[0.08, 0]} />
      <meshStandardMaterial 
        color="#a855f7" 
        emissive="#d946ef" 
        emissiveIntensity={2} 
        toneMapped={false} 
        transparent 
        opacity={0.8}
        wireframe
      />
    </instancedMesh>
  );
}
