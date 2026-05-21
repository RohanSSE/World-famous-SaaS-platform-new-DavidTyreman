import React, { useState, useEffect } from 'react';
import '../components/PageTransition.css';

const PageTransition = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    // Very short delay - just enough to smooth the transition
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 150); // Reduced from 300ms to 150ms

    return () => clearTimeout(timer);
  }, []);

  return (
    <div className={`page-content ${isLoading ? 'loading' : 'loaded'}`}>
      {children}
    </div>
  );
};

export default PageTransition;
