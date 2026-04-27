import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Background from './components/Background';
import Terminal from './components/Terminal';
import OutputPanel from './components/OutputPanel';
import './index.css';

function App() {
  const [result, setResult] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState("");

  const handleProcess = async (endpoint, payload) => {
    setIsProcessing(true);
    setResult(null);
    
    // Cycle loading messages for the "over-the-top AI" vibe
    const msgs = [
      "Initializing Ornstein-Uhlenbeck sequence...",
      "Bypassing Turnitin Global Pattern matching...",
      "Injecting semantic jitter...",
      "Applying Bernoulli punctuation friction...",
      "Laundering AI signature..."
    ];
    let msgIdx = 0;
    setLoadingMsg(msgs[0]);
    const interval = setInterval(() => {
      msgIdx = (msgIdx + 1) % msgs.length;
      setLoadingMsg(msgs[msgIdx]);
    }, 2500);

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
      clearInterval(interval);
      setIsProcessing(false);
    }
  };

  return (
    <>
      <Background />
      <div className="app-container" style={{ position: 'relative', zIndex: 10, minHeight: '100vh', padding: '3rem 1rem' }}>
        <header style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <motion.h1 
            className="neon-text"
            style={{ fontSize: '3.5rem', fontFamily: 'var(--font-ui)', margin: 0, letterSpacing: '-0.02em' }}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            ENTROPY ENGINE
          </motion.h1>
          <motion.p 
            style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginTop: '0.5rem' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            Tactical Stylometric Obfuscation. <span style={{color: 'var(--secondary-neon)'}}>Break the pattern.</span>
          </motion.p>
        </header>

        <main style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <Terminal onProcess={handleProcess} isProcessing={isProcessing} />

          <AnimatePresence>
            {isProcessing && (
              <motion.div 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                style={{ textAlign: 'center', padding: '2rem' }}
              >
                <div style={{ 
                  display: 'inline-block',
                  padding: '1rem 2rem',
                  borderRadius: '30px',
                  border: '1px solid var(--primary-neon)',
                  color: 'var(--primary-neon)',
                  fontFamily: 'var(--font-mono)',
                  boxShadow: '0 0 20px rgba(217, 70, 239, 0.2)'
                }}>
                  <motion.span
                    animate={{ opacity: [1, 0.5, 1] }}
                    transition={{ repeat: Infinity, duration: 1.5 }}
                  >
                    ⚡ {loadingMsg}
                  </motion.span>
                </div>
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
