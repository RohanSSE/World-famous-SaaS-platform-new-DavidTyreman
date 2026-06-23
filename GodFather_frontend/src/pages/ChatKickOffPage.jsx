// import React, { useEffect, useRef, useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { toast } from "react-toastify";
// import "../components/ChatKickoffPage.css";
// import ChatNavbar from "../pages/ChatNavbar";
// import attachment from "../assets/attachment.png";
// import chatIcon1 from "../assets/chat-icon1.png";
// import chatIcon2 from "../assets/chat-icon2.png";
// import authService from "../services/authService";

// export default function ChatKickoffPage() {
//   const navigate = useNavigate();
//   const [attachedFileName, setAttachedFileName] = useState("");
//   const fileInputRef = useRef(null);
//   const savedSessionJson = localStorage.getItem("session");
//   const initialSession = savedSessionJson ? JSON.parse(savedSessionJson) : null;
//   const [session, setSession] = useState(initialSession);

//   // State for API data
//   const [questions, setQuestions] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [loadError, setLoadError] = useState("");
//   const [messages, setMessages] = useState([]);
//   const [activeQuestionIdx, setActiveQuestionIdx] = useState(null);
//   const [inputValue, setInputValue] = useState("");
//   const [editingMessageIdx, setEditingMessageIdx] = useState(null); // ✅ ADD THIS

//   const initialViewMode = localStorage.getItem("agencyViewMode") === "true";
//   const [viewMode, setViewMode] = useState(initialViewMode);
//   const allAnswered =
//     questions.length > 0 && messages.length >= questions.length;

//   const [showCommentModal, setShowCommentModal] = useState(false);
//   const [commentText, setCommentText] = useState("");
//   const [commentLoading, setCommentLoading] = useState(false);
//   const [currentSessionId, setCurrentSessionId] = useState(null); // set when opening modal

//   const handleCommentSubmit = async () => {
//     if (!commentText.trim() || !currentSessionId) return;

//     setCommentLoading(true);
//     try {
//       await authService.addComment(currentSessionId, {
//         comment: commentText.trim(),
//       });
//       toast.success("Comment saved successfully!");
//       setShowCommentModal(false);
//       setCommentText("");
//       // Optionally refresh comments/messages here
//     } catch (error) {
//       toast.error(error.message || "Failed to save comment");
//     } finally {
//       setCommentLoading(false);
//     }
//   };
//   // ✅ ADD THIS: Handle Edit button click
//   function handleEditMessage(i) {
//     const msg = messages[i];
//     setEditingMessageIdx(i);
//     setInputValue(msg.answer);
//     // Find the question index
//     const qIdx = questions.findIndex((q) => q.id === msg.qId);
//     setActiveQuestionIdx(qIdx);
//   }

//   const IDENTITY_STAGE_NUM = 2;
//   useEffect(() => {
//     // Detect agency view-only mode
//     setViewMode(localStorage.getItem("agencyViewMode") === "true");
//     // Clear the flag after use (optional for security)
//     return () => localStorage.removeItem("agencyViewMode");
//   }, []);
//   // Load questions from API on mount
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
//               q &&
//               q.is_active !== false &&
//               Number(q.stage) === Number(IDENTITY_STAGE_NUM)
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
//             raw: q,
//           }));
//         setQuestions(filtered);
//       } catch (err) {
//         const errorMsg = err?.message || "Failed to load questions";
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

//   // ✅ NEW: Load existing answers from backend when component mounts
//   useEffect(() => {
//     let cancelled = false;

//     async function loadExistingAnswers() {
//       if (!Array.isArray(questions) || questions.length === 0) return;

//       const sessionId = localStorage.getItem("sessionId");
//       if (!sessionId) return;

//       try {
//         // Fetch all answers for this session
//         const remoteAnswers = await authService.getAnswers(sessionId, {});

//         if (cancelled) return;

//         // Create a map of question IDs to their answers
//         const answerMap = {};
//         if (Array.isArray(remoteAnswers)) {
//           remoteAnswers.forEach((answer) => {
//             const questionId = answer.question;
//             const answerText = answer.answer_text;

//             // Find the question object to get its full details
//             const question = questions.find(
//               (q) => q.id === questionId || q.raw?.id === questionId
//             );

//             if (question && answerText && String(answerText).trim() !== "") {
//               answerMap[question.id] = {
//                 qId: question.id,
//                 question: question.text,
//                 answer: answerText,
//               };
//             }
//           });
//         }

//         // Convert map to array and set messages
//         if (!cancelled) {
//           const loadedMessages = Object.values(answerMap);
//           setMessages(loadedMessages);
//         }
//       } catch (err) {
//         console.warn("Failed to load existing answers:", err);
//         // Don't show error to user - just continue with empty messages
//       }
//     }

//     loadExistingAnswers();

//     return () => {
//       cancelled = true;
//     };
//   }, [questions]); // Re-run when questions change
//   // ✅ FIXED - includes editingMessageIdx in dependency array
//   // ✅ FIXED - Remove guard that blocks repeated attempts
//   useEffect(() => {
//     if (viewMode) return;
//     const allAnswered =
//       messages.length > 0 &&
//       questions.length > 0 &&
//       messages.length === questions.length;

//     if (allAnswered) {
//       const sessionId = localStorage.getItem("sessionId");
//       if (!sessionId) return;

//       console.log(
//         "✓ All answered, hitting complete API for session:",
//         sessionId
//       );

//       const completeSessionAsync = async () => {
//         try {
//           await authService.completeSession(sessionId);
//           toast.success("Assessment completed!");
//           console.log("✓ Session marked as completed");
//         } catch (err) {
//           console.error("❌ Failed to complete session:", err.message);
//           toast("You can only view this Page ", {
//             type: "error",
//             className: "toast-agency-error",
//             icon: "🚫", // or use a custom SVG/component if desired
//             progressStyle: { background: "#1c1670ff" },
//             autoClose: 8000, // Longer display
//           });
//         }
//       };

//       completeSessionAsync();
//     }
//   }, [viewMode, messages, questions.length, editingMessageIdx]);

//   function openFilePicker() {
//     fileInputRef.current?.click();
//   }

//   function onFileChange(e) {
//     const f = e.target.files && e.target.files[0];
//     if (f) setAttachedFileName(f.name);
//     else setAttachedFileName("");
//   }

//   function clearAttachment(e) {
//     e.stopPropagation();
//     setAttachedFileName("");
//     if (fileInputRef.current) fileInputRef.current.value = "";
//   }

//   function handleSidebarQuestion(idx) {
//     // ✅ NEW: Check if question is already answered
//     const isAnswered = messages.some((m) => m.qId === questions[idx].id);
//     if (isAnswered) {
//       toast.info(
//         "This question has already been answered. You can edit it using the Edit button."
//       );
//       return;
//     }
//     setActiveQuestionIdx(idx);
//     setInputValue("");
//     setEditingMessageIdx(null);
//   }

//   function handleKickoffQuestion(idx) {
//     setActiveQuestionIdx(idx);
//     setInputValue("");
//     setEditingMessageIdx(null);
//   }

//   // ✅ NEW: Handle Edit button click
//   function handleEditMessage(idx) {
//     const msg = messages[idx];
//     setEditingMessageIdx(idx);
//     setInputValue(msg.answer);
//     // Find the question index
//     const qIdx = questions.findIndex((q) => q.id === msg.qId);
//     setActiveQuestionIdx(qIdx);
//   }

//   async function handleSend() {
//     if (viewMode) return;
//     const trimmed = inputValue.trim();
//     if (!trimmed) return;
//     const q = questions[activeQuestionIdx];
//     if (!q) return;

//     const sessionId = localStorage.getItem("sessionId");

//     // ✅ NEW: Handle edit mode
//     if (editingMessageIdx !== null) {
//       // Update existing message
//       setMessages((prev) => {
//         const updated = [...prev];
//         updated[editingMessageIdx] = {
//           ...updated[editingMessageIdx],
//           answer: trimmed,
//         };
//         return updated;
//       });

//       // Send updated answer to backend
//       try {
//         await authService.createAnswer(sessionId, {
//           question: Number(q.id),
//           answer_text: trimmed,
//         });
//         toast.success("Answer updated successfully!");
//       } catch (err) {
//         toast.error(err?.message || "Failed to update answer");
//       }

//       // ✅ FIXED: Don't change activeQuestionIdx, just reset editing mode and input
//       setEditingMessageIdx(null);
//       setInputValue("");
//       // Keep the same question visible - don't set to null
//       return;
//     }

//     // Optimistically add to chat UI (new answer)
//     setMessages((prev) => [
//       ...prev,
//       { qId: q.id, question: q.text, answer: trimmed },
//     ]);
//     setInputValue("");

//     // Send to backend
//     try {
//       await authService.createAnswer(sessionId, {
//         question: Number(q.id),
//         answer_text: trimmed,
//       });
//     } catch (err) {
//       toast.error(err?.message || "Failed to save answer");
//     }

//     // Move to next question, or finish
//     if (activeQuestionIdx < questions.length - 1) {
//       setActiveQuestionIdx(activeQuestionIdx + 1);
//     } else {
//       setActiveQuestionIdx(null); // All done - show summary/thank you
//     }
//   }

//   // Handle "Enter" key in input
//   function onKeyDown(e) {
//     if (e.key === "Enter") {
//       e.preventDefault();
//       handleSend();
//     }
//   }

//   const handleSave = () => {
//     toast.success("Chat saved successfully!");
//   };

//   const handleDownloadManifesto = async () => {
//   if (!session?.id) {
//     toast.error("Session ID not found");
//     return;
//   }
//   try {
//     const blob = await authService.downloadManifesto(session.id);
//     const url = window.URL.createObjectURL(new Blob([blob]));
//     const link = document.createElement("a");
//     link.href = url;
//     link.setAttribute("download", "manifesto.pdf"); // Filename
//     document.body.appendChild(link);
//     link.click();
//     link.parentNode.removeChild(link);
//     toast.success("Manifesto PDF download started");
//   } catch (error) {
//     toast.error(error.message || "Failed to download manifesto");
//   }
// };

//   // Render
//   return (
//     <>
//       <ChatNavbar
//         onSave={handleSave}
//         onDownloadPdf={handleDownloadManifesto}
//         showSaveButton={true}
//         showDownloadButton={true}
//         showLogoutButton={true}
//         showCommentButton={true}
//         onCommentClick={() => {
//           setCurrentSessionId(session.id); // pass correct session id from your state/context
//           setShowCommentModal(true);
//         }}
//       />

