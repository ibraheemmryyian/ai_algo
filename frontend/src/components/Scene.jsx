import { Canvas } from '@react-three/fiber';
import { Environment, EffectComposer, Bloom } from '@react-three/drei';
import ParticleField from './ParticleField';

export default function Scene() {
  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', zIndex: -1, background: '#020205' }}>
      <Canvas camera={{ position: [0, 0, 15], fov: 60 }}>
        <color attach="background" args={['#020205']} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#d946ef" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#0ea5e9" />
        
        <ParticleField count={3000} />
        
        <EffectComposer disableNormalPass>
          <Bloom luminanceThreshold={0.2} mipmapBlur intensity={1.5} />
        </EffectComposer>
        <Environment preset="city" />
      </Canvas>
      
      {/* Vignette Overlay for depth */}
      <div style={{
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(circle at center, transparent 30%, #020205 100%)',
        pointerEvents: 'none'
      }} />
    </div>
  );
}
