// // src/pages/FoundationQuestionScreen.jsx
// import React, { useEffect, useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
// import "../components/FoundationQuestionScreen.css";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";
// import ChatUnlockModal from "../components/ChatUnlockModal";
// // <-- import the modal

// export default function FoundationQuestionScreen() {
//   const navigate = useNavigate();

//   // Load any pre-existing session from localStorage
//   const savedSessionJson = localStorage.getItem("session");
//   const savedSessionId = localStorage.getItem("sessionId");
//   const initialSession = savedSessionJson
//     ? JSON.parse(savedSessionJson)
//     : savedSessionId
//       ? { id: savedSessionId }
//       : null;

//   const [session, setSession] = useState(initialSession);
//   // 3. *Now* you can safely create sessionId and storageKey using current state
//   const sessionId = (session && (session.id || session.pk)) || savedSessionId;
//   const inputRef = useRef(null);
//   // Add this useEffect right here:
//   useEffect(() => {
//     async function checkAndStartSession() {
//       if (session && session.status === "draft") {
//         try {
//           await authService.startSession(session.id);
//           // Refresh session with updated status from backend
//           // You can re-fetch session from backend or update state accordingly
//           const updatedSessions = await authService.getSessions();
//           const updatedSession = updatedSessions.find(
//             (s) => s.id === session.id,
//           );
//           if (updatedSession) {
//             setSession(updatedSession);
//             // Also update localStorage if used elsewhere
//             localStorage.setItem("session", JSON.stringify(updatedSession));
//           }
//         } catch (error) {
//           console.error("Failed to start session:", error);
//         }
//       }
//     }
//     checkAndStartSession();
//   }, [session]);
//   const storageKey = sessionId
//     ? `foundationAnswers_${sessionId}`
//     : "foundationAnswers";
//   // Questions loaded from API (state)
//   const [questions, setQuestions] = useState([
//     {
//       id: "01",
//       key: "brandName",
//       question: "Q.1. What is your brand's name?",
//       description:
//         "Your name isn't just what people call your business — it's what they remember you by.",
//       placeholder: "Enter your brand name...",
//       raw: { text: "What is your brand's name?" },
//     },
//   ]);
//   const [questionsLoading, setQuestionsLoading] = useState(true);
//   const [questionsError, setQuestionsError] = useState("");

//   // Agencies dropdown state (modal)
//   const [agencies, setAgencies] = useState([]);
//   const [selectedAgency, setSelectedAgency] = useState(0);
//   const [agenciesLoading, setAgenciesLoading] = useState(false);
//   const [agenciesError, setAgenciesError] = useState("");

//   const [showTitleModal, setShowTitleModal] = useState(!initialSession);

//   const [modalTitle, setModalTitle] = useState("");
//   const [modalTouched, setModalTouched] = useState(false);
//   const [modalLoading, setModalLoading] = useState(false);
//   const [modalError, setModalError] = useState("");

//   const [currentStep, setCurrentStep] = useState(0);

//   // NEW: show unlock modal after final submit
//   // const [showUnlockModal, setShowUnlockModal] = useState(false);
//   // useEffect(() => {
//   //   // When there is no blocking modal, keep the answer input focused
//   //   if (!showTitleModal && !showUnlockModal && inputRef.current) {
//   //     inputRef.current.focus();
//   //     // Optional: select existing text so user can just start typing
//   //     // inputRef.current.select();
//   //   }
//   // }, [currentStep, showTitleModal, showUnlockModal]);
//   useEffect(() => {
//   if (!showTitleModal && inputRef.current) {
//     inputRef.current.focus();
//   }
// }, [currentStep, showTitleModal]);

//   // Answers stored in localStorage
//   const [answers, setAnswers] = useState(() => {
//     try {
//       const raw = localStorage.getItem(storageKey);
//       return raw ? JSON.parse(raw) : { brandName: "" };
//     } catch {
//       return { brandName: "" };
//     }
//   });
//   // Validation/error on submit
//   const [submitError, setSubmitError] = useState("");

//   useEffect(() => {
//     let cancelled = false;
//     const FOUNDATION_STAGE = 1; // Adjust if needed

//     async function loadQuestions() {
//       setQuestionsLoading(true);
//       setQuestionsError("");
//       try {
//         const list = await authService.getQuestions(); // Or your correct service reference
//         if (cancelled) return;

//         const foundation = Array.isArray(list)
//           ? list.filter((q) => String(q.stage) === String(FOUNDATION_STAGE))
//           : [];

//         const mapped =
//           foundation.length > 0
//             ? foundation.map((q, idx) => ({
//                 id: String(q.id).padStart(2, "0"),
//                 key: `q_${q.id}`,
//                 question: `Q.${idx + 1}. ${q.text}`,
//                 description: q.help_text ?? "",
//                 placeholder: q.placeholder ?? "",
//                 raw: q,
//               }))
//             : [
//                 {
//                   id: "01",
//                   key: "brandName",
//                   question: "Q.1. What is your brand's name?",
//                   description:
//                     "Your name isn't just what people call your business — it's what they remember you by.",
//                   placeholder: "Enter your brand name...",
//                   raw: { text: "What is your brand's name?" },
//                 },
//               ];

//         if (!cancelled) setQuestions(mapped);
//       } catch (err) {
//         console.error("getQuestions error:", err);
//         if (!cancelled)
//           setQuestionsError(err?.message || "Failed to load questions");
//       } finally {
//         if (!cancelled) setQuestionsLoading(false);
//       }
//     }

//     loadQuestions();
//     return () => {
//       cancelled = true;
//     };
//   }, []);

//   // -------- Load questions from API on mount --------
//   useEffect(() => {
//     let cancelled = false;

//     async function loadExistingAnswers() {
//       if (!Array.isArray(questions) || questions.length === 0) return;
//       // Get sessionId
//       const sessionId =
//         (session && (session.id || session.pk)) ||
//         localStorage.getItem("sessionId");

//       if (!sessionId) return;
//       try {
//         // Get the current questionId and answer (if needed)
//         const currentQ = questions[currentStep];
//         const apiQuestionId = currentQ?.raw?.id ?? currentQ?.raw?.pk ?? null;
//         const value = (currentQ?.key && answers[currentQ.key]) || "";

//         // Pass the payload expected by your backend.
//         const payload = {
//           question: apiQuestionId,
//           answer_text: value, // If required - otherwise omit this field
//         };

//         const remoteAnswers = await authService.getAnswers(sessionId, payload);

//         if (cancelled) return;
//         // Build map: questionId -> UI key
//         const idToKey = {};
//         questions.forEach((q) => {
//           const qid = q?.raw?.id ?? q?.raw?.pk ?? null;
//           if (qid != null) idToKey[String(qid)] = q.key;
//         });
//         // Merge remote answers into state
//         setAnswers((prev) => {
//           const next = { ...prev };
//           (Array.isArray(remoteAnswers) ? remoteAnswers : []).forEach((a) => {
//             const qid = a.question;
//             const key = idToKey[String(qid)] || `q_${qid}`;
//             if (
//               typeof a.answer_text === "string" &&
//               a.answer_text.trim() !== ""
//             ) {
//               next[key] = a.answer_text;
//             }
//           });
//           localStorage.setItem(storageKey, JSON.stringify(next));
//           return next;
//         });
//       } catch (err) {
//         console.warn("Failed to load existing answers:", err);
//       }
//     }

//     loadExistingAnswers();
//     return () => {
//       cancelled = true;
//     };
//   }, [session, questions]);

//   // Prefill brandName from session if empty
//   useEffect(() => {
//     if (!session) return;
//     const title = session.title || session.name || "";
//     if (title && (!answers.brandName || answers.brandName.trim() === "")) {
//       const next = { ...answers, brandName: title };
//       setAnswers(next);
//       localStorage.setItem(storageKey, JSON.stringify(next));
//     }
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, [session]);

//   // Fetch agencies when the title modal opens
//   useEffect(() => {
//     if (!showTitleModal) return;

//     let cancelled = false;
//     const load = async () => {
//       setAgenciesLoading(true);
//       setAgenciesError("");
//       try {
//         const list = await authService.getAgencies();
//         if (cancelled) return;
//         const normalized = Array.isArray(list) ? list : [];
//         setAgencies(normalized);
//         if (normalized.length > 0) {
//           const id = normalized[0].id ?? normalized[0].pk ?? 0;
//           setSelectedAgency(id);
//         } else {
//           setSelectedAgency(0);
//         }
//       } catch (err) {
//         console.error("getAgencies error:", err);
//         if (!cancelled)
//           setAgenciesError(err.message || "Failed to load agencies");
//       } finally {
//         if (!cancelled) setAgenciesLoading(false);
//       }
//     };
//     load();
//     return () => {
//       cancelled = true;
//     };
//   }, [showTitleModal]);

//   const updateAnswer = (key, value) => {
//     setAnswers((prev) => {
//       const next = { ...prev, [key]: value };
//       localStorage.setItem(storageKey, JSON.stringify(next));
//       return next;
//     });
//   };

//   // Helper: check all questions answered (non-empty)
//   const allAnswered = () => {
//     if (!Array.isArray(questions) || questions.length === 0) return false;
//     return questions.every((q) => {
//       const val = answers[q.key];
//       return val !== undefined && val !== null && String(val).trim() !== "";
//     });
//   };

//   const handleNext = async () => {
//     setSubmitError("");
//     const currentQ = questions[currentStep];
//     const key = currentQ?.key;
//     const value = (key && answers[key]) || "";

