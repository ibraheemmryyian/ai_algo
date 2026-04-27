import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers, Sparkles, UploadCloud, Fingerprint } from 'lucide-react';

export default function Terminal({ onProcess, isProcessing }) {
  const [activeTab, setActiveTab] = useState('generate');
  
  // Form States
  const [topic, setTopic] = useState('');
  const [mode, setMode] = useState('pulse');
  const [targetWords, setTargetWords] = useState(300);
  const [pasteText, setPasteText] = useState('');

  const tabs = [
    { id: 'generate', label: 'Generate', icon: Layers },
    { id: 'humanize', label: 'Humanize', icon: Sparkles },
    { id: 'upload', label: 'Upload', icon: UploadCloud },
    { id: 'tone', label: 'Tone Extract', icon: Fingerprint },
  ];

  const handleSubmit = () => {
    if (activeTab === 'generate') {
      onProcess('generate', { topic, mode, target_words: parseInt(targetWords) });
    } else if (activeTab === 'humanize') {
      onProcess('humanize', { text: pasteText, mode });
    } else {
      alert("This tab is under construction for the UI demo.");
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '3rem', position: 'relative' }}>
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '2rem', marginBottom: '3rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{ 
              background: 'transparent',
              border: 'none',
              color: activeTab === t.id ? 'var(--primary)' : 'var(--text-muted)',
              padding: '0.5rem 0',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontWeight: activeTab === t.id ? '800' : '400',
              fontSize: '1.1rem',
              position: 'relative',
              transition: 'all 0.3s ease',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            <t.icon size={18} style={{ opacity: activeTab === t.id ? 1 : 0.6 }} />
            {t.label}
            {activeTab === t.id && (
              <motion.div 
                layoutId="activeTabIndicator3D"
                style={{
                  position: 'absolute',
                  bottom: '-17px',
                  left: 0,
                  right: 0,
                  height: '3px',
                  background: 'var(--primary)',
                  boxShadow: '0 0 10px var(--primary)'
                }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ minHeight: '220px', transform: 'translateZ(10px)', transformStyle: 'preserve-3d' }}>
        <AnimatePresence mode="wait">
          {activeTab === 'generate' && (
            <motion.div 
              key="generate"
              initial={{ opacity: 0, rotateX: -10 }}
              animate={{ opacity: 1, rotateX: 0 }}
              exit={{ opacity: 0, rotateX: 10 }}
              transition={{ duration: 0.3 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}
            >
              <div>
                <label style={{ display: 'block', marginBottom: '1rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.9rem', letterSpacing: '0.1em' }}>INSTRUCTION VECTOR</label>
                <textarea 
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={4} 
                  placeholder="e.g., A cold outreach email to a chemical plant procurement manager..."
                  disabled={isProcessing}
                  style={{ resize: 'vertical', minHeight: '100px' }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '1rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.9rem', letterSpacing: '0.1em' }}>STYLOMETRIC PROFILE</label>
                  <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={isProcessing}>
                    <option value="pulse">Pulse (Short, bursty)</option>
                    <option value="narrative">Narrative (Varied pacing)</option>
                    <option value="scholar">Scholar (Dense logic)</option>
                    <option value="academic">Academic (Formal, strict)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.9rem', letterSpacing: '0.1em' }}>
                    <span>TARGET LENGTH (WORDS)</span>
                    <span style={{ color: 'var(--primary)' }}>{targetWords}</span>
                  </label>
                  <input 
                    type="range" 
                    min="50" max="2500" step="50" 
                    value={targetWords}
                    onChange={(e) => setTargetWords(e.target.value)}
                    disabled={isProcessing}
                    style={{ padding: 0, height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', appearance: 'none' }}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'humanize' && (
            <motion.div 
              key="humanize"
              initial={{ opacity: 0, rotateX: -10 }}
              animate={{ opacity: 1, rotateX: 0 }}
              exit={{ opacity: 0, rotateX: 10 }}
              transition={{ duration: 0.3 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '2.5rem' }}
            >
              <div>
                <label style={{ display: 'block', marginBottom: '1rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.9rem', letterSpacing: '0.1em' }}>RAW AI PAYLOAD</label>
                <textarea 
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  rows={6} 
                  placeholder="Paste existing AI text here to apply structural jitter..."
                  disabled={isProcessing}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '1rem', color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.9rem', letterSpacing: '0.1em' }}>STYLOMETRIC PROFILE</label>
                <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={isProcessing} style={{ width: '50%' }}>
                  <option value="pulse">Pulse</option>
                  <option value="narrative">Narrative</option>
                  <option value="scholar">Scholar</option>
                  <option value="academic">Academic</option>
                </select>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Action Bar */}
      <div style={{ marginTop: '4rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isProcessing ? 'var(--primary)' : 'var(--secondary)', boxShadow: `0 0 10px ${isProcessing ? 'var(--primary)' : 'var(--secondary)'}` }} />
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', letterSpacing: '0.1em' }}>
            STATUS: {isProcessing ? 'INJECTING ENTROPY' : 'READY'}
          </span>
        </div>
        
        <button 
          className="btn-magnetic" 
          onClick={handleSubmit}
          disabled={isProcessing || (activeTab === 'generate' && !topic) || (activeTab === 'humanize' && !pasteText)}
        >
          {activeTab === 'generate' ? 'Generate' : 'Process Payload'}
        </button>
      </div>
    </div>
  );
}
