import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Background from './components/Background';
import Terminal from './components/Terminal';
import OutputPanel from './components/OutputPanel';
import './index.css';

function App() {
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleProcess = async (endpoint, payload) => {
    setIsProcessing(true);
    setResult(null);

    try {
      const response = await fetch(`http://localhost:8000/api/${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
    }
  };

  return (
    <>
      <Background />
      <div className="app-container" style={{ position: 'relative', zIndex: 10, minHeight: '100vh', padding: '4rem 2rem' }}>
        <header style={{ textAlign: 'center', marginBottom: '4rem' }}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <h1 
              className="text-gradient"
              style={{ fontSize: '4.5rem', margin: 0, lineHeight: 1.1, letterSpacing: '-0.04em' }}
            >
              Entropy Engine
            </h1>
            <p style={{ 
              color: 'var(--text-muted)', 
              fontSize: '1.25rem', 
              marginTop: '1rem',
              fontWeight: 400,
              letterSpacing: '-0.01em',
              maxWidth: '600px',
              margin: '1rem auto 0 auto'
            }}>
              Tactical stylometric obfuscation to bypass semantic detectors. 
              Built for high-variance, undetectable generation.
            </p>
          </motion.div>
        </header>

        <main style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <Terminal onProcess={handleProcess} isProcessing={isProcessing} />

          <AnimatePresence>
            {isProcessing && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                style={{ textAlign: 'center', padding: '2rem', overflow: 'hidden' }}
              >
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '1rem' }}>
                  {/* Elegant spinner */}
                  <div style={{
                    width: '18px',
                    height: '18px',
                    border: '2px solid var(--border-light)',
                    borderTopColor: 'var(--text-main)',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>Processing stylistic variance...</span>
                </div>
                <style>{`
                  @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                `}</style>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {result && !isProcessing && (
              <OutputPanel result={result} onClear={() => setResult(null)} />
            )}
          </AnimatePresence>
        </main>
      </div>
    </>
  );
}

export default App;
