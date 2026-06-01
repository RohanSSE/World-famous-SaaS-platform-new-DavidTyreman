// import React, { useEffect, useState } from "react";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";

// export default function BrandSummaryPage() {
//   const [summary, setSummary] = useState("");
//   const [loading, setLoading] = useState(true);

//   useEffect(() => {
//     const loadSummary = async () => {
//       try {
//         const sessionId = localStorage.getItem("sessionId");
//         const resp = await authService.generateBrandSummary(sessionId);
//         setSummary(resp?.summary || "");
//       } catch (e) {
//         console.error(e);
//       } finally {
//         setLoading(false);
//       }
//     };
//     loadSummary();
//   }, []);

//   return (
//     <>
//       <ChatNavbar />

//       <div className="summary-page">
//         <div className="summary-card">
//           <h1>Your Brand Summary</h1>

//           {loading && <p>Creating your brand snapshot…</p>}

//           {!loading &&
//             summary
//               .split("\n\n")
//               .map((para, i) => <p key={i}>{para}</p>)}

//           <div className="summary-actions">
//             <button
//               className="primary"
//               onClick={() => (window.location.href = "/ChatKickoffPage")}
//             >
//               Continue to Chat
//             </button>
//           </div>
//         </div>
//       </div>
//     </>
//   );
// }

// import React, { useEffect, useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
// import HTMLFlipBook from "react-pageflip";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";
// import "../components/BrandSummaryPage.css";

// export default function BrandSummaryPage() {
//   const navigate = useNavigate();
//   const [loading, setLoading] = useState(true);
//   const [summary, setSummary] = useState("");
//   const [error, setError] = useState("");
//   const [pages, setPages] = useState([]);
//   const bookRef = useRef(null);

//   // Enable scrolling (you already have this)
//   useEffect(() => {
//     // ... your existing scroll enabling code ...
//   }, []);

//   useEffect(() => {
//     const loadSummary = async () => {
//       try {
//         const sessionId = localStorage.getItem("sessionId");
//         if (!sessionId) {
//           setError("No session found");
//           setLoading(false);
//           return;
//         }
//         const resp = await authService.generateFoundationSummary(sessionId);
//         const rawSummary = resp?.summary || "";
//         setSummary(rawSummary);

//         // ── Convert summary → magazine-style pages ──
//         const generatedPages = createMagazinePages(rawSummary);
//         setPages(generatedPages);
//       } catch (e) {
//         console.error(e);
//         setError("Failed to load summary");
//       } finally {
//         setLoading(false);
//       }
//     };
//     loadSummary();
//   }, []);

//   // This function turns your markdown-like summary into nice magazine pages
//   const createMagazinePages = (text) => {
//     if (!text) return [];

//     const lines = text.split("\n").filter(Boolean);
//     const pages = [];
//     let currentPageContent = [];
//     let pageNumber = 1;

//     // Cover page
//     pages.push(
//       <div key="cover" className="page page-cover">
//         <div className="cover-content">
//           <h1>Brand Foundation</h1>
//           <h2>Summary</h2>
//           <div className="cover-subtitle">Your Strategic Overview</div>
//           <div className="page-number">Cover</div>
//         </div>
//       </div>
//     );

//     // Content pages
//     lines.forEach((line, idx) => {
//       const trimmed = line.trim();

//       if (trimmed.startsWith("**") && trimmed.endsWith("**")) {
//         // New section → try to put on new page if possible
//         if (currentPageContent.length > 4) {
//           pages.push(createContentPage(currentPageContent, pageNumber++));
//           currentPageContent = [];
//         }
//         currentPageContent.push(<h2 key={idx}>{trimmed.replace(/\*\*/g, "")}</h2>);
//       } else if (/^\d+\./.test(trimmed) || trimmed.startsWith("-")) {
//         currentPageContent.push(
//           <li key={idx}>{trimmed.replace(/^[-\d.]+\s*/, "")}</li>
//         );
//       } else if (trimmed) {
//         currentPageContent.push(<p key={idx}>{trimmed}</p>);
//       }

//       // Rough page break logic (~8–12 elements per page)
//       if (currentPageContent.length >= 10) {
//         pages.push(createContentPage(currentPageContent, pageNumber++));
//         currentPageContent = [];
//       }
//     });

//     if (currentPageContent.length > 0) {
//       pages.push(createContentPage(currentPageContent, pageNumber++));
//     }

//     // Back cover
//     pages.push(
//       <div key="back" className="page page-back">
//         <div className="back-content">
//           <h2>End of Summary</h2>
//           <button
//             className="btn-continue"
//             onClick={() => navigate("/ChatKickoffPage")}
//           >
//             Continue to Chat Kickoff →
//           </button>
//         </div>
//       </div>
//     );

//     return pages;
//   };

//   const createContentPage = (content, pageNum) => (
//     <div key={`page-${pageNum}`} className="page page-content">
//       <div className="page-inner">
//         {content.length > 0 ? (
//           content[0].type === "h2" ? (
//             <>
//               {content[0]}
//               <div className="page-body">{content.slice(1)}</div>
//             </>
//           ) : (
//             <div className="page-body">{content}</div>
//           )
//         ) : null}
//       </div>
//       <div className="page-number">{pageNum}</div>
//     </div>
//   );

//   if (loading) {
//     return (
//       <div className="brand-summary-loader">
//         <div className="loader-spinner"></div>
//         <p>Preparing your brand magazine...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return <div className="brand-summary-error">{error}</div>;
//   }

//   return (
//     <>
//       <ChatNavbar showSaveButton={true} showDownloadButton={true} />

//       <div className="brand-summary-magazine-wrapper">
//         {pages.length > 0 ? (
//           <HTMLFlipBook
//             ref={bookRef}
//             width={550}           // single page width
//             height={780}          // single page height
//             size="stretch"
//             minWidth={320}
//             maxWidth={1000}
//             minHeight={480}
//             maxHeight={1350}
//             drawShadow={true}
//             flippingTime={1200}
//             usePortrait={true}
//             startPage={0}
//             startZIndex={0}
//             autoSize={true}
//             clickEventForward={true}
//             useMouseEvents={true}
//             swipeDistance={40}
//             showPageCorners={true}
//             disableFlipByClick={false}
//             mobileScrollSupport={true}
//             onFlip={(e) => console.log("Page flipped to:", e.data)}
//             onChangeOrientation={() => {}}
//             onChangeState={() => {}}
//           >
//             {pages}
//           </HTMLFlipBook>
//         ) : (
//           <p>No content to display</p>
//         )}
//       </div>
//     </>
//   );
// }

// import React, { useEffect, useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
// import HTMLFlipBook from "react-pageflip";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";
// import "../components/BrandSummaryPage.css";
// // 🔁 Toggle this: true = dummy data, false = real API
// const USE_DUMMY_DATA = true;

// const DUMMY_SUMMARY = `
// **Your Brand at a Glance**
// A modern, customer-first brand focused on simplicity, trust, and clarity.

// **Vision**
// To become the most trusted solution in our category.

// **Mission**
// We help people achieve their goals with simple, powerful tools.

// **Core Values**
// 1. Simplicity
// 2. Transparency
// 3. Reliability
// 4. Innovation

// **Target Audience**
// - Small business owners
// - Startups and founders
// - Marketing teams

// **Brand Personality**
// Friendly, confident, and helpful.

// **Positioning**
// A premium-feeling product that is still easy and approachable.

// **Messaging Pillars**
// - Easy to use
// - Saves time
// - Builds trust
// - Scales with you

// **Tone of Voice**
// Clear, supportive, and motivating.

// **Next Steps**
// Refine messaging, align visuals, and test with users.
// `;

// export default function BrandSummaryPage() {
//   const navigate = useNavigate();
//   const [loading, setLoading] = useState(true);
//   const [summary, setSummary] = useState("");
//   const [error, setError] = useState("");
//   const [pages, setPages] = useState([]);
//   const [dimensions, setDimensions] = useState({ width: 550, height: 780 });
//   const bookRef = useRef(null);

