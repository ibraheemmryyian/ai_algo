import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { useScroll, Text } from '@react-three/drei';
import * as THREE from 'three';

// Generate jagged line for the tear
function generateJaggedLine(startX, startY, endX, endY, segments, variance) {
  const points = [];
  points.push(new THREE.Vector2(startX, startY));
  
  for (let i = 1; i < segments; i++) {
    const t = i / segments;
    const x = startX + (endX - startX) * t;
    const y = startY + (endY - startY) * t;
    
    // Add random variance perpendicular to the line
    const dx = endX - startX;
    const dy = endY - startY;
    const len = Math.sqrt(dx*dx + dy*dy);
    const nx = -dy / len;
    const ny = dx / len;
    
    const jitter = (Math.random() - 0.5) * variance;
    points.push(new THREE.Vector2(x + nx * jitter, y + ny * jitter));
  }
  
  points.push(new THREE.Vector2(endX, endY));
  return points;
}

// Create the two halves of the paper
const createPaperHalves = () => {
  const width = 6;
  const height = 8;
  const hw = width / 2;
  const hh = height / 2;
  
  // The shared jagged line down the middle
  const jaggedPoints = generateJaggedLine(0, hh, 0, -hh, 15, 0.8);
  
  // Left half shape
  const leftShape = new THREE.Shape();
  leftShape.moveTo(-hw, hh);
  leftShape.lineTo(jaggedPoints[0].x, jaggedPoints[0].y);
  for (let i = 1; i < jaggedPoints.length; i++) {
    leftShape.lineTo(jaggedPoints[i].x, jaggedPoints[i].y);
  }
  leftShape.lineTo(-hw, -hh);
  leftShape.lineTo(-hw, hh);
  
  // Right half shape
  const rightShape = new THREE.Shape();
  rightShape.moveTo(jaggedPoints[0].x, jaggedPoints[0].y);
  rightShape.lineTo(hw, hh);
  rightShape.lineTo(hw, -hh);
  rightShape.lineTo(jaggedPoints[jaggedPoints.length - 1].x, jaggedPoints[jaggedPoints.length - 1].y);
  for (let i = jaggedPoints.length - 2; i >= 0; i--) {
    rightShape.lineTo(jaggedPoints[i].x, jaggedPoints[i].y);
  }
  
  return { leftShape, rightShape };
};

const DUMMY_ESSAY = `
Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. 
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris 
nisi ut aliquip ex ea commodo consequat. 

Duis aute irure dolor in reprehenderit in voluptate velit esse 
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat 
cupidatat non proident, sunt in culpa qui officia deserunt 
mollit anim id est laborum.

This document represents original intellectual property.
Any attempt to obfuscate or launder the stylometric
signatures contained within will result in immediate
flagging by automated detection systems.

-- ACADEMIC INTEGRITY BOARD
`;

function PaperHalf({ shape, side, scrollData }) {
  const meshRef = useRef();
  
  // Simple thin extrusion for paper
  const extrudeSettings = useMemo(() => ({
    depth: 0.01,
    bevelEnabled: false
  }), []);

  useFrame(() => {
    if (!meshRef.current) return;
    
    // scroll.offset goes from 0 to 1
    const offset = scrollData.offset;
    
    // The "effort" phase: from 0 to 0.3, it jiggles slightly but holds together
    // The "rip" phase: from 0.3 to 0.8, it rips violently apart
    // The "hide" phase: floats off screen
    
    let targetX = 0;
    let targetY = 0;
    let targetZ = 0;
    let rotX = 0;
    let rotY = 0;
    let rotZ = 0;

    if (offset < 0.1) {
      // Resting state
    } else if (offset < 0.3) {
      // Tension state - jiggle
      const tension = (offset - 0.1) / 0.2; // 0 to 1
      targetX = (Math.random() - 0.5) * 0.05 * tension;
      targetY = (Math.random() - 0.5) * 0.05 * tension;
    } else {
      // Rip and float away
      const ripProgress = Math.min((offset - 0.3) / 0.5, 1); // 0 to 1
      
      // Left piece goes left, up, and rotates left
      // Right piece goes right, up, and rotates right
      const dir = side === 'left' ? -1 : 1;
      
      // Easing function for the snap
      const snap = 1 - Math.pow(1 - ripProgress, 3);
      
      targetX = dir * (snap * 5);
      targetY = snap * 2;
      targetZ = snap * 3; // Moves toward camera
      
      rotX = snap * 0.5;
      rotY = dir * snap * 0.8;
      rotZ = dir * snap * 0.5;
    }

    // Smooth dampening
    meshRef.current.position.x += (targetX - meshRef.current.position.x) * 0.1;
    meshRef.current.position.y += (targetY - meshRef.current.position.y) * 0.1;
    meshRef.current.position.z += (targetZ - meshRef.current.position.z) * 0.1;
    
    meshRef.current.rotation.x += (rotX - meshRef.current.rotation.x) * 0.1;
    meshRef.current.rotation.y += (rotY - meshRef.current.rotation.y) * 0.1;
    meshRef.current.rotation.z += (rotZ - meshRef.current.rotation.z) * 0.1;
  });

  return (
    <group ref={meshRef}>
      <mesh receiveShadow castShadow>
        <extrudeGeometry args={[shape, extrudeSettings]} />
        <meshStandardMaterial 
          color="#f4f4f5" 
          roughness={0.8}
          metalness={0.1}
        />
      </mesh>
      
      {/* Paper Text Overlay */}
      <Text
        position={[side === 'left' ? -1.5 : 1.5, 0, 0.02]}
        fontSize={0.2}
        color="#334155"
        maxWidth={2.5}
        textAlign={side === 'left' ? 'right' : 'left'}
        anchorX={side === 'left' ? 'right' : 'left'}
        anchorY="middle"
        lineHeight={1.5}
      >
        {DUMMY_ESSAY}
      </Text>
    </group>
  );
}

export default function Scene() {
  const scrollData = useScroll();
  const { leftShape, rightShape } = useMemo(() => createPaperHalves(), []);

  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight 
        position={[5, 10, 5]} 
        intensity={1.5} 
        color="#ffffff" 
        castShadow 
      />
      <directionalLight position={[-5, 5, -5]} intensity={0.5} color="#e2e8f0" />
      
      <group position={[0, 0, 0]}>
        <PaperHalf shape={leftShape} side="left" scrollData={scrollData} />
        <PaperHalf shape={rightShape} side="right" scrollData={scrollData} />
      </group>
    </>
  );
}