//     // Validate
//     if (!value || String(value).trim() === "") {
//       setSubmitError("Please answer before continuing.");
//       return;
//     }

//     // Save this answer to backend if possible
//     const sessionId =
//       (session && (session.id || session.pk)) ||
//       localStorage.getItem("sessionId");
//     const apiQuestionId = currentQ?.raw?.id ?? currentQ?.raw?.pk ?? null;

//     if (sessionId && apiQuestionId) {
//       try {
//         await authService.createAnswer(sessionId, {
//           question: Number(apiQuestionId),
//           answer_text: String(value),
//         });
//       } catch (err) {
//         setSubmitError(
//           err?.message || "Failed to save answer. Please try again.",
//         );
//         return;
//       }
//     }

//     if (currentStep < questions.length - 1) {
//       setCurrentStep((s) => s + 1);
//       return;
//     }

//     if (!allAnswered()) {
//       setSubmitError("Please answer all questions before continuing.");
//       return;
//     }

//     // Optionally: submit all answers again to API for safety
//     try {
//       if (sessionId) {
//         const promises = questions
//           .map((q) => {
//             const qid = q?.raw?.id ?? q?.raw?.pk ?? null;
//             const val = answers[q.key];
//             if (!qid || val == null || String(val).trim() === "") return null;
//             return authService.createAnswer(sessionId, {
//               question: Number(qid),
//               answer_text: String(val),
//             });
//           })
//           .filter(Boolean);
//         if (promises.length > 0) await Promise.all(promises);
//       }
//     } catch (err) {
//       // Don't block on minor failures
//     }

//     try {
//       localStorage.setItem(storageKey, JSON.stringify(answers));
//     } catch {}
//     // setShowUnlockModal(true);
//     // Go to Brand Summary page after final submit
// navigate("/brand-summary");

//   };

//   const handleBack = () => {
//     if (currentStep > 0) setCurrentStep((s) => s - 1);
//     else navigate(-1);
//   };

//   // Modal handlers (title modal already implemented below)
//   const isModalTitleValid = modalTitle.trim().length > 0;

//   const handleModalSubmit = async (e) => {
//     e?.preventDefault?.();
//     setModalTouched(true);
//     setModalError("");
//     setSession(sessionObj);
//     setShowTitleModal(false);
//     const titleVal = sessionObj.title || modalTitle.trim();
//     setAnswers({ brandName: "" });
//     localStorage.setItem(storageKey, JSON.stringify({ brandName: "" }));
//     if (!isModalTitleValid) return;

//     setModalLoading(true);
//     try {
//       const payload = {
//         title: modalTitle.trim(),
//         agency: Number(selectedAgency) || null,
//       };

//       const data = await authService.createSession(payload);

//       let sessionObj = null;
//       if (data?.session) sessionObj = data.session;
//       else if (data?.id || data?.title || data?.name) sessionObj = data;
//       else sessionObj = { title: modalTitle.trim() };

//       try {
//         localStorage.setItem("session", JSON.stringify(sessionObj));
//         if (sessionObj.id) localStorage.setItem("sessionId", sessionObj.id);
//       } catch {}

//       setSession(sessionObj);
//       setShowTitleModal(false);
//       const titleVal = sessionObj.title || modalTitle.trim();
//       setAnswers((prev) => {
//         const next = {
//           ...prev,
//           brandName: prev.brandName?.trim() ? prev.brandName : titleVal,
//         };
//         localStorage.setItem(storageKey, JSON.stringify(next));
//         return next;
//       });
//     } catch (err) {
//       console.error("createSession error:", err);
//       const message = err?.message || "Failed to create session. Try again.";
//       setModalError(message);
//     } finally {
//       setModalLoading(false);
//     }
//   };

//   // Hide title modal if session becomes available
//   useEffect(() => {
//     if (session) setShowTitleModal(false);
//   }, [session]);

//   // Save answers handler
//   const handleSave = () => {
//     try {
//       localStorage.setItem(storageKey, JSON.stringify(answers));
//       console.log("Saved answers:", answers);
//     } catch (error) {
//       console.error("Save error:", error);
//     }
//   };

//   // Render pill number
//   const renderPill = (idx) => <div className="pill-content">{idx + 1}</div>;

//   const currentQuestion = questions[currentStep] || questions[0];
//   const currentValue = answers[currentQuestion.key] ?? "";

//   const answeredCount = questions.filter(
//     (q) => answers[q.key] && answers[q.key].trim() !== "",
//   ).length;

//   const totalCount = questions.length;

//   return (
//     <>
//       <ChatNavbar
//         onSave={handleSave}
//         showSaveButton={false}
//         showDownloadButton={false}
//         showLogoutButton={true}
//       />

//       {/* <div
//         className={`fqs-app ${showTitleModal ? "modal-open" : ""} ${
//           showUnlockModal ? "modal-open" : ""
//         }`}
//       > */}
//       <div className={`fqs-app ${showTitleModal ? "modal-open" : ""}`}>

//         {/* TITLE MODAL (unchanged) */}
//         {showTitleModal && (
//           <div className="title-modal-overlay">
//             <div className="title-modal" role="dialog" aria-modal="true">
//               <h3>Give your session a title</h3>
//               <p className="modal-sub">
//                 This will be used as your session name and prefills the first
//                 question.
//               </p>

//               <form onSubmit={handleModalSubmit} className="modal-form">
//                 <input
//                   className="modal-input"
//                   placeholder="Enter a title for this session"
//                   value={modalTitle}
//                   onChange={(e) => setModalTitle(e.target.value)}
//                   onBlur={() => setModalTouched(true)}
//                   disabled={modalLoading}
//                   autoFocus
//                 />

//                 <label
//                   style={{
//                     color: "rgba(255,255,255,0.6)",
//                     fontSize: 13,
//                     marginTop: 4,
//                   }}
//                 >
//                   Agency (Optional)
//                 </label>

//                 {agenciesLoading ? (
//                   <div
//                     style={{
//                       padding: "10px 12px",
//                       color: "rgba(255,255,255,0.6)",
//                     }}
//                   >
//                     Loading agencies...
//                   </div>
//                 ) : agenciesError ? (
//                   <div style={{ color: "#ffb3b3", fontSize: 13 }}>
//                     {agenciesError}
//                   </div>
//                 ) : (
//                   <select
//                     className="modal-input"
//                     value={selectedAgency}
//                     onChange={(e) => setSelectedAgency(Number(e.target.value))}
//                     disabled={modalLoading}
//                     style={{ appearance: "none", WebkitAppearance: "none" }}
//                   >
//                     <option value={0}>-- No Agency --</option>
//                     {agencies.map((a) => {
//                       const id = a.id ?? a.pk ?? a.value ?? a.key ?? 0;
//                       const label =
//                         a.name ?? a.title ?? a.label ?? `Agency ${id}`;
//                       return (
//                         <option key={String(id)} value={id}>
//                           {label}
//                         </option>
//                       );
//                     })}
//                   </select>
//                 )}

//                 {modalTouched && !isModalTitleValid && (
//                   <div className="modal-validation">
//                     Please enter a session title
//                   </div>
//                 )}
//                 {modalError && <div className="modal-error">{modalError}</div>}

//                 <div className="modal-actions">
//                   <button
//                     type="button"
//                     className="modal-cancel"
//                     onClick={() => navigate(-1)}
//                     disabled={modalLoading}
//                   >
//                     Cancel
//                   </button>
//                   <button
//                     type="submit"
//                     className="modal-submit"
//                     disabled={
//                       !isModalTitleValid || modalLoading || agenciesLoading
//                     }
//                   >
//                     {modalLoading ? "Creating..." : "Create Session"}
//                   </button>
//                 </div>
//               </form>
//             </div>
//           </div>
//         )}

//         {/* LEFT SIDEBAR */}
//         <aside
//           className="fqs-left"
//           // aria-hidden={showTitleModal || showUnlockModal}
//           aria-hidden={showTitleModal}

//         >
//           <div className="fqs-left-inner">
//             <div className="fqs-intro">
//               <h1>
//                 Every great brand begins with you.
//                 <br />
//                 Eight questions. One honest minute. Ready?
//               </h1>
//             </div>

//             <nav className="fqs-left-nav">
//               {questions.map((it, i) => (
//                 <div
//                   key={it.id}
//                   className={`fqs-nav-row ${currentStep === i ? "active" : ""}`}
//                   onClick={() => setCurrentStep(i)}
//                   title={it.raw?.text ?? it.question}
//                 >
//                   <div className="fqs-nav-num">
//                     {String(i + 1).padStart(2, "0")}
//                   </div>
//                   <div className="fqs-nav-label">
//                     {i === 0
//                       ? "Brand Name"
//                       : (it.raw?.text ?? it.question).replace(
//                           /^Q\.\d+\.\s*/,
//                           "",
//                         )}
//                   </div>
//                 </div>
//               ))}
//             </nav>
//           </div>
//         </aside>

//         {/* MAIN CONTENT */}
//         <main
//           className="fqs-main"
//           // aria-hidden={showTitleModal || showUnlockModal}
//           aria-hidden={showTitleModal}

//         >
//           <div className="fqs-glow-left" />
//           <div className="fqs-card-wrapper">
//             <div className="fqs-card glow_wrapper">
//               <div class="glow-circle"></div>
//               <div class="glow-circle second"></div>
//               <div className="content">
//                 <h2 className="fqs-title">Get Started!</h2>