//   // Enable scrolling (you already have this)
//   useEffect(() => {
//     // ... your existing scroll enabling code ...
//   }, []);

//   // Responsive sizing
//   useEffect(() => {
//     const handleResize = () => {
//       const screenWidth = window.innerWidth;
//       const screenHeight = window.innerHeight - 100; // Adjust for navbar and padding
//       let newWidth = Math.min(screenWidth * 0.45, 550); // For double page view (~90% of screen)
//       let newHeight = (newWidth / 550) * 780;
//       if (newHeight > screenHeight) {
//         newHeight = screenHeight;
//         newWidth = (newHeight / 780) * 550;
//       }
//       setDimensions({ width: newWidth, height: newHeight });
//     };
//     handleResize();
//     window.addEventListener("resize", handleResize);
//     return () => window.removeEventListener("resize", handleResize);
//   }, []);

//   useEffect(() => {
//   const loadSummary = async () => {
//     try {
//       let rawSummary = "";

//       if (USE_DUMMY_DATA) {
//         // 🧪 Use fake data (no API, no credits)
//         rawSummary = DUMMY_SUMMARY;
//       } else {
//         // 🌐 Use real API
//         const sessionId = localStorage.getItem("sessionId");
//         if (!sessionId) {
//           setError("No session found");
//           setLoading(false);
//           return;
//         }
//         const resp = await authService.generateFoundationSummary(sessionId);
//         rawSummary = resp?.summary || "";
//       }

//       setSummary(rawSummary);
//       const generatedPages = createMagazinePages(rawSummary);
//       setPages(generatedPages);
//     } catch (e) {
//       console.error(e);
//       setError("Failed to load summary");
//     } finally {
//       setLoading(false);
//     }
//   };

//   loadSummary();
// }, []);

//   // useEffect(() => {
//   //   const loadSummary = async () => {
//   //     try {
//   //       const sessionId = localStorage.getItem("sessionId");
//   //       if (!sessionId) {
//   //         setError("No session found");
//   //         setLoading(false);
//   //         return;
//   //       }
//   //       const resp = await authService.generateFoundationSummary(sessionId);
//   //       const rawSummary = resp?.summary || "";
//   //       setSummary(rawSummary);
//   //       // ── Convert summary → magazine-style pages ──
//   //       const generatedPages = createMagazinePages(rawSummary);
//   //       setPages(generatedPages);
//   //     } catch (e) {
//   //       console.error(e);
//   //       setError("Failed to load summary");
//   //     } finally {
//   //       setLoading(false);
//   //     }
//   //   };
//   //   loadSummary();
//   // }, []);

//   // This function turns your markdown-like summary into nice magazine pages
//   const createMagazinePages = (text) => {
//     if (!text) return [];
//     const lines = text.split("\n").filter(Boolean);
//     const pages = [];
//     let currentPageContent = [];
//     let pageNumber = 1;
//     let shortSummary = "Your Strategic Overview";

//     // Extract short summary from first bold line
//     if (lines.length > 0) {
//       const first = lines[0].trim();
//       if (first.startsWith("**") && first.endsWith("**")) {
//         shortSummary = first.replace(/\*\*/g, "");
//         lines.shift(); // Remove the title line from content
//       }
//     }

//     // Cover page with button
//     pages.push(
//       <div key="cover" className="page page-cover">
//         <div className="cover-content">
//           <h1>Brand Foundation</h1>
//           <h2>Summary</h2>
//           <div className="cover-subtitle">{shortSummary}</div>
//           <button
//             className="btn-open"
//             onClick={() => bookRef.current.pageFlip().flipNext()}
//           >
//             Click to Open
//           </button>
//           <div className="page-number">Cover</div>
//         </div>
//       </div>
//     );

//     // Content pages
//     lines.forEach((line, idx) => {
//       const trimmed = line.trim();
//       if (trimmed.startsWith("**") && trimmed.endsWith("**")) {
//         // New section → try to put on new page if possible
//         if (currentPageContent.length > 4) {
//           pages.push(createContentPage(currentPageContent, pageNumber++));
//           currentPageContent = [];
//         }
//         currentPageContent.push(<h2 key={idx}>{trimmed.replace(/\*\*/g, "")}</h2>);
//       } else if (/^\d+\./.test(trimmed) || trimmed.startsWith("-")) {
//         currentPageContent.push(
//           <li key={idx}>{trimmed.replace(/^[-\d.]+\s*/, "")}</li>
//         );
//       } else if (trimmed) {
//         currentPageContent.push(<p key={idx}>{trimmed}</p>);
//       }
//       // Rough page break logic (~8–12 elements per page)
//       if (currentPageContent.length >= 10) {
//         pages.push(createContentPage(currentPageContent, pageNumber++));
//         currentPageContent = [];
//       }
//     });
//     if (currentPageContent.length > 0) {
//       pages.push(createContentPage(currentPageContent, pageNumber++));
//     }

//     // Back cover
//     pages.push(
//       <div key="back" className="page page-back">
//         <div className="back-content">
//           <h2>End of Summary</h2>
//           <button
//             className="btn-continue"
//             onClick={() => navigate("/ChatKickoffPage")}
//           >
//             Continue to Chat Kickoff →
//           </button>
//         </div>
//       </div>
//     );
//     return pages;
//   };

//   const createContentPage = (content, pageNum) => (
//     <div key={`page-${pageNum}`} className="page page-content">
//       <div className="page-inner">
//         {content.length > 0 ? (
//           content[0].type === "h2" ? (
//             <>
//               {content[0]}
//               <div className="page-body">{content.slice(1)}</div>
//             </>
//           ) : (
//             <div className="page-body">{content}</div>
//           )
//         ) : null}
//       </div>
//       <div className="page-number">{pageNum}</div>
//     </div>
//   );

//   if (loading) {
//     return (
//       <div className="brand-summary-loader">
//         <div className="loader-spinner"></div>
//         <p>Preparing your brand magazine...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return <div className="brand-summary-error">{error}</div>;
//   }

//   return (
//     <>
//       <ChatNavbar showSaveButton={true} showDownloadButton={true} />
//       <div className="brand-summary-magazine-wrapper">
//         {pages.length > 0 ? (
//           <HTMLFlipBook
//             ref={bookRef}
//             width={dimensions.width}
//             height={dimensions.height}
//             size="stretch"
//             minWidth={320}
//             maxWidth={1000}
//             minHeight={480}
//             maxHeight={1350}
//             drawShadow={true}
//             flippingTime={1200}
//             usePortrait={false} // Double page view for left-right spread
//             startPage={0}
//             startZIndex={0}
//             autoSize={true}
//             clickEventForward={true}
//             useMouseEvents={true}
//             swipeDistance={40}
//             showPageCorners={true}
//             disableFlipByClick={false}
//             mobileScrollSupport={true}
//             onFlip={(e) => console.log("Page flipped to:", e.data)}
//             onChangeOrientation={() => {}}
//             onChangeState={() => {}}
//           >
//             {pages}
//           </HTMLFlipBook>
//         ) : (
//           <p>No content to display</p>
//         )}
//       </div>
//     </>
//   );
// }



// import React, { useEffect, useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
// import HTMLFlipBook from "react-pageflip";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";
// import "../components/BrandSummaryPage.css";

// // 🔁 Toggle this: true = dummy data, false = real API
// const USE_DUMMY_DATA = true;

// const DUMMY_SUMMARY = `
// **Your Brand at a Glance**
// A modern, customer-first brand focused on simplicity, trust, and clarity.

// **Vision**
// To become the most trusted solution in our category.

// **Mission**
// We help people achieve their goals with simple, powerful tools.

// **Core Values**
// 1. Simplicity
// 2. Transparency
// 3. Reliability
// 4. Innovation