//       <div className="chat-root">
//         <div className="chat-body">
//           {/* SIDEBAR */}
//           <aside className="chat-sidebar">
//             <h2 className="sidebar-title">Brand Manifesto</h2>
//             <div className="sidebar-divider"></div>
//             {loading ? (
//               <div
//                 style={{
//                   padding: 12,
//                   color: "rgba(255,255,255,0.5)",
//                   fontSize: 13,
//                 }}
//               >
//                 Loading questions...
//               </div>
//             ) : loadError ? (
//               <div style={{ color: "#ffb3b3", padding: 12, fontSize: 13 }}>
//                 {loadError}
//               </div>
//             ) : questions.length === 0 ? (
//               <div
//                 style={{
//                   padding: 12,
//                   color: "rgba(255,255,255,0.5)",
//                   fontSize: 13,
//                 }}
//               >
//                 No questions found for Identity stage.
//               </div>
//             ) : (
//               <div className="sidebar-list">
//                 {questions.map((item, idx) => {
//                   // ✅ NEW: Check if question is answered
//                   const isAnswered = messages.some((m) => m.qId === item.id);

//                   return (
//                     <div
//                       className={`sidebar-step-row${
//                         activeQuestionIdx === idx ? " selected" : ""
//                       }${isAnswered ? " answered" : ""}`}
//                       key={String(item.id)}
//                       onClick={() => {
//                         if (viewMode) return;
//                         handleSidebarQuestion(idx);
//                       }}
//                       title={
//                         isAnswered ? "Question answered - Click to edit" : ""
//                       }
//                       style={{
//                         cursor: viewMode
//                           ? "not-allowed"
//                           : isAnswered
//                           ? "not-allowed"
//                           : "pointer",
//                         opacity: viewMode ? 0.6 : isAnswered ? 0.6 : 1,
//                       }}
//                     >
//                       {idx < questions.length - 1 && (
//                         <div className="sidebar-step-connector" />
//                       )}
//                       <div className="sidebar-step">
//                         <div className="sidebar-circle">
//                           {String(idx + 1).padStart(2, "0")}
//                           {isAnswered && <span className="checkmark">✓</span>}
//                         </div>
//                         <div
//                           className="sidebar-pill"
//                           title={item.title || item.text}
//                         >
//                           {item.title || item.text}
//                         </div>
//                       </div>
//                     </div>
//                   );
//                 })}
//               </div>
//             )}
//             <h2 className="sidebar-title mt">Foundation</h2>
//             <div className="sidebar-divider"></div>
//             <button
//               className="sidebar-item"
//               onClick={() => navigate("/foundation-questions")}
//             >
//               <div className="sidebar-num">01</div>
//               <div className="sidebar-label">Name your Brand</div>
//             </button>
//           </aside>

//           {/* MAIN */}
//           <main className="chat-main">
//             <div className="chat-center">
//               {viewMode && messages.length === 0 && (
//                 <div
//                   style={{
//                     margin: "48px auto",
//                     background: "rgba(44,12,33,0.7)",
//                     border: "1.5px solid #EC6251",
//                     borderRadius: "16px",
//                     color: "#ffafb9",
//                     padding: "32px",
//                     textAlign: "center",
//                     fontWeight: 600,
//                     fontSize: "1.1em",
//                     maxWidth: 420,
//                   }}
//                 >
//                   🚫 No questions have been answered yet. You have{" "}
//                   <span style={{ color: "#EC6251" }}>view-only</span> access.
//                 </div>
//               )}

//               {/* ✅ NEW: Show chat when all answered OR actively answering */}
//               {messages.length > 0 && messages.length >= questions.length ? (
//                 // All questions answered - show complete chat transcript
//                 <>
//                   {/* Chat transcript/history */}
//                   <div className="chat-messages">
//                     {messages.map((msg, i) => (
//                       <React.Fragment key={`${msg.qId}-${i}`}>
//                         {/* Bot bubble - Left aligned */}
//                         <div className="chat-bubble bot-bubble">
//                           <div className="bubble-content">{msg.question}</div>
//                         </div>
//                         {/* User bubble - Right aligned with Edit icon in corner */}
//                         <div className="chat-bubble user-bubble">
//                           {/* ✅ Pen icon in top corner */}
//                           {!viewMode && (
//                             <button
//                               className="edit-icon-btn"
//                               onClick={() => handleEditMessage(i)}
//                               title="Edit this answer"
//                             >
//                               ✎
//                             </button>
//                           )}

//                           <div className="bubble-content">{msg.answer}</div>
//                         </div>
//                       </React.Fragment>
//                     ))}
//                   </div>

//                   {/* Show completion message */}
//                   <div
//                     style={{
//                       textAlign: "center",
//                       marginTop: "40px",
//                       padding: "20px",
//                       color: "rgba(255, 255, 255, 0.6)",
//                       fontSize: "14px",
//                     }}
//                   >
//                     ✓ Assessment Complete - You can review and edit answers
//                     above
//                   </div>
//                 </>
//               ) : activeQuestionIdx === null ? (
//                 // Kickoff/intro - show only if no messages loaded yet
//                 <>
//                   <h1 className="main-title">
//                     "Alright, Superstar — this is where the real work starts"
//                   </h1>
//                   <p className="main-subtext">
//                     We're about to shape what your brand stands for, not just
//                     what it sells.
//                   </p>
//                   <p className="main-subtext-2">
//                     Forget fancy jargon or marketing fluff — I want honesty, raw
//                     purpose, and a bit of fire.
//                   </p>
//                   <h2 className="main-kickoff">
//                     Let's kick off. Choose one of these to start the journey.
//                   </h2>
//                   <div className="question-grid">
//                     {loading ? (
//                       <div
//                         style={{
//                           gridColumn: "1 / -1",
//                           textAlign: "center",
//                           color: "rgba(255,255,255,0.5)",
//                           padding: "40px",
//                           fontSize: "14px",
//                         }}
//                       >
//                         Loading questions...
//                       </div>
//                     ) : questions.length > 0 ? (
//                       questions.slice(0, 4).map((q, i) => (
//                         <button
//                           key={q.id}
//                           className="question-card"
//                           onClick={() => {
//                             if (viewMode) return;
//                             handleKickoffQuestion(i);
//                           }}
//                           disabled={viewMode}
//                           style={{
//                             cursor: viewMode ? "not-allowed" : "pointer",
//                             opacity: viewMode ? 0.6 : 1,
//                           }}
//                         >
//                           <span className="question-num">
//                             {String(i + 1).padStart(2, "0")}
//                           </span>
//                           <p className="question-text">{q.text}</p>
//                         </button>
//                       ))
//                     ) : (
//                       [
//                         {
//                           id: "fallback-1",
//                           text: 'What is your brand\'s core mission statement? (One sentence that captures "why" you exist.)',
//                         },
//                         {
//                           id: "fallback-2",
//                           text: 'List 3-5 core values that define your brand (e.g., "Innovation, Sustainability, Empathy"). Explain one briefly.',
//                         },
//                         {
//                           id: "fallback-3",
//                           text: "What problem in the world does your brand aim to solve?",
//                         },
//                         {
//                           id: "fallback-4",
//                           text: "How do you measure success beyond profits (e.g., impact metrics)?",
//                         },
//                       ].map((q, i) => (
//                         <button
//                           key={q.id}
//                           className="question-card"
//                           onClick={() => handleKickoffQuestion(i)}
//                         >
//                           <span className="question-num">
//                             {String(i + 1).padStart(2, "0")}
//                           </span>
//                           <p className="question-text">{q.text}</p>
//                         </button>
//                       ))
//                     )}
//                   </div>
//                 </>
//               ) : (
//                 // Currently answering - show chat with current question
//                 <>
//                   {/* Chat transcript/history */}
//                   <div className="chat-messages">
//                     {messages.map((msg, i) => (
//                       <React.Fragment key={`${msg.qId}-${i}`}>
//                         <div className="chat-bubble bot-bubble">
//                           <div className="bubble-content">{msg.question}</div>
//                         </div>
//                         <div className="chat-bubble user-bubble">
//                           {!viewMode && (
//                             <button
//                               className="edit-icon-btn"
//                               onClick={() => handleEditMessage(i)}
//                               title="Edit this answer"
//                             >
//                               ✎
//                             </button>
//                           )}

//                           <div className="bubble-content">{msg.answer}</div>
//                         </div>
//                       </React.Fragment>
//                     ))}
//                   </div>

//                   {/* Show current Q prompt */}
//                   {activeQuestionIdx < questions.length && (
//                     <>
//                       <div
//                         className="chat-question"
//                         style={{ margin: "36px 0 8px 0" }}
//                       >
//                         {editingMessageIdx !== null ? "Edit Answer" : ""}
//                         {questions[activeQuestionIdx].text}
//                       </div>
//                     </>
//                   )}
//                 </>
//               )}
//             </div>

//             {/* ✅ Only show input if still answering (not all completed) */}
//             {!viewMode &&
//               !(messages.length > 0 && messages.length >= questions.length) && (
//                 <div className="chat-input-wrap">
//                   <div className="chat-input">
//                     <input
//                       ref={fileInputRef}
//                       type="file"
//                       style={{ display: "none" }}
//                       onChange={onFileChange}
//                     />
//                     <button
//                       type="button"
//                       className="attachment-btn"
//                       onClick={openFilePicker}
//                     >
//                       {attachedFileName ? (
//                         <span className="attach-name">
//                           <img
//                             src={attachment}
//                             alt="Attachment"
//                             className="attach-icon"
//                           />
//                           <span className="attach-filename">
//                             {attachedFileName}
//                           </span>
//                           <button
//                             className="clear-attach"
//                             onClick={clearAttachment}
//                             aria-label="Remove attachment"
//                           >
//                             ✕
//                           </button>
//                         </span>
//                       ) : (
//                         <img
//                           src={attachment}
//                           alt="Attachment"
//                           className="attach-icon"
//                         />
//                       )}
//                     </button>
//                     <input
//                       type="text"
//                       value={inputValue}
//                       onChange={(e) => setInputValue(e.target.value)}
//                       onKeyDown={onKeyDown}
//                       placeholder={
//                         editingMessageIdx !== null
//                           ? "Update your answer..."
//                           : "Type your answer..."
//                       }
//                       className="chat-text-input"
//                     />
//                     <div className="chat-right-icons">
//                       <button className="icon-btn" title="Quick chat">
//                         <img
//                           src={chatIcon1}
//                           alt="Chat Icon 1"
//                           className="icon-small"
//                         />
//                         <div className="tip-bubble">
//                           Sharpen it the World-Famous way. Let David refine
//                           this.
//                         </div>
//                       </button>
//                       <div className="icon-wrap">
//                         <button
//                           className="icon-btn magic-pen-btn"
//                           onClick={handleSend}
//                         >
//                           <img
//                             src={chatIcon2}
//                             alt="Magic Pen"
//                             className="icon-small"
//                           />
//                         </button>
//                       </div>
//                     </div>
//                   </div>
//                 </div>
//               )}
//           </main>
//         </div>
//       </div>