//                 {/* <div className="fqs-stepper">
//                   {questions.map((q, idx) => (
//                     <React.Fragment key={q.id}>
//                       <div
//                         className={`fqs-pill ${
//                           idx === currentStep ? "pill-active" : ""
//                         }`}
//                       >
//                         {renderPill(idx)}
//                       </div>
//                       {idx < questions.length - 1 && (
//                         <div className="fqs-stepline" />
//                       )}
//                     </React.Fragment>
//                   ))}
//                 </div> */}
//                 <div className="fqs-stepper">
//                   {questions.map((q, idx) => (
//                     <React.Fragment key={q.id}>
//                       <div
//                         className={`fqs-pill ${
//                           idx === currentStep ? "pill-active" : ""
//                         }`}
//                         onClick={() => setCurrentStep(idx)}
//                         style={{ cursor: "pointer" }}
//                         title={`Go to Question ${idx + 1}`}
//                       >
//                         {renderPill(idx)}
//                       </div>
//                       {idx < questions.length - 1 && (
//                         <div className="fqs-stepline" />
//                       )}
//                     </React.Fragment>
//                   ))}
//                 </div>

//                 <div className="fqs-question">
//                   <h3 className="fqs-q">{currentQuestion.question}</h3>
//                   <p className="fqs-desc">{currentQuestion.description}</p>
//                 </div>

//                 <div className="fqs-input-area">
//                   <input
//                     ref={inputRef}
//                     className="fqs-input"
//                     placeholder={currentQuestion.placeholder}
//                     value={currentValue}
//                     onChange={(e) =>
//                       updateAnswer(currentQuestion.key, e.target.value)
//                     }
//                   />
//                 </div>

//                 {submitError && (
//                   <div className="submit-error">{submitError}</div>
//                 )}

//                 <div className="fqs-footer">
//                   <button
//                     className={`fqs-back ${
//                       currentStep === 0 ? "disabled" : ""
//                     }`}
//                     onClick={handleBack}
//                     disabled={currentStep === 0}
//                   >
//                     Back
//                   </button>
//                   <button className="fqs-next" onClick={handleNext}>
//                     {currentStep < questions.length - 1 ? "Next" : "Submit"}
//                   </button>
//                 </div>
//               </div>
//             </div>
//             {/* <div className="fqs-progress-box">
//               <div className="fqs-progress-count">
//                 {String(answeredCount).padStart(2, "0")} /{" "}
//                 {String(totalCount).padStart(2, "0")}
//               </div>
//               <div className="fqs-progress-time"> 8–9 mins</div>
//             </div>{" "} */}
//             <div className="fqs-progress-box">
//               {/* <div className="fqs-progress-header">Progress</div> */}
//               <div className="fqs-progress-count">
//                 {String(answeredCount).padStart(2, "0")}/
//                 {String(totalCount).padStart(2, "0")}
//               </div>
//               <div className="fqs-progress-bar">
//                 <div
//                   className="fqs-progress-fill"
//                   style={{ width: `${(answeredCount / totalCount) * 100}%` }}
//                 />
//               </div>
//               <div className="fqs-progress-time">Quick · {totalCount} mins</div>
//             </div>
//           </div>
//         </main>

//         {/* UNLOCK MODAL — opens when user finishes and clicks Submit */}
//         {/* <ChatUnlockModal
//           isOpen={showUnlockModal}
//           onClose={() => setShowUnlockModal(false)}
//         /> */}
//       </div>
//     </>
//   );
// }

// import React, { useEffect, useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
// import "../components/FoundationQuestionScreen.css";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";
// import ChatUnlockModal from "../components/ChatUnlockModal";
// // <-- import the modal

// export default function FoundationQuestionScreen() {
//   const navigate = useNavigate();

//   // Load any pre-existing session from localStorage
//   const savedSessionJson = localStorage.getItem("session");
//   const savedSessionId = localStorage.getItem("sessionId");
//   const initialSession = savedSessionJson
//     ? JSON.parse(savedSessionJson)
//     : savedSessionId
//       ? { id: savedSessionId }
//       : null;

//   const [session, setSession] = useState(initialSession);
//   // 3. *Now* you can safely create sessionId and storageKey using current state
//   const sessionId = (session && (session.id || session.pk)) || savedSessionId;
//   const inputRef = useRef(null);
//   // Add this useEffect right here:
//   useEffect(() => {
//     async function checkAndStartSession() {
//       if (session && session.status === "draft") {
//         try {
//           await authService.startSession(session.id);
//           // Refresh session with updated status from backend
//           // You can re-fetch session from backend or update state accordingly
//           const updatedSessions = await authService.getSessions();
//           const updatedSession = updatedSessions.find(
//             (s) => s.id === session.id,
//           );
//           if (updatedSession) {
//             setSession(updatedSession);
//             // Also update localStorage if used elsewhere
//             localStorage.setItem("session", JSON.stringify(updatedSession));
//           }
//         } catch (error) {
//           console.error("Failed to start session:", error);
//         }
//       }
//     }
//     checkAndStartSession();
//   }, [session]);
//   const storageKey = sessionId
//     ? `foundationAnswers_${sessionId}`
//     : "foundationAnswers";
//   // Questions loaded from API (state)
//   const [steps, setSteps] = useState([]);
//   const [currentStep, setCurrentStep] = useState(0);
//   // const [questions, setQuestions] = useState([
//   //   {
//   //     id: "01",
//   //     key: "brandName",
//   //     question: "Q.1. What is your brand's name?",
//   //     description:
//   //       "Your name isn't just what people call your business — it's what they remember you by.",
//   //     placeholder: "Enter your brand name...",
//   //     raw: { text: "What is your brand's name?" },
//   //   },
//   // ]);
//   const [questions, setQuestions] = useState([]);

//   const currentStepObj = steps[currentStep];

//   const [questionsLoading, setQuestionsLoading] = useState(true);
//   const [questionsError, setQuestionsError] = useState("");

//   // Agencies dropdown state (modal)
//   const [agencies, setAgencies] = useState([]);
//   const [selectedAgency, setSelectedAgency] = useState(0);
//   const [agenciesLoading, setAgenciesLoading] = useState(false);
//   const [agenciesError, setAgenciesError] = useState("");

//   const [showTitleModal, setShowTitleModal] = useState(!initialSession);

//   const [modalTitle, setModalTitle] = useState("");
//   const [modalTouched, setModalTouched] = useState(false);
//   const [modalLoading, setModalLoading] = useState(false);
//   const [modalError, setModalError] = useState("");

//   // NEW: show unlock modal after final submit
//   // const [showUnlockModal, setShowUnlockModal] = useState(false);
//   // useEffect(() => {
//   //   // When there is no blocking modal, keep the answer input focused
//   //   if (!showTitleModal && !showUnlockModal && inputRef.current) {
//   //     inputRef.current.focus();
//   //     // Optional: select existing text so user can just start typing
//   //     // inputRef.current.select();
//   //   }
//   // }, [currentStep, showTitleModal, showUnlockModal]);
//   useEffect(() => {
//     if (!showTitleModal && inputRef.current) {
//       inputRef.current.focus();
//     }
//   }, [currentStep, showTitleModal]);

//   // Answers stored in localStorage
//   const [answers, setAnswers] = useState(() => {
//     try {
//       const raw = localStorage.getItem(storageKey);
//       return raw ? JSON.parse(raw) : { brandName: "" };
//     } catch {
//       return { brandName: "" };
//     }
//   });
//   // Validation/error on submit
//   const [submitError, setSubmitError] = useState("");

//   // useEffect(() => {
//   //   let cancelled = false;
//   //   const FOUNDATION_STAGE = 1; // Adjust if needed

//   //   async function loadQuestions() {
//   //     setQuestionsLoading(true);
//   //     setQuestionsError("");
//   //     try {
//   //       const list = await authService.getQuestions(); // Or your correct service reference
//   //       if (cancelled) return;

//   //       const foundation = Array.isArray(list)
//   //         ? list.filter((q) => String(q.stage) === String(FOUNDATION_STAGE))
//   //         : [];

//   //       const mapped =
//   //         foundation.length > 0
//   //           ? foundation.map((q, idx) => ({
//   //               id: String(q.id).padStart(2, "0"),
//   //               key: `q_${q.id}`,
//   //               question: `Q.${idx + 1}. ${q.text}`,
//   //               description: q.help_text ?? "",
//   //               placeholder: q.placeholder ?? "",
//   //               raw: q,
//   //             }))
//   //           : [
//   //               {
//   //                 id: "01",
//   //                 key: "brandName",
//   //                 question: "Q.1. What is your brand's name?",
//   //                 description:
//   //                   "Your name isn't just what people call your business — it's what they remember you by.",
//   //                 placeholder: "Enter your brand name...",
//   //                 raw: { text: "What is your brand's name?" },
//   //               },
//   //             ];

//   //       if (!cancelled) setQuestions(mapped);
//   //     } catch (err) {
//   //       console.error("getQuestions error:", err);
//   //       if (!cancelled)
//   //         setQuestionsError(err?.message || "Failed to load questions");
//   //     } finally {
//   //       if (!cancelled) setQuestionsLoading(false);
//   //     }
//   //   }

//   //   loadQuestions();
//   //   return () => {
//   //     cancelled = true;
//   //   };
//   // }, []);

//   useEffect(() => {
//     let cancelled = false;

//     const BASIC_STAGE = 1; // multiple questions on one screen
//     const FOUNDATION_STAGE = 2; // one by one

//     async function loadQuestions() {
//       setQuestionsLoading(true);
//       setQuestionsError("");

//       try {
//         const res = await authService.getQuestions();
//         if (cancelled) return;

//         let all = [];

