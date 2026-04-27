import { motion } from 'framer-motion';
import { Copy, Download, RefreshCcw } from 'lucide-react';
import Tilt from 'react-parallax-tilt';

export default function OutputPanel({ result, onClear }) {
  if (!result) return null;

  const { text, stats, jitter_stats, mode, actual_words } = result;

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
  };

  const statCards = [
    { label: "Words", val: actual_words },
    { label: "O-U Length STD", val: stats?.std ? stats.std.toFixed(1) : "-" },
    { label: "Logprob Swaps", val: jitter_stats?.logprob_swaps || 0 },
    { label: "Punctuation Breaks", val: jitter_stats?.punct_breaks || 0 },
    { label: "Coordination Embargos", val: jitter_stats?.embargo_rewrites || 0 },
    { label: "Structural Injections", val: (jitter_stats?.fragment_rewrites || 0) + (jitter_stats?.temporal_injections || 0) },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.5 }}
    >
      <Tilt tiltMaxAngleX={1} tiltMaxAngleY={1} glareEnable={true} glareMaxOpacity={0.05} glareColor="#fff" glarePosition="all" scale={1.0}>
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Processed Output</h2>
              <span style={{ 
                background: 'rgba(6, 182, 212, 0.1)', 
                color: 'var(--secondary-neon)', 
                padding: '0.2rem 0.6rem', 
                borderRadius: '4px', 
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                border: '1px solid rgba(6, 182, 212, 0.3)'
              }}>
                {mode}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={handleCopy} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem' }} title="Copy">
                <Copy size={16} /> <span style={{fontSize: '0.8rem'}}>Copy</span>
              </button>
              <button onClick={onClear} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem' }} title="Clear">
                <RefreshCcw size={16} /> <span style={{fontSize: '0.8rem'}}>Clear</span>
              </button>
            </div>
          </div>

          <div style={{ 
            background: 'rgba(0,0,0,0.5)', 
            padding: '1.5rem', 
            borderRadius: '8px', 
            border: '1px solid rgba(255,255,255,0.05)',
            fontFamily: 'var(--font-body)',
            fontSize: '1rem',
            lineHeight: 1.8,
            color: 'var(--text-main)',
            whiteSpace: 'pre-wrap',
            maxHeight: '400px',
            overflowY: 'auto'
          }}>
            {text}
          </div>

          {/* Stats Grid */}
          <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '1rem' }}>
            {statCards.map((s, idx) => (
              <div key={idx} style={{ 
                background: 'rgba(255,255,255,0.02)', 
                padding: '1rem', 
                borderRadius: '8px', 
                textAlign: 'center',
                border: '1px solid rgba(255,255,255,0.05)'
              }}>
                <div style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: 700, 
                  fontFamily: 'var(--font-mono)',
                  background: 'linear-gradient(135deg, var(--primary-neon), var(--secondary-neon))',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  {s.val}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.2rem' }}>
                  {s.label}
                </div>
              </div>
            ))}
          </div>

        </div>
      </Tilt>
    </motion.div>
  );
}
