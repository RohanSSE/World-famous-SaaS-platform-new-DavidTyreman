import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAssistant } from '../context/AuthProvider';
import authService from '../services/authService';
import avatarImg from '../assets/avatar.png';
import OrbPresence from './orb/OrbPresence';
import './AssistantAvatar.css';

const SUGGESTION_POLL_MS = 18 * 1000; // Poll for contextual suggestion every 18s
const SUGGESTION_COOLDOWN_MS = 90 * 1000; // Don't show another suggestion for 90s after one was shown
const SUGGESTION_INITIAL_DELAY_MS = 2500; // Call API 2–3s after landing on page
const IDLE_ACTION_MS = 30 * 1000; // After 30s no activity, set last_action to idle
const FALLBACK_MESSAGE = "Keep going — you're doing great!";
const WELCOME_SHOWN_KEY = 'assistantWelcomeShown';

// Semi-circle help menu options (angles for bottom arc: 180° = left, 270° = bottom, 360° = right)
const HELP_MENU_OPTIONS = [
  { id: 'onboarding', label: 'Onboarding & steps', angle: 210 },
  { id: 'review', label: 'Review journey', angle: 270 },
  { id: 'tips', label: 'Quick tips', angle: 330 },
];

// Routes where assistant should be visible (user-facing routes from user-dashboard onwards)
const allowedRoutes = [
  '/user-dashboard',
  '/foundation-questions',
  '/ChatKickoffPage',
  '/brand-summary',
  '/manifesto',
  '/manifestoFirstPage',
  '/chat-unlock',
];

// Per-screen primary actions so AI and UI can suggest "click on X". Used with assistant-suggestion API and in bubble.
const ROUTE_ACTIONS = {
  '/user-dashboard': {
    actions: ['New Session'],
    buttonLabel: 'New Session',
    actionText: 'start your journey from the left menu.',
  },
  '/foundation-questions': {
    actions: ['Next', 'Submit', 'Create Session'],
    buttonLabel: 'Next',
    actionText: 'continue to the next question.',
  },
  '/phase-questions/1': {
    actions: ['Submit', 'Save', 'Next'],
    buttonLabel: 'Submit',
    actionText: 'answer the manifesto question and submit.',
  },
  '/ChatKickoffPage': {
    actions: ['Save', 'Select a question', 'Send'],
    buttonLabel: 'Save',
    actionText: 'finalize this answer.',
  },
  '/brand-summary': {
    actions: ['Save', 'Download', 'Continue to chat'],
    buttonLabel: 'Continue to chat',
    actionText: 'move to the next brand stage.',
  },
  '/manifesto': {
    actions: ['Download', 'Edit', 'Save'],
    buttonLabel: 'Download',
    actionText: 'save your manifesto.',
  },
  '/manifestoFirstPage': {
    actions: ['Next', 'Start', 'Create'],
    buttonLabel: 'Next',
    actionText: 'build your manifesto.',
  },
  '/chat-unlock': {
    actions: ['Unlock Next Step', 'Upgrade'],
    buttonLabel: 'Unlock Next Step',
    actionText: 'open the chat kickoff stage.',
  },
};

const buildRouteSuggestionMessage = (pathname, includeWelcome = false) => {
  const config = ROUTE_ACTIONS[pathname];
  if (!config?.buttonLabel || !config?.actionText) {
    return includeWelcome ? `Welcome! ${FALLBACK_MESSAGE}` : FALLBACK_MESSAGE;
  }
  const prefix = includeWelcome ? 'Welcome! ' : '';
  return `${prefix}Great going! Click ${config.buttonLabel} to ${config.actionText}`;
};