//       {/* PLACE COMMENT MODAL HERE */}
//       {showCommentModal && (
//         <div
//           className="modal-overlay"
//           onClick={() => setShowCommentModal(false)}
//         >
//           <div className="modal-content" onClick={(e) => e.stopPropagation()}>
//             <h3>Add Comment</h3>
//             <textarea
//               value={commentText}
//               onChange={(e) => setCommentText(e.target.value)}
//               rows={5}
//               placeholder="Enter your comment here"
//             />
//             <div className="modal-actions">
//               <button
//                 onClick={() => setShowCommentModal(false)}
//                 disabled={commentLoading}
//               >
//                 Cancel
//               </button>
//               <button
//                 onClick={handleCommentSubmit}
//                 disabled={commentLoading || !commentText.trim()}
//               >
//                 {commentLoading ? "Saving..." : "Submit"}
//               </button>
//             </div>
//           </div>
//         </div>
//       )}
//     </>
//   );
// }

import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import "../components/ChatKickoffPage.css";
import ChatNavbar from "./ChatNavbar";
import attachment from "../assets/attachment.png";
import chatIcon1 from "../assets/chat-icon1.png";
import chatIcon2 from "../assets/chat-icon2.png";
import avatar from "../assets/ChatQuestionIcon.png";
import authService from "../services/authService";
import { downloadManifestoPdf } from "../utils/ManifestoPdfGenerator";
import { History } from "lucide-react";
import Confetti from "../components/Confetti";
import IdentityCompleteModal from "./IdentityCompleteModal";
import ThinkingPipeline from "../components/rag/ThinkingPipeline";
import SourceCards from "../components/rag/SourceCards";
import RetrievalDebugPanel from "../components/rag/RetrievalDebugPanel";
import StrategyTensionCard from "../components/rag/StrategyTensionCard";
import TypewriterText from "../components/rag/TypewriterText";
import useThinkingPipeline from "../hooks/useThinkingPipeline";
import { useOrbPresence } from "../context/OrbPresenceContext";