//         // ✅ Case 1: API returns plain array
//         if (Array.isArray(res)) {
//           all = res;
//         }
//         // ✅ Case 2: API returns { stage, mode, questions: [...] }
//         else if (res && Array.isArray(res.questions)) {
//           all = res.questions;
//         }

//         // sort by order
//         all.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

//         const BASIC_STAGE = 1; // multiple questions on one screen
//         const FOUNDATION_STAGE = 2; // one by one

//         const basic = all.filter(
//           (q) => String(q.stage) === String(BASIC_STAGE),
//         );
//         const foundation = all.filter(
//           (q) => String(q.stage) === String(FOUNDATION_STAGE),
//         );

//         const builtSteps = [];

//         // Step 0: Basic group (multiple questions together)
//         if (basic.length > 0) {
//           builtSteps.push({
//             type: "basic_group",
//             questions: basic.map((q, idx) => ({
//               id: String(q.id),
//               key: `q_${q.id}`,
//               question: `Q.${idx + 1}. ${q.text}`,
//               description: q.help_text ?? "",
//               placeholder: q.placeholder ?? "",
//               raw: q,
//             })),
//           });
//         }

//         // Next steps: Foundation (one by one)
//         foundation.forEach((q) => {
//           builtSteps.push({
//             type: "single",
//             question: {
//               id: String(q.id).padStart(2, "0"),
//               key: `q_${q.id}`,
//               question: q.text,
//               description: q.help_text ?? "",
//               placeholder: q.placeholder ?? "",
//               raw: q,
//             },
//           });
//         });

//         // Fallback if API returns nothing
//         if (builtSteps.length === 0) {
//           builtSteps.push({
//             type: "single",
//             question: {
//               id: "01",
//               key: "brandName",
//               question: "What is your brand's name?",
//               description:
//                 "Your name isn't just what people call your business — it's what they remember you by.",
//               placeholder: "Enter your brand name...",
//               raw: { text: "What is your brand's name?" },
//             },
//           });
//         }

//         if (!cancelled) setSteps(builtSteps);
//       } catch (err) {
//         console.error("getQuestions error:", err);
//         if (!cancelled) {
//           setQuestionsError(err?.message || "Failed to load questions");
//         }
//       } finally {
//         if (!cancelled) setQuestionsLoading(false);
//       }
//     }

//     loadQuestions();
//     return () => {
//       cancelled = true;
//     };
//   }, []);

//   // -------- Load questions from API on mount --------
//   useEffect(() => {
//     let cancelled = false;

//     async function loadExistingAnswers() {
//       if (!Array.isArray(questions) || questions.length === 0) return;
//       // Get sessionId
//       const sessionId =
//         (session && (session.id || session.pk)) ||
//         localStorage.getItem("sessionId");

//       if (!sessionId) return;
//       try {
//         // Get the current questionId and answer (if needed)
//         const currentQ = questions[currentStep];
//         const apiQuestionId = currentQ?.raw?.id ?? currentQ?.raw?.pk ?? null;
//         const value = (currentQ?.key && answers[currentQ.key]) || "";

//         // Pass the payload expected by your backend.
//         const payload = {
//           question: apiQuestionId,
//           answer_text: value, // If required - otherwise omit this field
//         };

//         const remoteAnswers = await authService.getAnswers(sessionId, payload);

//         if (cancelled) return;
//         // Build map: questionId -> UI key
//         const idToKey = {};
//         questions.forEach((q) => {
//           const qid = q?.raw?.id ?? q?.raw?.pk ?? null;
//           if (qid != null) idToKey[String(qid)] = q.key;
//         });
//         // Merge remote answers into state
//         setAnswers((prev) => {
//           const next = { ...prev };
//           (Array.isArray(remoteAnswers) ? remoteAnswers : []).forEach((a) => {
//             const qid = a.question;
//             const key = idToKey[String(qid)] || `q_${qid}`;
//             if (
//               typeof a.answer_text === "string" &&
//               a.answer_text.trim() !== ""
//             ) {
//               next[key] = a.answer_text;
//             }
//           });
//           localStorage.setItem(storageKey, JSON.stringify(next));
//           return next;
//         });
//       } catch (err) {
//         console.warn("Failed to load existing answers:", err);
//       }
//     }

//     loadExistingAnswers();
//     return () => {
//       cancelled = true;
//     };
//   }, [session, questions]);

//   // Prefill brandName from session if empty
//   useEffect(() => {
//     if (!session) return;
//     const title = session.title || session.name || "";
//     if (title && (!answers.brandName || answers.brandName.trim() === "")) {
//       const next = { ...answers, brandName: title };
//       setAnswers(next);
//       localStorage.setItem(storageKey, JSON.stringify(next));
//     }
//     // eslint-disable-next-line react-hooks/exhaustive-deps
//   }, [session]);

//   // Fetch agencies when the title modal opens
//   useEffect(() => {
//     if (!showTitleModal) return;

//     let cancelled = false;
//     const load = async () => {
//       setAgenciesLoading(true);
//       setAgenciesError("");
//       try {
//         const list = await authService.getAgencies();
//         if (cancelled) return;
//         const normalized = Array.isArray(list) ? list : [];
//         setAgencies(normalized);
//         if (normalized.length > 0) {
//           const id = normalized[0].id ?? normalized[0].pk ?? 0;
//           setSelectedAgency(id);
//         } else {
//           setSelectedAgency(0);
//         }
//       } catch (err) {
//         console.error("getAgencies error:", err);
//         if (!cancelled)
//           setAgenciesError(err.message || "Failed to load agencies");
//       } finally {
//         if (!cancelled) setAgenciesLoading(false);
//       }
//     };
//     load();
//     return () => {
//       cancelled = true;
//     };
//   }, [showTitleModal]);

//   const updateAnswer = (key, value) => {
//     setAnswers((prev) => {
//       const next = { ...prev, [key]: value };
//       localStorage.setItem(storageKey, JSON.stringify(next));
//       return next;
//     });
//   };

//   // Helper: check all questions answered (non-empty)
//   const allAnswered = () => {
//     if (!Array.isArray(questions) || questions.length === 0) return false;
//     return questions.every((q) => {
//       const val = answers[q.key];
//       return val !== undefined && val !== null && String(val).trim() !== "";
//     });
//   };

//   const handleNext = async () => {
//     setSubmitError("");

//     const stepObj = steps[currentStep];

//     const sessionId =
//       (session && (session.id || session.pk)) ||
//       localStorage.getItem("sessionId");

//     // ========== CASE 1: BASIC GROUP ==========
//     if (stepObj?.type === "basic_group") {
//       // Validate all fields
//       for (let q of stepObj.questions) {
//         const val = answers[q.key];
//         if (!val || String(val).trim() === "") {
//           setSubmitError("Please fill all fields before continuing.");
//           return;
//         }
//       }

//       // Save all answers
//       if (sessionId) {
//         try {
//           for (let q of stepObj.questions) {
//             const apiQuestionId = q?.raw?.id ?? q?.raw?.pk ?? null;
//             const val = answers[q.key];
//             if (!apiQuestionId) continue;

//             await authService.createAnswer(sessionId, {
//               question: Number(apiQuestionId),
//               answer_text: String(val),
//             });
//           }
//         } catch (err) {
//           setSubmitError(
//             err?.message || "Failed to save answers. Please try again.",
//           );
//           return;
//         }
//       }

//       // Next step
//       if (currentStep < steps.length - 1) {
//         setCurrentStep((s) => s + 1);
//         return;
//       }
//     }

//     // ========== CASE 2: SINGLE QUESTION ==========
//     if (stepObj?.type === "single") {
//       const currentQ = stepObj.question;
//       const key = currentQ?.key;
//       const value = (key && answers[key]) || "";

//       if (!value || String(value).trim() === "") {
//         setSubmitError("Please answer before continuing.");
//         return;
//       }

//       const apiQuestionId = currentQ?.raw?.id ?? currentQ?.raw?.pk ?? null;

//       if (sessionId && apiQuestionId) {
//         try {
//           await authService.createAnswer(sessionId, {
//             question: Number(apiQuestionId),
//             answer_text: String(value),
//           });
//         } catch (err) {
//           setSubmitError(
//             err?.message || "Failed to save answer. Please try again.",
//           );
//           return;
//         }
//       }

//       if (currentStep < steps.length - 1) {
//         setCurrentStep((s) => s + 1);
//         return;
//       }
//     }

//     // ========== FINAL ==========
//     try {
//       localStorage.setItem(storageKey, JSON.stringify(answers));
//     } catch {}

//     navigate("/brand-summary");
//   };

//   const handleBack = () => {
//     if (currentStep > 0) setCurrentStep((s) => s - 1);
//     else navigate(-1);
//   };

//   // Modal handlers (title modal already implemented below)
//   const isModalTitleValid = modalTitle.trim().length > 0;

//   const handleModalSubmit = async (e) => {
//     e?.preventDefault?.();
//     setModalTouched(true);
//     setModalError("");
//     setSession(sessionObj);
//     setShowTitleModal(false);
//     const titleVal = sessionObj.title || modalTitle.trim();
//     setAnswers({ brandName: "" });
//     localStorage.setItem(storageKey, JSON.stringify({ brandName: "" }));
//     if (!isModalTitleValid) return;

//     setModalLoading(true);
//     try {
//       const payload = {
//         title: modalTitle.trim(),
//         agency: Number(selectedAgency) || null,
//       };

//       const data = await authService.createSession(payload);

