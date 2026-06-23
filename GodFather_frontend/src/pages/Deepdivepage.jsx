// import React, { useEffect, useRef, useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { toast } from "react-toastify";
// import "../components/Deepdivepage.css";
// import ChatNavbar from "./ChatNavbar";
// import avatar from "../assets/ChatQuestionIcon.png";
// import chatIcon1 from "../assets/chat-icon1.png";
// import chatIcon2 from "../assets/chat-icon2.png";
// import authService from "../services/authService";

// // ─────────────────────────────────────────────────────────────────────────────
// // CONSTANTS
// // ─────────────────────────────────────────────────────────────────────────────
// const DEEP_DIVE_STAGE = 4;

// // ─────────────────────────────────────────────────────────────────────────────
// // MAIN COMPONENT
// // ─────────────────────────────────────────────────────────────────────────────
// export default function DeepDivePage() {
//   const navigate = useNavigate();

//   // ── session ──
//   const savedSessionJson = localStorage.getItem("session");
//   const initialSession = savedSessionJson ? JSON.parse(savedSessionJson) : null;
//   const [session] = useState(initialSession);

//   // ── questions (stage 4) ──
//   const [questions, setQuestions] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [loadError, setLoadError] = useState("");

//   // ── chat state ──
//   const [chatMessages, setChatMessages] = useState([]);
//   const [messages, setMessages] = useState([]); // { qId, question, answer }
//   const [finalizedQuestionIds, setFinalizedQuestionIds] = useState(new Set());
//   const [activeQuestionIdx, setActiveQuestionIdx] = useState(null);
//   const [inputValue, setInputValue] = useState("");
//   const [editingMessageIdx, setEditingMessageIdx] = useState(null);
//   const [isSessionComplete, setIsSessionComplete] = useState(false);

//   // ── AI state ──
//   const [isLoading, setIsLoading] = useState(false);
//   const [isAssistantTyping, setIsAssistantTyping] = useState(false);
//   const [typingText, setTypingText] = useState("");
//   const [isAiDraft, setIsAiDraft] = useState(false);
//   const [refineLoading, setRefineLoading] = useState(false);

//   // ── sidebar ──
//   const [sidebarOpen, setSidebarOpen] = useState(true);

//   // ── intro animation ──
//   const [introVisible, setIntroVisible] = useState(true);

//   // ── refs ──
//   const typewriterIntervalRef = useRef(null);
//   const chatEndRef = useRef(null);

//   const totalQ = questions.length;
//   const answeredCount = finalizedQuestionIds.size;
//   const progressPct =
//     totalQ > 0 ? Math.round((answeredCount / totalQ) * 100) : 0;
//   const hasConversation = chatMessages.length > 0 || messages.length > 0;

//   // ─────────────────────────────────────────────────────────────────────────
//   // LOAD STAGE 4 QUESTIONS
//   // ─────────────────────────────────────────────────────────────────────────
//   useEffect(() => {
//     let cancelled = false;

//     async function loadQuestions() {
//       setLoading(true);
//       setLoadError("");
//       try {
//         const list = await authService.getQuestions();
//         if (cancelled) return;
//         const arr = Array.isArray(list) ? list : [];
//         const filtered = arr
//           .filter(
//             (q) =>
//               q && q.is_active !== false && Number(q.stage) === DEEP_DIVE_STAGE,
//           )
//           .sort((a, b) => {
//             const oa = Number(a.order ?? 0);
//             const ob = Number(b.order ?? 0);
//             if (oa !== ob) return oa - ob;
//             return (a.id ?? 0) - (b.id ?? 0);
//           })
//           .map((q, i) => ({
//             id: q.id ?? i,
//             title: q.text ?? q.title ?? `Question ${i + 1}`,
//             text: q.text ?? q.title ?? "",
//             helpText: q.help_text ?? "",
//             raw: q,
//           }));
//         setQuestions(filtered);
//       } catch (err) {
//         const errorMsg = err?.message || "Failed to load deep dive questions";
//         setLoadError(errorMsg);
//         toast.error(errorMsg);
//       } finally {
//         if (!cancelled) setLoading(false);
//       }
//     }

//     loadQuestions();
//     return () => {
//       cancelled = true;
//     };
//   }, []);

//   // ─────────────────────────────────────────────────────────────────────────
//   // LOAD EXISTING ANSWERS
//   // ─────────────────────────────────────────────────────────────────────────
//   const reloadAllAnswers = async () => {
//     if (!Array.isArray(questions) || questions.length === 0) return null;
//     const sessionId = localStorage.getItem("sessionId");
//     if (!sessionId) return null;

//     try {
//       const remoteAnswers = await authService.getAnswers(sessionId, {});
//       const answerMap = {};

//       if (Array.isArray(remoteAnswers)) {
//         remoteAnswers.forEach((answer) => {
//           const question = questions.find(
//             (q) => q.id === answer.question || q.raw?.id === answer.question,
//           );
//           if (
//             question &&
//             answer.answer_text &&
//             String(answer.answer_text).trim()
//           ) {
//             answerMap[question.id] = {
//               qId: question.id,
//               question: question.text,
//               answer: answer.answer_text,
//             };
//           }
//         });
//       }

//       const loadedMessages = Object.values(answerMap);
//       setMessages(loadedMessages);

//       const finalized = new Set(loadedMessages.map((m) => m.qId));
//       setFinalizedQuestionIds(finalized);

//       const initialChat = [];
//       loadedMessages.forEach((m) => {
//         initialChat.push(
//           { role: "assistant", text: m.question, qId: m.qId },
//           { role: "user", text: m.answer, qId: m.qId },
//         );
//       });
//       setChatMessages(initialChat);

//       if (questions.length > 0 && finalized.size >= questions.length) {
//         setIsSessionComplete(true);
//       }

//       return finalized;
//     } catch (err) {
//       console.warn("Failed to load deep dive answers:", err);
//       return null;
//     }
//   };

//   useEffect(() => {
//     let cancelled = false;
//     async function load() {
//       if (!cancelled) await reloadAllAnswers();
//     }
//     load();
//     return () => {
//       cancelled = true;
//     };
//   }, [questions]);

//   // ─────────────────────────────────────────────────────────────────────────
//   // AUTO-SCROLL
//   // ─────────────────────────────────────────────────────────────────────────
//   useEffect(() => {
//     chatEndRef.current?.scrollIntoView({
//       behavior: "smooth",
//       block: "nearest",
//     });
//   }, [chatMessages, typingText, isLoading, isAssistantTyping]);

//   // ─────────────────────────────────────────────────────────────────────────
//   // CLEANUP
//   // ─────────────────────────────────────────────────────────────────────────
//   useEffect(() => {
//     return () => {
//       if (typewriterIntervalRef.current)
//         clearInterval(typewriterIntervalRef.current);
//     };
//   }, []);

//   // ─────────────────────────────────────────────────────────────────────────
//   // NAVIGATION
//   // ─────────────────────────────────────────────────────────────────────────
//   function selectQuestion(idx) {
//     const q = questions[idx];
//     if (!q) return;

//     const existing = messages.find((m) => m.qId === q.id);
//     if (existing) {
//       setEditingMessageIdx(messages.findIndex((m) => m.qId === q.id));
//       setInputValue(existing.answer);
//     } else {
//       setEditingMessageIdx(null);
//       setInputValue("");
//     }

//     setActiveQuestionIdx(idx);
//     setIntroVisible(false);

//     // Add question bubble if not in chat yet
//     const alreadyInChat = chatMessages.some(
//       (m) => m.qId === q.id && m.role === "assistant",
//     );
//     if (!alreadyInChat) {
//       setChatMessages((prev) => [
//         ...prev,
//         { role: "assistant", text: q.text, qId: q.id, helpText: q.helpText },
//       ]);
//     }
//   }

//   function handleSkip() {
//     if (activeQuestionIdx === null) return;
//     const next = activeQuestionIdx + 1;
//     if (next < questions.length) {
//       const nextQ = questions[next];
//       setActiveQuestionIdx(next);
//       setInputValue("");
//       setEditingMessageIdx(null);
//       setChatMessages((prev) => [
//         ...prev,
//         {
//           role: "assistant",
//           text: nextQ.text,
//           qId: nextQ.id,
//           helpText: nextQ.helpText,
//         },
//       ]);
//       setTimeout(
//         () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
//         100,
//       );
//     }
//   }

//   function handleReturn() {
//     if (activeQuestionIdx === null || activeQuestionIdx === 0) return;
//     const prev = activeQuestionIdx - 1;
//     const prevQ = questions[prev];
//     setActiveQuestionIdx(prev);
//     setInputValue("");
//     setEditingMessageIdx(null);
//     setChatMessages((prev2) => [
//       ...prev2,
//       {
//         role: "assistant",
//         text: prevQ.text,
//         qId: prevQ.id,
//         helpText: prevQ.helpText,
//       },
//     ]);
//     setTimeout(
//       () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
//       100,
//     );
//   }

//   // ─────────────────────────────────────────────────────────────────────────
//   // SEND
//   // ─────────────────────────────────────────────────────────────────────────
//   async function handleSend() {
//     if (
//       isLoading ||
//       isAssistantTyping ||
//       chatMessages.some((m) => m.pending || m.isTyping)
//     ) {
//       toast.info("Please wait for the previous message to finish.");
//       return;
//     }

//     const trimmed = inputValue.trim();
//     if (!trimmed) return;

//     const q = questions[activeQuestionIdx];
//     if (!q) {
//       toast.info("Select a question first.");
//       return;
//     }

//     const sessionId = localStorage.getItem("sessionId") || session?.id;
//     if (!sessionId) {
//       toast.error("Session ID not found");
//       return;
//     }

//     const realQuestionId = q.raw?.id ?? q.id;

//     // ── Edit mode: save directly ──
//     if (editingMessageIdx !== null) {
//       setIsLoading(true);
//       try {
//         await authService.createAnswer(sessionId, {
//           question: Number(realQuestionId),
//           answer_text: trimmed,
//         });
//         setMessages((prev) => {
//           const updated = [...prev];
//           updated[editingMessageIdx] = {
//             ...updated[editingMessageIdx],
//             answer: trimmed,
//           };
//           return updated;
//         });
//         if (!finalizedQuestionIds.has(q.id)) {
//           setFinalizedQuestionIds((prev) => new Set([...prev, q.id]));
//         }
//         setChatMessages((prev) => {
//           const updated = [...prev];
//           let lastUserIdx = -1;
//           for (let i = updated.length - 1; i >= 0; i--) {
//             if (updated[i].qId === q.id && updated[i].role === "user") {
//               lastUserIdx = i;
//               break;
//             }
//           }
//           if (lastUserIdx !== -1)
//             updated[lastUserIdx] = { ...updated[lastUserIdx], text: trimmed };
//           return updated;
//         });
//         toast.success("Answer updated!");
//         setEditingMessageIdx(null);
//         setInputValue("");
//       } catch (err) {
//         toast.error(err?.message || "Failed to update answer");
//       } finally {
//         setIsLoading(false);
//       }
//       return;
//     }

//     // ── New answer flow ──
//     setInputValue("");
//     setIsAiDraft(false);
//     setChatMessages((prev) => [
//       ...prev,
//       { role: "user", text: trimmed, qId: q.id, pending: true },
//     ]);
//     setIsLoading(true);

//     try {
//       const aiResp = await authService.aiSuggestionDraft(
//         sessionId,
//         realQuestionId,
//         trimmed,
//         isAiDraft,
//       );

//       const improved = (aiResp?.improved_answer || trimmed).trim();
//       const followUp = (aiResp?.follow_up_question || "").trim();

//       setMessages((prev) => {
//         const updated = [...prev];
//         const idx = updated.findIndex((m) => m.qId === q.id);
//         if (idx !== -1) {
//           updated[idx] = {
//             ...updated[idx],
//             question: q.text,
//             answer: improved,
//           };
//         } else {
//           updated.push({ qId: q.id, question: q.text, answer: improved });
//         }
//         return updated;
//       });

