import { useEffect, useState, useRef } from 'react';
import './App.css';

function App() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;

      const scrollTop = window.scrollY;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = docHeight > 0 ? scrollTop / docHeight : 0;

      setScrollProgress(Math.min(scrolled, 1));
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Calculate transforms based on scroll
  const rotateX = scrollProgress * 720; // Full 2x rotations
  const rotateY = scrollProgress * 1080; // 3x rotations on Y
  const rotateZ = scrollProgress * 360; // 1x rotation on Z
  const scale = 1 + scrollProgress * 1.5; // Grows as you scroll
  const skewX = scrollProgress * 15; // Subtle skew
  const perspective = 1200 - scrollProgress * 600; // Gets closer as you scroll

  return (
    <div ref={containerRef} className="scroll-container">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>3D Scroll Experience</h1>
          <p>Scroll down to witness the transformation</p>
        </div>
      </section>

      {/* Main 3D Transform Zone */}
      <section className="transform-zone">
        <div className="stage" style={{ perspective: `${perspective}px` }}>
          <div
            className="core-element"
            style={{
              transform: `
                rotateX(${rotateX}deg)
                rotateY(${rotateY}deg)
                rotateZ(${rotateZ}deg)
                scale(${scale})
                skewX(${skewX}deg)
              `,
            }}
          >
            <div className="element-face front">
              <div className="content">
                <span className="label">FRONT</span>
              </div>
            </div>
            <div className="element-face back">
              <div className="content">
                <span className="label">BACK</span>
              </div>
            </div>
            <div className="element-face top">
              <div className="content">
                <span className="label">TOP</span>
              </div>
            </div>
            <div className="element-face bottom">
              <div className="content">
                <span className="label">BOTTOM</span>
              </div>
            </div>
            <div className="element-face left">
              <div className="content">
                <span className="label">LEFT</span>
              </div>
            </div>
            <div className="element-face right">
              <div className="content">
                <span className="label">RIGHT</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress indicator */}
        <div className="scroll-indicator">
          <div
            className="progress-bar"
            style={{ width: `${scrollProgress * 100}%` }}
          />
        </div>
      </section>

      {/* Secondary Effects Section */}
      <section className="effects-zone">
        <div className="effect-grid">
          {[...Array(12)].map((_, i) => (
            <div
              key={i}
              className="effect-item"
              style={{
                transform: `
                  translateY(${scrollProgress * 50 * (i % 3 - 1)}px)
                  rotateZ(${scrollProgress * 45 * (i % 2 === 0 ? 1 : -1)}deg)
                  scale(${1 + scrollProgress * 0.3 * (i % 3)})
                `,
                opacity: 0.3 + scrollProgress * 0.4,
              }}
            >
              <div className="item-inner" />
            </div>
          ))}
        </div>
      </section>

      {/* Content Section */}
      <section className="content-section">
        <div className="content-wrapper">
          <h2>Mastercraft</h2>
          <p>
            Every frame a deliberate choice. Every transform calculated for impact.
            This is not decoration—this is motion as communication.
          </p>
          <div className="divider" />
          <p>
            The scroll becomes the story. Each rotation reveals new angles.
            Each scale shift emphasizes momentum. Watch the geometry dance.
          </p>
        </div>
      </section>

      {/* Final Section */}
      <section className="final-section">
        <div className="final-content">
          <h3>The End</h3>
          <p style={{ opacity: scrollProgress }}>Scroll complete</p>
        </div>
      </section>
    </div>
  );
}

export default App;