//       let sessionObj = null;
//       if (data?.session) sessionObj = data.session;
//       else if (data?.id || data?.title || data?.name) sessionObj = data;
//       else sessionObj = { title: modalTitle.trim() };

//       try {
//         localStorage.setItem("session", JSON.stringify(sessionObj));
//         if (sessionObj.id) localStorage.setItem("sessionId", sessionObj.id);
//       } catch {}

//       setSession(sessionObj);
//       setShowTitleModal(false);
//       const titleVal = sessionObj.title || modalTitle.trim();
//       setAnswers((prev) => {
//         const next = {
//           ...prev,
//           brandName: prev.brandName?.trim() ? prev.brandName : titleVal,
//         };
//         localStorage.setItem(storageKey, JSON.stringify(next));
//         return next;
//       });
//     } catch (err) {
//       console.error("createSession error:", err);
//       const message = err?.message || "Failed to create session. Try again.";
//       setModalError(message);
//     } finally {
//       setModalLoading(false);
//     }
//   };

//   // Hide title modal if session becomes available
//   useEffect(() => {
//     if (session) setShowTitleModal(false);
//   }, [session]);

//   // Save answers handler
//   const handleSave = () => {
//     try {
//       localStorage.setItem(storageKey, JSON.stringify(answers));
//       console.log("Saved answers:", answers);
//     } catch (error) {
//       console.error("Save error:", error);
//     }
//   };

//   // Render pill number
//   // const renderPill = (idx) => <div className="pill-content">{idx}</div>;
//   const renderPill = (idx) => <div className="pill-content">{idx + 1}</div>;

//   // const currentQuestion = questions[currentStep] || questions[0];
//   // const currentValue = answers[currentQuestion.key] ?? "";

//   let currentQuestion = null;
//   let currentValue = "";

//   if (currentStepObj?.type === "single") {
//     currentQuestion = currentStepObj.question;
//     currentValue = answers[currentQuestion.key] ?? "";
//   }

//   // const answeredCount = steps.filter(
//   //   (q) => answers[q.key] && answers[q.key].trim() !== "",
//   // ).length;
//   const answeredCount = steps.reduce((count, step) => {
//     if (step.type === "basic_group") {
//       return (
//         count +
//         step.questions.filter((q) => {
//           const v = answers[q.key];
//           return v && String(v).trim() !== "";
//         }).length
//       );
//     }

//     if (step.type === "single") {
//       const q = step.question;
//       const v = answers[q.key];
//       return count + (v && String(v).trim() !== "" ? 1 : 0);
//     }

//     return count;
//   }, 0);

//   // const totalCount = steps.length;
//   const totalCount = steps.reduce((count, step) => {
//     if (step.type === "basic_group") return count + step.questions.length;
//     if (step.type === "single") return count + 1;
//     return count;
//   }, 0);

//   return (
//     <>
//       <ChatNavbar
//         onSave={handleSave}
//         showSaveButton={false}
//         showDownloadButton={false}
//         showLogoutButton={true}
//       />

//       {/* <div
//         className={`fqs-app ${showTitleModal ? "modal-open" : ""} ${
//           showUnlockModal ? "modal-open" : ""
//         }`}
//       > */}
//       <div className={`fqs-app ${showTitleModal ? "modal-open" : ""}`}>
//         {/* TITLE MODAL (unchanged) */}
//         {showTitleModal && (
//           <div className="title-modal-overlay">
//             <div className="title-modal" role="dialog" aria-modal="true">
//               <h3>Give your session a title</h3>
//               <p className="modal-sub">
//                 This will be used as your session name and prefills the first
//                 question.
//               </p>

//               <form onSubmit={handleModalSubmit} className="modal-form">
//                 <input
//                   className="modal-input"
//                   placeholder="Enter a title for this session"
//                   value={modalTitle}
//                   onChange={(e) => setModalTitle(e.target.value)}
//                   onBlur={() => setModalTouched(true)}
//                   disabled={modalLoading}
//                   autoFocus
//                 />

//                 <label
//                   style={{
//                     color: "rgba(255,255,255,0.6)",
//                     fontSize: 13,
//                     marginTop: 4,
//                   }}
//                 >
//                   Agency (Optional)
//                 </label>

//                 {agenciesLoading ? (
//                   <div
//                     style={{
//                       padding: "10px 12px",
//                       color: "rgba(255,255,255,0.6)",
//                     }}
//                   >
//                     Loading agencies...
//                   </div>
//                 ) : agenciesError ? (
//                   <div style={{ color: "#ffb3b3", fontSize: 13 }}>
//                     {agenciesError}
//                   </div>
//                 ) : (
//                   <select
//                     className="modal-input"
//                     value={selectedAgency}
//                     onChange={(e) => setSelectedAgency(Number(e.target.value))}
//                     disabled={modalLoading}
//                     style={{ appearance: "none", WebkitAppearance: "none" }}
//                   >
//                     <option value={0}>-- No Agency --</option>
//                     {agencies.map((a) => {
//                       const id = a.id ?? a.pk ?? a.value ?? a.key ?? 0;
//                       const label =
//                         a.name ?? a.title ?? a.label ?? `Agency ${id}`;
//                       return (
//                         <option key={String(id)} value={id}>
//                           {label}
//                         </option>
//                       );
//                     })}
//                   </select>
//                 )}

//                 {modalTouched && !isModalTitleValid && (
//                   <div className="modal-validation">
//                     Please enter a session title
//                   </div>
//                 )}
//                 {modalError && <div className="modal-error">{modalError}</div>}

//                 <div className="modal-actions">
//                   <button
//                     type="button"
//                     className="modal-cancel"
//                     onClick={() => navigate(-1)}
//                     disabled={modalLoading}
//                   >
//                     Cancel
//                   </button>
//                   <button
//                     type="submit"
//                     className="modal-submit"
//                     disabled={
//                       !isModalTitleValid || modalLoading || agenciesLoading
//                     }
//                   >
//                     {modalLoading ? "Creating..." : "Create Session"}
//                   </button>
//                 </div>
//               </form>
//             </div>
//           </div>
//         )}

//         {/* LEFT SIDEBAR */}
//         <aside
//           className="fqs-left"
//           // aria-hidden={showTitleModal || showUnlockModal}
//           aria-hidden={showTitleModal}
//         >
//           <div className="fqs-left-inner">
//             <div className="fqs-intro">
//               <h1>
//                 Every great brand begins with you.
//                 <br />
//                 Eight questions. One honest minute. Ready?
//               </h1>
//             </div>

//             <nav className="fqs-left-nav">
//               {steps.map((step, i) => {
//                 const label =
//                   step.type === "basic_group"
//                     ? "Basic Info"
//                     : step.question?.question || "Question";

//                 return (
//                   <div
//                     key={i}
//                     className={`fqs-nav-row ${currentStep === i ? "active" : ""}`}
//                     onClick={() => setCurrentStep(i)}
//                   >
//                     {/* <div className="fqs-nav-num">
//                       {String(i).padStart(2, "0")}
//                     </div> */}
//                     <div className="fqs-nav-num">
//                       {String(i + 1).padStart(2, "0")}
//                     </div>

//                     <div className="fqs-nav-label">{label}</div>
//                   </div>
//                 );
//               })}
//             </nav>
//           </div>
//         </aside>

//         {/* MAIN CONTENT */}
//         <main
//           className="fqs-main"
//           // aria-hidden={showTitleModal || showUnlockModal}
//           aria-hidden={showTitleModal}
//         >
//           <div className="fqs-glow-left" />
//           <div className="fqs-card-wrapper">
//             <div className="fqs-card glow_wrapper">
//               <div className="glow-circle"></div>
//               <div className="glow-circle second"></div>
//               <div className="content">
//                 <h2 className="fqs-title">Get Started!</h2>

//                 {/* <div className="fqs-stepper">
//                   {questions.map((q, idx) => (
//                     <React.Fragment key={q.id}>
//                       <div
//                         className={`fqs-pill ${
//                           idx === currentStep ? "pill-active" : ""
//                         }`}
//                       >
//                         {renderPill(idx)}
//                       </div>
//                       {idx < questions.length - 1 && (
//                         <div className="fqs-stepline" />
//                       )}
//                     </React.Fragment>
//                   ))}
//                 </div> */}
//                 <div className="fqs-stepper">
//                   {steps.map((step, idx) => (
//                     <React.Fragment key={idx}>
//                       <div
//                         className={`fqs-pill ${idx === currentStep ? "pill-active" : ""}`}
//                         onClick={() => setCurrentStep(idx)}
//                       >
//                         {renderPill(idx)}
//                       </div>
//                       {idx < steps.length - 1 && (
//                         <div className="fqs-stepline" />
//                       )}
//                     </React.Fragment>
//                   ))}
//                 </div>

//                 {/* <div className="fqs-question">
//                   <h3 className="fqs-q">{currentQuestion.question}</h3>
//                   <p className="fqs-desc">{currentQuestion.description}</p>
//                 </div> */}

//                 <div className="fqs-input-area">
//                   {currentStepObj?.type === "single" && currentQuestion && (
//                     <>
//                       <h3 className="fqs-q">{currentQuestion.question}</h3>
//                       <p className="fqs-desc">{currentQuestion.description}</p>
//                     </>
//                   )}

//                   {currentStepObj?.type === "basic_group" && (
//                     <>
//                       <h3 className="fqs-q">Basic Information</h3>