//       setChatMessages((prev) => {
//         const updated = [...prev];
//         let lastUserIdx = -1;
//         for (let i = updated.length - 1; i >= 0; i--) {
//           if (updated[i].qId === q.id && updated[i].role === "user") {
//             lastUserIdx = i;
//             break;
//           }
//         }
//         if (lastUserIdx !== -1) {
//           updated[lastUserIdx] = { ...updated[lastUserIdx], pending: false };
//         } else {
//           updated.push({ role: "user", text: trimmed, qId: q.id });
//         }
//         return updated;
//       });

//       setIsLoading(false);
//       setEditingMessageIdx(null);
//       setIsAiDraft(false);

//       // Typewriter for follow-up
//       if (followUp) {
//         if (typewriterIntervalRef.current)
//           clearInterval(typewriterIntervalRef.current);
//         setIsAssistantTyping(true);
//         setTypingText("");
//         setChatMessages((prev) => [
//           ...prev,
//           { role: "assistant", text: "", qId: q.id, isTyping: true },
//         ]);

//         let charIdx = 0;
//         typewriterIntervalRef.current = setInterval(() => {
//           if (charIdx < followUp.length) {
//             setTypingText(followUp.slice(0, charIdx + 1));
//             charIdx++;
//           } else {
//             clearInterval(typewriterIntervalRef.current);
//             typewriterIntervalRef.current = null;
//             setIsAssistantTyping(false);
//             setTypingText("");
//             setChatMessages((prev) => {
//               const updated = [...prev];
//               const typingIdx = updated.findIndex((m) => m.isTyping);
//               if (typingIdx !== -1)
//                 updated[typingIdx] = {
//                   role: "assistant",
//                   text: followUp,
//                   qId: q.id,
//                 };
//               return updated;
//             });
//           }
//         }, 20);
//       }
//     } catch (err) {
//       setIsLoading(false);
//       toast.error(err?.message || "Failed to send answer.");
//       // fallback: still record raw text
//       setMessages((prev) => {
//         const updated = [...prev];
//         const idx = updated.findIndex((m) => m.qId === q.id);
//         if (idx !== -1) {
//           updated[idx] = { ...updated[idx], question: q.text, answer: trimmed };
//         } else {
//           updated.push({ qId: q.id, question: q.text, answer: trimmed });
//         }
//         return updated;
//       });
//       setChatMessages((prev) => {
//         const updated = [...prev];
//         let lastUserIdx = -1;
//         for (let i = updated.length - 1; i >= 0; i--) {
//           if (updated[i].qId === q.id && updated[i].role === "user") {
//             lastUserIdx = i;
//             break;
//           }
//         }
//         if (lastUserIdx !== -1)
//           updated[lastUserIdx] = {
//             ...updated[lastUserIdx],
//             text: trimmed,
//             pending: false,
//           };
//         else updated.push({ role: "user", text: trimmed, qId: q.id });
//         return updated;
//       });
//       setEditingMessageIdx(null);
//     }
//   }

//   // ─────────────────────────────────────────────────────────────────────────
//   // SAVE
//   // ─────────────────────────────────────────────────────────────────────────
//   const handleSave = async () => {
//     if (isSessionComplete) return;
//     const sessionId = localStorage.getItem("sessionId") || session?.id;
//     if (!sessionId) {
//       toast.error("Session ID not found");
//       return;
//     }

//     let qIdx = activeQuestionIdx;
//     if (qIdx === null || qIdx < 0) {
//       if (messages.length === 0) {
//         toast.info("No answer to save yet.");
//         return;
//       }
//       const lastMsg = messages[messages.length - 1];
//       qIdx = questions.findIndex((q) => q.id === lastMsg.qId);
//       if (qIdx === -1) {
//         toast.info("No matching question found.");
//         return;
//       }
//     }

//     const q = questions[qIdx];
//     if (!q) {
//       toast.info("No question selected.");
//       return;
//     }

//     const latestForQ = [...messages].reverse().find((m) => m.qId === q.id);
//     if (!latestForQ?.answer?.trim()) {
//       toast.info("Write an answer before saving.");
//       return;
//     }

//     try {
//       await authService.createAnswer(sessionId, {
//         question: Number(q.id),
//         answer_text: latestForQ.answer.trim(),
//       });

//       const finalized = await reloadAllAnswers();
//       if (finalized) {
//         const allDone =
//           questions.length > 0 && finalized.size >= questions.length;
//         if (allDone) {
//           setIsSessionComplete(true);
//           toast.success("Deep Dive complete! 🎉");
//           return;
//         }

//         toast.success("Answer saved!");
//         const nextIdx = questions.findIndex(
//           (question) => !finalized.has(question.id),
//         );
//         if (nextIdx !== -1) {
//           const nextQ = questions[nextIdx];
//           setActiveQuestionIdx(nextIdx);
//           setInputValue("");
//           setChatMessages((prev) => [
//             ...prev,
//             {
//               role: "assistant",
//               text: nextQ.text,
//               qId: nextQ.id,
//               helpText: nextQ.helpText,
//             },
//           ]);
//         }
//       } else {
//         toast.success("Answer saved!");
//       }
//     } catch (err) {
//       toast.error(err?.message || "Failed to save answer.");
//     }
//   };

//   // ─────────────────────────────────────────────────────────────────────────
//   // QUICK REFINE
//   // ─────────────────────────────────────────────────────────────────────────
//   const handleQuickRefine = async () => {
//     const sessionId = localStorage.getItem("sessionId") || session?.id;
//     if (!sessionId) {
//       toast.error("Session ID not found");
//       return;
//     }

//     let qIdx = activeQuestionIdx;
//     if (qIdx === null || qIdx < 0) {
//       if (messages.length === 0) {
//         toast.info("Select a question first.");
//         return;
//       }
//       const lastMsg = messages[messages.length - 1];
//       qIdx = questions.findIndex((q) => q.id === lastMsg.qId);
//       if (qIdx === -1) {
//         toast.info("Select a question first.");
//         return;
//       }
//     }

//     const q = questions[qIdx];
//     if (!q) {
//       toast.info("Select a question first.");
//       return;
//     }

//     const existing = [...messages].reverse().find((m) => m.qId === q.id);
//     const draft = inputValue || existing?.answer || "";
//     if (!draft.trim()) {
//       toast.info("Write something first.");
//       return;
//     }

//     setRefineLoading(true);
//     try {
//       const realQuestionId = q.raw?.id ?? q.id;
//       const resp = await authService.aiSuggestionDraft(
//         sessionId,
//         realQuestionId,
//         draft,
//         true,
//       );
//       const improved = (resp?.improved_answer || draft).trim();
//       setInputValue(improved);
//       setIsAiDraft(true);
//       toast.success("AI refined your text — review and click Send.");
//     } catch (err) {
//       toast.error(err?.message || "AI refinement failed.");
//     } finally {
//       setRefineLoading(false);
//     }
//   };

//   function onKeyDown(e) {
//     if (e.key === "Enter") {
//       e.preventDefault();
//       if (
//         !isLoading &&
//         !isAssistantTyping &&
//         !chatMessages.some((m) => m.pending || m.isTyping)
//       ) {
//         handleSend();
//       }
//     }
//   }

//   // ─────────────────────────────────────────────────────────────────────────
//   // RENDER
//   // ─────────────────────────────────────────────────────────────────────────
//   return (
//     <>
//       <ChatNavbar
//         sessionId={session?.id}
//         onSave={handleSave}
//         showSaveButton={true}
//         showLogoutButton={true}
//         showDownloadButton={false}
//         canGenerate={false}
//       />

//       <div className="ddp-root">
//         {/* ── SIDEBAR ── */}
//         <aside
//           className={`ddp-sidebar ${sidebarOpen ? "ddp-sidebar--open" : "ddp-sidebar--closed"}`}
//         >
//           <div className="ddp-sidebar-header">
//             <div className="ddp-sidebar-badge">
//               <span className="ddp-badge-icon">✦</span>
//               Deep Dive
//             </div>
//             <button
//               className="ddp-sidebar-toggle"
//               onClick={() => setSidebarOpen((v) => !v)}
//               aria-label="Toggle sidebar"
//             >
//               {sidebarOpen ? "◀" : "▶"}
//             </button>
//           </div>

//           <div className="ddp-sidebar-subtitle">Optional · Stage 4</div>

//           {/* Progress */}
//           {totalQ > 0 && (
//             <div className="ddp-progress-wrap">
//               <div className="ddp-progress-bar">
//                 <div
//                   className="ddp-progress-fill"
//                   style={{ width: `${progressPct}%` }}
//                 />
//               </div>
//               <span className="ddp-progress-label">
//                 {answeredCount}/{totalQ} answered
//               </span>
//             </div>
//           )}

//           <div className="ddp-sidebar-divider" />

//           {/* Question list */}
//           <div className="ddp-q-list">
//             {loading ? (
//               <div className="ddp-sidebar-msg">Loading questions…</div>
//             ) : loadError ? (
//               <div className="ddp-sidebar-error">{loadError}</div>
//             ) : questions.length === 0 ? (
//               <div className="ddp-sidebar-msg">
//                 No deep dive questions found.
//               </div>
//             ) : (
//               questions.map((q, idx) => {
//                 const isActive = activeQuestionIdx === idx;
//                 const isAnswered = finalizedQuestionIds.has(q.id);
//                 return (
//                   <button
//                     key={q.id}
//                     className={`ddp-q-item ${isActive ? "ddp-q-item--active" : ""} ${isAnswered ? "ddp-q-item--answered" : ""}`}
//                     onClick={() => selectQuestion(idx)}
//                   >
//                     <span className="ddp-q-num">
//                       {String(idx + 1).padStart(2, "0")}
//                     </span>
//                     <span className="ddp-q-text">{q.title}</span>
//                     {isAnswered && <span className="ddp-q-check">✓</span>}
//                   </button>
//                 );
//               })
//             )}
//           </div>

//           {/* Back link */}
//           <div className="ddp-sidebar-footer">
//             <button className="ddp-back-btn" onClick={() => navigate(-1)}>
//               ← Back to Identity
//             </button>
//           </div>
//         </aside>

//         {/* ── MAIN AREA ── */}
//         <main className="ddp-main">
//           {/* Page header */}
//           <div className="ddp-page-header">
//             <div className="ddp-page-header-inner">
//               <span className="ddp-header-pill">✦ Deep Dive · Stage 4</span>
//               <h1 className="ddp-header-title">Go Beyond the Surface</h1>
//               <p className="ddp-header-sub">
//                 These optional questions sharpen your brand's edge — audience
//                 precision, positioning, and the details that separate memorable
//                 brands from forgettable ones.
//               </p>
//             </div>
//           </div>

//           {/* Chat / Intro area */}
//           <div className="ddp-chat-area">
//             {/* Intro screen */}
//             {introVisible && !hasConversation && !loading && (
//               <div className="ddp-intro">
//                 <div className="ddp-intro-icon">✦</div>
//                 <h2 className="ddp-intro-title">Where do you want to start?</h2>
//                 <p className="ddp-intro-body">
//                   Pick any question from the sidebar, or start with the first
//                   one below.
//                 </p>
//                 {questions.length > 0 && (
//                   <div className="ddp-intro-cards">
//                     {questions.slice(0, 3).map((q, i) => (
//                       <button
//                         key={q.id}
//                         className="ddp-intro-card"
//                         onClick={() => selectQuestion(i)}
//                       >
//                         <span className="ddp-intro-card-num">
//                           {String(i + 1).padStart(2, "0")}
//                         </span>
//                         <p className="ddp-intro-card-text">{q.text}</p>
//                         {q.helpText && (
//                           <p className="ddp-intro-card-hint">{q.helpText}</p>
//                         )}
//                       </button>
//                     ))}
//                   </div>
//                 )}
//               </div>
//             )}

