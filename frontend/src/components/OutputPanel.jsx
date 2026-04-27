import { motion } from 'framer-motion';
import { Copy, RefreshCw } from 'lucide-react';

export default function OutputPanel({ result, onClear }) {
  if (!result) return null;

  const { text, stats, jitter_stats, mode, actual_words } = result;

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
  };

  const statCards = [
    { label: "WORDS", val: actual_words },
    { label: "O-U LENGTH STD", val: stats?.std ? stats.std.toFixed(1) : "-" },
    { label: "LOGPROB SWAPS", val: jitter_stats?.logprob_swaps || 0 },
    { label: "PUNCT BREAKS", val: jitter_stats?.punct_breaks || 0 },
    { label: "EMBARGOS", val: jitter_stats?.embargo_rewrites || 0 },
    { label: "INJECTIONS", val: (jitter_stats?.fragment_rewrites || 0) + (jitter_stats?.temporal_injections || 0) },
  ];

  return (
    <div className="glass-panel" style={{ padding: '3rem', position: 'relative' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.2rem', margin: 0, fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>DECRYPTED PAYLOAD</h2>
          <span style={{ 
            color: 'var(--primary)', 
            fontSize: '0.8rem',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
            background: 'rgba(217, 70, 239, 0.1)',
            padding: '4px 8px',
            borderRadius: '4px',
            border: '1px solid rgba(217, 70, 239, 0.3)'
          }}>
            {mode}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button onClick={handleCopy} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'transparent' }} title="Copy">
            <Copy size={16} /> <span style={{letterSpacing: '0.05em'}}>COPY</span>
          </button>
          <button onClick={onClear} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'transparent' }} title="Clear">
            <RefreshCw size={16} /> <span style={{letterSpacing: '0.05em'}}>CLEAR</span>
          </button>
        </div>
      </div>

      {/* Main Text Box */}
      <div style={{ 
        background: 'rgba(0,0,0,0.4)', 
        padding: '2.5rem', 
        borderRadius: '12px', 
        border: '1px solid rgba(255,255,255,0.05)',
        fontFamily: 'var(--font-ui)',
        fontSize: '1.1rem',
        lineHeight: 1.8,
        color: 'var(--text-main)',
        whiteSpace: 'pre-wrap',
        maxHeight: '400px',
        overflowY: 'auto',
        boxShadow: 'inset 0 10px 20px rgba(0,0,0,0.5)'
      }}>
        {text}
      </div>

      {/* Stylometric Fingerprint Stats */}
      <div style={{ marginTop: '3rem' }}>
        <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: '1.5rem', fontWeight: 600 }}>STYLOMETRIC FINGERPRINT</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem' }}>
          {statCards.map((s, idx) => (
            <motion.div 
              key={idx} 
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1, type: 'spring' }}
              style={{ 
                background: 'rgba(255,255,255,0.03)', 
                padding: '1.5rem', 
                borderRadius: '8px', 
                border: '1px solid rgba(255,255,255,0.1)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 4px 15px rgba(0,0,0,0.2)'
              }}
            >
              <div style={{ 
                fontSize: '1.8rem', 
                fontWeight: 700, 
                fontFamily: 'var(--font-mono)',
                color: 'var(--secondary)',
                textShadow: '0 0 10px rgba(14, 165, 233, 0.5)'
              }}>
                {s.val}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', letterSpacing: '0.05em', textAlign: 'center' }}>
                {s.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
