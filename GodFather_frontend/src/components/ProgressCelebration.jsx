import { useEffect, useState } from 'react';
import './ProgressCelebration.css';

const ProgressCelebration = ({ show, categoryTitle, onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (!show) {
      setProgress(0);
      setIsComplete(false);
      return;
    }

    // Animate progress from 0 to 100
    const duration = 1500; // 1.5 seconds
    const steps = 60;
    const increment = 100 / steps;
    const stepDuration = duration / steps;

    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      const newProgress = Math.min(currentStep * increment, 100);
      setProgress(newProgress);

      if (newProgress >= 100) {
        clearInterval(interval);
        setIsComplete(true);
        
        // Call onComplete after showing completion state
        setTimeout(() => {
          if (onComplete) onComplete();
        }, 2000);
      }
    }, stepDuration);

    return () => clearInterval(interval);
  }, [show, onComplete]);

  if (!show) return null;

  return (
    <div className="progress-celebration-container">
      <div className="progress-celebration-content">
        <div className="progress-celebration-header">
          <div className="celebration-icon">
            {isComplete ? (
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" className="check-circle"/>
                <path d="M8 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="check-mark"/>
              </svg>
            ) : (
              <div className="spinner"></div>
            )}
          </div>
          <h3 className="celebration-title">
            {isComplete ? 'Category Complete!' : 'Completing Category...'}
          </h3>
          {categoryTitle && (
            <p className="celebration-subtitle">{categoryTitle}</p>
          )}
        </div>
        
        <div className="progress-bar-wrapper">
          <div className="progress-bar-background">
            <div 
              className={`progress-bar-fill ${isComplete ? 'complete' : ''}`}
              style={{ width: `${progress}%` }}
            >
              <div className="progress-bar-shine"></div>
            </div>
          </div>
          <div className="progress-percentage">{Math.round(progress)}%</div>
        </div>

        {isComplete && (
          <div className="celebration-particles">
            {[...Array(12)].map((_, i) => {
              const angle = (i * 30) * (Math.PI / 180); // Convert to radians
              const distance = 100;
              const x = Math.cos(angle) * distance;
              const y = Math.sin(angle) * distance;
              return (
                <div
                  key={i}
                  className="celebration-particle"
                  style={{
                    '--x': `${x}px`,
                    '--y': `${y}px`,
                    '--delay': `${i * 0.1}s`,
                  }}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressCelebration;