//             {/* Session complete screen */}
//             {isSessionComplete && (
//               <>
//                 <div className="ddp-chat-messages">
//                   {messages.map((msg, i) => (
//                     <React.Fragment key={`${msg.qId}-${i}`}>
//                       <div className="ddp-bubble ddp-bubble--bot">
//                         <div className="ddp-avatar">
//                           <img src={avatar} alt="Bot" />
//                         </div>
//                         <div className="ddp-bubble-content">{msg.question}</div>
//                       </div>
//                       <div className="ddp-bubble ddp-bubble--user">
//                         <div className="ddp-bubble-content">{msg.answer}</div>
//                       </div>
//                     </React.Fragment>
//                   ))}
//                 </div>
//                 <div className="ddp-complete-banner">
//                   <span className="ddp-complete-icon">🎉</span>
//                   <div>
//                     <strong>Deep Dive Complete!</strong>
//                     <p>
//                       You've answered all optional questions. Your brand story
//                       is fully shaped.
//                     </p>
//                   </div>
//                   <button
//                     className="ddp-back-btn ddp-back-btn--cta"
//                     onClick={() => navigate(-1)}
//                   >
//                     ← Back to Identity
//                   </button>
//                 </div>
//               </>
//             )}

//             {/* Active chat view */}
//             {!isSessionComplete && hasConversation && (
//               <div className="ddp-chat-messages">
//                 {chatMessages.map((m, i) => {
//                   const isUser = m.role === "user";
//                   const isLast = i === chatMessages.length - 1;
//                   const isFinalized = m.qId && finalizedQuestionIds.has(m.qId);
//                   let msgIdx = -1;
//                   if (isUser && isFinalized && !m.pending && !m.isTyping) {
//                     msgIdx = messages.findIndex((msg) => msg.qId === m.qId);
//                   }
//                   const canEdit =
//                     isUser &&
//                     isFinalized &&
//                     msgIdx !== -1 &&
//                     !m.pending &&
//                     !m.isTyping;
//                   const showNav =
//                     isLast &&
//                     !m.pending &&
//                     !m.isTyping &&
//                     !isSessionComplete &&
//                     activeQuestionIdx !== null;
//                   const canSkip =
//                     showNav && activeQuestionIdx < questions.length - 1;
//                   const canReturn = showNav && activeQuestionIdx > 0;

//                   return (
//                     <React.Fragment key={i}>
//                       <div
//                         className={`ddp-bubble ${isUser ? "ddp-bubble--user" : "ddp-bubble--bot"}`}
//                       >
//                         {!isUser && (
//                           <div className="ddp-avatar">
//                             {m.isTyping || m.pending ? (
//                               <span className="ddp-star-avatar">✦</span>
//                             ) : (
//                               <img src={avatar} alt="Bot" />
//                             )}
//                           </div>
//                         )}
//                         {canEdit && (
//                           <button
//                             className="ddp-edit-btn"
//                             onClick={() => {
//                               setEditingMessageIdx(msgIdx);
//                               setInputValue(messages[msgIdx].answer);
//                               setIsAiDraft(false);
//                               const qIdx = questions.findIndex(
//                                 (q) => q.id === m.qId,
//                               );
//                               if (qIdx !== -1) setActiveQuestionIdx(qIdx);
//                             }}
//                             title="Edit answer"
//                           >
//                             ✎
//                           </button>
//                         )}
//                         <div className="ddp-bubble-content">
//                           {m.isTyping ? (
//                             <p>
//                               {typingText}
//                               <span className="ddp-cursor">|</span>
//                             </p>
//                           ) : m.pending && !isUser ? (
//                             <div className="ddp-thinking">
//                               <span />
//                               <span />
//                               <span />
//                             </div>
//                           ) : (
//                             m.text
//                               .split(/\n\s*\n/)
//                               .map((para, idx) => <p key={idx}>{para}</p>)
//                           )}
//                         </div>
//                         {/* help text badge on bot messages */}
//                         {!isUser && m.helpText && !m.isTyping && !m.pending && (
//                           <div className="ddp-help-badge">💡 {m.helpText}</div>
//                         )}
//                       </div>

//                       {/* Nav buttons */}
//                       {showNav && (
//                         <div
//                           className={`ddp-nav-buttons ${isUser ? "ddp-nav--user" : "ddp-nav--bot"}`}
//                         >
//                           {canReturn && (
//                             <button
//                               className="ddp-nav-btn ddp-nav-btn--return"
//                               onClick={handleReturn}
//                             >
//                               ← Return
//                             </button>
//                           )}
//                           {canSkip && (
//                             <button
//                               className="ddp-nav-btn ddp-nav-btn--skip"
//                               onClick={handleSkip}
//                             >
//                               Skip →
//                             </button>
//                           )}
//                         </div>
//                       )}
//                     </React.Fragment>
//                   );
//                 })}

//                 {/* Loader bubble */}
//                 {isLoading && !chatMessages.some((m) => m.isTyping) && (
//                   <div className="ddp-bubble ddp-bubble--bot">
//                     <div className="ddp-avatar">
//                       <span className="ddp-star-avatar">✦</span>
//                     </div>
//                     <div className="ddp-bubble-content">
//                       <div className="ddp-thinking">
//                         <span />
//                         <span />
//                         <span />
//                       </div>
//                     </div>
//                   </div>
//                 )}
//                 <div ref={chatEndRef} />
//               </div>
//             )}

//             {/* Ref anchor when intro is visible */}
//             {introVisible && <div ref={chatEndRef} />}
//           </div>

//           {/* ── INPUT BAR ── */}
//           {!isSessionComplete && (
//             <div className="ddp-input-wrap">
//               {activeQuestionIdx !== null &&
//                 questions[activeQuestionIdx]?.helpText && (
//                   <div className="ddp-input-hint">
//                     💡 {questions[activeQuestionIdx].helpText}
//                   </div>
//                 )}
//               <div className="ddp-input-bar">
//                 <input
//                   type="text"
//                   className="ddp-input"
//                   value={inputValue}
//                   onChange={(e) => {
//                     setInputValue(e.target.value);
//                     setIsAiDraft(false);
//                   }}
//                   onKeyDown={onKeyDown}
//                   placeholder={
//                     activeQuestionIdx === null
//                       ? "Select a question from the sidebar to begin…"
//                       : editingMessageIdx !== null
//                         ? "Update your answer…"
//                         : "Type your answer…"
//                   }
//                   disabled={
//                     activeQuestionIdx === null ||
//                     isLoading ||
//                     isAssistantTyping ||
//                     chatMessages.some((m) => m.pending || m.isTyping)
//                   }
//                 />
//                 <div className="ddp-input-actions">
//                   {/* Refine button */}
//                   <button
//                     className={`ddp-refine-btn ${refineLoading ? "ddp-refine-btn--loading" : ""}`}
//                     onClick={handleQuickRefine}
//                     disabled={refineLoading || activeQuestionIdx === null}
//                     title="AI Refine"
//                   >
//                     {refineLoading ? (
//                       <span className="ddp-spinner" />
//                     ) : (
//                       <img
//                         src={chatIcon1}
//                         alt="Refine"
//                         className="ddp-btn-icon"
//                       />
//                     )}
//                     <span className="ddp-refine-tooltip">
//                       Let AI sharpen your answer
//                     </span>
//                   </button>

//                   {/* Send button */}
//                   <button
//                     className="ddp-send-btn"
//                     onClick={handleSend}
//                     disabled={
//                       !inputValue.trim() ||
//                       isLoading ||
//                       isAssistantTyping ||
//                       chatMessages.some((m) => m.pending || m.isTyping) ||
//                       activeQuestionIdx === null
//                     }
//                     title="Send"
//                   >
//                     <img src={chatIcon2} alt="Send" className="ddp-btn-icon" />
//                   </button>
//                 </div>
//               </div>

//               {/* Save bar */}
//               {messages.some(
//                 (m) => !finalizedQuestionIds.has(m.qId) || inputValue.trim(),
//               ) && (
//                 <div className="ddp-save-bar">
//                   <button className="ddp-save-btn" onClick={handleSave}>
//                     Save Answer & Continue
//                   </button>
//                 </div>
//               )}
//             </div>
//           )}
//         </main>
//       </div>
//     </>
//   );
// }

// import React, { useEffect, useRef, useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { toast } from "react-toastify";
// import "../components/Deepdivepage.css";
// import ChatNavbar from "./ChatNavbar";
// import avatar from "../assets/ChatQuestionIcon.png";
// import chatIcon1 from "../assets/chat-icon1.png";
// import chatIcon2 from "../assets/chat-icon2.png";
// import authService from "../services/authService";
// import { IoChevronBack } from "react-icons/io5";

// const DEEP_DIVE_STAGE = 4;

// export default function DeepDivePage() {
//   const navigate = useNavigate();
//   const saved = localStorage.getItem("session");
//   const [session] = useState(saved ? JSON.parse(saved) : null);
//   const [questions, setQuestions] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [loadError, setLoadError] = useState("");
//   const [chatMessages, setChatMessages] = useState([]);
//   const [messages, setMessages] = useState([]);
//   const [finalizedQuestionIds, setFinalizedQuestionIds] = useState(new Set());
//   const [activeQuestionIdx, setActiveQuestionIdx] = useState(null);
//   const [inputValue, setInputValue] = useState("");
//   const [editingMessageIdx, setEditingMessageIdx] = useState(null);
//   const [isSessionComplete, setIsSessionComplete] = useState(false);
//   const [isLoading, setIsLoading] = useState(false);
//   const [isAssistantTyping, setIsAssistantTyping] = useState(false);
//   const [typingText, setTypingText] = useState("");
//   const [isAiDraft, setIsAiDraft] = useState(false);
//   const [refineLoading, setRefineLoading] = useState(false);
//   // const [sidebarOpen,setSidebarOpen]=useState(true);
//   const [introVisible, setIntroVisible] = useState(true);
//   const typewriterRef = useRef(null);
//   const chatEndRef = useRef(null);
//   const totalQ = questions.length;
//   const answeredCount = finalizedQuestionIds.size;
//   const progressPct =
//     totalQ > 0 ? Math.round((answeredCount / totalQ) * 100) : 0;
//   const hasConvo = chatMessages.length > 0 || messages.length > 0;

//   useEffect(() => {
//     let cancelled = false;
//     async function load() {
//       setLoading(true);
//       try {
//         const list = await authService.getQuestions();
//         if (cancelled) return;
//         const arr = Array.isArray(list) ? list : [];
//         const filtered = arr
//           .filter(
//             (q) =>
//               q && q.is_active !== false && Number(q.stage) === DEEP_DIVE_STAGE,
//           )
//           .sort((a, b) => {
//             const d = Number(a.order ?? 0) - Number(b.order ?? 0);
//             return d !== 0 ? d : (a.id ?? 0) - (b.id ?? 0);
//           })
//           .map((q, i) => ({
//             id: q.id ?? i,
//             title: q.text ?? q.title ?? `Q${i + 1}`,
//             text: q.text ?? q.title ?? "",
//             helpText: q.help_text ?? "",
//             raw: q,
//           }));
//         setQuestions(filtered);
//       } catch (err) {
//         const m = err?.message || "Failed";
//         setLoadError(m);
//         toast.error(m);
//       } finally {
//         if (!cancelled) setLoading(false);
//       }
//     }
//     load();
//     return () => {
//       cancelled = true;
//     };
//   }, []);

//   const reloadAllAnswers = async () => {
//     if (!questions.length) return null;
//     const sid = localStorage.getItem("sessionId");
//     if (!sid) return null;
//     try {
//       const remote = await authService.getAnswers(sid, {});
//       const map = {};
//       if (Array.isArray(remote)) {
//         remote.forEach((a) => {
//           const q = questions.find(
//             (q) => q.id === a.question || q.raw?.id === a.question,
//           );
//           if (q && String(a.answer_text || "").trim())
//             map[q.id] = { qId: q.id, question: q.text, answer: a.answer_text };
//         });
//       }
//       const loaded = Object.values(map);
//       setMessages(loaded);
//       const fin = new Set(loaded.map((m) => m.qId));
//       setFinalizedQuestionIds(fin);
//       const chat = [];
//       loaded.forEach((m) => {
//         chat.push(
//           { role: "assistant", text: m.question, qId: m.qId },
//           { role: "user", text: m.answer, qId: m.qId },
//         );
//       });
//       setChatMessages(chat);
//       if (questions.length > 0 && fin.size >= questions.length)
//         setIsSessionComplete(true);
//       return fin;
//     } catch (err) {
//       console.warn(err);
//       return null;
//     }
//   };

