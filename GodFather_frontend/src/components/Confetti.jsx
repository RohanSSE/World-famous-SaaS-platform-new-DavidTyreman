import { useEffect, useState } from 'react';
import './Confetti.css';

const Confetti = ({ show, onComplete }) => {
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    if (!show) {
      setParticles([]);
      return;
    }

    // Generate confetti particles
    const newParticles = [];
    const colors = [
      '#3959E5', // Primary blue
      '#C0F9FF', // Cyan
      '#8B5CF6', // Purple
      '#EC6251', // Orange/Red
      '#4FC3F7', // Light blue
      '#86E3FF', // Light cyan
    ];

    for (let i = 0; i < 150; i++) {
      newParticles.push({
        id: i,
        color: colors[Math.floor(Math.random() * colors.length)],
        left: Math.random() * 100,
        animationDelay: Math.random() * 0.5,
        animationDuration: 2 + Math.random() * 2,
        size: 8 + Math.random() * 12,
        rotation: Math.random() * 360,
        xVelocity: (Math.random() - 0.5) * 0.3,
        yVelocity: 0.5 + Math.random() * 0.5,
      });
    }

    setParticles(newParticles);

    // Call onComplete after animation
    const timer = setTimeout(() => {
      if (onComplete) onComplete();
    }, 4000);

    return () => clearTimeout(timer);
  }, [show, onComplete]);

  if (!show) return null;

  return (
    <div className="confetti-container">
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="confetti-particle"
          style={{
            left: `${particle.left}%`,
            backgroundColor: particle.color,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            animationDelay: `${particle.animationDelay}s`,
            animationDuration: `${particle.animationDuration}s`,
            '--rotation': `${particle.rotation}deg`,
            '--x-velocity': String(particle.xVelocity),
            '--y-velocity': String(particle.yVelocity),
          }}
        />
      ))}
    </div>
  );
};

export default Confetti;