// **Target Audience**
// - Small business owners
// - Startups and founders
// - Marketing teams

// **Brand Personality**
// Friendly, confident, and helpful.

// **Positioning**
// A premium-feeling product that is still easy and approachable.

// **Messaging Pillars**
// - Easy to use
// - Saves time
// - Builds trust
// - Scales with you

// **Tone of Voice**
// Clear, supportive, and motivating.

// **Next Steps**
// Refine messaging, align visuals, and test with users.
// `;

// export default function BrandSummaryPage() {
//   const navigate = useNavigate();
//   const [loading, setLoading] = useState(true);
//   const [generating, setGenerating] = useState(true);
//   const [summary, setSummary] = useState("");
//   const [error, setError] = useState("");
//   const [pages, setPages] = useState([]);
//   const [dimensions, setDimensions] = useState({ width: 400, height: 600 });
//   const [showCover, setShowCover] = useState(true);
//   const bookRef = useRef(null);

//   // Enable scrolling
//   useEffect(() => {
//     document.body.style.overflow = "auto";
//     return () => {
//       document.body.style.overflow = "";
//     };
//   }, []);

//   // Responsive sizing - optimized for double-page spread
//   useEffect(() => {
//     const handleResize = () => {
//       const screenWidth = window.innerWidth;
//       const screenHeight = window.innerHeight;

//       // Calculate dimensions for double-page spread
//       // Each page should be roughly half the available width
//       const maxSinglePageWidth = Math.min(screenWidth * 0.4, 450);
//       const maxHeight = Math.min(screenHeight * 0.75, 650);

//       // Maintain aspect ratio (roughly 3:4 for a book page)
//       let width = maxSinglePageWidth;
//       let height = width * 1.5; // 3:2 aspect ratio

//       // Adjust if height exceeds max
//       if (height > maxHeight) {
//         height = maxHeight;
//         width = height / 1.5;
//       }

//       // Ensure minimum readable size
//       if (width < 300) {
//         width = 300;
//         height = 450;
//       }

//       setDimensions({ width: Math.floor(width), height: Math.floor(height) });
//     };

//     handleResize();
//     window.addEventListener("resize", handleResize);
//     return () => window.removeEventListener("resize", handleResize);
//   }, []);

//   useEffect(() => {
//     const loadSummary = async () => {
//       try {
//         setGenerating(true);
//         let rawSummary = "";

//         if (USE_DUMMY_DATA) {
//           // Simulate AI generation delay
//           await new Promise((resolve) => setTimeout(resolve, 2000));
//           rawSummary = DUMMY_SUMMARY;
//         } else {
//           const sessionId = localStorage.getItem("sessionId");
//           if (!sessionId) {
//             setError("No session found");
//             setLoading(false);
//             setGenerating(false);
//             return;
//           }
//           const resp = await authService.generateFoundationSummary(sessionId);
//           rawSummary = resp?.summary || "";
//         }

//         setSummary(rawSummary);
//         const generatedPages = createMagazinePages(rawSummary);
//         setPages(generatedPages);
//         setGenerating(false);
//       } catch (e) {
//         console.error(e);
//         setError("Failed to load summary");
//         setGenerating(false);
//       } finally {
//         setLoading(false);
//       }
//     };

//     loadSummary();
//   }, []);

//   const createMagazinePages = (text) => {
//     if (!text) return [];
//     const lines = text.split("\n").filter(Boolean);
//     const pages = [];
//     let currentPageContent = [];
//     let pageNumber = 1;
//     let shortSummary = "Your Strategic Overview";

//     // Extract short summary from first bold line
//     if (lines.length > 0) {
//       const first = lines[0].trim();
//       if (first.startsWith("**") && first.endsWith("**")) {
//         shortSummary = first.replace(/\*\*/g, "");
//         lines.shift();
//       }
//     }

//     // Cover page with click to open
//     pages.push(
//       <div key="cover" className="page page-cover" data-density="hard">
//         <div className="cover-content">
//           <div className="cover-ornament">✦</div>
//           <h1 className="cover-title">Brand Foundation</h1>
//           <h2 className="cover-subtitle-main">Summary</h2>
//           <p className="cover-description">{shortSummary}</p>

//           {generating ? (
//             <div className="cover-loading">
//               <div className="spinner"></div>
//               <p className="loading-text">Generating your summary...</p>
//             </div>
//           ) : (
//             <button
//               className="btn-open"
//               onClick={() => {
//                 setShowCover(false);
//                 setTimeout(() => {
//                   bookRef.current?.pageFlip().flipNext();
//                 }, 100);
//               }}
//             >
//               Click to Open
//             </button>
//           )}

//           <div className="cover-footer">Page 1</div>
//         </div>
//       </div>,
//     );

//     // Content pages - distribute evenly between left and right
//     lines.forEach((line, idx) => {
//       const trimmed = line.trim();

//       if (trimmed.startsWith("**") && trimmed.endsWith("**")) {
//         // New section - create page break if content exists
//         if (currentPageContent.length > 3) {
//           pages.push(createContentPage(currentPageContent, pageNumber++));
//           currentPageContent = [];
//         }
//         currentPageContent.push(
//           <h2 key={idx} className="section-title">
//             {trimmed.replace(/\*\*/g, "")}
//           </h2>,
//         );
//       } else if (/^\d+\./.test(trimmed)) {
//         currentPageContent.push(
//           <li key={idx} className="list-item numbered">
//             {trimmed.replace(/^\d+\.\s*/, "")}
//           </li>,
//         );
//       } else if (trimmed.startsWith("-")) {
//         currentPageContent.push(
//           <li key={idx} className="list-item bullet">
//             {trimmed.replace(/^-\s*/, "")}
//           </li>,
//         );
//       } else if (trimmed) {
//         currentPageContent.push(
//           <p key={idx} className="body-text">
//             {trimmed}
//           </p>,
//         );
//       }

//       // Page break logic - aim for 8-12 elements per page
//       if (currentPageContent.length >= 10) {
//         pages.push(createContentPage(currentPageContent, pageNumber++));
//         currentPageContent = [];
//       }
//     });

//     if (currentPageContent.length > 0) {
//       pages.push(createContentPage(currentPageContent, pageNumber++));
//     }

//     // Back cover with continue button
//     pages.push(
//       <div key="back" className="page page-back" data-density="hard">
//         <div className="back-content">
//           <div className="back-ornament">✦</div>
//           <h2 className="back-title">End of Summary</h2>
//           <p className="back-message">Your brand foundation is ready</p>
//           <button
//             className="btn-continue"
//             onClick={() => navigate("/ChatKickoffPage")}
//           >
//             Continue to Chat Kickoff →
//           </button>
//           <div className="back-footer">The End</div>
//         </div>
//       </div>,
//     );

//     return pages;
//   };

//   const createContentPage = (content, pageNum) => {
//     const hasTitle = content.length > 0 && content[0].type === "h2";

//     return (
//       <div key={`page-${pageNum}`} className="page page-content">
//         <div className="page-inner">
//           {hasTitle ? (
//             <>
//               {content[0]}
//               <div className="page-body">
//                 {content.slice(1).map((item, i) => (
//                   <React.Fragment key={i}>{item}</React.Fragment>
//                 ))}
//               </div>
//             </>
//           ) : (
//             <div className="page-body">
//               {content.map((item, i) => (
//                 <React.Fragment key={i}>{item}</React.Fragment>
//               ))}
//             </div>
//           )}
//         </div>
//         <div className="page-number">{pageNum + 1}</div>
//       </div>
//     );
//   };

//   if (loading && !pages.length) {
//     return (
//       <div className="brand-summary-loader">
//         <div className="loader-spinner"></div>
//         <p>Preparing your brand magazine...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="brand-summary-error">
//         <p>{error}</p>
//         <button onClick={() => navigate("/")}>Go Back</button>
//       </div>
//     );
//   }

