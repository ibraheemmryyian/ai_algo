import { useState, useRef } from 'react';
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from 'framer-motion';
import Scene from './components/Scene';
import Terminal from './components/Terminal';
import OutputPanel from './components/OutputPanel';
import './index.css';

function App() {
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [glitchTitle, setGlitchTitle] = useState(false);

  // 3D Tilt Physics for entire container
  const containerRef = useRef(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const mouseXSpring = useSpring(x, { stiffness: 40, damping: 15 });
  const mouseYSpring = useSpring(y, { stiffness: 40, damping: 15 });
  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["10deg", "-10deg"]);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-10deg", "10deg"]);

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xPct = mouseX / width - 0.5;
    const yPct = mouseY / height - 0.5;
    x.set(xPct);
    y.set(yPct);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const handleProcess = async (endpoint, payload) => {
    setIsProcessing(true);
    setGlitchTitle(true);
    setResult(null);

    try {
      const response = await fetch(`http://localhost:8000/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Processing failed");
      }
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
      setGlitchTitle(false);
    }
  };

  return (
    <div 
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ width: '100vw', minHeight: '100vh', perspective: '1200px' }}
    >
      <Scene />
      
      <motion.div 
        style={{ 
          position: 'relative', 
          zIndex: 10, 
          padding: '4rem 2rem',
          rotateX,
          rotateY,
          transformStyle: "preserve-3d"
        }}
      >
        <header style={{ textAlign: 'center', marginBottom: '4rem', transform: 'translateZ(50px)' }}>
          <motion.h1 
            className={`text-gradient ${glitchTitle ? 'glitch-text' : ''}`}
            data-text="ENTROPY ENGINE"
            style={{ fontSize: '5rem', margin: 0, lineHeight: 1, letterSpacing: '0.05em', textTransform: 'uppercase' }}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, type: 'spring' }}
          >
            ENTROPY ENGINE
          </motion.h1>
        </header>

        <main style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '3rem', transformStyle: "preserve-3d" }}>
          
          <motion.div style={{ transform: 'translateZ(30px)' }}>
             <Terminal onProcess={handleProcess} isProcessing={isProcessing} />
          </motion.div>

          <AnimatePresence>
            {isProcessing && (
              <motion.div 
                initial={{ opacity: 0, y: 50, rotateX: -20 }}
                animate={{ opacity: 1, y: 0, rotateX: 0 }}
                exit={{ opacity: 0, scale: 0.8, filter: 'blur(10px)' }}
                style={{ textAlign: 'center', padding: '2rem', transform: 'translateZ(80px)' }}
              >
                <h2 className="glitch-text" data-text="BYPASSING SEMANTIC FILTERS..." style={{ color: 'var(--primary)', fontFamily: 'var(--font-mono)' }}>
                  BYPASSING SEMANTIC FILTERS...
                </h2>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {result && !isProcessing && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.8, y: 100, rotateX: 45 }}
                animate={{ opacity: 1, scale: 1, y: 0, rotateX: 0 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={{ type: "spring", damping: 15, stiffness: 100 }}
                style={{ transform: 'translateZ(60px)' }}
              >
                <OutputPanel result={result} onClear={() => setResult(null)} />
              </motion.div>
            )}
          </AnimatePresence>

        </main>
      </motion.div>
    </div>
  );
}

export default App;
