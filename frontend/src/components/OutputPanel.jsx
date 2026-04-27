import { motion } from 'framer-motion';
import { Copy, RefreshCw } from 'lucide-react';

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
    { label: "Punct Breaks", val: jitter_stats?.punct_breaks || 0 },
    { label: "Embargos", val: jitter_stats?.embargo_rewrites || 0 },
    { label: "Injections", val: (jitter_stats?.fragment_rewrites || 0) + (jitter_stats?.temporal_injections || 0) },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className="glass-panel" 
      style={{ padding: '2.5rem', marginTop: '2rem' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.1rem', margin: 0, fontWeight: 500 }}>Output Result</h2>
          <span style={{ 
            color: 'var(--text-muted)', 
            fontSize: '0.8rem',
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Mode: {mode}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={handleCopy} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }} title="Copy">
            <Copy size={14} /> <span>Copy</span>
          </button>
          <button onClick={onClear} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }} title="Clear">
            <RefreshCw size={14} /> <span>Clear</span>
          </button>
        </div>
      </div>

      <div style={{ 
        background: 'rgba(255,255,255,0.02)', 
        padding: '2rem', 
        borderRadius: '8px', 
        border: '1px solid var(--border-light)',
        fontFamily: 'var(--font-body)',
        fontSize: '0.95rem',
        lineHeight: 1.8,
        color: 'var(--text-main)',
        whiteSpace: 'pre-wrap',
        maxHeight: '500px',
        overflowY: 'auto',
        fontWeight: 400
      }}>
        {text}
      </div>

      {/* Stats Grid */}
      <div style={{ marginTop: '2.5rem' }}>
        <h3 style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '1rem', fontWeight: 600 }}>Stylometric Fingerprint</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
          {statCards.map((s, idx) => (
            <div key={idx} style={{ 
              background: 'rgba(255,255,255,0.01)', 
              padding: '1.25rem 1rem', 
              borderRadius: '6px', 
              border: '1px solid var(--border-light)',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem'
            }}>
              <div style={{ 
                fontSize: '1.25rem', 
                fontWeight: 500, 
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-main)'
              }}>
                {s.val}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