//   useEffect(() => {
//     let c = false;
//     async function r() {
//       if (!c) await reloadAllAnswers();
//     }
//     r();
//     return () => {
//       c = true;
//     };
//   }, [questions]);
//   useEffect(() => {
//     chatEndRef.current?.scrollIntoView({
//       behavior: "smooth",
//       block: "nearest",
//     });
//   }, [chatMessages, typingText, isLoading, isAssistantTyping]);
//   useEffect(() => {
//     return () => {
//       if (typewriterRef.current) clearInterval(typewriterRef.current);
//     };
//   }, []);

//   function selectQuestion(idx) {
//     const q = questions[idx];
//     if (!q) return;
//     const ex = messages.find((m) => m.qId === q.id);
//     if (ex) {
//       setEditingMessageIdx(messages.findIndex((m) => m.qId === q.id));
//       setInputValue(ex.answer);
//     } else {
//       setEditingMessageIdx(null);
//       setInputValue("");
//     }
//     setActiveQuestionIdx(idx);
//     setIntroVisible(false);
//     if (!chatMessages.some((m) => m.qId === q.id && m.role === "assistant"))
//       setChatMessages((prev) => [
//         ...prev,
//         { role: "assistant", text: q.text, qId: q.id, helpText: q.helpText },
//       ]);
//   }

//   function handleSkip() {
//     if (activeQuestionIdx === null) return;
//     const n = activeQuestionIdx + 1;
//     if (n < questions.length) {
//       const nq = questions[n];
//       setActiveQuestionIdx(n);
//       setInputValue("");
//       setEditingMessageIdx(null);
//       setChatMessages((prev) => [
//         ...prev,
//         { role: "assistant", text: nq.text, qId: nq.id, helpText: nq.helpText },
//       ]);
//       setTimeout(
//         () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
//         80,
//       );
//     }
//   }
//   function handleReturn() {
//     if (!activeQuestionIdx) return;
//     const p = activeQuestionIdx - 1;
//     const pq = questions[p];
//     setActiveQuestionIdx(p);
//     setInputValue("");
//     setEditingMessageIdx(null);
//     setChatMessages((prev) => [
//       ...prev,
//       { role: "assistant", text: pq.text, qId: pq.id, helpText: pq.helpText },
//     ]);
//     setTimeout(
//       () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
//       80,
//     );
//   }

//   async function handleSend() {
//     const isBusy =
//       isLoading ||
//       isAssistantTyping ||
//       chatMessages.some((m) => m.pending || m.isTyping);
//     if (isBusy) {
//       toast.info("Please wait...");
//       return;
//     }
//     const trimmed = inputValue.trim();
//     if (!trimmed) return;
//     const q = questions[activeQuestionIdx];
//     if (!q) {
//       toast.info("Select a question first.");
//       return;
//     }
//     const sid = localStorage.getItem("sessionId") || session?.id;
//     if (!sid) {
//       toast.error("Session ID not found");
//       return;
//     }
//     const rid = q.raw?.id ?? q.id;
//     if (editingMessageIdx !== null) {
//       setIsLoading(true);
//       try {
//         await authService.createAnswer(sid, {
//           question: Number(rid),
//           answer_text: trimmed,
//         });
//         setMessages((prev) => {
//           const u = [...prev];
//           u[editingMessageIdx] = { ...u[editingMessageIdx], answer: trimmed };
//           return u;
//         });
//         if (!finalizedQuestionIds.has(q.id))
//           setFinalizedQuestionIds((p) => new Set([...p, q.id]));
//         setChatMessages((prev) => {
//           const u = [...prev];
//           let li = -1;
//           for (let i = u.length - 1; i >= 0; i--) {
//             if (u[i].qId === q.id && u[i].role === "user") {
//               li = i;
//               break;
//             }
//           }
//           if (li !== -1) u[li] = { ...u[li], text: trimmed };
//           return u;
//         });
//         toast.success("Answer updated!");
//         setEditingMessageIdx(null);
//         setInputValue("");
//       } catch (err) {
//         toast.error(err?.message || "Failed");
//       } finally {
//         setIsLoading(false);
//       }
//       return;
//     }
//     setInputValue("");
//     setIsAiDraft(false);
//     setChatMessages((prev) => [
//       ...prev,
//       { role: "user", text: trimmed, qId: q.id, pending: true },
//     ]);
//     setIsLoading(true);
//     try {
//       const ai = await authService.aiSuggestionDraft(
//         sid,
//         rid,
//         trimmed,
//         isAiDraft,
//       );
//       const imp = (ai?.improved_answer || trimmed).trim();
//       const fu = (ai?.follow_up_question || "").trim();
//       setMessages((prev) => {
//         const u = [...prev];
//         const i = u.findIndex((m) => m.qId === q.id);
//         if (i !== -1) u[i] = { ...u[i], question: q.text, answer: imp };
//         else u.push({ qId: q.id, question: q.text, answer: imp });
//         return u;
//       });
//       setChatMessages((prev) => {
//         const u = [...prev];
//         let li = -1;
//         for (let i = u.length - 1; i >= 0; i--) {
//           if (u[i].qId === q.id && u[i].role === "user") {
//             li = i;
//             break;
//           }
//         }
//         if (li !== -1) u[li] = { ...u[li], pending: false };
//         else u.push({ role: "user", text: trimmed, qId: q.id });
//         return u;
//       });
//       setIsLoading(false);
//       setEditingMessageIdx(null);
//       setIsAiDraft(false);
//       if (fu) {
//         if (typewriterRef.current) clearInterval(typewriterRef.current);
//         setIsAssistantTyping(true);
//         setTypingText("");
//         setChatMessages((prev) => [
//           ...prev,
//           { role: "assistant", text: "", qId: q.id, isTyping: true },
//         ]);
//         let ci = 0;
//         typewriterRef.current = setInterval(() => {
//           if (ci < fu.length) {
//             setTypingText(fu.slice(0, ci + 1));
//             ci++;
//           } else {
//             clearInterval(typewriterRef.current);
//             typewriterRef.current = null;
//             setIsAssistantTyping(false);
//             setTypingText("");
//             setChatMessages((prev) => {
//               const u = [...prev];
//               const ti = u.findIndex((m) => m.isTyping);
//               if (ti !== -1) u[ti] = { role: "assistant", text: fu, qId: q.id };
//               return u;
//             });
//           }
//         }, 20);
//       }
//     } catch (err) {
//       setIsLoading(false);
//       toast.error(err?.message || "Failed to send.");
//       setMessages((prev) => {
//         const u = [...prev];
//         const i = u.findIndex((m) => m.qId === q.id);
//         if (i !== -1) u[i] = { ...u[i], question: q.text, answer: trimmed };
//         else u.push({ qId: q.id, question: q.text, answer: trimmed });
//         return u;
//       });
//       setChatMessages((prev) => {
//         const u = [...prev];
//         let li = -1;
//         for (let i = u.length - 1; i >= 0; i--) {
//           if (u[i].qId === q.id && u[i].role === "user") {
//             li = i;
//             break;
//           }
//         }
//         if (li !== -1) u[li] = { ...u[li], text: trimmed, pending: false };
//         else u.push({ role: "user", text: trimmed, qId: q.id });
//         return u;
//       });
//       setEditingMessageIdx(null);
//     }
//   }

//   const handleSave = async () => {
//     if (isSessionComplete) return;
//     const sid = localStorage.getItem("sessionId") || session?.id;
//     if (!sid) {
//       toast.error("Session ID not found");
//       return;
//     }
//     let qi = activeQuestionIdx;
//     if (qi === null || qi < 0) {
//       if (!messages.length) {
//         toast.info("No answer to save yet.");
//         return;
//       }
//       qi = questions.findIndex(
//         (q) => q.id === messages[messages.length - 1].qId,
//       );
//       if (qi === -1) {
//         toast.info("No matching question.");
//         return;
//       }
//     }
//     const q = questions[qi];
//     if (!q) {
//       toast.info("No question selected.");
//       return;
//     }
//     const lat = [...messages].reverse().find((m) => m.qId === q.id);
//     if (!lat?.answer?.trim()) {
//       toast.info("Write an answer first.");
//       return;
//     }
//     try {
//       await authService.createAnswer(sid, {
//         question: Number(q.id),
//         answer_text: lat.answer.trim(),
//       });
//       const fin = await reloadAllAnswers();
//       if (fin) {
//         if (questions.length > 0 && fin.size >= questions.length) {
//           setIsSessionComplete(true);
//           toast.success("Deep Dive complete! 🎉");
//           return;
//         }
//         toast.success("Answer saved!");
//         const ni = questions.findIndex((question) => !fin.has(question.id));
//         if (ni !== -1) {
//           const nq = questions[ni];
//           setActiveQuestionIdx(ni);
//           setInputValue("");
//           setChatMessages((prev) => [
//             ...prev,
//             {
//               role: "assistant",
//               text: nq.text,
//               qId: nq.id,
//               helpText: nq.helpText,
//             },
//           ]);
//         }
//       } else toast.success("Answer saved!");
//     } catch (err) {
//       toast.error(err?.message || "Failed to save.");
//     }
//   };

//   const handleQuickRefine = async () => {
//     const sid = localStorage.getItem("sessionId") || session?.id;
//     if (!sid) {
//       toast.error("Session ID not found");
//       return;
//     }
//     let qi = activeQuestionIdx;
//     if (qi === null || qi < 0) {
//       if (!messages.length) {
//         toast.info("Select a question first.");
//         return;
//       }
//       qi = questions.findIndex(
//         (q) => q.id === messages[messages.length - 1].qId,
//       );
//       if (qi === -1) {
//         toast.info("Select a question first.");
//         return;
//       }
//     }
//     const q = questions[qi];
//     if (!q) {
//       toast.info("Select a question first.");
//       return;
//     }
//     const ex = [...messages].reverse().find((m) => m.qId === q.id);
//     const draft = inputValue || ex?.answer || "";
//     if (!draft.trim()) {
//       toast.info("Write something first.");
//       return;
//     }
//     setRefineLoading(true);
//     try {
//       const r = await authService.aiSuggestionDraft(
//         sid,
//         q.raw?.id ?? q.id,
//         draft,
//         true,
//       );
//       setInputValue((r?.improved_answer || draft).trim());
//       setIsAiDraft(true);
//       toast.success("AI refined — review and click Send.");
//     } catch (err) {
//       toast.error(err?.message || "Refinement failed.");
//     } finally {
//       setRefineLoading(false);
//     }
//   };

//   function onKeyDown(e) {
//     if (e.key === "Enter") {
//       e.preventDefault();
//       const b =
//         isLoading ||
//         isAssistantTyping ||
//         chatMessages.some((m) => m.pending || m.isTyping);
//       if (!b) handleSend();
//     }
//   }
//   const isBusy =
//     isLoading ||
//     isAssistantTyping ||
//     chatMessages.some((m) => m.pending || m.isTyping);