//   return (
//     <>
//       <ChatNavbar showSaveButton={true} showDownloadButton={true} />
//       <div className="brand-summary-magazine-wrapper">
//         <div className="magazine-container">
//           {pages.length > 0 ? (
//             <HTMLFlipBook
//               ref={bookRef}
//               width={dimensions.width}
//               height={dimensions.height}
//               size="stretch"
//               minWidth={300}
//               maxWidth={500}
//               minHeight={450}
//               maxHeight={750}
//               drawShadow={true}
//               flippingTime={800}
//               usePortrait={false}
//               startPage={0}
//               startZIndex={10}
//               autoSize={false}
//               clickEventForward={true}
//               useMouseEvents={true}
//               swipeDistance={30}
//               showPageCorners={true}
//               disableFlipByClick={false}
//               mobileScrollSupport={true}
//               className="flipbook"
//               style={{}}
//               onFlip={(e) => console.log("Flipped to page:", e.data)}
//             >
//               {pages}
//             </HTMLFlipBook>
//           ) : (
//             <div className="no-content">
//               <p>No content to display</p>
//             </div>
//           )}
//         </div>

//         {/* Page flip hint */}
//         {!showCover && pages.length > 2 && (
//           <div className="flip-hint">
//             <span className="hint-text">Click on page edges to flip</span>
//           </div>
//         )}
//       </div>
//     </>
//   );
// }

// import React, { useEffect, useState, useRef } from "react";
// import { useNavigate } from "react-router-dom";
// import HTMLFlipBook from "react-pageflip";
// import ChatNavbar from "./ChatNavbar";
// import authService from "../services/authService";
// import "../components/BrandSummaryPage.css";


// // 🔁 Toggle this: true = dummy data, false = real API
// const USE_DUMMY_DATA = true;

// const DUMMY_SUMMARY = `
// **Your Brand at a Glance**
// A modern, customer-first brand focused on simplicity, trust, and clarity.

// **Vision**
// To become the most trusted solution in our category.

// **Mission**
// We help people achieve their goals with simple, powerful tools.

// **Core Values**
// 1. Simplicity
// 2. Transparency
// 3. Reliability
// 4. Innovation

// **Target Audience**
// - Small business owners
// - Startups and founders
// - Marketing teams

// **Brand Personality**
// Friendly, confident, and helpful.

// **Positioning**
// A premium-feeling product that is still easy and approachable.

// **Messaging Pillars**
// - Easy to use
// - Saves time
// - Builds trust
// - Scales with you

// **Tone of Voice**
// Clear, supportive, and motivating.

// **Next Steps**
// Refine messaging, align visuals, and test with users.
// `;

// export default function BrandSummaryPage() {
//   const navigate = useNavigate();
//   const [loading, setLoading] = useState(true);
//   const [generating, setGenerating] = useState(true);
//   const [summary, setSummary] = useState("");
//   const [error, setError] = useState("");
//   const [pages, setPages] = useState([]);
//   const [dimensions, setDimensions] = useState({ width: 400, height: 600 });
//   const [showCover, setShowCover] = useState(true);
//   const bookRef = useRef(null);

//   // Enable scrolling
//   useEffect(() => {
//     document.body.style.overflow = "auto";
//     return () => {
//       document.body.style.overflow = "";
//     };
//   }, []);

//   // Responsive sizing - optimized for double-page spread
//   useEffect(() => {
//     const handleResize = () => {
//       const screenWidth = window.innerWidth;
//       const screenHeight = window.innerHeight;
      
//       // Calculate dimensions for double-page spread
//       // Each page should be roughly half the available width
//       const maxSinglePageWidth = Math.min(screenWidth * 0.4, 450);
//       const maxHeight = Math.min(screenHeight * 0.75, 650);
      
//       // Maintain aspect ratio (roughly 3:4 for a book page)
//       let width = maxSinglePageWidth;
//       let height = width * 1.5; // 3:2 aspect ratio
      
//       // Adjust if height exceeds max
//       if (height > maxHeight) {
//         height = maxHeight;
//         width = height / 1.5;
//       }
      
//       // Ensure minimum readable size
//       if (width < 300) {
//         width = 300;
//         height = 450;
//       }
      
//       setDimensions({ width: Math.floor(width), height: Math.floor(height) });
//     };
    
//     handleResize();
//     window.addEventListener("resize", handleResize);
//     return () => window.removeEventListener("resize", handleResize);
//   }, []);

//   useEffect(() => {
//     const loadSummary = async () => {
//       try {
//         setGenerating(true);
//         let rawSummary = "";

//         if (USE_DUMMY_DATA) {
//           // Simulate AI generation delay
//           await new Promise(resolve => setTimeout(resolve, 2000));
//           rawSummary = DUMMY_SUMMARY;
//         } else {
//           const sessionId = localStorage.getItem("sessionId");
//           if (!sessionId) {
//             setError("No session found");
//             setLoading(false);
//             setGenerating(false);
//             return;
//           }
//           const resp = await authService.generateFoundationSummary(sessionId);
//           rawSummary = resp?.summary || "";
//         }

//         setSummary(rawSummary);
//         const generatedPages = createMagazinePages(rawSummary);
//         setPages(generatedPages);
//         setGenerating(false);
//       } catch (e) {
//         console.error(e);
//         setError("Failed to load summary");
//         setGenerating(false);
//       } finally {
//         setLoading(false);
//       }
//     };

//     loadSummary();
//   }, []);

//   const createMagazinePages = (text) => {
//     if (!text) return [];
//     const lines = text.split("\n").filter(Boolean);
//     const pages = [];
//     let shortSummary = "Your Strategic Overview";

//     // Extract short summary from first bold line
//     if (lines.length > 0) {
//       const first = lines[0].trim();
//       if (first.startsWith("**") && first.endsWith("**")) {
//         shortSummary = first.replace(/\*\*/g, "");
//         lines.shift();
//       }
//     }

//     // Page 1: Cover page (shows alone first)
//     pages.push(
//       <div key="cover" className="page page-cover" data-density="hard">
//         <div className="cover-content">
//           <div className="cover-ornament">✦</div>
//           <h1 className="cover-title">Brand Foundation</h1>
//           <h2 className="cover-subtitle-main">Summary</h2>
//           <p className="cover-description">{shortSummary}</p>
          
//           {generating ? (
//             <div className="cover-loading">
//               <div className="spinner"></div>
//               <p className="loading-text">Generating your summary...</p>
//             </div>
//           ) : (
//             <button
//               className="btn-open"
//               onClick={() => {
//                 setShowCover(false);
//                 setTimeout(() => {
//                   bookRef.current?.pageFlip().flipNext();
//                 }, 100);
//               }}
//             >
//               Click to Open
//             </button>
//           )}
          
//           <div className="cover-footer">Page 1</div>
//         </div>
//       </div>
//     );

//     // Collect all content elements
//     const allContent = [];
//     lines.forEach((line, idx) => {
//       const trimmed = line.trim();
      
//       if (trimmed.startsWith("**") && trimmed.endsWith("**")) {
//         allContent.push(
//           <h2 key={idx} className="section-title">
//             {trimmed.replace(/\*\*/g, "")}
//           </h2>
//         );
//       } else if (/^\d+\./.test(trimmed)) {
//         allContent.push(
//           <li key={idx} className="list-item numbered">
//             {trimmed.replace(/^\d+\.\s*/, "")}
//           </li>
//         );
//       } else if (trimmed.startsWith("-")) {
//         allContent.push(
//           <li key={idx} className="list-item bullet">
//             {trimmed.replace(/^-\s*/, "")}
//           </li>
//         );
//       } else if (trimmed) {
//         allContent.push(
//           <p key={idx} className="body-text">
//             {trimmed}
//           </p>
//         );
//       }
//     });