const AI_THINKING_STEPS = [
  "Understanding your positioning…",
  "Recalling manifesto principles…",
  "Analyzing differentiation patterns…",
  "Connecting strategic concepts…",
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

// Modal component to show chat history for a question
function ChatHistoryModal({
  isOpen,
  onClose,
  sessionId,
  questionId,
  questionTitle,
}) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !sessionId || !questionId) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    authService
      .getConversations(sessionId, questionId)
      .then((data) => {
        if (!cancelled) {
          setConversations(Array.isArray(data) ? data : data?.results || []);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load chat history");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isOpen, sessionId, questionId]);

  if (!isOpen) return null;

  return (
    <div className="chat-history-modal-overlay" onClick={onClose}>
      <div className="chat-history-modal" onClick={(e) => e.stopPropagation()}>
        <div className="chat-history-modal-header">
          <h3>Chat History</h3>
          <span className="chat-history-modal-subtitle">{questionTitle}</span>
          <button className="chat-history-modal-close" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="chat-history-modal-body">
          {loading ? (
            <div className="chat-history-loading">Loading conversations...</div>
          ) : error ? (
            <div className="chat-history-error">{error}</div>
          ) : conversations.length === 0 ? (
            <div className="chat-history-empty">
              No conversation history yet
            </div>
          ) : (
            <div className="chat-history-messages">
              {conversations.map((conv, idx) => (
                <div key={conv.id || idx} className="chat-history-item">
                  {conv.role === "user" || conv.sender === "user" ? (
                    <div className="history-user-msg">
                      {conv.message || conv.text || conv.content}
                    </div>
                  ) : (
                    <div className="history-bot-msg">
                      {conv.message || conv.text || conv.content}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ChatKickOffPage() {
  const navigate = useNavigate();
  const [attachedFileName, setAttachedFileName] = useState("");
  const fileInputRef = useRef(null);
  const savedSessionJson = localStorage.getItem("session");
  const initialSession = savedSessionJson ? JSON.parse(savedSessionJson) : null;
  const [session, setSession] = useState(initialSession);

  // State for API data
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [messages, setMessages] = useState([]); // [{ qId, question, answer }]
  const [activeQuestionIdx, setActiveQuestionIdx] = useState(null);
  const [inputValue, setInputValue] = useState("");
  const [editingMessageIdx, setEditingMessageIdx] = useState(null);

  const initialViewMode = localStorage.getItem("agencyViewMode") === "true";
  const [viewMode, setViewMode] = useState(initialViewMode);
  const isReadOnly = viewMode;

  const [showCommentModal, setShowCommentModal] = useState(false);
  const [commentText, setCommentText] = useState("");
  const [commentLoading, setCommentLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [refineLoading, setRefineLoading] = useState(false); // Separate state for refine button
  const [suggestionError, setSuggestionError] = useState(null);
  const [suggestions, setSuggestions] = useState([]); // Array of suggestion strings
  const [hoveredSuggestionIdx, setHoveredSuggestionIdx] = useState(null);
  const suggestionsDebounceRef = useRef(null);
  const hoverTimeoutRef = useRef(null);
  const suggestionSelectedRef = useRef(false); // Track if a suggestion was just selected

  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [finalizedQuestionIds, setFinalizedQuestionIds] = useState(
    () => new Set(),
  );
  const [isSessionComplete, setIsSessionComplete] = useState(false);
  const [manifestoGenerated, setManifestoGenerated] = useState(false);

  // NEW: chat timeline state
  const [chatMessages, setChatMessages] = useState([]);
  // each item: { role: "assistant" | "user", text: string, qId?: number }

  const [isAiDraft, setIsAiDraft] = useState(false);
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [typingText, setTypingText] = useState("");
  const [showRefinedPreview, setShowRefinedPreview] = useState(false);
  const [historyModalData, setHistoryModalData] = useState(null); // { questionId, questionTitle }
  const typewriterIntervalRef = useRef(null);
  const chatMessagesEndRef = useRef(null);
  const chatMessagesContainerRef = useRef(null);
  const manifestoAutoNavRef = useRef(null);

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
  const [retrievalDebug, setRetrievalDebug] = useState(null);
  const [strategicInsights, setStrategicInsights] = useState([]);
  const [retrievalConfidence, setRetrievalConfidence] = useState(null);
  const [ragEvaluation, setRagEvaluation] = useState(null);
  const thinkingMessage = useThinkingPipeline(isLoading, AI_THINKING_STEPS, 1500);

  const [showIdentityCompleteModal, setShowIdentityCompleteModal] =
    useState(false);

  // Accordion state - all closed by default
  const [openCategories, setOpenCategories] = useState({
    category1: false,
    category2: false,
    category3: false,
  });

  // Category completion tracking
  const [completedCategories, setCompletedCategories] = useState(new Set());
  const [showConfetti, setShowConfetti] = useState(false);
  const [confettiKey, setConfettiKey] = useState(0);

  const totalQuestions = questions.length || 0;
  const answeredCount = finalizedQuestionIds.size || 0;
  const progressPercent =
    totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0;
  const hasConversation = chatMessages.length > 0 || messages.length > 0;

  const IDENTITY_STAGE_NUM = 3;

  useEffect(() => {
    setViewMode(localStorage.getItem("agencyViewMode") === "true");
    return () => localStorage.removeItem("agencyViewMode");
  }, []);

  // Load questions from API on mount
  useEffect(() => {
    let cancelled = false;

    async function loadQuestions() {
      setLoading(true);
      setLoadError("");
      try {
        const list = await authService.getQuestions();
        if (cancelled) return;
        const arr = Array.isArray(list) ? list : [];
        const filtered = arr
          .filter(
            (q) =>
              q &&
              q.is_active !== false &&
              Number(q.stage) === Number(IDENTITY_STAGE_NUM),
          )
          .sort((a, b) => {
            const oa = Number(a.order ?? 0);
            const ob = Number(b.order ?? 0);
            if (oa !== ob) return oa - ob;
            return (a.id ?? 0) - (b.id ?? 0);
          })
          .map((q, i) => ({
            id: q.id ?? i,
            title: q.text ?? q.title ?? `Question ${i + 1}`,
            text: q.text ?? q.title ?? "",
            raw: q,
          }));
        setQuestions(filtered);
      } catch (err) {
        const errorMsg = err?.message || "Failed to load questions";
        setLoadError(errorMsg);
        toast.error(errorMsg);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadQuestions();

    return () => {
      cancelled = true;
    };
  }, []);

  // Function to reload all answers from backend - can be called after save
  const reloadAllAnswers = async () => {
    if (!Array.isArray(questions) || questions.length === 0) return null;

    const sessionId = localStorage.getItem("sessionId");
    if (!sessionId) return null;

    try {
      const remoteAnswers = await authService.getAnswers(sessionId, {});

      const answerMap = {};
      if (Array.isArray(remoteAnswers)) {
        remoteAnswers.forEach((answer) => {
          const questionId = answer.question;
          const answerText = answer.answer_text;

          const question = questions.find(
            (q) => q.id === questionId || q.raw?.id === questionId,
          );

          if (question && answerText && String(answerText).trim() !== "") {
            answerMap[question.id] = {
              qId: question.id,
              question: question.text,
              answer: answerText,
              isAiAccepted: Boolean(answer?.is_ai_accepted),
              aiSuggestion: answer?.ai_suggestion || "",
            };
          }
        });
      }

      const loadedMessages = Object.values(answerMap);
      setMessages(loadedMessages);

      // Mark these as finalized
      const finalized = new Set(loadedMessages.map((m) => m.qId));
      setFinalizedQuestionIds(finalized);

      // Build initial chat history as Q → A pairs
      const initialChat = [];
      loadedMessages.forEach((m) => {
        initialChat.push(
          {
            role: "assistant",
            text: m.question,
            qId: m.qId,
          },
          {
            role: "user",
            text: m.answer,
            qId: m.qId,
          },
        );
      });
      setChatMessages(initialChat);

      // If we already have answers for all questions, mark session complete
      if (questions.length > 0 && finalized.size >= questions.length) {
        setIsSessionComplete(true);
        // Show modal if all questions are completed
        const sessionId = localStorage.getItem("sessionId");
        if (sessionId) {
          authService.completeSession(sessionId).catch((err) => {
            console.warn("Failed to complete session:", err);
          });
        }
        // Show modal after a small delay to ensure state is updated
        setTimeout(() => {
          setShowIdentityCompleteModal(true);
        }, 500);
      }

      return finalized; // Return the finalized set for immediate use
    } catch (err) {
      console.warn("Failed to load existing answers:", err);
      return null;
    }
  };

  // Load existing answers when questions available
  useEffect(() => {
    let cancelled = false;

    async function loadExistingAnswers() {
      if (cancelled) return;
      await reloadAllAnswers();
    }

    loadExistingAnswers();

    return () => {
      cancelled = true;
    };
  }, [questions]);

  // Detect category completion and trigger confetti
  useEffect(() => {
    if (questions.length === 0 || finalizedQuestionIds.size === 0) return;

    const questionsPerCategory = 4;
    const categories = [
      {
        id: "category1",
        title: "Brand Perception",
        questions: questions.slice(0, questionsPerCategory),
      },
      {
        id: "category2",
        title: "Brand Identity",
        questions: questions.slice(
          questionsPerCategory,
          questionsPerCategory * 2,
        ),
      },
      {
        id: "category3",
        title: "Brand Vision",
        questions: questions.slice(
          questionsPerCategory * 2,
          questionsPerCategory * 3,
        ),
      },
    ];

    categories.forEach((category) => {
      const allQuestionsAnswered = category.questions.every((q) =>
        finalizedQuestionIds.has(q.id),
      );

      if (allQuestionsAnswered) {
        setCompletedCategories((prev) => {
          // Only trigger confetti if category wasn't already completed
          if (!prev.has(category.id)) {
            setShowConfetti(true);
            setConfettiKey((prevKey) => prevKey + 1);

            // Auto-hide confetti after animation
            setTimeout(() => {
              setShowConfetti(false);
            }, 4000);
          }
          return new Set([...prev, category.id]);
        });
      }
    });
  }, [finalizedQuestionIds, questions]);

  // Check if manifesto exists when session is available
  useEffect(() => {
    let cancelled = false;

    async function checkManifestoExists() {
      if (!session?.id) return;

      try {
        const response = await authService.getManifesto(session.id);
        // Check if manifesto data exists (could be in different formats)
        const hasManifesto =
          response &&
          (response.brandName ||
            response.coreBelief ||
            (typeof response === "object" && Object.keys(response).length > 0));
        if (!cancelled) {
          setManifestoGenerated(!!hasManifesto);
        }
      } catch (err) {
        // Manifesto doesn't exist yet, which is fine
        if (!cancelled) {
          setManifestoGenerated(false);
        }
      }
    }

    checkManifestoExists();

    return () => {
      cancelled = true;
    };
  }, [session?.id]);

  // Show modal if all questions are completed when page loads
  useEffect(() => {
    if (
      questions.length > 0 &&
      finalizedQuestionIds.size >= questions.length &&
      !showIdentityCompleteModal
    ) {
      // Mark session as complete if not already
      const sessionId = localStorage.getItem("sessionId");
      if (sessionId && !isSessionComplete) {
        authService.completeSession(sessionId).then(() => {
          setIsSessionComplete(true);
        }).catch((err) => {
          console.warn("Failed to complete session:", err);
        });
      }
      // Show modal after a small delay to ensure state is updated
      const timer = setTimeout(() => {
        setShowIdentityCompleteModal(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [questions.length, finalizedQuestionIds.size, showIdentityCompleteModal, isSessionComplete]);

  // Cleanup typewriter interval on unmount
  useEffect(() => {
    return () => {
      if (typewriterIntervalRef.current) {
        clearInterval(typewriterIntervalRef.current);
        typewriterIntervalRef.current = null;
      }
      if (manifestoAutoNavRef.current) {
        clearTimeout(manifestoAutoNavRef.current);
        manifestoAutoNavRef.current = null;
      }
    };
  }, []);

  // Auto-scroll to bottom when messages change or typing
  useEffect(() => {
    if (chatMessagesEndRef.current) {
      chatMessagesEndRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
      });
    }
  }, [chatMessages, typingText, isLoading, isAssistantTyping]);

  // Auto-scroll during typewriter effect (line by line)
  useEffect(() => {
    if (isAssistantTyping && typingText) {
      if (chatMessagesEndRef.current) {
        chatMessagesEndRef.current.scrollIntoView({
          behavior: "smooth",
          block: "nearest",
        });
      }
    }
  }, [typingText, isAssistantTyping]);

  // Debounced effect to fetch AI suggestions from API when user types
  useEffect(() => {
    // Skip API call if a suggestion was just selected
    if (suggestionSelectedRef.current) {
      suggestionSelectedRef.current = false; // Reset flag after skipping
      return;
    }

    // Clear previous timeout
    if (suggestionsDebounceRef.current) {
      clearTimeout(suggestionsDebounceRef.current);
    }

    // Don't show suggestions if:
    // - No active question
    // - Input is empty or too short
    // - View mode is active
    // - Session is complete
    if (
      activeQuestionIdx === null ||
      !inputValue.trim() ||
      inputValue.trim().length < 3 ||
      viewMode ||
      isSessionComplete
    ) {
      setSuggestions([]);
      setHoveredSuggestionIdx(null);
      return;
    }

    const q = questions[activeQuestionIdx];
    if (!q) return;

    const sessionId = localStorage.getItem("sessionId") || session?.id;
    if (!sessionId) {
      setSuggestions([]);
      return;
    }

    // Debounce the API call by 800ms
    suggestionsDebounceRef.current = setTimeout(async () => {
      // Double-check flag before making API call
      if (suggestionSelectedRef.current) {
        suggestionSelectedRef.current = false;
        return;
      }

      setSuggestionLoading(true);
      setSuggestionError(null);
      setSuggestions([]);
      setHoveredSuggestionIdx(null);

      try {
        const response = await authService.getAiAnswerSuggestions(
          sessionId,
          q.id,
          inputValue.trim(),
        );

        // Handle response - array or object with suggestions/suggestion property
        let suggestionList = [];
        if (Array.isArray(response)) {
          suggestionList = response;
        } else if (response && typeof response === "object") {
          suggestionList =
            response.suggestions ??
            response.suggestion ??
            (Array.isArray(response.results) ? response.results : []);
        }
        setSuggestions(Array.isArray(suggestionList) ? suggestionList : []);
      } catch (err) {
        console.error("AI suggestion error", err);
        setSuggestionError(err?.message || "Failed to get AI suggestions");
        setSuggestions([]);
      } finally {
        setSuggestionLoading(false);
      }
    }, 800);

    // Cleanup function
    return () => {
      if (suggestionsDebounceRef.current) {
        clearTimeout(suggestionsDebounceRef.current);
      }
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, [
    inputValue,
    activeQuestionIdx,
    questions,
    viewMode,
    isSessionComplete,
    session,
  ]);

  // ===== File attachment handlers =====
  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function onFileChange(e) {
    const f = e.target.files && e.target.files[0];
    if (f) setAttachedFileName(f.name);
    else setAttachedFileName("");
  }

  function clearAttachment(e) {
    e.stopPropagation();
    setAttachedFileName("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  // ===== Question navigation =====
  function handleSidebarQuestion(idx) {
    const q = questions[idx];
    if (!q) return;

    // Check if this question has an answer - if so, load it for editing
    const existingAnswer = messages.find((m) => m.qId === q.id);
    if (existingAnswer) {
      setEditingMessageIdx(messages.findIndex((m) => m.qId === q.id));
      setInputValue(existingAnswer.answer);
    } else {
      setEditingMessageIdx(null);
      setInputValue("");
    }

    setActiveQuestionIdx(idx);
    setFollowUpQuestion(""); // clear previous follow-up

    // Append the main question as assistant bubble if not already in chat
    const questionInChat = chatMessages.some(
      (m) => m.qId === q.id && m.role === "assistant",
    );
    if (!questionInChat) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: q.text,
          qId: q.id,
        },
      ]);
    }
  }

  function handleKickoffQuestion(idx) {
    const q = questions[idx];
    if (!q) return;

    setActiveQuestionIdx(idx);
    setInputValue("");
    setEditingMessageIdx(null);
    setFollowUpQuestion("");

    // Append the main question as assistant bubble
    setChatMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        text: q.text,
        qId: q.id,
      },
    ]);
  }

  // Handle Edit button click
  function handleEditMessage(i) {
    const msg = messages[i];
    if (!msg) return;

    setEditingMessageIdx(i);
    setInputValue(msg.answer);
    setIsAiDraft(false);
    const qIdx = questions.findIndex((q) => q.id === msg.qId);
    if (qIdx !== -1) {
      setActiveQuestionIdx(qIdx);
    }
    setFollowUpQuestion("");

    // Scroll to input area
    setTimeout(() => {
      const inputWrap = document.querySelector(".chat-input-wrap");
      if (inputWrap) {
        inputWrap.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }, 100);
  }

  // Handle Skip button - move to next question
  function handleSkip() {
    if (activeQuestionIdx === null || activeQuestionIdx === undefined) return;

    const nextIdx = activeQuestionIdx + 1;
    if (nextIdx < questions.length) {
      const nextQ = questions[nextIdx];
      setActiveQuestionIdx(nextIdx);
      setInputValue("");
      setEditingMessageIdx(null);
      setFollowUpQuestion("");

      // Reset textarea height
      const textarea = document.querySelector('.chat-input-wrap .chat-text-input');
      if (textarea) {
        textarea.style.height = 'auto';
      }

      // Always add the next question as a new chat bubble (even if it was shown before)
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: nextQ.text,
          qId: nextQ.id,
        },
      ]);

      // Scroll to the newly added question after a short delay
      setTimeout(() => {
        if (chatMessagesEndRef.current) {
          chatMessagesEndRef.current.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
          });
        }
      }, 100);
    }
  }

  // Handle Return button - move to previous question
  function handleReturn() {
    if (activeQuestionIdx === null || activeQuestionIdx === undefined) return;

    const prevIdx = activeQuestionIdx - 1;
    if (prevIdx >= 0) {
      const prevQ = questions[prevIdx];
      setActiveQuestionIdx(prevIdx);
      setInputValue("");
      setEditingMessageIdx(null);
      setFollowUpQuestion("");

      // Always add the previous question as a new chat bubble (similar to Skip)
      // This ensures it appears as a new bubble even if it was shown before
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: prevQ.text,
          qId: prevQ.id,
        },
      ]);

      // Scroll to the newly added question after a short delay
      setTimeout(() => {
        if (chatMessagesEndRef.current) {
          chatMessagesEndRef.current.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
          });
        }
      }, 100);
    }
  }

  // ===== Magic Pen (AI refine draft) =====
  async function handleSend() {
    if (viewMode) return;

    // Prevent sending if a message is currently being processed or typed
    if (
      isLoading ||
      isAssistantTyping ||
      chatMessages.some((m) => m.pending || m.isTyping)
    ) {
      toast.info("Please wait for the previous message to finish processing.");
      return;
    }

    const rawText = inputValue; // keep original text
    const trimmed = rawText.trim();
    if (!trimmed) return;

    const q = questions[activeQuestionIdx];
    if (!q) {
      toast.info("Select a question first.");
      return;
    }

    const sessionId = localStorage.getItem("sessionId") || session?.id;
    if (!sessionId) {
      toast.error("Session ID not found");
      return;
    }

    const realQuestionId = q.raw?.id ?? q.id;

    // If editing, save directly to backend using session_answer_create API
    if (editingMessageIdx !== null) {
      setIsLoading(true);
      try {
        // Save answer using the upsert API endpoint
        await authService.createAnswer(sessionId, {
          question: Number(realQuestionId),
          answer_text: trimmed,
        });

        // Update the message in state
        setMessages((prev) => {
          const updated = [...prev];
          updated[editingMessageIdx] = {
            ...updated[editingMessageIdx],
            answer: trimmed,
          };
          return updated;
        });

        // Ensure this question is marked as finalized (in case it wasn't before)
        if (!finalizedQuestionIds.has(q.id)) {
          setFinalizedQuestionIds((prev) => {
            const next = new Set(prev);
            next.add(q.id);
            return next;
          });
        }

        // Update chat messages if in active chat - only update finalized messages
        setChatMessages((prev) => {
          const updated = [...prev];
          let lastUserIdx = -1;
          for (let i = updated.length - 1; i >= 0; i--) {
            if (updated[i].qId === q.id && updated[i].role === "user") {
              lastUserIdx = i;
              break;
            }
          }
          if (lastUserIdx !== -1) {
            updated[lastUserIdx] = {
              ...updated[lastUserIdx],
              text: trimmed,
            };
          }
          return updated;
        });

        toast.success("Answer updated successfully!");
        setEditingMessageIdx(null);
        setInputValue("");
        setIsLoading(false);
        return;
      } catch (err) {
        setIsLoading(false);
        console.error("Failed to update answer:", err);
        toast.error(err?.message || "Failed to update answer");
        return;
      }
    }

    // Clear the input immediately so UI removes text when user clicks
    setInputValue("");
    setIsAiDraft(false); // user action -> not an AI-only draft

    // Show user message immediately in chatbox before API call
    if (editingMessageIdx === null) {
      setChatMessages((prev) => [
        ...prev,
        { role: "user", text: trimmed, qId: q.id, pending: true },
      ]);
    }

    setIsLoading(true);
    setOrbThinking("Thinking…");
    setOrbRetrieving("Retrieving brand knowledge…");

    try {
      let aiResp = null;
      let orbResp = null;
      let improved = trimmed;
      let followUp = "";
      let acceptedAiDraft = false;
      let orbStatus = "";

      try {
        const orbQId = resolveOrbQuestionId(q, activeQuestionIdx);
        orbResp = await authService.submitBrandGodFatherAnswer({
          sourceSessionId: sessionId,
          qId: orbQId,
          answer: trimmed,
          contextData: {
            frontend_page: "ChatKickOffPage",
            question_id: realQuestionId,
            question_text: q.text,
            question_bank: {
              [orbQId]: q.text,
            },
          },
        });
        followUp = formatOrbCoachReply(orbResp);
        orbStatus = String(orbResp?.status || "").toUpperCase();
        setOrbMemory(
          `ORB ${orbStatus || "checked"} · next ${orbResp?.next_q_id || "hold"} · depth ${orbResp?.depth_score ?? "n/a"}`,
        );
      } catch (orbError) {
        console.warn("BrandGodFather ORB unavailable, using draft fallback", orbError);
        toast.info("ORB engine unavailable right now; using fallback coaching response.");
        aiResp = await authService.aiSuggestionDraft(
          sessionId,
          realQuestionId,
          trimmed,
          isAiDraft,
        );
        improved = (aiResp?.improved_answer || trimmed).trim();
        followUp = (aiResp?.follow_up_question || "").trim();
        acceptedAiDraft = improved !== trimmed || isAiDraft;
      }

      const sources = aiResp?.sources || [];
      const concepts = aiResp?.graph_concepts || [];
      setRagSources(sources);
      setGraphConcepts(concepts);
      setRetrievalDebug(aiResp?.retrieval_debug || null);
      setStrategicInsights(aiResp?.strategic_insights || []);
      setRetrievalConfidence(aiResp?.retrieval_confidence || null);
      setRagEvaluation(aiResp?.evaluation || null);
      setOrbSources(sources);
      setOrbGraphConcepts(concepts);
      if (sources.length) {
        setOrbMemory("ORB connected concepts");
      }

      // Update per-question latest answer
      setMessages((prev) => {
        const updated = [...prev];
        const idx = updated.findIndex((m) => m.qId === q.id);

        if (idx !== -1) {
          updated[idx] = {
            ...updated[idx],
            question: q.text,
            answer: improved,
            isAiAccepted: acceptedAiDraft,
            aiSuggestion: acceptedAiDraft ? improved : "",
            originalAnswer: acceptedAiDraft ? trimmed : "",
            orbStatus,
            orbReply: orbResp?.reply || "",
            orbNextQId: orbResp?.next_q_id || null,
            orbDepthScore: orbResp?.depth_score ?? null,
            brandGodFatherSessionId: orbResp?.brandgodfather_session_id || null,
          };
        } else {
          updated.push({
            qId: q.id,
            question: q.text,
            answer: improved,
            isAiAccepted: acceptedAiDraft,
            aiSuggestion: acceptedAiDraft ? improved : "",
            originalAnswer: acceptedAiDraft ? trimmed : "",
            orbStatus,
            orbReply: orbResp?.reply || "",
            orbNextQId: orbResp?.next_q_id || null,
            orbDepthScore: orbResp?.depth_score ?? null,
            brandGodFatherSessionId: orbResp?.brandgodfather_session_id || null,
          });
        }

        return updated;
      });

      // 🔧 Update existing user bubble (pending or edit mode) - keep original user text
      setChatMessages((prev) => {
        const updated = [...prev];

        // find **last** user message for this question
        let lastUserIdx = -1;
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].qId === q.id && updated[i].role === "user") {
            lastUserIdx = i;
            break;
          }
        }

        if (lastUserIdx !== -1) {
          // Keep user's original text, just remove pending state
          updated[lastUserIdx] = {
            ...updated[lastUserIdx],
            pending: false,
          };
        } else {
          // Fallback: append as new message with original text
          updated.push({
            role: "user",
            text: trimmed,
            qId: q.id,
          });
        }

        return updated;
      });

      // Note: Don't auto-save here - user needs to click Save button to finalize
      // This keeps the conversation flow separate from saved answers
      // The answer is stored in messages state but not finalized until Save is clicked

      setIsLoading(false);
      setEditingMessageIdx(null);
      setIsAiDraft(false);
      setFollowUpQuestion(followUp);

      // Typewriter effect for follow-up question
      if (followUp) {
        // Clear any existing typewriter interval
        if (typewriterIntervalRef.current) {
          clearInterval(typewriterIntervalRef.current);
          typewriterIntervalRef.current = null;
        }

        setIsAssistantTyping(true);
        setOrbSpeaking();
        setTypingText("");

        // Add placeholder for typing message
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "",
            qId: q.id,
            isTyping: true,
            orbStatus,
            orbNextQId: orbResp?.next_q_id || null,
            orbDepthScore: orbResp?.depth_score ?? null,
          },
        ]);

        let charIndex = 0;
        const typeInterval = setInterval(() => {
          if (charIndex < followUp.length) {
            setTypingText(followUp.slice(0, charIndex + 1));
            charIndex++;
            // Auto-scroll during typing (line by line)
            if (chatMessagesEndRef.current) {
              chatMessagesEndRef.current.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
              });
            }
          } else {
            clearInterval(typeInterval);
            typewriterIntervalRef.current = null;
            setIsAssistantTyping(false);
            setOrbIdle();
            setTypingText("");
            // Replace typing message with final text
            setChatMessages((prev) => {
              const updated = [...prev];
              const typingIdx = updated.findIndex((m) => m.isTyping);
              if (typingIdx !== -1) {
                updated[typingIdx] = {
                  role: "assistant",
                  text: followUp,
                  qId: q.id,
                  orbStatus,
                  orbNextQId: orbResp?.next_q_id || null,
                  orbDepthScore: orbResp?.depth_score ?? null,
                };
              }
              return updated;
            });
            // Final scroll after message is complete
            setTimeout(() => {
              if (chatMessagesEndRef.current) {
                chatMessagesEndRef.current.scrollIntoView({
                  behavior: "smooth",
                  block: "nearest",
                });
              }
            }, 100);
          }
        }, 20);
        typewriterIntervalRef.current = typeInterval;
      }
    } catch (err) {
      setIsLoading(false);
      setOrbIdle();
      console.error("AI suggestion or send failed", err);
      toast.error(err?.message || "Failed to send answer (AI error).");

      // Fallback: still push the raw user text to chat + messages
      setMessages((prev) => {
        const updated = [...prev];
        const idx = updated.findIndex((m) => m.qId === q.id);

        if (idx !== -1) {
          updated[idx] = {
            ...updated[idx],
            question: q.text,
            answer: trimmed,
          };
        } else {
          updated.push({
            qId: q.id,
            question: q.text,
            answer: trimmed,
          });
        }

        return updated;
      });

      // Update pending message in fallback (remove pending state)
      setChatMessages((prev) => {
        const updated = [...prev];
        let lastUserIdx = -1;
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].qId === q.id && updated[i].role === "user") {
            lastUserIdx = i;
            break;
          }
        }

        if (lastUserIdx !== -1) {
          updated[lastUserIdx] = {
            ...updated[lastUserIdx],
            text: trimmed,
            pending: false,
          };
        } else {
          updated.push({
            role: "user",
            text: trimmed,
            qId: q.id,
          });
        }

        return updated;
      });

      setEditingMessageIdx(null);
      setIsAiDraft(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      // Prevent sending if a message is currently being processed
      if (
        !isLoading &&
        !isAssistantTyping &&
        !chatMessages.some((m) => m.pending || m.isTyping)
      ) {
        handleSend();
      }
    }
  }

  // ===== Save button: persist latest answer + maybe complete session =====
  const handleSave = async () => {
    if (viewMode || isSessionComplete) return;

    const sessionId = localStorage.getItem("sessionId") || session?.id;
    if (!sessionId) {
      toast.error("Session ID not found");
      return;
    }

    // 1. Work out which question we’re saving
    let qIdx = activeQuestionIdx;

    if (qIdx === null || qIdx === undefined || qIdx < 0) {
      // fallback: use last answered question
      if (messages.length === 0) {
        toast.info("No answer to save yet.");
        return;
      }
      const lastMsg = messages[messages.length - 1];
      qIdx = questions.findIndex((q) => q.id === lastMsg.qId);
      if (qIdx === -1) {
        toast.info("No matching question found to save.");
        return;
      }
    }

    const q = questions[qIdx];
    if (!q) {
      toast.info("No question selected to save.");
      return;
    }

    // 2. Get the latest answer for this question
    const latestForQuestion = [...messages]
      .reverse()
      .find((m) => m.qId === q.id);

    if (!latestForQuestion || !latestForQuestion.answer?.trim()) {
      toast.info("Write and refine an answer before saving.");
      return;
    }

    if (String(latestForQuestion.orbStatus || "").toUpperCase() === "REJECT") {
      toast.info("ORB rejected this answer. Go deeper before saving it.");
      return;
    }

    const finalText = latestForQuestion.answer.trim();
    const wasAiAccepted = Boolean(latestForQuestion.isAiAccepted);

    try {
      // 3. Save answer to backend
      await authService.createAnswer(sessionId, {
        question: Number(q.id),
        answer_text: finalText,
        is_ai_accepted: wasAiAccepted,
        ai_suggestion: wasAiAccepted ? latestForQuestion.aiSuggestion || finalText : undefined,
        original_ai_text: latestForQuestion.originalAnswer || "",
      });

      // 4. Reload all answers from backend to refresh the entire component
      const finalized = await reloadAllAnswers();

      if (finalized) {
        const allFinal =
          questions.length > 0 && finalized.size >= questions.length;

        // if (allFinal) {
        //   await authService.completeSession(sessionId);
        //   setIsSessionComplete(true);
        //   setFollowUpQuestion("");
        //   toast.success("Assessment completed and saved!");
        //   return;
        // }

        if (allFinal) {
          await authService.completeSession(sessionId);
          setIsSessionComplete(true);
          setFollowUpQuestion("");
          toast.success("Assessment completed and saved!");
          // 🆕 Show achievement popup
          setShowIdentityCompleteModal(true);
          return;
        }

        toast.success("Answer saved for this question.");

        // Find the next NOT-finalized question
        const nextIdx = questions.findIndex(
          (question) => !finalized.has(question.id),
        );

        if (nextIdx !== -1) {
          const nextQ = questions[nextIdx];

          // move active index
          setActiveQuestionIdx(nextIdx);
          setFollowUpQuestion("");
          setInputValue("");

          // Push the *next* question into the chat
          setChatMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              text: nextQ.text,
              qId: nextQ.id,
            },
          ]);
        }
      } else {
        toast.success("Answer saved for this question.");
      }
    } catch (err) {
      console.error("Save or complete failed", err);
      toast.error(err?.message || "Failed to save answer.");
    }
  };

  // ----------------------------
  // Generate manifesto (NO DOWNLOAD or open)
  // ----------------------------
  const handleGenerateManifesto = async () => {
    if (!session?.id) {
      toast.error("Session ID not found");
      return;
    }

    try {
      toast.info("Generating manifesto… please wait...");
      const genResp = await authService.generateManifesto(session.id);

      console.log("generateManifesto response:", genResp);

      // Check if manifesto was successfully generated
      if (
        genResp?.ai_output?.manifesto ||
        genResp?.ai_output?.json_output ||
        genResp?.ai_output?.data
      ) {
        setManifestoGenerated(true);
      }

      toast.success("Manifesto generated successfully!");
    } catch (error) {
      console.error("Generate manifesto failed:", error);
      toast.error(error?.message || "Failed to generate manifesto");
    }
  };

  const handleDownloadPdf = async () => {
    try {
      const data = await authService.getManifesto(session.id);
      await downloadManifestoPdf(data, session.title || "BrandManifesto");
      toast.success("Manifesto PDF downloaded!");
    } catch (err) {
      toast.error("PDF download failed");
      console.error(err);
    }
  };

  const handleDownloadManifesto = async () => {
    if (!session?.id) {
      toast.error("Session ID not found");
      return;
    }
    try {
      const blob = await authService.downloadManifesto(session.id);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "manifesto.pdf");
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      toast.success("Manifesto PDF download started");
    } catch (error) {
      toast.error(error.message || "Failed to download manifesto");
    }
  };

  // ===== Quick Refine button (optional extra AI on current draft in input) =====
  const handleQuickRefine = async () => {
    if (viewMode || isSessionComplete) return;

    const sessionId = localStorage.getItem("sessionId") || session?.id;
    if (!sessionId) {
      toast.error("Session ID not found for AI suggestion");
      return;
    }

    // figure out which question we're working on
    let qIdx = activeQuestionIdx;
    if (qIdx === null || qIdx === undefined || qIdx < 0) {
      if (messages.length === 0) {
        toast.info("Select a question first to get a suggestion.");
        return;
      }
      const lastMsg = messages[messages.length - 1];
      qIdx = questions.findIndex((q) => q.id === lastMsg.qId);
      if (qIdx === -1) {
        toast.info("Select a question first to get a suggestion.");
        return;
      }
    }

    const q = questions[qIdx];
    if (!q) {
      toast.info("Select a question first to get a suggestion.");
      return;
    }

    const existingForQuestion = [...messages]
      .reverse()
      .find((m) => m.qId === q.id);

    const currentDraft = inputValue || existingForQuestion?.answer || "";

    if (!currentDraft.trim()) {
      toast.info("Write something first so I can refine it.");
      return;
    }

    setRefineLoading(true);
    setSuggestionError(null);

    try {
      const realQuestionId = q.raw?.id ?? q.id;

      const resp = await authService.aiSuggestionDraft(
        sessionId,
        realQuestionId,
        currentDraft,
        true,
      );

      const improved = (resp?.improved_answer || currentDraft).trim();
      const followUp = (resp?.follow_up_question || "").trim();

      if (resp?.rewrite_blocked || improved === currentDraft.trim()) {
        setInputValue(currentDraft);
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

      // Put the refined text back in the input box for user to review
      setInputValue(improved);
      setIsAiDraft(true);

      toast.success(
        "AI refined your text — review it and click Send when ready.",
      );
    } catch (err) {
      console.error("AI suggestion error", err);
      setSuggestionError(err?.message || "AI suggestion failed");
      toast.error(err?.message || "AI suggestion failed");
    } finally {
      setRefineLoading(false);
    }
  };

  // ==== Render =====
  return (
    <>
      <ChatNavbar
        sessionId={session?.id}
        onDownloadPdf={handleDownloadPdf}
        onSave={handleSave}
        onGenerate={handleGenerateManifesto}
        // onDownloadPdf={handleDownloadManifesto}
        showSaveButton={true}
        showDownloadButton={manifestoGenerated}
        showLogoutButton={true}
        showCommentButton={true}
        onCommentClick={() => {
          setCurrentSessionId(session?.id);
          setShowCommentModal(true);
        }}
        canGenerate={isSessionComplete}
      />

      <div className="chat-root">
        <div className="chat-body">
          {/* SIDEBAR */}
          <aside className="chat-sidebar">
            <h2 className="sidebar-title">Brand Manifesto</h2>
            <div className="sidebar-divider"></div>
            {loading ? (
              <div
                style={{
                  padding: 12,
                  color: "rgba(255,255,255,0.5)",
                  fontSize: 13,
                }}
              >
                Loading questions...
              </div>
            ) : loadError ? (
              <div style={{ color: "#ffb3b3", padding: 12, fontSize: 13 }}>
                {loadError}
              </div>
            ) : questions.length === 0 ? (
              <div
                style={{
                  padding: 12,
                  color: "rgba(255,255,255,0.5)",
                  fontSize: 13,
                }}
              >
                No questions found for Identity stage.
              </div>
            ) : (
              <div className="sidebar-categories">
                {(() => {
                  // Group questions into 3 categories (4 questions each)
                  const questionsPerCategory = 4;
                  const categories = [
                    {
                      id: "category1",
                      title: "Brand Perception",
                      questions: questions.slice(0, questionsPerCategory),
                      startIdx: 0,
                    },
                    {
                      id: "category2",
                      title: "Brand Identity",
                      questions: questions.slice(
                        questionsPerCategory,
                        questionsPerCategory * 2,
                      ),
                      startIdx: questionsPerCategory,
                    },
                    {
                      id: "category3",
                      title: "Brand Vision",
                      questions: questions.slice(
                        questionsPerCategory * 2,
                        questionsPerCategory * 3,
                      ),
                      startIdx: questionsPerCategory * 2,
                    },
                  ];

                  return categories.map((category) => {
                    const isOpen = openCategories[category.id];
                    const hasQuestions = category.questions.length > 0;
                    const allQuestionsAnswered = category.questions.every((q) =>
                      finalizedQuestionIds.has(q.id),
                    );
                    const isCompleted =
                      completedCategories.has(category.id) ||
                      allQuestionsAnswered;

                    return (
                      <div
                        key={category.id}
                        className={`sidebar-category ${isCompleted ? "category-completed" : ""}`}
                      >
                        <button
                          className={`sidebar-category-header ${isCompleted ? "completed" : ""}`}
                          onClick={(e) => {
                            // Add click animation
                            e.currentTarget.style.transform =
                              "translateX(2px) scale(0.98)";
                            setTimeout(() => {
                              e.currentTarget.style.transform = "";
                            }, 200);
                            setOpenCategories((prev) => ({
                              ...prev,
                              [category.id]: !prev[category.id],
                            }));
                          }}
                          disabled={!hasQuestions}
                          onMouseEnter={(e) => {
                            if (hasQuestions) {
                              e.currentTarget.style.transform =
                                "translateX(2px)";
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (hasQuestions) {
                              e.currentTarget.style.transform = "";
                            }
                          }}
                        >
                          <span className="category-title">
                            {category.title}
                            {isCompleted && (
                              <span className="category-checkmark"> ✓</span>
                            )}
                          </span>
                          <span
                            className={`category-arrow ${isOpen ? "open" : ""}`}
                          >
                            {isOpen ? "▼" : "▶"}
                          </span>
                        </button>
                        {isOpen && hasQuestions && (
                          <div className="sidebar-category-content">
                            {category.questions.map((item, localIdx) => {
                              const globalIdx = category.startIdx + localIdx;
                              const isAnswered = finalizedQuestionIds.has(
                                item.id,
                              );

                              return (
                                <div
                                  key={String(item.id)}
                                  className={`sidebar-step-row${
                                    activeQuestionIdx === globalIdx
                                      ? " selected"
                                      : ""
                                  }${isAnswered ? " answered" : ""}`}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (viewMode) return;
                                    // Add click animation
                                    e.currentTarget.style.transform =
                                      "translateX(8px) scale(0.98)";
                                    setTimeout(() => {
                                      e.currentTarget.style.transform = "";
                                    }, 200);
                                    handleSidebarQuestion(globalIdx);
                                  }}
                                  onMouseEnter={(e) => {
                                    if (!viewMode) {
                                      e.currentTarget.style.transform =
                                        "translateX(6px)";
                                    }
                                  }}
                                  onMouseLeave={(e) => {
                                    if (
                                      !viewMode &&
                                      activeQuestionIdx !== globalIdx
                                    ) {
                                      e.currentTarget.style.transform = "";
                                    }
                                  }}
                                  title={
                                    isAnswered
                                      ? "Question answered - Click to edit"
                                      : ""
                                  }
                                  style={{
                                    cursor: viewMode
                                      ? "not-allowed"
                                      : "pointer",
                                    opacity: viewMode ? 0.6 : 1,
                                  }}
                                >
                                  {localIdx < category.questions.length - 1 && (
                                    <div className="sidebar-step-connector" />
                                  )}
                                  <div className="sidebar-step">
                                    <div className="sidebar-circle">
                                      {String(globalIdx + 1).padStart(2, "0")}
                                      {isAnswered && (
                                        <span className="checkmark">✓</span>
                                      )}
                                    </div>
                                    <div
                                      className="sidebar-pill"
                                      title={item.title || item.text}
                                    >
                                      {item.title || item.text}
                                    </div>
                                  </div>
                                  <button
                                    className="chat-history-btn-hover"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      // Add click animation
                                      e.currentTarget.style.transform =
                                        "translateY(-50%) scale(0.9) rotate(-5deg)";
                                      setTimeout(() => {
                                        e.currentTarget.style.transform = "";
                                      }, 200);
                                      setHistoryModalData({
                                        questionId: item.id,
                                        questionTitle: item.title || item.text,
                                      });
                                    }}
                                    title="View chat history"
                                    onMouseEnter={(e) => {
                                      e.currentTarget.style.transform =
                                        "translateY(-50%) scale(1.15) rotate(5deg)";
                                    }}
                                    onMouseLeave={(e) => {
                                      e.currentTarget.style.transform = "";
                                    }}
                                  >
                                    <History size={14} />
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  });
                })()}
              </div>
            )}
            {isSessionComplete && (
              <>
                <h2 className="sidebar-title mt">Next steps</h2>
                <div className="sidebar-divider"></div>
                <button
                  className="sidebar-item sidebar-item-deepdive"
                  onClick={() => navigate("/DeepDivePage")}
                  title="Answer 10 optional questions to sharpen your brand's edge"
                >
                  <div className="sidebar-num">✦</div>
                  <div className="sidebar-label">
                    Deep Dive <span className="sidebar-optional">(optional)</span>
                  </div>
                </button>
              </>
            )}
            <h2 className="sidebar-title mt">Foundation</h2>
            <div className="sidebar-divider"></div>
            <button
              className="sidebar-item"
              onClick={() => navigate("/foundation-questions")}
            >
              <div className="sidebar-num">01</div>
              <div className="sidebar-label">Brand Information</div>
            </button>
          </aside>

          {/* MAIN */}
          <main className="chat-main">
            {!loading && totalQuestions > 0 && (
              <div className="chat-progress-compact">
                <div className="chat-progress-header">
                  <span className="chat-progress-label">
                    Brand Manifesto Progress
                  </span>
                  <span className="chat-progress-meta">
                    {answeredCount} / {totalQuestions} answered ·{" "}
                    {progressPercent}% done
                  </span>
                </div>

                <div className="chat-progress-track">
                  <div
                    className="chat-progress-fill"
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            )}
            <div
              className={`chat-center ${
                activeQuestionIdx === null && !hasConversation
                  ? "kickoff-mode"
                  : ""
              }`}
            >
              {viewMode && messages.length === 0 && (
                <div
                  style={{
                    margin: "48px auto",
                    background: "rgba(44,12,33,0.7)",
                    border: "1.5px solid #EC6251",
                    borderRadius: "16px",
                    color: "#ffafb9",
                    padding: "32px",
                    textAlign: "center",
                    fontWeight: 600,
                    fontSize: "1.1em",
                    maxWidth: 420,
                  }}
                >
                  🚫 No questions have been answered yet. You have{" "}
                  <span style={{ color: "#EC6251" }}>view-only</span> access.
                </div>
              )}

              {isSessionComplete ? (
                <>
                  <div className="chat-messages">
                    {messages.map((msg, i) => (
                      <React.Fragment key={`${msg.qId}-${i}`}>
                        <div className="chat-bubble bot-bubble">
                          <div className="bot-avatar">
                            <img src={avatar} alt="Bot Icon" />
                          </div>
                          <div className="bubble-content">{msg.question}</div>
                        </div>
                        <div className="chat-bubble user-bubble">
                          {!viewMode && (
                            <button
                              className="edit-icon-btn"
                              onClick={() => handleEditMessage(i)}
                              title="Edit this answer"
                            >
                              ✎
                            </button>
                          )}
                          <div className="bubble-content">{msg.answer}</div>
                        </div>
                      </React.Fragment>
                    ))}
                  </div>


                  {/* Show input when editing in completed session */}
                  {!viewMode && editingMessageIdx !== null && (
                    <div className="chat-input-wrap">
                      <div className="chat-input">
                        <input
                          type="text"
                          value={inputValue}
                          onChange={(e) => {
                            setInputValue(e.target.value);
                            setIsAiDraft(false);
                          }}
                          onKeyDown={onKeyDown}
                          placeholder="Update your answer..."
                          className="chat-text-input"
                        />
                        <div className="chat-right-icons">
                          <div className="icon-wrap">
                            <button
                              className="icon-btn magic-pen-btn"
                              onClick={handleSend}
                              disabled={isLoading || isAssistantTyping}
                              title="Save changes"
                            >
                              <img
                                src={chatIcon2}
                                alt="Save"
                                className="icon-small"
                              />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : !hasConversation && activeQuestionIdx === null ? (
                <>
                  <h1 className="main-title">
                    "Alright, Superstar — this is where the real work starts"
                  </h1>
                  <p className="main-subtext">
                    We're about to shape what your brand stands for, not just
                    what it sells.
                  </p>
                  <p className="main-subtext-2">
                    Forget fancy jargon or marketing fluff — I want honesty, raw
                    purpose, and a bit of fire.
                  </p>
                  <h2 className="main-kickoff">
                    Let's kick off. Choose one of these to start the journey.
                  </h2>
                  <div className="question-grid">
                    {loading ? (
                      <div
                        style={{
                          gridColumn: "1 / -1",
                          textAlign: "center",
                          color: "rgba(255,255,255,0.5)",
                          padding: "40px",
                          fontSize: "14px",
                        }}
                      >
                        Loading questions...
                      </div>
                    ) : questions.length > 0 ? (
                      questions.slice(0, 4).map((q, i) => (
                        <button
                          key={q.id}
                          className={`question-card ${activeQuestionIdx === i ? "selected" : ""}`}
                          onClick={(e) => {
                            if (viewMode) return;
                            e.currentTarget.style.transform = "scale(0.98)";
                            setTimeout(() => {
                              e.currentTarget.style.transform = "";
                            }, 150);
                            handleKickoffQuestion(i);
                          }}
                          disabled={viewMode}
                          style={{
                            cursor: viewMode ? "not-allowed" : "pointer",
                            opacity: viewMode ? 0.6 : 1,
                          }}
                          onMouseEnter={(e) => {
                            if (!viewMode) {
                              e.currentTarget.style.transform =
                                "translateY(-2px)";
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!viewMode && activeQuestionIdx !== i) {
                              e.currentTarget.style.transform = "";
                            }
                          }}
                        >
                          <span className="question-num">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <p className="question-text">{q.text}</p>
                        </button>
                      ))
                    ) : (
                      [
                        {
                          id: "fallback-1",
                          text: 'What is your brand\'s core mission statement? (One sentence that captures "why" you exist.)',
                        },
                        {
                          id: "fallback-2",
                          text: 'List 3-5 core values that define your brand (e.g., "Innovation, Sustainability, Empathy"). Explain one briefly.',
                        },
                        {
                          id: "fallback-3",
                          text: "What problem in the world does your brand aim to solve?",
                        },
                        {
                          id: "fallback-4",
                          text: "How do you measure success beyond profits (e.g., impact metrics)?",
                        },
                      ].map((q, i) => (
                        <button
                          key={q.id}
                          className="question-card"
                          onClick={() => handleKickoffQuestion(i)}
                        >
                          <span className="question-num">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          <p className="question-text">{q.text}</p>
                        </button>
                      ))
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="chat-messages" ref={chatMessagesContainerRef}>
                    {isLoading && (
                      <ThinkingPipeline message={thinkingMessage} visible />
                    )}
                    {chatMessages.map((m, i) => {
                      const isUser = m.role === "user";
                      const isLastMessage = i === chatMessages.length - 1;
                      // Check if this question has an answer (finalized or not)
                      const isFinalized =
                        m.qId && finalizedQuestionIds.has(m.qId);
                      const hasAnswer = messages.some(
                        (msg) => msg.qId === m.qId && msg.answer?.trim()
                      );
                      // Find corresponding message index for edit functionality
                      let messageIdx = -1;
                      if (isUser && (isFinalized || hasAnswer) && !m.pending && !m.isTyping) {
                        // Find the message that matches this question ID
                        messageIdx = messages.findIndex(
                          (msg) => msg.qId === m.qId,
                        );
                      }
                      // Show edit button if message has an answer (finalized or not)
                      const canEdit =
                        isUser &&
                        (isFinalized || hasAnswer) &&
                        messageIdx !== -1 &&
                        !viewMode &&
                        !m.pending &&
                        !m.isTyping &&
                        m.text &&
                        m.text.trim() !== "";

                      // Show navigation buttons on last message (only if not typing/pending)
                      const showNavButtons =
                        isLastMessage &&
                        !m.pending &&
                        !m.isTyping &&
                        !viewMode &&
                        !isSessionComplete &&
                        activeQuestionIdx !== null;
                      const canSkip =
                        showNavButtons &&
                        activeQuestionIdx < questions.length - 1;
                      const canReturn = showNavButtons && activeQuestionIdx > 0;

                      return (
                        <React.Fragment key={i}>
                          <div
                            className={`chat-bubble ${
                              isUser ? "user-bubble" : "bot-bubble"
                            }`}
                          >
                            {!isUser && (
                              <div className="bot-avatar">
                                {m.pending || m.isTyping ? (
                                  <span className="rotating-star-avatar">
                                    ⭐
                                  </span>
                                ) : (
                                  <img src={avatar} alt="Bot Icon" />
                                )}
                              </div>
                            )}

                            {canEdit && (
                              <button
                                className="edit-icon-btn"
                                onClick={(e) => {
                                  e.currentTarget.style.transform =
                                    "scale(0.9) rotate(0deg)";
                                  setTimeout(() => {
                                    e.currentTarget.style.transform = "";
                                  }, 200);
                                  handleEditMessage(messageIdx);
                                }}
                                title="Edit this answer"
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.transform =
                                    "scale(1.2) rotate(15deg)";
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.transform = "";
                                }}
                              >
                                ✎
                              </button>
                            )}

                            <div className="bubble-content">
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
                                  .map((para, idx) => <p key={idx}>{para}</p>)
                              )}
                            </div>
                          </div>

                          {/* Navigation buttons - only on last message, placed beneath the bubble */}
                          {showNavButtons && (
                            <div
                              className={`chat-nav-buttons ${isUser ? "user-nav-buttons" : "bot-nav-buttons"}`}
                            >
                              {canReturn && (
                                <button
                                  className="nav-btn return-btn"
                                  onClick={(e) => {
                                    e.currentTarget.style.transform =
                                      "translateY(-2px) scale(0.95)";
                                    setTimeout(() => {
                                      e.currentTarget.style.transform = "";
                                    }, 200);
                                    handleReturn();
                                  }}
                                  title="Previous question"
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.transform =
                                      "translateY(-2px)";
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = "";
                                  }}
                                >
                                  ← Return
                                </button>
                              )}
                              {canSkip && (
                                <button
                                  className="nav-btn skip-btn"
                                  onClick={(e) => {
                                    e.currentTarget.style.transform =
                                      "translateY(-2px) scale(0.95)";
                                    setTimeout(() => {
                                      e.currentTarget.style.transform = "";
                                    }, 200);
                                    handleSkip();
                                  }}
                                  title="Next question"
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.transform =
                                      "translateY(-2px)";
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = "";
                                  }}
                                >
                                  Skip →
                                </button>
                              )}
                            </div>
                          )}
                        </React.Fragment>
                      );
                    })}
                    {isLoading &&
                      !chatMessages.some((m) => m.isTyping) &&
                      !suggestionLoading && (
                        <div className="chat-bubble bot-bubble">
                          <div className="bot-avatar">
                            <span className="rotating-star-avatar">⭐</span>
                          </div>
                          <div className="bubble-content">
                            <div className="typing-loader">
                              <span></span>
                              <span></span>
                              <span></span>
                            </div>
                          </div>
                        </div>
                      )}
                    {strategicInsights.length > 0 && (
                      <StrategyTensionCard insights={strategicInsights} />
                    )}
                    {!isLoading && ragSources.length > 0 && (
                      <SourceCards
                        sources={ragSources}
                        graphConcepts={graphConcepts}
                        retrievalConfidence={retrievalConfidence}
                        evaluation={ragEvaluation}
                      />
                    )}
                    {retrievalDebug && (
                      <RetrievalDebugPanel
                        debug={retrievalDebug}
                        insights={strategicInsights}
                      />
                    )}
                    <div ref={chatMessagesEndRef} />
                  </div>
                </>
              )}
            </div>

            {!isReadOnly && !isSessionComplete && (
              <>
                {/* AI Suggestions: render in portal so they are not clipped by chat-center overflow */}
                {(suggestions.length > 0 || suggestionLoading) &&
                  createPortal(
                    <>
                      {suggestions.length > 0 && (
                        <div className="suggestions-container">
                          <div className="suggestions-header">
                            <span className="suggestions-title">
                              💡 AI Suggestions
                            </span>
                            <button
                              className="suggestions-close-btn"
                              onClick={() => setSuggestions([])}
                              aria-label="Close suggestions"
                            >
                              ✕
                            </button>
                          </div>
                          <div
                            className="suggestions-grid"
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
                                hoveredSuggestionIdx !== null &&
                                hoveredSuggestionIdx !== idx;

                              return (
                                <div
                                  key={idx}
                                  className={`suggestion-card ${isHovered ? "suggestion-card-hovered" : ""} ${isHidden ? "suggestion-card-hidden" : ""}`}
                                  onClick={(e) => {
                                    e.currentTarget.style.transform =
                                      "translateY(-3px) scale(0.98)";
                                    setTimeout(() => {
                                      e.currentTarget.style.transform = "";
                                    }, 200);
                                    suggestionSelectedRef.current = true;
                                    setInputValue(suggestion);
                                    setSuggestions([]);
                                    setIsAiDraft(true);
                                    setHoveredSuggestionIdx(null);
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
                                  <div className="suggestion-content">
                                    {suggestion}
                                  </div>
                                  <div className="suggestion-footer">
                                    <span className="suggestion-hint">
                                      Click to use
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      {suggestionLoading && (
                        <div className="suggestions-loading">
                          <div className="suggestions-loading-spinner"></div>
                          <span>Generating suggestions...</span>
                        </div>
                      )}
                    </>,
                    document.body
                  )}
                <div className="chat-input-wrap">
                  <div className="chat-input">
                    <input
                      ref={fileInputRef}
                      type="file"
                      style={{ display: "none" }}
                      onChange={onFileChange}
                    />
                    <button
                      type="button"
                      className="attachment-btn"
                      onClick={openFilePicker}
                    >
                      {attachedFileName ? (
                        <span className="attach-name">
                          <img
                            src={attachment}
                            alt="Attachment"
                            className="attach-icon"
                          />
                          <span className="attach-filename">
                            {attachedFileName}
                          </span>
                          <button
                            className="clear-attach"
                            onClick={clearAttachment}
                            aria-label="Remove attachment"
                          >
                            ✕
                          </button>
                        </span>
                      ) : (
                        <img
                          src={attachment}
                          alt="Attachment"
                          className="attach-icon"
                        />
                      )}
                    </button>
                    <textarea
                      value={inputValue}
                      onChange={(e) => {
                        setInputValue(e.target.value);
                        setIsAiDraft(false); // 👈 user changed text, no longer "pure AI draft"
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
                        editingMessageIdx !== null
                          ? "Update your answer..."
                          : "Type your answer..."
                      }
                      className="chat-text-input"
                      disabled={
                        isLoading ||
                        isAssistantTyping ||
                        chatMessages.some((m) => m.pending || m.isTyping)
                      }
                      rows={1}
                    />
                    <div className="chat-right-icons">
                      {isAiDraft && inputValue.length > 100 && (
                        <button
                          className="icon-btn preview-btn"
                          title="Preview full text"
                          onClick={() => setShowRefinedPreview(true)}
                          style={{ fontSize: 12, padding: "4px 8px" }}
                        >
                          👁 Preview
                        </button>
                      )}
                      <button
                        className={`icon-btn refine-btn ${refineLoading ? "loading" : ""}`}
                        title="Quick chat"
                        onClick={(e) => {
                          if (viewMode || refineLoading) return;
                          e.currentTarget.style.transform = "scale(0.9)";
                          setTimeout(() => {
                            e.currentTarget.style.transform = "";
                          }, 200);
                          handleQuickRefine();
                        }}
                        disabled={viewMode || refineLoading}
                        style={{ position: "relative" }}
                        onMouseEnter={(e) => {
                          if (!viewMode && !refineLoading) {
                            e.currentTarget.style.transform = "scale(1.1)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = "";
                        }}
                      >
                        <img
                          src={chatIcon1}
                          alt="Chat Icon 1"
                          className={`icon-small ${refineLoading ? "icon-hidden" : ""}`}
                        />
                        {refineLoading && (
                          <div className="modern-spinner"></div>
                        )}
                        <div className="tip-bubble">
                          Sharpen it the World-Famous way. Let David refine
                          this.
                        </div>
                      </button>
                      <div className="icon-wrap">
                        <button
                          className="icon-btn magic-pen-btn"
                          onClick={(e) => {
                            if (
                              isLoading ||
                              isAssistantTyping ||
                              chatMessages.some((m) => m.pending || m.isTyping)
                            )
                              return;
                            e.currentTarget.style.transform = "scale(0.9)";
                            setTimeout(() => {
                              e.currentTarget.style.transform = "";
                            }, 200);
                            handleSend();
                          }}
                          disabled={
                            isLoading ||
                            isAssistantTyping ||
                            chatMessages.some((m) => m.pending || m.isTyping)
                          }
                          title={
                            isLoading ||
                            isAssistantTyping ||
                            chatMessages.some((m) => m.pending || m.isTyping)
                              ? "Please wait for the previous message to finish"
                              : "Send message"
                          }
                          onMouseEnter={(e) => {
                            if (
                              !isLoading &&
                              !isAssistantTyping &&
                              !chatMessages.some((m) => m.pending || m.isTyping)
                            ) {
                              e.currentTarget.style.transform = "scale(1.1)";
                            }
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.transform = "";
                          }}
                        >
                          <img
                            src={chatIcon2}
                            alt="Magic Pen"
                            className="icon-small"
                          />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
          </main>
        </div>
      </div>

      {/* REFINED TEXT PREVIEW MODAL */}
      {showRefinedPreview && (
        <div
          className="modal-overlay"
          onClick={() => setShowRefinedPreview(false)}
        >
          <div
            className="modal-content preview-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h3>AI Refined Text Preview</h3>
            <div className="preview-text-content">
              {inputValue.split(/\n\s*\n/).map((para, idx) => (
                <p key={idx}>{para}</p>
              ))}
            </div>
            <div className="modal-actions">
              <button onClick={() => setShowRefinedPreview(false)}>
                Close
              </button>
              <button
                onClick={() => {
                  setShowRefinedPreview(false);
                  handleSend();
                }}
              >
                Send Message
              </button>
            </div>
          </div>
        </div>
      )}

      {/* COMMENT MODAL */}
      {showCommentModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowCommentModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Add Comment</h3>
            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              rows={5}
              placeholder="Enter your comment here"
            />
            <div className="modal-actions">
              <button
                onClick={() => setShowCommentModal(false)}
                disabled={commentLoading}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!commentText.trim() || !currentSessionId) return;
                  setCommentLoading(true);
                  try {
                    await authService.addComment(currentSessionId, {
                      comment: commentText.trim(),
                    });
                    toast.success("Comment saved successfully!");
                    setShowCommentModal(false);
                    setCommentText("");
                  } catch (error) {
                    toast.error(error.message || "Failed to save comment");
                  } finally {
                    setCommentLoading(false);
                  }
                }}
                disabled={commentLoading || !commentText.trim()}
              >
                {commentLoading ? "Saving..." : "Submit"}
              </button>
            </div>
          </div>
        </div>
      )}

      <IdentityCompleteModal
        isOpen={showIdentityCompleteModal}
        onClose={() => {
          setShowIdentityCompleteModal(false);
        }}
        onDeepDive={() => {
          setShowIdentityCompleteModal(false);
          navigate("/DeepDivePage");
        }}
        onManifesto={() => {
          setShowIdentityCompleteModal(false);
          navigate("/manifesto");
        }}
      />

      {/* CHAT HISTORY MODAL */}
      <ChatHistoryModal
        isOpen={!!historyModalData}
        onClose={() => setHistoryModalData(null)}
        sessionId={session?.id}
        questionId={historyModalData?.questionId}
        questionTitle={historyModalData?.questionTitle}
      />

      {/* CONFETTI ANIMATION */}
      <Confetti
        key={confettiKey}
        show={showConfetti}
        onComplete={() => setShowConfetti(false)}
      />
    </>
  );
}
