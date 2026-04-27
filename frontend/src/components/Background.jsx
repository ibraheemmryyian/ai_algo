import { motion } from 'framer-motion';

export default function Background() {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: -1,
      overflow: 'hidden',
      pointerEvents: 'none',
      backgroundColor: '#000000',
    }}>
      {/* Organic Mesh Gradient blobs (Highly Blurred) */}
      <motion.div
        animate={{
          x: [0, 50, -50, 0],
          y: [0, 30, -30, 0],
          scale: [1, 1.1, 0.9, 1],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        style={{
          position: 'absolute',
          top: '-10%',
          left: '10%',
          width: '50vw',
          height: '50vw',
          background: 'radial-gradient(circle, rgba(79, 70, 229, 0.15) 0%, rgba(0,0,0,0) 60%)', // Indigo
          borderRadius: '50%',
          filter: 'blur(100px)',
        }}
      />
      <motion.div
        animate={{
          x: [0, -60, 40, 0],
          y: [0, -40, 60, 0],
          scale: [1, 1.2, 0.8, 1],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
        style={{
          position: 'absolute',
          bottom: '-10%',
          right: '5%',
          width: '60vw',
          height: '60vw',
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.12) 0%, rgba(0,0,0,0) 60%)', // Violet
          borderRadius: '50%',
          filter: 'blur(120px)',
        }}
      />

      {/* High-density dot matrix overlay for texture */}
      <div style={{
        position: 'absolute',
        inset: 0,
        backgroundImage: `radial-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px)`,
        backgroundSize: '16px 16px',
        opacity: 0.4,
        maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)',
        WebkitMaskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 80%)',
      }} />
      
      {/* Gradient fade out at bottom */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        width: '100%',
        height: '40vh',
        background: 'linear-gradient(to top, #000000 0%, transparent 100%)',
      }} />
    </div>
  );
}