//     // Split content into two pages (left and right)
//     const midPoint = Math.ceil(allContent.length / 2);
//     const leftContent = allContent.slice(0, midPoint);
//     const rightContent = allContent.slice(midPoint);

//     // Page 2: Left side content
//     pages.push(
//       <div key="page-left" className="page page-content">
//         <div className="page-inner">
//           <div className="page-body">
//             {leftContent.map((item, i) => (
//               <React.Fragment key={i}>{item}</React.Fragment>
//             ))}
//           </div>
//         </div>
//         <div className="page-number">2</div>
//       </div>
//     );

//     // Page 3: Right side content
//     pages.push(
//       <div key="page-right" className="page page-content">
//         <div className="page-inner">
//           <div className="page-body">
//             {rightContent.map((item, i) => (
//               <React.Fragment key={i}>{item}</React.Fragment>
//             ))}
//           </div>
//         </div>
//         <div className="page-number">3</div>
//       </div>
//     );

//     // Page 4: Back cover with continue button
//     pages.push(
//       <div key="back" className="page page-back" data-density="hard">
//         <div className="back-content">
//           <div className="back-ornament">✦</div>
//           <h2 className="back-title">End of Summary</h2>
//           <p className="back-message">Your brand foundation is ready</p>
//           <button
//             className="btn-continue"
//             onClick={() => navigate("/ChatKickoffPage")}
//           >
//             Continue to Chat Kickoff →
//           </button>
//           <div className="back-footer">The End</div>
//         </div>
//       </div>
//     );

//     return pages;
//   };

//   if (loading && !pages.length) {
//     return (
//       <div className="brand-summary-loader">
//         <div className="loader-spinner"></div>
//         <p>Preparing your brand magazine...</p>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="brand-summary-error">
//         <p>{error}</p>
//         <button onClick={() => navigate("/")}>Go Back</button>
//       </div>
//     );
//   }

//   return (
//     <>
//       <ChatNavbar showSaveButton={true} showDownloadButton={true} />
//       <div className="brand-summary-magazine-wrapper">
//         <div className="magazine-container">
//           {pages.length > 0 ? (
//             <HTMLFlipBook
//               ref={bookRef}
//               width={dimensions.width}
//               height={dimensions.height}
//               size="stretch"
//               minWidth={300}
//               maxWidth={500}
//               minHeight={450}
//               maxHeight={750}
//               drawShadow={true}
//               flippingTime={800}
//               usePortrait={false}
//               startPage={0}
//               startZIndex={10}
//               autoSize={false}
//               clickEventForward={true}
//               useMouseEvents={true}
//               swipeDistance={30}
//               showPageCorners={true}
//               disableFlipByClick={false}
//               mobileScrollSupport={true}
//               className="flipbook"
//               style={{}}
//               onFlip={(e) => console.log("Flipped to page:", e.data)}
//             >
//               {pages}
//             </HTMLFlipBook>
//           ) : (
//             <div className="no-content">
//               <p>No content to display</p>
//             </div>
//           )}
//         </div>
        
//         {/* Page flip hint */}
//         {!showCover && pages.length > 2 && (
//           <div className="flip-hint">
//             <span className="hint-text">Click on page edges to flip</span>
//           </div>
//         )}
//       </div>
//     </>
//   );
// }

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import authService from "../services/authService";
import "../components/BrandSummaryPage.css";
import logo from "../assets/mask-group.png";
import BrandOrb from "../components/orb/BrandOrb";
import OrbPresence from "../components/orb/OrbPresence";
import { useOrbPresence } from "../context/OrbPresenceContext";
import { downloadBrandBookScreenPdf } from "../utils/BrandBookPdfGenerator";

// Set to false to use real API (generateFoundationSummary); true for dummy data
const USE_DUMMY_DATA = false;

const DUMMY_SUMMARY = `
**Your Brand at a Glance**
A modern, customer-first brand focused on simplicity, trust, and clarity.

**Vision**
To become the most trusted solution in our category.

**Mission**
We help people achieve their goals with simple, powerful tools.

**Core Values**
1. Simplicity
2. Transparency
3. Reliability
4. Innovation

**Target Audience**
- Small business owners
- Startups and founders
- Marketing teams

**Brand Personality**
Friendly, confident, and helpful.

**Positioning**
A premium-feeling product that is still easy and approachable.

**Messaging Pillars**
- Easy to use
- Saves time
- Builds trust
- Scales with you

**Tone of Voice**
Clear, supportive, and motivating.

**Next Steps**
Refine messaging, align visuals, and test with users.
`;

/** Map backend type to our display type (heading, subsection, body, bullet, numbered, blockquote) */
function normalizeBlockType(backendType) {
  const t = String(backendType || "").toLowerCase();
  if (
    t === "heading" ||
    t === "section" ||
    t === "title" ||
    t === "header" ||
    t === "section_title" ||
    t === "h1" ||
    t === "h2"
  ) return "heading";
  if (
    t === "subheading" ||
    t === "subsection" ||
    t === "sub_title" ||
    t === "subtitle" ||
    t === "sub_header" ||
    t === "h3" ||
    t === "h4"
  ) return "subsection";
  if (t === "blockquote" || t === "quote" || t === "pull_quote" || t === "highlight") return "blockquote";
  if (t === "paragraph" || t === "body" || t === "text" || t === "content") return "body";
  if (t === "list_item" || t === "bullet" || t === "bullet_point") return "bullet";
  if (t === "numbered_item" || t === "numbered" || t === "numbered_point") return "numbered";
  return "body";
}

/** Safely get a single display string from a block item */
function blockItemToText(item) {
  const raw = item?.text ?? item?.content ?? item?.label ?? item?.body ?? "";
  if (typeof raw === "string") return raw.trim();
  if (Array.isArray(raw)) return raw.map((x) => (typeof x === "string" ? x : x?.text ?? x?.content ?? "")).join("\n").trim();
  if (raw != null && typeof raw === "object") return String(raw.text ?? raw.content ?? "").trim();
  return "";
}

/** Build elements from backend structured response (sections/blocks with type + text) */
function parseStructuredResponse(resp) {
  const brandName = resp?.brand_name || resp?.brandName || resp?.title || "Your Brand at a Glance";
  const heading = resp?.heading || resp?.headline || null;
  const subheading = resp?.subheading || resp?.sub_headline || resp?.subtitle || null;
  const title = resp?.title || (heading ? null : brandName);
  const rawSections = resp?.sections ?? resp?.blocks ?? resp?.content ?? [];
  if (!Array.isArray(rawSections) || rawSections.length === 0) {
    return { brandName, heading, subheading, title, elements: [] };
  }
  const elements = rawSections.map((item, idx) => {
    const text = blockItemToText(item);
    const type = normalizeBlockType(item?.type);
    return { type, text, key: idx };
  }).filter((el) => el.text);
  return { brandName, heading, subheading, title, elements };
}

/** Always return a string from API summary field (string, array, or object) */
function summaryToDisplayString(raw) {
  if (raw == null) return "";
  if (typeof raw === "string") return raw;
  if (Array.isArray(raw)) return raw.map((x) => (typeof x === "string" ? x : x?.text ?? x?.content ?? "")).join("\n");
  if (typeof raw === "object" && (raw.text != null || raw.content != null)) return String(raw.text ?? raw.content ?? "");
  return "";
}