//                       {currentStepObj.questions.map((q, idx) => (
//                         <div key={q.key} style={{ marginBottom: 16 }}>
//                           <p className="fqs-desc">{q.question}</p>
//                           <input
//                             className="fqs-input"
//                             placeholder={q.placeholder || ""}
//                             value={answers[q.key] || ""}
//                             onChange={(e) =>
//                               updateAnswer(q.key, e.target.value)
//                             }
//                           />
//                         </div>
//                       ))}
//                     </>
//                   )}

//                   {currentStepObj?.type === "single" && currentQuestion && (
//                     <input
//                       ref={inputRef}
//                       className="fqs-input"
//                       placeholder={currentQuestion.placeholder}
//                       value={currentValue}
//                       onChange={(e) =>
//                         updateAnswer(currentQuestion.key, e.target.value)
//                       }
//                     />
//                   )}
//                 </div>

//                 {submitError && (
//                   <div className="submit-error">{submitError}</div>
//                 )}

//                 <div className="fqs-footer">
//                   <button
//                     className={`fqs-back ${
//                       currentStep === 0 ? "disabled" : ""
//                     }`}
//                     onClick={handleBack}
//                     disabled={currentStep === 0}
//                   >
//                     Back
//                   </button>
//                   <button className="fqs-next" onClick={handleNext}>
//                     {currentStep < steps.length - 1 ? "Next" : "Submit"}
//                   </button>
//                 </div>
//               </div>
//             </div>
//             {/* <div className="fqs-progress-box">
//               <div className="fqs-progress-count">
//                 {String(answeredCount).padStart(2, "0")} /{" "}
//                 {String(totalCount).padStart(2, "0")}
//               </div>
//               <div className="fqs-progress-time"> 8–9 mins</div>
//             </div>{" "} */}

//             {/* quick 8 mins */}

//             {/* <div className="fqs-progress-box">
//               <div className="fqs-progress-count">
//                 {String(answeredCount).padStart(2, "0")}/
//                 {String(totalCount).padStart(2, "0")}
//               </div>
//               <div className="fqs-progress-bar">
//                 <div
//                   className="fqs-progress-fill"
//                   style={{ width: `${(answeredCount / totalCount) * 100}%` }}
//                 />
//               </div>
//               <div className="fqs-progress-time">Quick · {totalCount} mins</div>
//             </div> */}
//           </div>
//         </main>

//         {/* UNLOCK MODAL — opens when user finishes and clicks Submit */}
//         {/* <ChatUnlockModal
//           isOpen={showUnlockModal}
//           onClose={() => setShowUnlockModal(false)}
//         /> */}
//       </div>
//     </>
//   );
// }

