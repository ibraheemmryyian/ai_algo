import { useState } from 'react';
import { motion } from 'framer-motion';
import Tilt from 'react-parallax-tilt';
import { TerminalSquare, Sparkles, UploadCloud, Fingerprint } from 'lucide-react';

export default function Terminal({ onProcess, isProcessing }) {
  const [activeTab, setActiveTab] = useState('generate');
  
  // Form States
  const [topic, setTopic] = useState('');
  const [mode, setMode] = useState('pulse');
  const [targetWords, setTargetWords] = useState(300);
  const [pasteText, setPasteText] = useState('');

  const tabs = [
    { id: 'generate', label: 'Generate', icon: TerminalSquare },
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
    <Tilt tiltMaxAngleX={2} tiltMaxAngleY={2} glareEnable={true} glareMaxOpacity={0.1} glareColor="#fff" glarePosition="all" scale={1.01} transitionSpeed={2000}>
      <motion.div 
        className="glass-panel"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={{ padding: '2rem' }}
      >
        {/* Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1rem' }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={activeTab === t.id ? 'btn-secondary' : ''}
              style={{ 
                background: activeTab === t.id ? 'rgba(217, 70, 239, 0.1)' : 'transparent',
                border: activeTab === t.id ? '1px solid var(--primary-neon)' : '1px solid transparent',
                color: activeTab === t.id ? 'var(--text-main)' : 'var(--text-muted)',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: activeTab === t.id ? '600' : '500'
              }}
            >
              <t.icon size={16} color={activeTab === t.id ? 'var(--primary-neon)' : 'currentColor'} />
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ minHeight: '200px' }}>
          {activeTab === 'generate' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Target Topic / Prompt</label>
                <textarea 
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  rows={4} 
                  placeholder="e.g. A cold outreach email to a chemical plant procurement manager..."
                  disabled={isProcessing}
                />
              </div>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Stylometric Mode</label>
                  <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={isProcessing}>
                    <option value="pulse">Pulse (Short, bursty, DMs)</option>
                    <option value="narrative">Narrative (Story-driven, varied)</option>
                    <option value="scholar">Scholar (Dense, professional)</option>
                    <option value="academic">Academic (Formal, hedged, rigid)</option>
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Target Word Count: {targetWords}</label>
                  <input 
                    type="range" 
                    min="50" max="2500" step="50" 
                    value={targetWords}
                    onChange={(e) => setTargetWords(e.target.value)}
                    disabled={isProcessing}
                  />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'humanize' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Raw AI Output</label>
                <textarea 
                  value={pasteText}
                  onChange={(e) => setPasteText(e.target.value)}
                  rows={6} 
                  placeholder="Paste ChatGPT/Claude output here..."
                  disabled={isProcessing}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Stylometric Mode</label>
                <select value={mode} onChange={(e) => setMode(e.target.value)} disabled={isProcessing}>
                  <option value="pulse">Pulse</option>
                  <option value="narrative">Narrative</option>
                  <option value="scholar">Scholar</option>
                  <option value="academic">Academic</option>
                </select>
              </div>
            </div>
          )}
          
          {(activeTab === 'upload' || activeTab === 'tone') && (
            <div style={{ padding: '3rem', textAlign: 'center', border: '1px dashed var(--glass-border)', borderRadius: '8px' }}>
              <UploadCloud size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem auto' }} />
              <p style={{ color: 'var(--text-muted)' }}>Drag and drop files here (UI Demo only - use CLI for full file pipeline)</p>
            </div>
          )}
        </div>

        {/* Action Bar */}
        <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
          <button 
            className="btn-primary" 
            onClick={handleSubmit}
            disabled={isProcessing || (activeTab === 'generate' && !topic) || (activeTab === 'humanize' && !pasteText)}
          >
            {isProcessing ? 'Processing...' : (activeTab === 'generate' ? 'Initiate Entropy' : 'Launder Text')}
          </button>
        </div>
      </motion.div>
    </Tilt>
  );
}