function parseSummary(text) {
  const str = summaryToDisplayString(text);
  if (!str) return { brandName: "Your Brand at a Glance", heading: null, subheading: null, title: null, elements: [] };
  const lines = str.split("\n").filter(Boolean);
  const elements = [];
  let brandName = "Your Brand at a Glance";
  let headingCount = 0;

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (idx === 0 && trimmed.startsWith("**") && trimmed.endsWith("**")) {
      brandName = trimmed.replace(/\*\*/g, "");
      return;
    }
    if (trimmed.startsWith("###")) {
      const subText = trimmed.replace(/^#+\s*(\d+\.\s*)?/, "").trim();
      elements.push({ type: "subsection", text: subText, key: idx });
      headingCount += 1;
      return;
    }
    if (trimmed.startsWith("**") && trimmed.endsWith("**") && !trimmed.slice(2, -2).includes("**")) {
      elements.push({ type: "heading", text: trimmed.replace(/\*\*/g, ""), key: idx });
      headingCount += 1;
    } else if (/^#{1,2}\s+/.test(trimmed)) {
      elements.push({ type: "heading", text: trimmed.replace(/^#{1,2}\s*/, "").trim(), key: idx });
      headingCount += 1;
    } else if (/^#{4,6}\s+/.test(trimmed)) {
      elements.push({ type: "subsection", text: trimmed.replace(/^#{4,6}\s*/, "").trim(), key: idx });
      headingCount += 1;
    } else if (/^[A-Za-z][A-Za-z0-9&/(),\-\s]{1,60}:$/.test(trimmed)) {
      elements.push({ type: "heading", text: trimmed.replace(/:$/, ""), key: idx });
      headingCount += 1;
    } else if (/^\d+\./.test(trimmed)) {
      elements.push({ type: "numbered", text: trimmed.replace(/^\d+\.\s*/, ""), key: idx });
    } else if (trimmed.startsWith("-")) {
      elements.push({ type: "bullet", text: trimmed.replace(/^-\s*/, ""), key: idx });
    } else if (trimmed) {
      elements.push({ type: "body", text: trimmed, key: idx });
    }
  });

  // Fallback: if legacy text has no explicit heading markers,
  // promote short title-like lines to headings/subheadings.
  if (headingCount === 0) {
    const promoted = elements.map((el, i) => {
      if (el.type !== "body") return el;
      const txt = String(el.text || "").trim();
      const words = txt.split(/\s+/).filter(Boolean);
      const isTitleLike =
        words.length > 0 &&
        words.length <= 7 &&
        !/[.!?]$/.test(txt) &&
        /^[A-Z0-9][A-Za-z0-9&/(),\-\s]+$/.test(txt);
      if (!isTitleLike) return el;
      return { ...el, type: i % 2 === 0 ? "heading" : "subsection" };
    });
    return { brandName, heading: null, subheading: null, title: null, elements: promoted };
  }

  return { brandName, heading: null, subheading: null, title: null, elements };
}

/** Get top-level or nested sections/blocks/content from API response */
function getStructuredPayload(resp) {
  if (!resp || typeof resp !== "object") return null;
  const top = resp?.sections ?? resp?.blocks ?? resp?.content;
  if (Array.isArray(top) && top.length > 0) return { ...resp, sections: top };
  const data = resp?.data;
  if (data && typeof data === "object") {
    const inData = data?.sections ?? data?.blocks ?? data?.content;
    if (Array.isArray(inData) && inData.length > 0) return { ...data, sections: inData };
  }
  const summary = resp?.summary;
  if (summary && typeof summary === "object" && !Array.isArray(summary)) {
    const inSummary = summary?.sections ?? summary?.blocks ?? summary?.content;
    if (Array.isArray(inSummary) && inSummary.length > 0) return { ...summary, sections: inSummary };
  }
  return null;
}

/** Decide whether API returned structured (sections/blocks) or legacy summary string */
function getElementsFromApiResponse(resp) {
  const structured = getStructuredPayload(resp);
  if (structured) return parseStructuredResponse(structured);
  const summaryStr = summaryToDisplayString(resp?.summary);
  return parseSummary(summaryStr);
}

/** Total word count for density-based font scaling */
function countWords(elements) {
  return (elements || []).reduce((acc, el) => {
    const t = el?.text;
    const s = typeof t === "string" ? t : t != null ? String(t) : "";
    return acc + (s.split(/\s+/).filter(Boolean).length);
  }, 0);
}

/** Renders text with inline **bold** and *italic* as React nodes */
function renderInlineFormatted(text, keyPrefix = "i") {
  if (!text || typeof text !== "string") return text;
  const parts = [];
  let lastIndex = 0;
  const re = /\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_/g;
  let m;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) {
      parts.push(<React.Fragment key={`${keyPrefix}-${key++}`}>{text.slice(lastIndex, m.index)}</React.Fragment>);
    }
    if (m[1]) parts.push(<strong key={`${keyPrefix}-${key++}`}>{m[1]}</strong>);
    else if (m[2]) parts.push(<em key={`${keyPrefix}-${key++}`}>{m[2]}</em>);
    else if (m[3]) parts.push(<em key={`${keyPrefix}-${key++}`}>{m[3]}</em>);
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(<React.Fragment key={`${keyPrefix}-${key++}`}>{text.slice(lastIndex)}</React.Fragment>);
  }
  return parts.length > 0 ? parts : text;
}

function RenderElement({ el, dropCap = false }) {
  if (el.type === "heading") {
    return (
      <h3 className="bsp-section-title">
        {renderInlineFormatted(el.text, `h-${el.key}`)}
      </h3>
    );
  }
  if (el.type === "subsection") {
    return (
      <h4 className="bsp-subsection-title">
        {renderInlineFormatted(el.text, `sub-${el.key}`)}
      </h4>
    );
  }
  if (el.type === "blockquote") {
    return (
      <blockquote className="bsp-blockquote">
        <span className="bsp-blockquote-open">"</span>
        {renderInlineFormatted(el.text, `q-${el.key}`)}
        <span className="bsp-blockquote-close">"</span>
      </blockquote>
    );
  }
  if (el.type === "numbered") {
    return (
      <li className="bsp-list-item bsp-numbered">
        <span className="bsp-marker">▸</span>
        {renderInlineFormatted(el.text, `n-${el.key}`)}
      </li>
    );
  }
  if (el.type === "bullet") {
    return (
      <li className="bsp-list-item bsp-bullet">
        <span className="bsp-marker">◆</span>
        {renderInlineFormatted(el.text, `b-${el.key}`)}
      </li>
    );
  }
  return (
    <p className={`bsp-body-text ${dropCap ? "bsp-drop-cap" : ""}`}>
      {renderInlineFormatted(el.text, `p-${el.key}`)}
    </p>
  );
}

// Stages:
// "cover"   — single page centered
// "opening" — flip animation outward
// "spread"  — double-page spread visible
// "closing" — right page flipping away
// "end"     — end single page

export default function BrandSummaryPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { setOrbThinking, setOrbSpeaking, setOrbIdle } = useOrbPresence();
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [brandName, setBrandName] = useState("Your Brand");
  const [elements, setElements] = useState([]);
  const [brandBookPages, setBrandBookPages] = useState([]);
  const [sidebarTitle, setSidebarTitle] = useState("Brand Book");
  const [sessionId, setSessionId] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  // const [rawApiResponse, setRawApiResponse] = useState(null);
  // const [showRawResponse, setShowRawResponse] = useState(false);
  const [heading, setHeading] = useState(null);
  const [subheading, setSubheading] = useState(null);
  const [title, setTitle] = useState(null);
  const [orbInsight, setOrbInsight] = useState("");
  const [orbInsightLoading, setOrbInsightLoading] = useState(false);
  const insightCacheRef = useRef({});

  useEffect(() => {
    document.body.style.overflow = "auto";
    return () => {
      document.body.style.overflow = "";
    };
  }, []);

  useEffect(() => {
    const load = async () => {
      try {
        let raw = "";
        if (USE_DUMMY_DATA) {
          await new Promise((r) => setTimeout(r, 900));
          raw = DUMMY_SUMMARY;
        } else {
          let sid = localStorage.getItem("sessionId");
          if (!sid) {
            try {
              const sessionJson = localStorage.getItem("session");
              const session = sessionJson ? JSON.parse(sessionJson) : null;
              sid = session?.id ?? session?.pk ?? null;
            } catch (_) {}
          }
          if (!sid) {
            setError("No session found. Complete foundation questions or start a session first.");
            setLoading(false);
            return;
          }
          setSessionId(String(sid));
          let resp = null;
          try {
            // Final brand book should use all 30 answers.
            resp = await authService.generateSessionSummary(sid);
          } catch {
            // Backward fallback when full summary endpoint is unavailable.
            resp = await authService.generateFoundationSummary(sid);
          }
          const serverBook = Array.isArray(resp?.brand_book?.pages) ? resp.brand_book.pages : [];
          if (serverBook.length > 0) {
            setBrandBookPages(serverBook);
            setSidebarTitle(resp?.brand_book?.sidebar_title || "Brand Book");
            setBrandName(resp?.brand_book?.brand_name || "Your Brand");
          }
          // setRawApiResponse(resp);
          let parsed;
          try {
            parsed = getElementsFromApiResponse(resp);
          } catch (_) {
            parsed = parseSummary(summaryToDisplayString(resp?.summary));
          }
          const { brandName: bn, heading: h, subheading: sh, title: t, elements } = parsed;
          setBrandName(bn);
          setHeading(h || resp?.heading || resp?.headline || null);
          setSubheading(sh || resp?.subheading || resp?.sub_headline || resp?.subtitle || null);
          setTitle(t || resp?.title || null);
          setElements(elements);
          return;
        }
        const { brandName: bn, heading: h, subheading: sh, title: t, elements } = parseSummary(raw);
        setBrandName(bn);
        setHeading(h);
        setSubheading(sh);
        setTitle(t);
        setElements(elements);
      } catch (e) {
        console.error("Brand summary load error:", e);
        const message =
          e?.response?.data?.detail ||
          (Array.isArray(e?.response?.data?.detail) ? e.response.data.detail[0] : null) ||
          e?.response?.data?.message ||
          e?.message ||
          "Failed to load summary";
        setError(typeof message === "string" ? message : "Failed to load summary");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const pages = useMemo(() => {
    if (brandBookPages.length > 0) {
      return brandBookPages;
    }
    const output = [];
    let bucket = [];
    const maxPerPage = 8;
    elements.forEach((el) => {
      const isBreakCandidate = el.type === "heading" || el.type === "subsection";
      if (bucket.length >= maxPerPage || (isBreakCandidate && bucket.length >= maxPerPage - 2)) {
        output.push(bucket);
        bucket = [];
      }
      bucket.push(el);
    });
    if (bucket.length > 0) output.push(bucket);
    return output.length > 0 ? output : [[]];
  }, [elements]);

  useEffect(() => {
    if (currentPage > pages.length - 1) {
      setCurrentPage(0);
    }
  }, [currentPage, pages.length]);

  const handleExport = async () => {
    if (exporting) return;
    setExporting(true);
    try {
      await downloadBrandBookScreenPdf({
        brandName,
        contentDensity,
        elements,
        heading,
        pages,
        sidebarTitle,
        subheading,
        title,
      });
    } catch (err) {
      const msg = err?.message || "Export failed";
      setError(msg);
    } finally {
      setExporting(false);
    }
  };

  const userInitial = (() => {
    try {
      const auth = localStorage.getItem("auth");
      const parsed = auth ? JSON.parse(auth) : null;
      return (parsed?.user?.name || parsed?.user?.email || "A").charAt(0).toUpperCase();
    } catch {
      return "A";
    }
  })();

  const activePage = pages[currentPage] || {};
  const activeElements = Array.isArray(activePage) ? activePage : activePage?.elements || [];
  const totalPages = pages.length;
  const words = countWords(elements);
  const contentDensity = words > 450 ? "compact" : words < 180 ? "spacious" : "normal";

  const goPrev = () => setCurrentPage((p) => Math.max(0, p - 1));
  const goNext = () => setCurrentPage((p) => Math.min(totalPages - 1, p + 1));

  useEffect(() => {
    const requestedPage = Number(location.state?.page);
    if (Number.isFinite(requestedPage) && requestedPage >= 0) {
      setCurrentPage(Math.min(requestedPage, Math.max(0, totalPages - 1)));
    }
  }, [location.state, totalPages]);

  const pageHasOverview = Array.isArray(activePage?.overview_fields) && activePage.overview_fields.length > 0;
  const renderMetaFields = pageHasOverview || currentPage === 0;

  const getMeta = (label) => {
    const source = elements.find(
      (el) => el.type === "heading" && String(el.text || "").toLowerCase().includes(label.toLowerCase()),
    );
    if (!source) return "Not specified";
    const idx = elements.findIndex((x) => x.key === source.key);
    const next = elements[idx + 1];
    return next?.text || "Not specified";
  };

  const showHeadingInsight = async (headingText, contentText = "") => {
    const key = `${currentPage}::${headingText}::${contentText.slice(0, 120)}`;
    if (insightCacheRef.current[key]) {
      setOrbInsight(insightCacheRef.current[key]);
      setOrbSpeaking();
      return;
    }
    if (!sessionId) return;
    setOrbInsightLoading(true);
    setOrbThinking("Reading this section...");
    try {
      const res = await authService.getBrandBookHeadingInsight(sessionId, {
        heading: headingText,
        content: contentText,
        page_id: activePage?.id || "",
      });
      const toEnglishInsight = (heading, content, serverMsg = "") => {
        const h = String(heading || "").toLowerCase();
        const c = String(content || "").trim();
        const first = c ? `${c.split(".")[0].trim()}.` : "";
        if (h.includes("overview")) {
          return `This section gives a high-level brand blueprint: identity, category position, and core purpose.${first ? ` Key insight: ${first}` : ""}`;
        }
        if (h.includes("dna")) {
          return `This section reveals your brand's core traits that shape tone, behavior, and decisions.${first ? ` Key insight: ${first}` : ""}`;
        }
        if (h.includes("promise")) {
          return `This heading clarifies the consistent outcome and experience customers should expect.${first ? ` Key insight: ${first}` : ""}`;
        }
        if (h.includes("emotional")) {
          return `This section highlights the emotional before/after transformation for customers.${first ? ` Key insight: ${first}` : ""}`;
        }
        if (h.includes("differentiation")) {
          return `This point explains your unique market edge and why your brand stands apart.${first ? ` Key insight: ${first}` : ""}`;
        }
        if (h.includes("style") || h.includes("tone") || h.includes("visual")) {
          return `This section decodes brand expression: voice, visual mood, and design direction.${first ? ` Key insight: ${first}` : ""}`;
        }
        if (h.includes("tagline")) {
          return `This section provides concise messaging options that make the brand memorable.${first ? ` Key insight: ${first}` : ""}`;
        }
        const s = String(serverMsg || "").trim();
        const hasHinglishCue = /\b(ka|ki|se|hai|aur|yahaan|yahan|samajh|aap|milta|dikhta|kyu|kya)\b/i.test(s);
        if (!s || hasHinglishCue) {
          return `This heading explains a focused strategic angle that can guide execution decisions.${first ? ` Key insight: ${first}` : ""}`;
        }
        return s;
      };

      const msg = toEnglishInsight(headingText, contentText, res?.message || "");
      if (msg) {
        insightCacheRef.current[key] = msg;
        setOrbInsight(msg);
        setOrbSpeaking();
      }
    } catch {
      /* non-fatal */
    } finally {
      setOrbInsightLoading(false);
    }
  };

  const clearHeadingInsight = () => {
    setOrbInsight("");
    setOrbIdle();
  };

  if (loading) {
    return (
      <div className="bsp-fullscreen-state">
        <div className="bsp-spinner" />
        <p>Preparing your brand summary…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bsp-fullscreen-state">
        <p className="bsp-error-text">{error}</p>
        <button className="bsp-btn-primary" onClick={() => navigate("/")}>
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="bsp-book-screen">
      <header className="bsp-book-topbar">
        <img src={logo} alt="The Godfather" className="bsp-book-logo" />
        <div className="bsp-book-top-actions">
          <button
            type="button"
            className="bsp-export-btn"
            disabled={exporting || totalPages === 0}
            onClick={handleExport}
          >
            {exporting ? "Exporting..." : "Export"}
          </button>
          <button type="button" className="bsp-avatar-btn" aria-label="Profile">
            {userInitial}
          </button>
        </div>
      </header>

      <div className="bsp-book-frame">
        <aside className="bsp-book-rail">
          <button type="button" className="bsp-back-btn" onClick={() => navigate(-1)}>
            Back
          </button>
          <div className="bsp-rail-title-wrap">
            <span className="bsp-rail-watermark">{sidebarTitle}</span>
            <span className="bsp-rail-title">{sidebarTitle}</span>
          </div>
        </aside>

        <main className="bsp-book-content">
          {currentPage === totalPages - 1 && activePage?.cta_label && (
            <div className="bsp-top-cta-wrap">
              <button
                type="button"
                className="bsp-top-cta-btn"
                onClick={() => navigate("/brand-book-ready")}
              >
                {activePage.cta_label}
              </button>
            </div>
          )}

          {renderMetaFields && (
            <section className="bsp-overview">
              <h2>{activePage?.title || "Brand Overview"}</h2>
              <div className="bsp-meta-grid">
                {(activePage?.overview_fields || [
                  { label: "Brand Name", value: brandName || "Example Brand" },
                  { label: "Industry/Category", value: getMeta("industry") },
                  { label: "Core Belief (1-line Purpose)", value: getMeta("belief") },
                ]).map((field, idx) => (
                  <div
                    key={`meta-${idx}`}
                    onMouseEnter={() => showHeadingInsight(field.label, field.value)}
                    onMouseLeave={clearHeadingInsight}
                  >
                    <p className="bsp-meta-label">{field.label}</p>
                    <p className="bsp-meta-value">{field.value}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className={`bsp-content-flow bsp-density-${contentDensity}`}>
            {currentPage === 0 && !activePage?.title && title && (
              <h3
                className="bsp-main-title"
                onMouseEnter={() => showHeadingInsight(title, subheading || "")}
                onMouseLeave={clearHeadingInsight}
              >
                {title}
              </h3>
            )}
            {currentPage === 0 && !activePage?.title && heading && (
              <h4
                className="bsp-main-heading"
                onMouseEnter={() => showHeadingInsight(heading, subheading || "")}
                onMouseLeave={clearHeadingInsight}
              >
                {heading}
              </h4>
            )}
            {currentPage === 0 && !activePage?.title && subheading && (
              <h5
                className="bsp-main-subheading"
                onMouseEnter={() => showHeadingInsight(subheading, "")}
                onMouseLeave={clearHeadingInsight}
              >
                {subheading}
              </h5>
            )}

            {Array.isArray(activePage?.sections) &&
              activePage.sections.map((sec, idx) => (
                <article key={`section-${idx}`} className="bsp-structured-section">
                  <h3
                    className="bsp-section-title"
                    onMouseEnter={() => showHeadingInsight(sec.title, sec.content)}
                    onMouseLeave={clearHeadingInsight}
                  >
                    {sec.title}
                  </h3>
                  <p className="bsp-body-text">{sec.content}</p>
                </article>
              ))}

            {Array.isArray(activePage?.dna_points) && activePage.dna_points.length > 0 && (
              <article className="bsp-structured-section">
                <h3
                  className="bsp-section-title"
                  onMouseEnter={() => showHeadingInsight(activePage.title || "Brand DNA", activePage.dna_points.join(" "))}
                  onMouseLeave={clearHeadingInsight}
                >
                  {activePage.title || "Brand DNA"}
                </h3>
                <ul className="bsp-dna-list">
                  {activePage.dna_points.map((p, idx) => (
                    <li key={`dna-${idx}`} className="bsp-list-item">{p}</li>
                  ))}
                </ul>
              </article>
            )}

            {activePage?.emotional_connection && (
              <article className="bsp-structured-section">
                <h3
                  className="bsp-section-title"
                  onMouseEnter={() =>
                    showHeadingInsight(
                      activePage.emotional_connection.title,
                      `${activePage.emotional_connection.before} ${activePage.emotional_connection.after}`,
                    )
                  }
                  onMouseLeave={clearHeadingInsight}
                >
                  {activePage.emotional_connection.title}
                </h3>
                <div className="bsp-two-col">
                  <div>
                    <p className="bsp-meta-label">{activePage.emotional_connection.before_title}</p>
                    <p className="bsp-body-text">{activePage.emotional_connection.before}</p>
                  </div>
                  <div>
                    <p className="bsp-meta-label">{activePage.emotional_connection.after_title}</p>
                    <p className="bsp-body-text">{activePage.emotional_connection.after}</p>
                  </div>
                </div>
              </article>
            )}

            {activePage?.style_tone && (
              <article className="bsp-structured-section">
                <h3
                  className="bsp-section-title"
                  onMouseEnter={() => showHeadingInsight(activePage.style_tone.title, activePage.style_tone.summary)}
                  onMouseLeave={clearHeadingInsight}
                >
                  {activePage.style_tone.title}
                </h3>
                <p className="bsp-body-text">{activePage.style_tone.summary}</p>
                <div className="bsp-three-col">
                  <div>
                    <p className="bsp-meta-label">Tone of Voice</p>
                    <p className="bsp-body-text">{activePage.style_tone.tone}</p>
                  </div>
                  <div>
                    <p className="bsp-meta-label">Visual Mood</p>
                    <p className="bsp-body-text">{activePage.style_tone.visual}</p>
                  </div>
                  <div>
                    <p className="bsp-meta-label">Design Style</p>
                    <p className="bsp-body-text">{activePage.style_tone.design}</p>
                  </div>
                </div>
              </article>
            )}

            {Array.isArray(activePage?.taglines) && activePage.taglines.length > 0 && (
              <article className="bsp-structured-section">
                <h3
                  className="bsp-section-title"
                  onMouseEnter={() => showHeadingInsight("Brand Tagline Drafts", activePage.taglines.join(" "))}
                  onMouseLeave={clearHeadingInsight}
                >
                  Brand Tagline Drafts
                </h3>
                <ol className="bsp-tagline-list">
                  {activePage.taglines.map((t, idx) => (
                    <li key={`tag-${idx}`} className="bsp-list-item">{t}</li>
                  ))}
                </ol>
              </article>
            )}

            {!activePage?.sections &&
              activeElements.map((el, idx) => {
                const isFirstBody = el.type === "body" && activeElements.findIndex((e) => e.type === "body") === idx;
                return <RenderElement key={el.key} el={el} dropCap={isFirstBody} />;
              })}
          </section>

          <footer className="bsp-book-pager">
            <button type="button" className="bsp-pager-btn" onClick={goPrev} disabled={currentPage === 0}>
              ‹
            </button>
            <div className="bsp-pager-dots">
              {pages.map((_, idx) => (
                <button
                  type="button"
                  key={`dot-${idx}`}
                  className={`bsp-pager-dot ${idx === currentPage ? "active" : ""}`}
                  onClick={() => setCurrentPage(idx)}
                  aria-label={`Go to page ${idx + 1}`}
                />
              ))}
            </div>
            <button
              type="button"
              className="bsp-pager-btn"
              onClick={goNext}
              disabled={currentPage >= totalPages - 1}
            >
              ›
            </button>
          </footer>
        </main>
      </div>

      <div className="bsp-corner-orb" aria-hidden="true">
        <OrbPresence>
          <BrandOrb size="welcome" />
        </OrbPresence>
        {(orbInsightLoading || orbInsight) && (
          <div className="bsp-orb-insight">
            <p className="bsp-orb-insight-title">ORB Insight</p>
            <p className="bsp-orb-insight-text">
              {orbInsightLoading ? "Orb is reading this heading..." : orbInsight}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}