const AssistantAvatar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { assistantState, closeChat, openChat } = useAssistant();
  const { show, isOpen, step, status, steps } = assistantState;
  const userClosedRef = useRef(false);
  const lastPathRef = useRef(location.pathname);
  const [helpMenuOpen, setHelpMenuOpen] = useState(false);
  // Activity-based suggestion from API (message + optional cta)
  const [dynamicSuggestion, setDynamicSuggestion] = useState(null);
  const [timeOnPageSeconds, setTimeOnPageSeconds] = useState(0);
  const [lastAction, setLastAction] = useState('idle');
  const [showWelcomeOnce, setShowWelcomeOnce] = useState(() => !localStorage.getItem(WELCOME_SHOWN_KEY));
  const lastSuggestionShownAtRef = useRef(0);
  const idleTimerRef = useRef(null);

  // Check if current route should show assistant
  const shouldShow =
    allowedRoutes.includes(location.pathname) ||
    location.pathname.startsWith("/phase-questions");

  // Reset userClosedRef and time when route changes
  useEffect(() => {
    if (lastPathRef.current !== location.pathname) {
      userClosedRef.current = false;
      lastPathRef.current = location.pathname;
      setTimeOnPageSeconds(0);
    }
  }, [location.pathname]);

  // Show route-specific guidance immediately on page entry.
  useEffect(() => {
    if (!shouldShow) return;
    setDynamicSuggestion({
      message: buildRouteSuggestionMessage(location.pathname, false),
      cta: null,
    });
    if (showWelcomeOnce) {
      localStorage.setItem(WELCOME_SHOWN_KEY, '1');
      setShowWelcomeOnce(false);
    }
  }, [location.pathname, shouldShow, showWelcomeOnce]);

  // Increment time on page every second when visible
  useEffect(() => {
    if (!shouldShow) return;
    const t = setInterval(() => {
      setTimeOnPageSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(t);
  }, [shouldShow]);

  // Track last_action: focus -> focused, scroll -> scrolled, then idle after IDLE_ACTION_MS
  useEffect(() => {
    if (!shouldShow) return;
    const resetIdle = () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      idleTimerRef.current = setTimeout(() => setLastAction('idle'), IDLE_ACTION_MS);
    };
    const onFocus = () => {
      setLastAction('focused');
      resetIdle();
    };
    const onScroll = () => {
      setLastAction('scrolled');
      resetIdle();
    };
    window.addEventListener('focus', onFocus);
    window.addEventListener('scroll', onScroll, { passive: true });
    resetIdle();

    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('scroll', onScroll);
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [shouldShow]);

  // Show contextual suggestion (API when session exists, else fallback). Always show something after initial delay.
  useEffect(() => {
    if (!shouldShow) return;

    const sessionId = localStorage.getItem('sessionId');
    const routeActions = ROUTE_ACTIONS[location.pathname];

    const showFallback = () => {
      const now = Date.now();
      if (now - lastSuggestionShownAtRef.current < SUGGESTION_COOLDOWN_MS) return;
      lastSuggestionShownAtRef.current = now;
      setDynamicSuggestion({ message: buildRouteSuggestionMessage(location.pathname), cta: null });
    };

    const fetchSuggestion = async () => {
      const now = Date.now();
      if (now - lastSuggestionShownAtRef.current < SUGGESTION_COOLDOWN_MS) return;

      if (!sessionId) {
        showFallback();
        return;
      }

      try {
        const data = await authService.getAssistantSuggestion(sessionId, {
          route: location.pathname,
          time_on_page_seconds: timeOnPageSeconds,
          current_step_index: null,
          total_steps: null,
          answers_count: null,
          last_action: lastAction,
          available_actions: routeActions?.actions ?? null,
        });
        if (data?.message && typeof data.message === 'string') {
          lastSuggestionShownAtRef.current = now;
          setDynamicSuggestion({ message: data.message, cta: data.cta ?? null });
        } else {
          showFallback();
        }
      } catch {
        showFallback();
      }
    };

    const initialTimer = setTimeout(fetchSuggestion, SUGGESTION_INITIAL_DELAY_MS);
    const timer = sessionId ? setInterval(fetchSuggestion, SUGGESTION_POLL_MS) : null;

    return () => {
      clearTimeout(initialTimer);
      if (timer) clearInterval(timer);
    };
  }, [shouldShow, location.pathname, timeOnPageSeconds, lastAction]);


  const handleReviewJourneyClick = () => {
    setHelpMenuOpen(false);
    navigate('/stepper');
  };

  const handleHelpOptionClick = (id) => {
    if (id === 'onboarding') {
      setHelpMenuOpen(false);
      openChat();
    } else if (id === 'review') {
      handleReviewJourneyClick();
    } else if (id === 'tips') {
      setHelpMenuOpen(false);
      openChat(); // or a dedicated tips view
    }
  };

  if (!show || !shouldShow) return null;

  const currentStep = step < steps.length ? steps[step] : null;
  const nextStep = step + 1 < steps.length ? steps[step + 1] : null;
  const isComplete = step >= steps.length;

  const handleCloseChat = (e) => {
    e.stopPropagation();
    userClosedRef.current = true;
    closeChat();
  };

  const handleCloseSuggestion = (e) => {
    e.stopPropagation();
    setDynamicSuggestion(null);
  };

  const handleAvatarClick = (e) => {
    e.stopPropagation();
    if (helpMenuOpen) return; // let circle items handle clicks
    setHelpMenuOpen(true);
  };

  return (
    <div className="assistant-avatar-root">
      {helpMenuOpen && (
        <div
          className="assistant-help-backdrop"
          onClick={() => setHelpMenuOpen(false)}
          onKeyDown={(e) => e.key === 'Escape' && setHelpMenuOpen(false)}
          role="button"
          tabIndex={-1}
          aria-label="Close help menu"
        />
      )}

      <div className="assistant-avatar-wrapper" onClick={(e) => e.stopPropagation()}>
        {(isOpen || dynamicSuggestion) && (
        <div className="assistant-bubble-container">
          <div className="assistant-bubble">
            <button
              className="bubble-close-btn"
              onClick={dynamicSuggestion ? handleCloseSuggestion : handleCloseChat}
              type="button"
            >
              &times;
            </button>
            {dynamicSuggestion ? (
              <div className="bubble-intro">
                <p>{dynamicSuggestion.message}</p>
                {dynamicSuggestion.cta === 'review_journey' && (
                  <button
                    type="button"
                    className="assistant-bubble-cta"
                    onClick={() => {
                      setDynamicSuggestion(null);
                      setHelpMenuOpen(false);
                      navigate('/stepper');
                    }}
                  >
                    Review journey
                  </button>
                )}
                {dynamicSuggestion.cta === 'quick_tips' && (
                  <button
                    type="button"
                    className="assistant-bubble-cta"
                    onClick={() => {
                      setDynamicSuggestion(null);
                      openChat();
                    }}
                  >
                    Quick tips
                  </button>
                )}
              </div>
            ) : isComplete ? (
              <div className="bubble-complete">
                <div className="complete-icon">✓</div>
                <h4>All steps completed</h4>
              </div>
            ) : (
              <div className="bubble-steps">
                <div className="step-info">
                  <span className="step-label">Current</span>
                  <p className="step-text">{currentStep}</p>
                </div>
                {nextStep && (
                  <div className="step-info next">
                    <span className="step-label">Next</span>
                    <p className="step-text">{nextStep}</p>
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="bubble-pointer"></div>
        </div>
        )}

        <div className="assistant-help-center">
          {helpMenuOpen ? (
            <div className="assistant-semicircle-box">
              {HELP_MENU_OPTIONS.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  className="assistant-circle-option"
                  style={{ '--angle': `${opt.angle}deg` }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleHelpOptionClick(opt.id);
                  }}
                >
                  <span className="assistant-circle-option-inner">{opt.label}</span>
                </button>
              ))}
            </div>
          ) : null}

          <div
            className="assistant-avatar-container"
            onClick={handleAvatarClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleAvatarClick(e);
              }
            }}
            aria-label="Click me for help"
          >
            <OrbPresence className="assistant-orb-wrap">
              <img src={avatarImg} alt="Assistant" className="assistant-avatar-img" />
            </OrbPresence>
            {!helpMenuOpen && (
              <span className="assistant-click-for-help">Click me for help</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssistantAvatar;