//   return (
//     <>
//       <ChatNavbar
//         sessionId={session?.id}
//         onSave={handleSave}
//         showSaveButton={true}
//         showLogoutButton={true}
//         showDownloadButton={false}
//         canGenerate={false}
//       />
//       <div className="ddp-root">
//         {/* <aside className={`ddp-sidebar ${sidebarOpen?"ddp-sidebar--open":"ddp-sidebar--closed"}`}> */}
//         <aside className="ddp-sidebar">
//           <div className="ddp-sidebar-header">
//             <h2 className="ddp-sidebar-title">Deep Dive</h2>
//             {/* <button onClick={()=>setSidebarOpen(v=>!v)} aria-label="Toggle sidebar" style={{background:"none",border:"1px solid rgba(255,255,255,0.1)",color:"rgba(255,255,255,0.35)",borderRadius:6,width:24,height:24,cursor:"pointer",fontSize:10,display:"flex",alignItems:"center",justifyContent:"center",transition:"all 0.2s",flexShrink:0}}>{sidebarOpen?"◀":"▶"}</button> */}
//           </div>
//           {/* <div className="ddp-stage-pill">✦ Optional · Stage 4</div> */}
//           <div className="ddp-sidebar-divider" />
//           {totalQ > 0 && (
//             <div className="ddp-progress-wrap">
//               <div className="ddp-progress-track">
//                 <div
//                   className="ddp-progress-fill"
//                   style={{ width: `${progressPct}%` }}
//                 />
//               </div>
//               <span className="ddp-progress-label">
//                 {answeredCount} / {totalQ} answered
//               </span>
//             </div>
//           )}
//           <div className="ddp-q-list">
//             {loading ? (
//               <div className="ddp-sidebar-msg">Loading questions…</div>
//             ) : loadError ? (
//               <div className="ddp-sidebar-error">{loadError}</div>
//             ) : questions.length === 0 ? (
//               <div className="ddp-sidebar-msg">
//                 No deep dive questions found.
//               </div>
//             ) : (
//               questions.map((q, idx) => (
//                 <button
//                   key={q.id}
//                   className={`ddp-q-item${activeQuestionIdx === idx ? " ddp-q-item--active" : ""}${finalizedQuestionIds.has(q.id) ? " ddp-q-item--answered" : ""}`}
//                   onClick={() => selectQuestion(idx)}
//                 >
//                   <span className="ddp-q-num">
//                     {String(idx + 1).padStart(2, "0")}
//                   </span>
//                   <span className="ddp-q-text">{q.title}</span>
//                   {finalizedQuestionIds.has(q.id) && (
//                     <span className="ddp-q-check">✓</span>
//                   )}
//                 </button>
//               ))
//             )}
//           </div>
//           <div className="ddp-sidebar-footer">
//             <button
//               className="ddp-back-btn"
//               onClick={() => navigate("/ChatKickoffPage")}
//             >
//               <IoChevronBack className="ddp-back-icon" />
//               Back to Identity
//             </button>
//           </div>
//         </aside>

//         <main className="ddp-main">
//           {/* <div className="ddp-page-header">
//             <p className="ddp-header-eyebrow">✦ Deep Dive · Stage 4 · Optional</p>
//             <h1 className="ddp-header-title">Go Beyond the Surface</h1>
//             <p className="ddp-header-sub">10 optional questions that sharpen your brand's edge — audience precision, positioning, and the details that separate memorable brands from forgettable ones.</p>
//           </div> */}
//           {/* {!loading&&totalQ>0&&(
//             <div className="ddp-main-progress">
//               <div className="ddp-main-progress-header"><span className="ddp-main-progress-label">Deep Dive Progress</span><span className="ddp-main-progress-meta">{answeredCount} / {totalQ} answered · {progressPct}% done</span></div>
//               <div className="ddp-main-progress-track"><div className="ddp-main-progress-fill" style={{width:`${progressPct}%`}}/></div>
//             </div>
//           )} */}
//           <div className="ddp-chat-area">
//             {introVisible && !hasConvo && !loading && (
//               <div className="ddp-intro">
//                 <h2 className="ddp-intro-title">
//                   "Let's go deeper — this is where brands get unforgettable."
//                 </h2>
//                 <p className="ddp-intro-body">
//                   Pick any question from the sidebar, or start with one of
//                   these.
//                 </p>

//                 {questions.length > 0 && (
//                   <div className="ddp-intro-cards">
//                     {questions.slice(0, 4).map((q, i) => (
//                       <button
//                         key={q.id}
//                         className="ddp-intro-card"
//                         onClick={() => selectQuestion(i)}
//                       >
//                         <span className="ddp-intro-card-num">
//                           {String(i + 1).padStart(2, "0")}
//                         </span>
//                         <p className="ddp-intro-card-text">{q.text}</p>
//                         {q.helpText && (
//                           <p className="ddp-intro-card-hint">{q.helpText}</p>
//                         )}
//                       </button>
//                     ))}
//                   </div>
//                 )}
//               </div>
//             )}
//             {isSessionComplete && (
//               <>
//                 <div className="ddp-chat-messages">
//                   {messages.map((msg, i) => (
//                     <React.Fragment key={`${msg.qId}-${i}`}>
//                       <div className="ddp-bubble ddp-bubble--bot">
//                         <div className="ddp-avatar">
//                           <img src={avatar} alt="Bot" />
//                         </div>
//                         <div className="ddp-bubble-content">{msg.question}</div>
//                       </div>
//                       <div className="ddp-bubble ddp-bubble--user">
//                         <div className="ddp-bubble-content">{msg.answer}</div>
//                       </div>
//                     </React.Fragment>
//                   ))}
//                 </div>
//                 <div className="ddp-complete-banner">
//                   <span className="ddp-complete-icon">🎉</span>
//                   <div>
//                     <strong>Deep Dive Complete!</strong>
//                     <p>
//                       You've answered all optional questions. Your brand story
//                       is fully shaped.
//                     </p>
//                   </div>
//                   <button
//                     className="ddp-back-btn ddp-back-btn--cta"
//                     onClick={() => navigate("/ChatKickoffPage")}
//                   >
//                     <IoChevronBack className="ddp-back-icon" />
//                     Back to Identity
//                   </button>
//                 </div>
//               </>
//             )}
//             {!isSessionComplete && hasConvo && (
//               <div className="ddp-chat-messages">
//                 {chatMessages.map((m, i) => {
//                   const isUser = m.role === "user";
//                   const isLast = i === chatMessages.length - 1;
//                   const isFin = m.qId && finalizedQuestionIds.has(m.qId);
//                   let mi = -1;
//                   if (isUser && isFin && !m.pending && !m.isTyping)
//                     mi = messages.findIndex((msg) => msg.qId === m.qId);
//                   const canEdit =
//                     isUser && isFin && mi !== -1 && !m.pending && !m.isTyping;
//                   const showNav =
//                     isLast &&
//                     !m.pending &&
//                     !m.isTyping &&
//                     !isSessionComplete &&
//                     activeQuestionIdx !== null;
//                   const canSkip =
//                     showNav && activeQuestionIdx < questions.length - 1;
//                   const canReturn = showNav && activeQuestionIdx > 0;
//                   return (
//                     <React.Fragment key={i}>
//                       <div
//                         className={`ddp-bubble ${isUser ? "ddp-bubble--user" : "ddp-bubble--bot"}`}
//                       >
//                         {!isUser && (
//                           <div className="ddp-avatar">
//                             {m.isTyping || m.pending ? (
//                               <span className="ddp-star-avatar">⭐</span>
//                             ) : (
//                               <img src={avatar} alt="Bot" />
//                             )}
//                           </div>
//                         )}
//                         {canEdit && (
//                           <button
//                             className="ddp-edit-btn"
//                             onClick={() => {
//                               setEditingMessageIdx(mi);
//                               setInputValue(messages[mi].answer);
//                               setIsAiDraft(false);
//                               const qi = questions.findIndex(
//                                 (q) => q.id === m.qId,
//                               );
//                               if (qi !== -1) setActiveQuestionIdx(qi);
//                             }}
//                             title="Edit answer"
//                           >
//                             ✎
//                           </button>
//                         )}
//                         <div className="ddp-bubble-content">
//                           {m.isTyping ? (
//                             <p>
//                               {typingText}
//                               <span className="ddp-cursor">|</span>
//                             </p>
//                           ) : m.pending && !isUser ? (
//                             <div className="ddp-thinking">
//                               <span />
//                               <span />
//                               <span />
//                             </div>
//                           ) : (
//                             m.text
//                               .split(/\n\s*\n/)
//                               .map((para, pi) => <p key={pi}>{para}</p>)
//                           )}
//                         </div>
//                         {!isUser && m.helpText && !m.isTyping && !m.pending && (
//                           <div className="ddp-help-badge">💡 {m.helpText}</div>
//                         )}
//                       </div>
//                       {showNav && (
//                         <div
//                           className={`ddp-nav-buttons ${isUser ? "ddp-nav--user" : ""}`}
//                         >
//                           {canReturn && (
//                             <button
//                               className="ddp-nav-btn ddp-nav-btn--return"
//                               onClick={handleReturn}
//                             >
//                               ← Return
//                             </button>
//                           )}
//                           {canSkip && (
//                             <button
//                               className="ddp-nav-btn ddp-nav-btn--skip"
//                               onClick={handleSkip}
//                             >
//                               Skip →
//                             </button>
//                           )}
//                         </div>
//                       )}
//                     </React.Fragment>
//                   );
//                 })}
//                 {isLoading && !chatMessages.some((m) => m.isTyping) && (
//                   <div className="ddp-bubble ddp-bubble--bot">
//                     <div className="ddp-avatar">
//                       <span className="ddp-star-avatar">⭐</span>
//                     </div>
//                     <div className="ddp-bubble-content">
//                       <div className="ddp-thinking">
//                         <span />
//                         <span />
//                         <span />
//                       </div>
//                     </div>
//                   </div>
//                 )}
//                 <div ref={chatEndRef} />
//               </div>
//             )}
//             {introVisible && <div ref={chatEndRef} />}
//           </div>
//           {!isSessionComplete && (
//             <div className="ddp-input-wrap">
//               {activeQuestionIdx !== null &&
//                 questions[activeQuestionIdx]?.helpText && (
//                   <div className="ddp-input-hint">
//                     💡 {questions[activeQuestionIdx].helpText}
//                   </div>
//                 )}
//               <div className="ddp-input-bar">
//                 <input
//                   type="text"
//                   className="ddp-input"
//                   value={inputValue}
//                   onChange={(e) => {
//                     setInputValue(e.target.value);
//                     setIsAiDraft(false);
//                   }}
//                   onKeyDown={onKeyDown}
//                   placeholder={
//                     activeQuestionIdx === null
//                       ? "Select a question from the sidebar to begin…"
//                       : editingMessageIdx !== null
//                         ? "Update your answer…"
//                         : "Type your answer…"
//                   }
//                   disabled={activeQuestionIdx === null || isBusy}
//                 />
//                 <div className="ddp-input-actions">
//                   <button
//                     className={`ddp-refine-btn${refineLoading ? " ddp-refine-btn--loading" : ""}`}
//                     onClick={handleQuickRefine}
//                     disabled={refineLoading || activeQuestionIdx === null}
//                     title="AI Refine"
//                   >
//                     {refineLoading ? (
//                       <span className="ddp-spinner" />
//                     ) : (
//                       <img
//                         src={chatIcon1}
//                         alt="Refine"
//                         className="ddp-btn-icon"
//                       />
//                     )}
//                     <span className="ddp-refine-tooltip">
//                       Sharpen it the World-Famous way
//                     </span>
//                   </button>
//                   <button
//                     className="ddp-send-btn"
//                     onClick={handleSend}
//                     disabled={
//                       !inputValue.trim() || isBusy || activeQuestionIdx === null
//                     }
//                     title="Send"
//                   >
//                     <img src={chatIcon2} alt="Send" className="ddp-btn-icon" />
//                   </button>
//                 </div>
//               </div>
//               {messages.some(
//                 (m) => m.qId === questions[activeQuestionIdx]?.id,
//               ) && (
//                 <div className="ddp-save-bar">
//                   <button className="ddp-save-btn" onClick={handleSave}>
//                     Save Answer & Continue
//                   </button>
//                 </div>
//               )}
//             </div>
//           )}
//         </main>
//       </div>
//     </>
//   );
// }
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import "../components/Deepdivepage.css";
import ChatNavbar from "./ChatNavbar";
import avatar from "../assets/ChatQuestionIcon.png";
import chatIcon1 from "../assets/chat-icon1.png";
import chatIcon2 from "../assets/chat-icon2.png";
import authService from "../services/authService";
import ThinkingPipeline from "../components/rag/ThinkingPipeline";
import SourceCards from "../components/rag/SourceCards";
import TypewriterText from "../components/rag/TypewriterText";
import useThinkingPipeline from "../hooks/useThinkingPipeline";
import { useOrbPresence } from "../context/OrbPresenceContext";
import { IoChevronBack } from "react-icons/io5";

