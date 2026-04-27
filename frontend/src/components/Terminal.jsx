import { useState } from 'react';
import { motion } from 'framer-motion';
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
    { id: 'upload', label: 'Smart Upload', icon: UploadCloud },
    { id: 'tone', label: 'Tone Mimic', icon: Fingerprint },
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
    <motion.div 
      className="glass-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      style={{ padding: '2.5rem', position: 'relative', overflow: 'hidden' }}
    >
      {/* Subtle top edge highlight */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)' }} />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2.5rem', borderBottom: '1px solid var(--border-light)', paddingBottom: '1rem' }}>
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            style={{ 
              background: 'transparent',
              border: 'none',
              color: activeTab === t.id ? 'var(--text-main)' : 'var(--text-muted)',
              padding: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontWeight: activeTab === t.id ? '500' : '400',
              position: 'relative',
              transition: 'color 0.2s ease'
            }}
          >
            <t.icon size={16} style={{ opacity: activeTab === t.id ? 1 : 0.6 }} />
            {t.label}
            {activeTab === t.id && (
              <motion.div 
                layoutId="activeTabIndicator"
                style={{
                  position: 'absolute',
                  bottom: '-17px',
                  left: 0,
                  right: 0,
                  height: '2px',
                  background: 'var(--text-main)',
                  borderRadius: '2px 2px 0 0'
                }}
              />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ minHeight: '220px' }}>
        <AnimatePresence mode="wait">
          {activeTab === 'generate' && (
            <motion.div 
              key="generate"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}
            >
              <div>
                <label style={{ display: 'block', marginBottom: '0.75rem', color: 'var(--text-dim)', fontWeight: 500, fontSize: '0.9rem' }}>TOPIC INSTRUCTION</label>
                <textarea 
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={4} 
                  placeholder="e.g., A cold outreach email to a chemical plant procurement manager..."
                  disabled={isProcessing}
                  style={{ resize: 'vertical', minHeight: '100px' }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.75rem', color: 'var(--text-dim)', fontWeight: 500, fontSize: '0.9rem' }}>STYLOMETRIC MODE</label>
                  <div style={{ position: 'relative' }}>
                    <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={isProcessing} style={{ appearance: 'none' }}>
                      <option value="pulse">Pulse (Short, bursty)</option>
                      <option value="narrative">Narrative (Varied pacing)</option>
                      <option value="scholar">Scholar (Dense logic)</option>
                      <option value="academic">Academic (Formal, strict)</option>
                    </select>
                    <div style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-muted)' }}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                    </div>
                  </div>
                </div>
                <div>
                  <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem', color: 'var(--text-dim)', fontWeight: 500, fontSize: '0.9rem' }}>
                    <span>TARGET WORDS</span>
                    <span style={{ color: 'var(--text-main)' }}>{targetWords}</span>
                  </label>
                  <input 
                    type="range" 
                    min="50" max="2500" step="50" 
                    value={targetWords}
                    onChange={(e) => setTargetWords(e.target.value)}
                    disabled={isProcessing}
                    style={{ padding: 0, height: '4px', background: 'var(--border-light)', borderRadius: '2px', appearance: 'none' }}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'humanize' && (
            <motion.div 
              key="humanize"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
              style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}
            >
              <div>
                <label style={{ display: 'block', marginBottom: '0.75rem', color: 'var(--text-dim)', fontWeight: 500, fontSize: '0.9rem' }}>RAW AI TEXT</label>
                <textarea 
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  rows={6} 
                  placeholder="Paste existing AI text here to apply structural jitter..."
                  disabled={isProcessing}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.75rem', color: 'var(--text-dim)', fontWeight: 500, fontSize: '0.9rem' }}>STYLOMETRIC MODE</label>
                <div style={{ position: 'relative', width: '50%' }}>
                  <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={isProcessing} style={{ appearance: 'none' }}>
                    <option value="pulse">Pulse</option>
                    <option value="narrative">Narrative</option>
                    <option value="scholar">Scholar</option>
                    <option value="academic">Academic</option>
                  </select>
                  <div style={{ position: 'absolute', right: '16px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-muted)' }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {(activeTab === 'upload' || activeTab === 'tone') && (
            <motion.div 
              key="upload"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
              style={{ padding: '4rem', textAlign: 'center', border: '1px dashed var(--border-light)', borderRadius: '8px', background: 'rgba(255,255,255,0.01)' }}
            >
              <UploadCloud size={32} color="var(--text-muted)" style={{ margin: '0 auto 1rem auto' }} />
              <p style={{ color: 'var(--text-main)', fontWeight: 500 }}>Upload files</p>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.5rem' }}>Drag and drop functionality not implemented in UI demo</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Action Bar */}
      <div style={{ marginTop: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
          Powered by Entropy Engine v1.0
        </span>
        <button 
          className="btn-primary" 
          onClick={handleSubmit}
          disabled={isProcessing || (activeTab === 'generate' && !topic) || (activeTab === 'humanize' && !pasteText)}
        >
          {isProcessing ? 'Processing...' : (activeTab === 'generate' ? 'Generate' : 'Process Text')}
        </button>
      </div>
    </motion.div>
  );
}