import React, { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "../components/FoundationQuestionScreen.css";
import ChatNavbar from "./ChatNavbar";
import authService from "../services/authService";
import ChatUnlockModal from "../components/ChatUnlockModal";

export default function FoundationQuestionScreen() {
  const navigate = useNavigate();

  const savedSessionJson = localStorage.getItem("session");
  const savedSessionId = localStorage.getItem("sessionId");
  const initialSession = savedSessionJson
    ? JSON.parse(savedSessionJson)
    : savedSessionId
      ? { id: savedSessionId }
      : null;

  const [session, setSession] = useState(initialSession);
  const sessionId = (session && (session.id || session.pk)) || savedSessionId;
  const inputRef = useRef(null);

  // ── Session title modal (shown when no session exists yet) ──────────────
  const [showTitleModal, setShowTitleModal] = useState(!initialSession);
  const [modalTitle, setModalTitle] = useState("");
  const [modalTouched, setModalTouched] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");

  // ── Agencies ────────────────────────────────────────────────────────────
  const [agencies, setAgencies] = useState([]);
  const [selectedAgency, setSelectedAgency] = useState(0);
  const [agenciesLoading, setAgenciesLoading] = useState(false);
  const [agenciesError, setAgenciesError] = useState("");

  // ── NEW: Basic Info Modal ────────────────────────────────────────────────
  // Shows all Stage-1 (basic_group) questions before foundation questions
  const [showBasicModal, setShowBasicModal] = useState(false);
  const [basicOpenedFromSidebar, setBasicOpenedFromSidebar] = useState(false);
  const [basicModalStep, setBasicModalStep] = useState(0); // which basic question is "active" (for highlight)
  const [basicSubmitting, setBasicSubmitting] = useState(false);
  const [basicError, setBasicError] = useState("");

  // ── Steps / questions ───────────────────────────────────────────────────
  const [steps, setSteps] = useState([]); // foundation-only steps (type="single")
  const [basicGroup, setBasicGroup] = useState(null); // type="basic_group" step
  const [currentStep, setCurrentStep] = useState(0);

  const [questionsLoading, setQuestionsLoading] = useState(true);
  const [questionsError, setQuestionsError] = useState("");

  // ── Answers ─────────────────────────────────────────────────────────────
  const storageKey = sessionId
    ? `foundationAnswers_${sessionId}`
    : "foundationAnswers";

  const [answers, setAnswers] = useState(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      return raw ? JSON.parse(raw) : { brandName: "" };
    } catch {
      return { brandName: "" };
    }
  });

  const [submitError, setSubmitError] = useState("");

  // ── Auto-start draft session ─────────────────────────────────────────────
  useEffect(() => {
    async function checkAndStartSession() {
      if (session && session.status === "draft") {
        try {
          await authService.startSession(session.id);
          const updatedSessions = await authService.getSessions();
          const updatedSession = updatedSessions.find(
            (s) => s.id === session.id,
          );
          if (updatedSession) {
            setSession(updatedSession);
            localStorage.setItem("session", JSON.stringify(updatedSession));
          }
        } catch (error) {
          console.error("Failed to start session:", error);
        }
      }
    }
    checkAndStartSession();
  }, [session]);

  // ── Focus input when not in a modal ─────────────────────────────────────
  useEffect(() => {
    if (!showTitleModal && !showBasicModal && inputRef.current) {
      inputRef.current.focus();
    }
  }, [currentStep, showTitleModal, showBasicModal]);

  // ── Load questions ───────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    async function loadQuestions() {
      setQuestionsLoading(true);
      setQuestionsError("");

      try {
        const res = await authService.getQuestions();
        if (cancelled) return;

        let all = [];
        if (Array.isArray(res)) {
          all = res;
        } else if (res && Array.isArray(res.questions)) {
          all = res.questions;
        }

        all.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

        const BASIC_STAGE = 1;
        const FOUNDATION_STAGE = 2;

        const basic = all.filter(
          (q) => String(q.stage) === String(BASIC_STAGE),
        );
        const foundation = all.filter(
          (q) => String(q.stage) === String(FOUNDATION_STAGE),
        );

        // Build basic group
        let basicStep = null;
        if (basic.length > 0) {
          basicStep = {
            type: "basic_group",
            questions: basic.map((q, idx) => ({
              id: String(q.id),
              key: `q_${q.id}`,
              question: q.text,
              description: q.help_text ?? "",
              placeholder: q.placeholder ?? "",
              raw: q,
            })),
          };
        }

        // Build foundation steps (one per question)
        const foundationSteps = foundation.map((q) => ({
          type: "single",
          question: {
            id: String(q.id).padStart(2, "0"),
            key: `q_${q.id}`,
            question: q.text,
            description: q.help_text ?? "",
            placeholder: q.placeholder ?? "",
            raw: q,
          },
        }));

        // Fallback
        if (foundationSteps.length === 0) {
          foundationSteps.push({
            type: "single",
            question: {
              id: "01",
              key: "brandName",
              question: "What is your brand's name?",
              description:
                "Your name isn't just what people call your business — it's what they remember you by.",
              placeholder: "Enter your brand name...",
              raw: { text: "What is your brand's name?" },
            },
          });
        }

        if (!cancelled) {
          setBasicGroup(basicStep);
          setSteps(foundationSteps);

          // Show basic modal only once session exists and we have basic questions

          // if (basicStep && basicStep.questions.length > 0) {
          //   // Check if basic questions are already answered
          //   const alreadyAnswered = basicStep.questions.every((q) => {
          //     const raw = localStorage.getItem(storageKey);
          //     const saved = raw ? JSON.parse(raw) : {};
          //     const val = saved[q.key];
          //     return val && String(val).trim() !== "";
          //   });
          //   if (!alreadyAnswered) {
          //     // Will open after title modal closes
          //     setShowBasicModal(true);
          //   }
          // }

          // ALWAYS show basic modal when entering this page (if basic questions exist)
          if (basicStep && basicStep.questions.length > 0) {
            setShowBasicModal(true);
          }
        }
      } catch (err) {
        console.error("getQuestions error:", err);
        if (!cancelled)
          setQuestionsError(err?.message || "Failed to load questions");
      } finally {
        if (!cancelled) setQuestionsLoading(false);
      }
    }

    loadQuestions();
    return () => {
      cancelled = true;
    };
  }, []);

  // ── Load existing answers ────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    async function loadExistingAnswers() {
      const allQuestions = [
        ...(basicGroup?.questions ?? []),
        ...steps.map((s) => s.question).filter(Boolean),
      ];
      if (allQuestions.length === 0) return;

      const sid =
        (session && (session.id || session.pk)) ||
        localStorage.getItem("sessionId");
      if (!sid) return;

      try {
        const remoteAnswers = await authService.getAnswers(sid, {});
        if (cancelled) return;

        const idToKey = {};
        allQuestions.forEach((q) => {
          const qid = q?.raw?.id ?? q?.raw?.pk ?? null;
          if (qid != null) idToKey[String(qid)] = q.key;
        });

        setAnswers((prev) => {
          const next = { ...prev };
          (Array.isArray(remoteAnswers) ? remoteAnswers : []).forEach((a) => {
            const key = idToKey[String(a.question)] || `q_${a.question}`;
            if (
              typeof a.answer_text === "string" &&
              a.answer_text.trim() !== ""
            ) {
              next[key] = a.answer_text;
            }
          });
          localStorage.setItem(storageKey, JSON.stringify(next));
          return next;
        });
      } catch (err) {
        console.warn("Failed to load existing answers:", err);
      }
    }

    loadExistingAnswers();
    return () => {
      cancelled = true;
    };
  }, [session, steps, basicGroup]);

  // ── Prefill brandName from session ──────────────────────────────────────
  useEffect(() => {
    if (!session) return;
    const title = session.title || session.name || "";
    if (title && (!answers.brandName || answers.brandName.trim() === "")) {
      const next = { ...answers, brandName: title };
      setAnswers(next);
      localStorage.setItem(storageKey, JSON.stringify(next));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  // ── Agencies (for title modal) ───────────────────────────────────────────
  useEffect(() => {
    if (!showTitleModal) return;
    let cancelled = false;
    const load = async () => {
      setAgenciesLoading(true);
      setAgenciesError("");
      try {
        const list = await authService.getAgencies();
        if (cancelled) return;
        const normalized = Array.isArray(list) ? list : [];
        setAgencies(normalized);
        if (normalized.length > 0) {
          const id = normalized[0].id ?? normalized[0].pk ?? 0;
          setSelectedAgency(id);
        }
      } catch (err) {
        if (!cancelled)
          setAgenciesError(err.message || "Failed to load agencies");
      } finally {
        if (!cancelled) setAgenciesLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [showTitleModal]);

  // Hide title modal when session is set
  useEffect(() => {
    if (session) setShowTitleModal(false);
  }, [session]);

  // ── Answer helpers ───────────────────────────────────────────────────────
  const updateAnswer = (key, value) => {
    setAnswers((prev) => {
      const next = { ...prev, [key]: value };
      localStorage.setItem(storageKey, JSON.stringify(next));
      return next;
    });
  };

  // ── Title modal submit ───────────────────────────────────────────────────
  const isModalTitleValid = modalTitle.trim().length > 0;

  const handleModalSubmit = async (e) => {
    e?.preventDefault?.();
    setModalTouched(true);
    setModalError("");
    if (!isModalTitleValid) return;

    setModalLoading(true);
    try {
      const payload = {
        title: modalTitle.trim(),
        agency: Number(selectedAgency) || null,
      };
      const data = await authService.createSession(payload);

      let sessionObj = null;
      if (data?.session) sessionObj = data.session;
      else if (data?.id || data?.title || data?.name) sessionObj = data;
      else sessionObj = { title: modalTitle.trim() };

      localStorage.setItem("session", JSON.stringify(sessionObj));
      if (sessionObj.id) localStorage.setItem("sessionId", sessionObj.id);

      setSession(sessionObj);
      setShowTitleModal(false);

      const titleVal = sessionObj.title || modalTitle.trim();
      setAnswers((prev) => {
        const next = {
          ...prev,
          brandName: prev.brandName?.trim() ? prev.brandName : titleVal,
        };
        localStorage.setItem(storageKey, JSON.stringify(next));
        return next;
      });
    } catch (err) {
      setModalError(err?.message || "Failed to create session. Try again.");
    } finally {
      setModalLoading(false);
    }
  };

  // ── Basic Modal submit ───────────────────────────────────────────────────
  const handleBasicModalSubmit = async () => {
    setBasicError("");

    if (!basicGroup) {
      setShowBasicModal(false);
      setBasicOpenedFromSidebar(false);
      return;
    }

    // Validate all basic fields
    for (let q of basicGroup.questions) {
      const val = answers[q.key];
      if (!val || String(val).trim() === "") {
        setBasicError("Please fill in all fields before continuing.");
        setBasicModalStep(basicGroup.questions.indexOf(q));
        return;
      }
    }

    const sid =
      (session && (session.id || session.pk)) ||
      localStorage.getItem("sessionId");

    if (sid) {
      setBasicSubmitting(true);
      try {
        for (let q of basicGroup.questions) {
          const apiQuestionId = q?.raw?.id ?? q?.raw?.pk ?? null;
          const val = answers[q.key];
          if (!apiQuestionId) continue;
          await authService.createAnswer(sid, {
            question: Number(apiQuestionId),
            answer_text: String(val),
          });
        }
      } catch (err) {
        setBasicError(err?.message || "Failed to save. Please try again.");
        setBasicSubmitting(false);
        return;
      } finally {
        setBasicSubmitting(false);
      }
    }

    setShowBasicModal(false);
  };

  // ── Foundation navigation ────────────────────────────────────────────────
  const handleNext = async () => {
    setSubmitError("");

    const stepObj = steps[currentStep];
    const sid =
      (session && (session.id || session.pk)) ||
      localStorage.getItem("sessionId");

    if (stepObj?.type === "single") {
      const currentQ = stepObj.question;
      const key = currentQ?.key;
      const value = (key && answers[key]) || "";

      if (!value || String(value).trim() === "") {
        setSubmitError("Please answer before continuing.");
        return;
      }

      const apiQuestionId = currentQ?.raw?.id ?? currentQ?.raw?.pk ?? null;
      if (sid && apiQuestionId) {
        try {
          await authService.createAnswer(sid, {
            question: Number(apiQuestionId),
            answer_text: String(value),
          });
        } catch (err) {
          setSubmitError(
            err?.message || "Failed to save answer. Please try again.",
          );
          return;
        }
      }

      if (currentStep < steps.length - 1) {
        setCurrentStep((s) => s + 1);
        return;
      }
    }

    try {
      localStorage.setItem(storageKey, JSON.stringify(answers));
    } catch {}

    navigate("/brand-summary");
  };

  const handleBack = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
    else navigate(-1);
  };

  const handleSave = () => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(answers));
    } catch (error) {
      console.error("Save error:", error);
    }
  };

  const handleOpenBasicFromSidebar = () => {
    setBasicOpenedFromSidebar(true);
    setShowBasicModal(true);
  };

  // ── Derived values ───────────────────────────────────────────────────────
  const currentStepObj = steps[currentStep];
  let currentQuestion = null;
  let currentValue = "";
  if (currentStepObj?.type === "single") {
    currentQuestion = currentStepObj.question;
    currentValue = answers[currentQuestion.key] ?? "";
  }

  const answeredCount = steps.reduce((count, step) => {
    if (step.type === "single") {
      const v = answers[step.question?.key];
      return count + (v && String(v).trim() !== "" ? 1 : 0);
    }
    return count;
  }, 0);

  const totalCount = steps.length;

  const basicAnsweredCount = basicGroup
    ? basicGroup.questions.filter((q) => {
        const v = answers[q.key];
        return v && String(v).trim() !== "";
      }).length
    : 0;

  const renderPill = (idx) => <div className="pill-content">{idx + 1}</div>;

  // Whether all basic fields are filled (enables Next button in modal)
  const allBasicFilled = basicGroup
    ? basicGroup.questions.every((q) => {
        const v = answers[q.key];
        return v && String(v).trim() !== "";
      })
    : true;

  return (
    <>
      <ChatNavbar
        onSave={handleSave}
        showSaveButton={false}
        showDownloadButton={false}
        showLogoutButton={true}
      />

      <div
        className={`fqs-app ${
          showTitleModal || showBasicModal ? "modal-open" : ""
        }`}
      >
        {/* ════════════════════════════════════════
            SESSION TITLE MODAL (unchanged)
        ════════════════════════════════════════ */}
        {showTitleModal && (
          <div className="title-modal-overlay">
            <div className="title-modal" role="dialog" aria-modal="true">
              <h3>Give your session a title</h3>
              <p className="modal-sub">
                This will be used as your session name and prefills the first
                question.
              </p>
              <form onSubmit={handleModalSubmit} className="modal-form">
                <input
                  className="modal-input"
                  placeholder="Enter a title for this session"
                  value={modalTitle}
                  onChange={(e) => setModalTitle(e.target.value)}
                  onBlur={() => setModalTouched(true)}
                  disabled={modalLoading}
                  autoFocus
                />
                <label
                  style={{
                    color: "rgba(255,255,255,0.6)",
                    fontSize: 13,
                    marginTop: 4,
                  }}
                >
                  Agency (Optional)
                </label>
                {agenciesLoading ? (
                  <div
                    style={{
                      padding: "10px 12px",
                      color: "rgba(255,255,255,0.6)",
                    }}
                  >
                    Loading agencies...
                  </div>
                ) : agenciesError ? (
                  <div style={{ color: "#ffb3b3", fontSize: 13 }}>
                    {agenciesError}
                  </div>
                ) : (
                  <select
                    className="modal-input"
                    value={selectedAgency}
                    onChange={(e) => setSelectedAgency(Number(e.target.value))}
                    disabled={modalLoading}
                    style={{ appearance: "none", WebkitAppearance: "none" }}
                  >
                    <option value={0}>-- No Agency --</option>
                    {agencies.map((a) => {
                      const id = a.id ?? a.pk ?? a.value ?? a.key ?? 0;
                      const label =
                        a.name ?? a.title ?? a.label ?? `Agency ${id}`;
                      return (
                        <option key={String(id)} value={id}>
                          {label}
                        </option>
                      );
                    })}
                  </select>
                )}
                {modalTouched && !isModalTitleValid && (
                  <div className="modal-validation">
                    Please enter a session title
                  </div>
                )}
                {modalError && <div className="modal-error">{modalError}</div>}
                <div className="modal-actions">
                  <button
                    type="button"
                    className="modal-cancel"
                    onClick={() => navigate(-1)}
                    disabled={modalLoading}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="modal-submit"
                    disabled={
                      !isModalTitleValid || modalLoading || agenciesLoading
                    }
                  >
                    {modalLoading ? "Creating..." : "Create Session"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════
            BASIC INFO MODAL  (NEW)
        ════════════════════════════════════════ */}
        {/* ════════════════════════════════════════
            BASIC INFO MODAL  (NEW)
        ════════════════════════════════════════ */}
        {showBasicModal && !showTitleModal && (
          <div className="basic-modal-overlay" role="dialog" aria-modal="true">
            <div className="basic-modal">
              {/* Header */}
              <div className="basic-modal-header">
                {/* <div className="basic-modal-badge">Quick Setup</div> */}
                {basicOpenedFromSidebar && (
                  <button
                    className="basic-modal-close"
                    onClick={() => {
                      setShowBasicModal(false);
                      setBasicOpenedFromSidebar(false);
                    }}
                    aria-label="Close"
                  >
                    ✕
                  </button>
                )}
                <h2 className="basic-modal-title">
                  Let’s get to know your business
                </h2>
                <p className="basic-modal-subtitle">
                  Just the basics—then we’ll dive into the real story.
                </p>

                {/* Progress dots */}
                {basicGroup && basicGroup.questions.length > 1 && (
                  <div className="basic-modal-progress">
                    {basicGroup.questions.map((_, i) => (
                      <button
                        key={i}
                        className={`basic-progress-dot ${
                          i === basicModalStep ? "active" : ""
                        } ${
                          answers[basicGroup.questions[i].key]?.trim()
                            ? "filled"
                            : ""
                        }`}
                        onClick={() => setBasicModalStep(i)}
                        aria-label={`Go to question ${i + 1}`}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Questions grid */}
              <div className="basic-modal-body">
                {basicGroup &&
                  basicGroup.questions.map((q, idx) => (
                    <div
                      key={q.key}
                      className={`basic-field-card ${
                        idx === basicModalStep ? "field-card-active" : ""
                      } ${answers[q.key]?.trim() ? "field-card-filled" : ""}`}
                      onClick={() => setBasicModalStep(idx)}
                    >
                      <div className="basic-field-header">
                        <span className="basic-field-num">
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <label className="basic-field-label">
                          {q.question}
                        </label>
                        {answers[q.key]?.trim() && (
                          <span className="basic-field-check">✓</span>
                        )}
                      </div>
                      {q.description && (
                        <p className="basic-field-desc">{q.description}</p>
                      )}
                      <input
                        className="basic-field-input"
                        placeholder={
                          q.placeholder || `Enter ${q.question.toLowerCase()}`
                        }
                        value={answers[q.key] || ""}
                        onChange={(e) => updateAnswer(q.key, e.target.value)}
                        onFocus={() => setBasicModalStep(idx)}
                        autoFocus={idx === 0}
                      />
                    </div>
                  ))}
              </div>

              {/* Footer */}
              <div className="basic-modal-footer">
                {basicError && (
                  <div className="basic-modal-error">{basicError}</div>
                )}
                <div className="basic-modal-footer-row">
                  <span className="basic-modal-counter">
                    <span className="basic-counter-filled">
                      {basicAnsweredCount}
                    </span>
                    <span className="basic-counter-sep"> / </span>
                    <span className="basic-counter-total">
                      {basicGroup?.questions.length ?? 0}
                    </span>
                    <span className="basic-counter-label"> answered</span>
                  </span>
                  <button
                    className={`basic-modal-next ${
                      !allBasicFilled || basicSubmitting ? "disabled" : ""
                    }`}
                    onClick={handleBasicModalSubmit}
                    disabled={!allBasicFilled || basicSubmitting}
                  >
                    {basicSubmitting ? (
                      <>
                        <span className="basic-btn-spinner" />
                        Saving…
                      </>
                    ) : (
                      <>
                        Continue
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 16 16"
                          fill="none"
                          style={{ marginLeft: 8 }}
                        >
                          <path
                            d="M3 8h10M9 4l4 4-4 4"
                            stroke="currentColor"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Decorative glow */}
              <div className="basic-modal-glow" />
            </div>
          </div>
        )}

        {/* <aside
          className="fqs-left"
          aria-hidden={showTitleModal || showBasicModal}
        >
          <div className="fqs-left-inner">
            <div className="fqs-intro">
              <h1>
                Every great brand begins with you.
                <br />
                Eight questions. One honest minute. Ready?
              </h1>
            </div>

            <nav className="fqs-left-nav">
              {basicGroup && basicGroup.questions?.length > 0 && (
                <button
                  type="button"
                  className="fqs-nav-row fqs-nav-basics-btn"
                  onClick={() => setShowBasicModal(true)}
                  aria-label="Back to basics – view or edit your business info"
                >
                  <span className="fqs-nav-basics-icon">◇</span>
                  <span className="fqs-nav-basics-label">
                    Your basics
                  </span>
                </button>
              )}
              {steps.map((step, i) => {
                const label =
                  step.type === "single"
                    ? step.question?.question || "Question"
                    : "Question";

                return (
                  <div
                    key={i}
                    className={`fqs-nav-row ${currentStep === i ? "active" : ""}`}
                    onClick={() => setCurrentStep(i)}
                  >
                    <div className="fqs-nav-num">
                      {String(i + 1).padStart(2, "0")}
                    </div>
                    <div className="fqs-nav-label">{label}</div>
                  </div>
                );
              })}
            </nav>
          </div>
        </aside> */}

        {/* ════════════════════════════════════════
            LEFT SIDEBAR
        ════════════════════════════════════════ */}

        <aside
          className="fqs-left"
          aria-hidden={showTitleModal || showBasicModal}
        >
          <div className="fqs-left-inner">
            <div className="fqs-intro">
              <h1>
                Every great brand begins with you.
                <br />
                Eight questions. One honest minute. Ready?
              </h1>
            </div>

            {/* Scrollable nav */}
            <nav className="fqs-left-nav">
              {steps.map((step, i) => {
                const label =
                  step.type === "single"
                    ? step.question?.question || "Question"
                    : "Question";

                return (
                  <div
                    key={i}
                    className={`fqs-nav-row ${currentStep === i ? "active" : ""}`}
                    onClick={() => setCurrentStep(i)}
                  >
                    <div className="fqs-nav-num">
                      {String(i + 1).padStart(2, "0")}
                    </div>
                    <div className="fqs-nav-label">{label}</div>
                  </div>
                );
              })}
            </nav>
          </div>

          {/* ✅ Button INSIDE aside, at the bottom */}
          {basicGroup && basicGroup.questions.length > 0 && (
            <div className="fqs-sidebar-footer">
              <button
                className="fqs-reopen-basic-btn"
                onClick={handleOpenBasicFromSidebar}
              >
                <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
                  <circle
                    cx="8"
                    cy="8"
                    r="6.5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  />
                  <path
                    d="M8 5v3.5L10 10"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                View Basic Info
              </button>
            </div>
          )}
        </aside>

        {/* ════════════════════════════════════════
            MAIN CONTENT
        ════════════════════════════════════════ */}
        <main
          className="fqs-main"
          aria-hidden={showTitleModal || showBasicModal}
        >
          <div className="fqs-glow-left" />
          <div className="fqs-card-wrapper">
            <div className="fqs-card glow_wrapper">
              <div className="glow-circle" />
              <div className="glow-circle second" />
              <div className="content">
                <h2 className="fqs-title">Get Started!</h2>

                <div className="fqs-stepper">
                  {steps.map((step, idx) => (
                    <React.Fragment key={idx}>
                      <div
                        className={`fqs-pill ${
                          idx === currentStep ? "pill-active" : ""
                        }`}
                        onClick={() => setCurrentStep(idx)}
                      >
                        {renderPill(idx)}
                      </div>
                      {idx < steps.length - 1 && (
                        <div className="fqs-stepline" />
                      )}
                    </React.Fragment>
                  ))}
                </div>

                <div className="fqs-input-area">
                  {currentStepObj?.type === "single" && currentQuestion && (
                    <>
                      <h3 className="fqs-q">{currentQuestion.question}</h3>
                      <p className="fqs-desc">{currentQuestion.description}</p>
                      <input
                        ref={inputRef}
                        className="fqs-input"
                        placeholder={currentQuestion.placeholder}
                        value={currentValue}
                        onChange={(e) =>
                          updateAnswer(currentQuestion.key, e.target.value)
                        }
                      />
                    </>
                  )}
                </div>

                {submitError && (
                  <div className="submit-error">{submitError}</div>
                )}

                <div className="fqs-footer">
                  <button
                    className={`fqs-back ${currentStep === 0 ? "disabled" : ""}`}
                    onClick={handleBack}
                    disabled={currentStep === 0}
                  >
                    Back
                  </button>
                  <button className="fqs-next" onClick={handleNext}>
                    {currentStep < steps.length - 1 ? "Next" : "Submit"}
                  </button>
                </div>
              </div>
            </div>
            <div className="fqs-progress-box">
              <div className="fqs-progress-count">
                {String(answeredCount).padStart(2, "0")}/
                {String(totalCount).padStart(2, "0")}
              </div>
              <div className="fqs-progress-bar">
                <div
                  // className="fqs-progress-fill"
                  style={{ width: `${(answeredCount / totalCount) * 100}%` }}
                />
              </div>
              <div className="fqs-progress-time">Quick · {totalCount} mins</div>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