const DEEP_DIVE_STAGE = 4;

const AI_THINKING_STEPS = [
  "Thinking…",
  "Analyzing your brand identity…",
  "Retrieving positioning knowledge…",
  "Generating strategic response…",
];

function resolveOrbQuestionId(question, questionIndex) {
  const rawId = question?.raw?.q_id || question?.raw?.brandgodfather_q_id;
  if (rawId) return String(rawId).toUpperCase().startsWith("Q") ? String(rawId).toUpperCase() : `Q${rawId}`;

  const order = Number(question?.raw?.order ?? question?.order);
  if (Number.isFinite(order) && order > 0) return `Q${order}`;

  return `Q${Number(questionIndex ?? 0) + 1}`;
}

function formatOrbCoachReply(orbResult) {
  const status = String(orbResult?.status || "UNKNOWN").toUpperCase();
  const nextQuestion = orbResult?.next_q_id || "Awaiting stronger answer";
  const depthScore = orbResult?.depth_score ?? "not scored";
  const reply = String(orbResult?.reply || "Let's go deeper before we move on.").trim();
  const blockedPhrases = Array.isArray(orbResult?.blocked_phrases)
    ? orbResult.blocked_phrases.filter(Boolean).join(", ")
    : "";
  const contradiction = orbResult?.contradiction_result || null;

  const lines = [
    `status: ${status}`,
    `challenge_type: ${orbResult?.challenge_type || "none"}`,
    `pressure_used: ${orbResult?.pressure_used ?? "n/a"}`,
    `resistance_count: ${orbResult?.resistance_count ?? 0}`,
    `emotional_state: ${orbResult?.emotional_state || "neutral"}`,
    `tone_mode: ${orbResult?.tone_mode || "direct_challenge"}`,
    `next_q_id: ${nextQuestion}`,
    `depth_score: ${depthScore}`,
  ];
  if (orbResult?.interruption_type === "vendor_language") {
    lines.push("interruption_type: vendor_language");
    if (blockedPhrases) lines.push(`blocked_phrases: ${blockedPhrases}`);
  }
  if (orbResult?.interruption_type === "contradiction") {
    lines.push("interruption_type: contradiction");
    if (contradiction?.conflicting_q_id) lines.push(`conflicts_with: ${contradiction.conflicting_q_id}`);
    if (orbResult?.contradiction_message) lines.push(`contradiction: ${orbResult.contradiction_message}`);
  }
  if (orbResult?.interruption_type === "adaptive_coaching") {
    lines.push("interruption_type: adaptive_coaching");
  }
  if (orbResult?.breakthrough_detected) {
    lines.push("breakthrough_detected: true");
    lines.push(`breakthrough_score: ${orbResult?.breakthrough_score ?? "n/a"}`);
    if (orbResult?.breakthrough_type) lines.push(`breakthrough_type: ${orbResult.breakthrough_type}`);
    if (orbResult?.breakthrough_seed) lines.push(`breakthrough_seed: ${orbResult.breakthrough_seed}`);
    if (orbResult?.breakthrough_reason) lines.push(`breakthrough_reason: ${orbResult.breakthrough_reason}`);
  }
  return [
    ...lines,
    `reply: ${reply}`,
    "",
  ].join("\n");
}

