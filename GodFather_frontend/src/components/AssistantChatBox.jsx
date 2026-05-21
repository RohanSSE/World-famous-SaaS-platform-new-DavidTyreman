import React from 'react';
import { useAssistant } from '../context/AuthProvider';
import './AssistantChatBox.css';

const AssistantChatBox = () => {
  const { assistantState, closeChat } = useAssistant();
  const { isOpen, step, status, steps } = assistantState;

  if (!isOpen) return null;

  const currentStep = step < steps.length ? steps[step] : null;
  const nextStep = step + 1 < steps.length ? steps[step + 1] : null;
  const isComplete = step >= steps.length;

  return (
    <div className="assistant-popup-container">
      <button className="assistant-popup-close" onClick={closeChat}>×</button>
      
      <div className="assistant-popup-content">
        {status === 'intro' ? (
          <div className="assistant-intro-section">
            <h3>Welcome to your onboarding!</h3>
            <p>Let me guide you through the process step by step.</p>
          </div>
        ) : isComplete ? (
          <div className="assistant-complete-section">
            <div className="complete-icon">✓</div>
            <h3>All steps completed!</h3>
            <p>You are ready to go. Great job!</p>
          </div>
        ) : (
          <div className="assistant-steps-section">
            <div className="current-step">
              <span className="step-label">Current Step</span>
              <div className="step-number">{step + 1}</div>
              <p className="step-title">{currentStep}</p>
            </div>
            
            {nextStep && (
              <div className="next-step">
                <span className="step-label">Next Step</span>
                <div className="step-number-next">{step + 2}</div>
                <p className="step-title-next">{nextStep}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AssistantChatBox;