export default function DeepDivePage() {
  const navigate = useNavigate();
  const saved = localStorage.getItem("session");
  const [session] = useState(saved ? JSON.parse(saved) : null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [messages, setMessages] = useState([]);
  const [finalizedQuestionIds, setFinalizedQuestionIds] = useState(new Set());
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [editingMessageIdx, setEditingMessageIdx] = useState(null);
  const [isSessionComplete, setIsSessionComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [typingText, setTypingText] = useState("");
  const [isAiDraft, setIsAiDraft] = useState(false);
  const [refineLoading, setRefineLoading] = useState(false);
  const [introVisible, setIntroVisible] = useState(true);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [suggestionMeta, setSuggestionMeta] = useState(null);
  const [suggestionError, setSuggestionError] = useState(null);
  const [hoveredSuggestionIdx, setHoveredSuggestionIdx] = useState(null);
  const typewriterRef = useRef(null);
  const chatEndRef = useRef(null);
  const suggestionsDebounceRef = useRef(null);
  const suggestionSelectedRef = useRef(false);
  const hoverTimeoutRef = useRef(null);

  const {
    setOrbIdle,
    setOrbThinking,
    setOrbRetrieving,
    setOrbSpeaking,
    setOrbMemory,
    setSources: setOrbSources,
    setGraphConcepts: setOrbGraphConcepts,
  } = useOrbPresence();

  const [ragSources, setRagSources] = useState([]);
  const [graphConcepts, setGraphConcepts] = useState([]);
  const thinkingMessage = useThinkingPipeline(isLoading, AI_THINKING_STEPS, 1500);

  const totalQ = questions.length;
  const answeredCount = finalizedQuestionIds.size;
  const progressPct =
    totalQ > 0 ? Math.round((answeredCount / totalQ) * 100) : 0;
  // FIX: hasConvo now also checks introVisible so intro shows on first load
  const hasConvo = chatMessages.length > 0 || messages.length > 0;
  const isBusy =
    isLoading ||
    isAssistantTyping ||
    chatMessages.some((m) => m.pending || m.isTyping);

  // ────────────────────────────────────────────────
  //  Loading questions + answers
  // ────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const list = await authService.getQuestions();
        if (cancelled) return;
        const filtered = list
          .filter(
            (q) =>
              q?.is_active !== false && Number(q.stage) === DEEP_DIVE_STAGE,
          )
          .sort(
            (a, b) =>
              Number(a.order ?? 0) - Number(b.order ?? 0) || a.id - b.id,
          )
          .map((q, i) => ({
            id: q.id ?? i,
            title: q.text ?? q.title ?? `Q${i + 1}`,
            text: q.text ?? q.title ?? "",
            helpText: q.help_text ?? "",
            raw: q,
          }));
        setQuestions(filtered);
      } catch (err) {
        const m = err?.message || "Failed to load questions";
        setLoadError(m);
        toast.error(m);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const reloadAllAnswers = async () => {
    if (!questions.length) return null;
    const sid = localStorage.getItem("sessionId") || session?.id;
    if (!sid) return null;
    try {
      const remote = await authService.getAnswers(sid, {});
      const map = {};
      if (Array.isArray(remote)) {
        remote.forEach((a) => {
          const q = questions.find(
            (q) => q.id === a.question || q.raw?.id === a.question,
          );
          if (q && String(a.answer_text || "").trim()) {
            map[q.id] = { qId: q.id, question: q.text, answer: a.answer_text };
          }
        });
      }
      const loaded = Object.values(map);
      setMessages(loaded);
      const fin = new Set(loaded.map((m) => m.qId));
      setFinalizedQuestionIds(fin);

      const chat = [];
      loaded.forEach((m) => {
        chat.push(
          { role: "assistant", text: m.question, qId: m.qId },
          { role: "user", text: m.answer, qId: m.qId },
        );
      });
      setChatMessages(chat);

      if (questions.length > 0 && fin.size >= questions.length) {
        setIsSessionComplete(true);
      }
      return fin;
    } catch (err) {
      console.warn("reloadAllAnswers failed", err);
      return null;
    }
  };

  useEffect(() => {
    let c = false;
    async function r() {
      if (!c) await reloadAllAnswers();
    }
    r();
    return () => {
      c = true;
    };
  }, [questions]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [chatMessages, typingText, isLoading, isAssistantTyping]);

  useEffect(() => {
    return () => {
      if (typewriterRef.current) clearInterval(typewriterRef.current);
    };
  }, []);

  // Debounced AI suggestions based on user input (same as ChatKickoffPage)
  useEffect(() => {
    if (suggestionSelectedRef.current) {
      suggestionSelectedRef.current = false;
      return;
    }
    if (suggestionsDebounceRef.current) {
      clearTimeout(suggestionsDebounceRef.current);
    }
    if (
      activeQuestionIdx === null ||
      !inputValue.trim() ||
      inputValue.trim().length < 3 ||
      isSessionComplete ||
      isBusy
    ) {
      setSuggestions([]);
      setSuggestionMeta(null);
      setHoveredSuggestionIdx(null);
      return;
    }
    const q = questions[activeQuestionIdx];
    if (!q) return;
    const sid = localStorage.getItem("sessionId") || session?.id;
    if (!sid) {
      setSuggestions([]);
      setSuggestionMeta(null);
      return;
    }
    suggestionsDebounceRef.current = setTimeout(async () => {
      if (suggestionSelectedRef.current) {
        suggestionSelectedRef.current = false;
        return;
      }
      setSuggestionLoading(true);
      setSuggestionError(null);
      setSuggestions([]);
      setSuggestionMeta(null);
      setHoveredSuggestionIdx(null);
      try {
        const response = await authService.getAiAnswerSuggestions(
          sid,
          q.id,
          inputValue.trim(),
        );
        let list = [];
        if (Array.isArray(response)) {
          list = response;
          setSuggestionMeta(null);
        } else if (response && typeof response === "object") {
          list =
            response.suggestions ??
            response.suggestion ??
            (Array.isArray(response.results) ? response.results : []);
          setSuggestionMeta(response);
        }
        setSuggestions(Array.isArray(list) ? list : []);
      } catch (err) {
        console.error("AI suggestion error", err);
        setSuggestionError(err?.message || "Failed to get AI suggestions");
        setSuggestions([]);
        setSuggestionMeta(null);
      } finally {
        setSuggestionLoading(false);
      }
    }, 800);
    return () => {
      if (suggestionsDebounceRef.current)
        clearTimeout(suggestionsDebounceRef.current);
      if (hoverTimeoutRef.current) clearTimeout(hoverTimeoutRef.current);
    };
  }, [
    inputValue,
    activeQuestionIdx,
    questions,
    isSessionComplete,
    isBusy,
    session,
  ]);

  // ────────────────────────────────────────────────
  //  Handlers
  // ────────────────────────────────────────────────

  function selectQuestion(idx) {
    const q = questions[idx];
    if (!q) return;
    const ex = messages.find((m) => m.qId === q.id);
    if (ex) {
      setEditingMessageIdx(messages.findIndex((m) => m.qId === q.id));
      setInputValue(ex.answer);
    } else {
      setEditingMessageIdx(null);
      setInputValue("");
    }
    setActiveQuestionIdx(idx);
    setIntroVisible(false);

    if (!chatMessages.some((m) => m.qId === q.id && m.role === "assistant")) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", text: q.text, qId: q.id, helpText: q.helpText },
      ]);
    }
  }

  function handleSkip() {
    if (activeQuestionIdx == null) return;
    const n = activeQuestionIdx + 1;
    if (n >= questions.length) return;
    const nq = questions[n];
    setActiveQuestionIdx(n);
    setInputValue("");
    setEditingMessageIdx(null);
    setChatMessages((prev) => [
      ...prev,
      { role: "assistant", text: nq.text, qId: nq.id, helpText: nq.helpText },
    ]);
    // Reset textarea height
    const textarea = document.querySelector('.ddp-input-wrap .chat-text-input');
    if (textarea) {
      textarea.style.height = 'auto';
    }
    setTimeout(
      () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
      80,
    );
  }

  function handleReturn() {
    if (activeQuestionIdx <= 0) return;
    const p = activeQuestionIdx - 1;
    const pq = questions[p];
    setActiveQuestionIdx(p);
    setInputValue("");
    setEditingMessageIdx(null);
    setChatMessages((prev) => [
      ...prev,
      { role: "assistant", text: pq.text, qId: pq.id, helpText: pq.helpText },
    ]);
    setTimeout(
      () => chatEndRef.current?.scrollIntoView({ behavior: "smooth" }),
      80,
    );
  }

  async function handleSend() {
    if (isBusy) {
      toast.info("Please wait...");
      return;
    }
    const trimmed = inputValue.trim();
    if (!trimmed) return;

    const q = questions[activeQuestionIdx];
    if (!q) {
      toast.info("Select a question first.");
      return;
    }

    const sid = localStorage.getItem("sessionId") || session?.id;
    if (!sid) {
      toast.error("Session ID not found");
      return;
    }

    const rid = q.raw?.id ?? q.id;

    if (editingMessageIdx !== null) {
      setIsLoading(true);
      try {
        await authService.createAnswer(sid, {
          question: Number(rid),
          answer_text: trimmed,
        });
        setMessages((prev) => {
          const u = [...prev];
          u[editingMessageIdx] = { ...u[editingMessageIdx], answer: trimmed };
          return u;
        });
        if (!finalizedQuestionIds.has(q.id)) {
          setFinalizedQuestionIds((p) => new Set([...p, q.id]));
        }
        setChatMessages((prev) => {
          const u = [...prev];
          let li = -1;
          for (let i = u.length - 1; i >= 0; i--) {
            if (u[i].qId === q.id && u[i].role === "user") {
              li = i;
              break;
            }
          }
          if (li !== -1) u[li] = { ...u[li], text: trimmed };
          return u;
        });
        toast.success("Answer updated!");
        setEditingMessageIdx(null);
        setInputValue("");
      } catch (err) {
        toast.error(err?.message || "Failed to update");
      } finally {
        setIsLoading(false);
      }
      return;
    }

    setInputValue("");
    setIsAiDraft(false);
    setChatMessages((prev) => [
      ...prev,
      { role: "user", text: trimmed, qId: q.id, pending: true },
    ]);

    setIsLoading(true);
    setOrbThinking("Thinking…");
    setOrbRetrieving("Retrieving brand knowledge…");
    try {
      let ai = null;
      let orb = null;
      let imp = trimmed;
      let fu = "";
      let orbStatus = "";

      try {
        const orbQId = resolveOrbQuestionId(q, activeQuestionIdx);
        orb = await authService.submitBrandGodFatherAnswer({
          sourceSessionId: sid,
          qId: orbQId,
          answer: trimmed,
          contextData: {
            frontend_page: "Deepdivepage",
            question_id: rid,
            question_text: q.text,
            question_bank: {
              [orbQId]: q.text,
            },
          },
        });
        fu = formatOrbCoachReply(orb);
        orbStatus = String(orb?.status || "").toUpperCase();
        setOrbMemory(
          `ORB ${orbStatus || "checked"} · next ${orb?.next_q_id || "hold"} · depth ${orb?.depth_score ?? "n/a"}`,
        );
      } catch (orbError) {
        console.warn("BrandGodFather ORB unavailable, using draft fallback", orbError);
        toast.info("ORB engine unavailable right now; using fallback coaching response.");
        ai = await authService.aiSuggestionDraft(
          sid,
          rid,
          trimmed,
          isAiDraft,
        );
        imp = (ai?.improved_answer || trimmed).trim();
        fu = (ai?.follow_up_question || "").trim();
      }

      const sources = ai?.sources || [];
      const concepts = ai?.graph_concepts || [];
      setRagSources(sources);
      setGraphConcepts(concepts);
      setOrbSources(sources);
      setOrbGraphConcepts(concepts);
      if (sources.length) {
        setOrbMemory("ORB connected concepts");
      }

      setMessages((prev) => {
        const u = [...prev];
        const i = u.findIndex((m) => m.qId === q.id);
        const nextMessage = {
          question: q.text,
          answer: imp,
          orbStatus,
          orbReply: orb?.reply || "",
          orbNextQId: orb?.next_q_id || null,
          orbDepthScore: orb?.depth_score ?? null,
          brandGodFatherSessionId: orb?.brandgodfather_session_id || null,
        };
        if (i !== -1) u[i] = { ...u[i], ...nextMessage };
        else u.push({ qId: q.id, ...nextMessage });
        return u;
      });

      setChatMessages((prev) => {
        const u = [...prev];
        let li = -1;
        for (let i = u.length - 1; i >= 0; i--) {
          if (u[i].qId === q.id && u[i].role === "user") {
            li = i;
            break;
          }
        }
        if (li !== -1) u[li] = { ...u[li], pending: false };
        else u.push({ role: "user", text: trimmed, qId: q.id });
        return u;
      });

      // FIX: finalize the question id after a successful send
      if (orbStatus !== "REJECT") {
        setFinalizedQuestionIds((prev) => new Set([...prev, q.id]));
      }

      setIsLoading(false);
      setEditingMessageIdx(null);
      setIsAiDraft(false);

      if (fu) {
        setOrbSpeaking();
        if (typewriterRef.current) clearInterval(typewriterRef.current);
        setIsAssistantTyping(true);
        setTypingText("");
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "",
            qId: q.id,
            isTyping: true,
            orbStatus,
            orbNextQId: orb?.next_q_id || null,
            orbDepthScore: orb?.depth_score ?? null,
          },
        ]);

        let ci = 0;
        typewriterRef.current = setInterval(() => {
          if (ci < fu.length) {
            setTypingText(fu.slice(0, ci + 1));
            ci++;
          } else {
            clearInterval(typewriterRef.current);
            typewriterRef.current = null;
            setIsAssistantTyping(false);
            setTypingText("");
            setChatMessages((prev) => {
              const u = [...prev];
              const ti = u.findIndex((m) => m.isTyping);
              if (ti !== -1) {
                u[ti] = {
                  role: "assistant",
                  text: fu,
                  qId: q.id,
                  orbStatus,
                  orbNextQId: orb?.next_q_id || null,
                  orbDepthScore: orb?.depth_score ?? null,
                };
              }
              return u;
            });
            setOrbIdle();
          }
        }, 20);
      } else {
        setOrbIdle();
      }
    } catch (err) {
      setIsLoading(false);
      setOrbIdle();
      toast.error(err?.message || "Failed to send.");
      // fallback: still save locally
      setMessages((prev) => {
        const u = [...prev];
        const i = u.findIndex((m) => m.qId === q.id);
        if (i !== -1) u[i] = { ...u[i], question: q.text, answer: trimmed };
        else u.push({ qId: q.id, question: q.text, answer: trimmed });
        return u;
      });
      setChatMessages((prev) => {
        const u = [...prev];
        let li = -1;
        for (let i = u.length - 1; i >= 0; i--) {
          if (u[i].qId === q.id && u[i].role === "user") {
            li = i;
            break;
          }
        }
        if (li !== -1) u[li] = { ...u[li], text: trimmed, pending: false };
        else u.push({ role: "user", text: trimmed, qId: q.id });
        return u;
      });
      setEditingMessageIdx(null);
    }
  }

  const handleSave = async () => {
    if (isSessionComplete) return;
    const sid = localStorage.getItem("sessionId") || session?.id;
    if (!sid) return toast.error("Session ID not found");

    let qi = activeQuestionIdx;
    if (qi == null || qi < 0) {
      if (!messages.length) return toast.info("No answer to save yet.");
      qi = questions.findIndex(
        (q) => q.id === messages[messages.length - 1].qId,
      );
      if (qi === -1) return toast.info("No matching question.");
    }

    const q = questions[qi];
    const lat = [...messages].reverse().find((m) => m.qId === q.id);
    if (!lat?.answer?.trim()) return toast.info("Write an answer first.");
    if (String(lat.orbStatus || "").toUpperCase() === "REJECT") {
      return toast.info("ORB rejected this answer. Go deeper before saving it.");
    }

    try {
      await authService.createAnswer(sid, {
        question: Number(q.id),
        answer_text: lat.answer.trim(),
      });

      const fin = await reloadAllAnswers();
      if (fin) {
        if (questions.length > 0 && fin.size >= questions.length) {
          setIsSessionComplete(true);
          toast.success("Deep Dive complete! 🎉");
          return;
        }
        toast.success("Answer saved!");
        const ni = questions.findIndex((q) => !fin.has(q.id));
        if (ni !== -1) {
          const nq = questions[ni];
          setActiveQuestionIdx(ni);
          setInputValue("");
          setChatMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              text: nq.text,
              qId: nq.id,
              helpText: nq.helpText,
            },
          ]);
        }
      } else {
        toast.success("Answer saved!");
      }
    } catch (err) {
      toast.error(err?.message || "Failed to save.");
    }
  };

  const handleQuickRefine = async () => {
    const sid = localStorage.getItem("sessionId") || session?.id;
    if (!sid) return toast.error("Session ID not found");

    let qi = activeQuestionIdx;
    if (qi == null || qi < 0) {
      if (!messages.length) return toast.info("Select a question first.");
      qi = questions.findIndex(
        (q) => q.id === messages[messages.length - 1].qId,
      );
      if (qi === -1) return toast.info("Select a question first.");
    }

    const q = questions[qi];
    const ex = [...messages].reverse().find((m) => m.qId === q.id);
    const draft = inputValue || ex?.answer || "";
    if (!draft.trim()) return toast.info("Write something first.");

    setRefineLoading(true);
    try {
      const r = await authService.aiSuggestionDraft(
        sid,
        q.raw?.id ?? q.id,
        draft,
        true,
      );
      const improved = (r?.improved_answer || draft).trim();
      const followUp = (r?.follow_up_question || "").trim();
      if (r?.rewrite_blocked || improved === draft.trim()) {
        setInputValue(draft);
        setIsAiDraft(false);
        if (followUp) {
          setChatMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              text: followUp,
              qId: q.id,
              orbStatus: "REJECT",
            },
          ]);
        }
        toast.info("ORB challenged the answer before improving the copy.");
        return;
      }
      setInputValue(improved);
      setIsAiDraft(true);
      toast.success("AI refined — review and click Send.");
    } catch (err) {
      toast.error(err?.message || "Refinement failed.");
    } finally {
      setRefineLoading(false);
    }
  };

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isBusy) handleSend();
    }
  }

  // ────────────────────────────────────────────────
  //  Render
  // ────────────────────────────────────────────────

  return (
    <>
      <ChatNavbar
        sessionId={session?.id}
        onSave={handleSave}
        showSaveButton={true}
        showLogoutButton={true}
        showDownloadButton={false}
        canGenerate={false}
      />

      <div className="ddp-root">
        {/* ── SIDEBAR ── */}
        <aside className="ddp-sidebar">
          <div className="ddp-sidebar-header">
            <h2 className="ddp-sidebar-title">Deep Dive</h2>
          </div>
          <div className="ddp-sidebar-divider" />

          {totalQ > 0 && (
            <div className="ddp-progress-wrap">
              <div className="ddp-progress-track">
                <div
                  className="ddp-progress-fill"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <span className="ddp-progress-label">
                {answeredCount} / {totalQ} answered
              </span>
            </div>
          )}

          <div className="ddp-q-list">
            {loading ? (
              <div className="ddp-sidebar-msg">Loading questions…</div>
            ) : loadError ? (
              <div className="ddp-sidebar-error">{loadError}</div>
            ) : questions.length === 0 ? (
              <div className="ddp-sidebar-msg">
                No deep dive questions found.
              </div>
            ) : (
              questions.map((q, idx) => (
                <button
                  key={q.id}
                  className={`ddp-q-item ${activeQuestionIdx === idx ? "ddp-q-item--active" : ""} ${finalizedQuestionIds.has(q.id) ? "ddp-q-item--answered" : ""}`}
                  onClick={() => selectQuestion(idx)}
                  title={q.title}
                >
                  <span className="ddp-q-num">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  <span className="ddp-q-text">{q.title}</span>
                  {finalizedQuestionIds.has(q.id) && (
                    <span className="ddp-q-check">✓</span>
                  )}
                </button>
              ))
            )}
          </div>

          <div className="ddp-sidebar-footer">
          <button
              className="ddp-back-btn"
              onClick={() => navigate("/ChatKickoffPage")}
            >
              <IoChevronBack className="ddp-back-icon" />
              Back to Identity
            </button>
          </div>
        </aside>

        {/* ── MAIN ── */}
        <main className="ddp-main">
          <div className="ddp-chat-area">
            {/* INTRO: shown when no conversation yet */}
            {introVisible && !hasConvo && !loading && (
              <div className="ddp-intro">
                <h2 className="ddp-intro-title">
                  "Let's go deeper — this is where brands get unforgettable."
                </h2>
                <p className="ddp-intro-body">
                  Pick any question from the sidebar, or start with one of these.
                </p>

                {/* FIX: List layout instead of grid, with helpText below each question */}
                {questions.length > 0 && (
                  <div className="ddp-intro-list">
                    {questions.slice(0, 4).map((q, i) => (
                      <button
                        key={q.id}
                        className="ddp-intro-item"
                        onClick={() => selectQuestion(i)}
                      >
                        <div className="ddp-intro-item-header">
                          <span className="ddp-intro-item-num">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <p className="ddp-intro-item-text">{q.text}</p>
                        </div>
                        {q.helpText && (
                          <p className="ddp-intro-item-hint">💡 {q.helpText}</p>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* SESSION COMPLETE VIEW */}
            {isSessionComplete ? (
              <>
                <div className="ddp-chat-messages">
                  {messages.map((msg, i) => (
                    <div key={`${msg.qId}-${i}`} className="ddp-message-row">
                      <div className="ddp-bubble ddp-bubble--bot">
                        <div className="bot-avatar">
                          <img src={avatar} alt="Bot" />
                        </div>
                        <div className="ddp-bubble-content">{msg.question}</div>
                      </div>

                      <div className="ddp-bubble ddp-bubble--user">
                        <button
                          className="ddp-edit-icon-btn"
                          onClick={() => {
                            const idx = messages.findIndex(
                              (m) => m.qId === msg.qId,
                            );
                            setEditingMessageIdx(idx);
                            setInputValue(msg.answer);
                          }}
                          title="Edit answer"
                        >
                          ✎
                        </button>
                        <div className="ddp-bubble-content">{msg.answer}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="ddp-complete-banner">
                  <span className="ddp-complete-icon">🎉</span>
                  <div>
                    <strong>Deep Dive Complete!</strong>
                    <p>
                      You've answered all optional questions. Your brand story
                      is fully shaped.
                    </p>
                  </div>
                  <button
                    className="ddp-back-btn ddp-back-btn--cta"
                    onClick={() => navigate("/ChatKickoffPage")}
                  >
                    <IoChevronBack className="ddp-back-icon" />
                    Back to Identity
                  </button>
                </div>
              </>
            ) : (
              /* ACTIVE CHAT VIEW */
              <div className="ddp-chat-messages">
                {chatMessages.map((m, i) => {
                  const isUser = m.role === "user";
                  const isLast = i === chatMessages.length - 1;
                  const isFinalized = m.qId && finalizedQuestionIds.has(m.qId);
                  let messageIdx = -1;
                  if (isUser && isFinalized && !m.pending && !m.isTyping) {
                    messageIdx = messages.findIndex((msg) => msg.qId === m.qId);
                  }
                  const canEdit =
                    isUser &&
                    isFinalized &&
                    messageIdx !== -1 &&
                    !m.pending &&
                    !m.isTyping;

                  const showNav =
                    isLast &&
                    !m.pending &&
                    !m.isTyping &&
                    !isSessionComplete &&
                    activeQuestionIdx !== null;
                  const canSkip =
                    showNav && activeQuestionIdx < questions.length - 1;
                  const canReturn = showNav && activeQuestionIdx > 0;

                  return (
                    <div
                      key={i}
                      className={`ddp-message-row ${isUser ? "user" : "bot"}`}
                    >
                      <div
                        className={`ddp-bubble ${isUser ? "ddp-bubble--user" : "ddp-bubble--bot"}`}
                      >
                        {!isUser && (
                          <div className="bot-avatar">
                            {m.isTyping || m.pending ? (
                              <span className="rotating-star-avatar">⭐</span>
                            ) : (
                              <img src={avatar} alt="Bot" />
                            )}
                          </div>
                        )}

                        {canEdit && (
                          <button
                            className="ddp-edit-icon-btn"
                            onClick={() => {
                              setEditingMessageIdx(messageIdx);
                              setInputValue(messages[messageIdx].answer);
                              setIsAiDraft(false);
                              const qi = questions.findIndex(
                                (q) => q.id === m.qId,
                              );
                              if (qi !== -1) setActiveQuestionIdx(qi);
                            }}
                            title="Edit this answer"
                          >
                            ✎
                          </button>
                        )}

                        <div className="ddp-bubble-content">
                          {m.isTyping ? (
                            <p>
                              <TypewriterText
                                text={typingText}
                                isTyping={isAssistantTyping}
                                showCursor
                              />
                            </p>
                          ) : m.pending && !isUser ? (
                            <ThinkingPipeline
                              message={thinkingMessage || "Thinking…"}
                              visible
                            />
                          ) : (
                            m.text
                              .split(/\n\s*\n/)
                              .map((para, pi) => <p key={pi}>{para}</p>)
                          )}
                        </div>

                        {/* FIX: helpText badge shows below bot bubble content, always */}
                        {!isUser && m.helpText && !m.isTyping && !m.pending && (
                          <div className="ddp-help-badge">💡 {m.helpText}</div>
                        )}
                      </div>

                      {showNav && (
                        <div
                          className={`ddp-nav-buttons ${isUser ? "ddp-nav--user" : ""}`}
                        >
                          {canReturn && (
                            <button
                              className="ddp-nav-btn ddp-nav-btn--return"
                              onClick={handleReturn}
                            >
                              ← Return
                            </button>
                          )}
                          {canSkip && (
                            <button
                              className="ddp-nav-btn ddp-nav-btn--skip"
                              onClick={handleSkip}
                            >
                              Skip →
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}

                {isLoading && !chatMessages.some((m) => m.isTyping) && (
                  <div className="ddp-message-row bot">
                    <div className="ddp-bubble ddp-bubble--bot">
                      <div className="bot-avatar">
                        <span className="rotating-star-avatar">⭐</span>
                      </div>
                      <div className="ddp-bubble-content">
                        <ThinkingPipeline
                          message={thinkingMessage}
                          visible
                        />
                      </div>
                    </div>
                  </div>
                )}

                {!isLoading && ragSources.length > 0 && (
                  <SourceCards
                    sources={ragSources}
                    graphConcepts={graphConcepts}
                  />
                )}

                <div ref={chatEndRef} />
              </div>
            )}
          </div>

          {/* ── INPUT BAR — sticky at bottom of main ── */}
          {!isSessionComplete && (
            <div className="ddp-input-wrap">
              {/* AI suggestions based on user input */}
              {(suggestions.length > 0 || suggestionLoading) && (
                <div className="ddp-suggestions-outer">
                  {suggestions.length > 0 && (
                    <div className="ddp-suggestions-container">
                      <div className="ddp-suggestions-header">
                        <span className="ddp-suggestions-title">💡 AI Suggestions</span>
                        <button
                          type="button"
                          className="ddp-suggestions-close"
                          onClick={() => {
                            setSuggestions([]);
                            setSuggestionMeta(null);
                          }}
                          aria-label="Close suggestions"
                        >
                          ✕
                        </button>
                      </div>
                      {suggestionMeta?.suggestion_quote?.enabled && suggestionMeta.suggestion_quote.quote && (
                        <blockquote className="ddp-suggestion-quote">
                          {suggestionMeta.suggestion_quote.quote}
                        </blockquote>
                      )}
                      <div
                        className="ddp-suggestions-grid"
                        onMouseLeave={() => {
                          hoverTimeoutRef.current = setTimeout(() => {
                            setHoveredSuggestionIdx(null);
                            hoverTimeoutRef.current = null;
                          }, 150);
                        }}
                      >
                        {suggestions.map((suggestion, idx) => {
                          const isHovered = hoveredSuggestionIdx === idx;
                          const isHidden =
                            hoveredSuggestionIdx !== null && hoveredSuggestionIdx !== idx;
                          return (
                            <div
                              key={idx}
                              role="button"
                              tabIndex={0}
                              className={`ddp-suggestion-card ${isHovered ? "ddp-suggestion-card-hovered" : ""} ${isHidden ? "ddp-suggestion-card-hidden" : ""}`}
                              onClick={() => {
                                suggestionSelectedRef.current = true;
                                setInputValue(suggestion);
                                setSuggestions([]);
                                setSuggestionMeta(null);
                                setIsAiDraft(false);
                                setHoveredSuggestionIdx(null);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                  e.preventDefault();
                                  suggestionSelectedRef.current = true;
                                  setInputValue(suggestion);
                                  setSuggestions([]);
                                  setSuggestionMeta(null);
                                  setIsAiDraft(false);
                                  setHoveredSuggestionIdx(null);
                                }
                              }}
                              onMouseEnter={() => {
                                if (hoverTimeoutRef.current) {
                                  clearTimeout(hoverTimeoutRef.current);
                                  hoverTimeoutRef.current = null;
                                }
                                setHoveredSuggestionIdx(idx);
                              }}
                              onMouseLeave={() => {
                                hoverTimeoutRef.current = setTimeout(() => {
                                  setHoveredSuggestionIdx(null);
                                  hoverTimeoutRef.current = null;
                                }, 150);
                              }}
                            >
                              <div className="ddp-suggestion-content">{suggestion}</div>
                              <div className="ddp-suggestion-footer">
                                <span className="ddp-suggestion-hint">Click to use</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  {suggestionLoading && (
                    <div className="ddp-suggestions-loading">
                      <div className="ddp-suggestions-spinner" />
                      <span>Generating suggestions...</span>
                    </div>
                  )}
                </div>
              )}

              <div className="chat-inputs">
                <textarea
                  className="chat-text-input"
                  value={inputValue}
                  onChange={(e) => {
                    setInputValue(e.target.value);
                    setIsAiDraft(false);
                    // Auto-resize textarea
                    e.target.style.height = 'auto';
                    e.target.style.height = e.target.scrollHeight + 'px';
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      onKeyDown(e);
                    }
                  }}
                  placeholder={
                    activeQuestionIdx === null
                      ? "Select a question from the sidebar to begin…"
                      : editingMessageIdx !== null
                        ? "Update your answer…"
                        : "Type your answer…"
                  }
                  disabled={activeQuestionIdx === null || isBusy}
                  rows={1}
                />

                <div className="chat-right-icons">
                  {/* Refine button */}
                  <button
                    className={`icon-btn refine-btn ${refineLoading ? "loading" : ""}`}
                    onClick={handleQuickRefine}
                    disabled={
                      refineLoading ||
                      activeQuestionIdx === null ||
                      !inputValue.trim()
                    }
                    title="Refine with AI"
                  >
                    {refineLoading ? (
                      <div className="modern-spinner"></div>
                    ) : (
                      <img
                        src={chatIcon1}
                        alt="Refine"
                        className="icon-small"
                      />
                    )}
                    <div className="tip-bubble">
                      Sharpen it the World-Famous way
                    </div>
                  </button>

                  {/* Send button */}
                  <button
                    className="icon-btn magic-pen-btn"
                    onClick={handleSend}
                    disabled={
                      isBusy || !inputValue.trim() || activeQuestionIdx === null
                    }
                    title={isBusy ? "Processing..." : "Send message"}
                  >
                    <img src={chatIcon2} alt="Send" className="icon-small" />
                  </button>
                </div>
              </div>

              {/* Save button — only when there's something to save for the active question */}
              {messages.some(
                (m) => m.qId === questions[activeQuestionIdx]?.id,
              ) && (
                <div className="ddp-save-bar">
                  <button className="ddp-save-btn" onClick={handleSave}>
                    Save Answer & Continue
                  </button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </>
  );
}