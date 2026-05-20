// import React from "react";
// import "../components/ManifestoPage2.css";

// export default function ManifestoSecondPage({ data }) {
//   const {
//     emotionalConnectionBefore = "Lorem ipsum...",
//     emotionalConnectionAfter = "Lorem ipsum...",
//     differentiationStatement = "Lorem ipsum...",
//     differentiationHighlight = "Unlike competitors, bata distinguishes itself through its unwavering commitment to innovation and customer satisfaction.",
//     toneOfVoice = "Confident, Warm, Honest",
//     visualMood = "Deep blue, soft glow accents",
//     designStyle = "Modern, Emotional, Authentic",
//     taglines = [
//       "Build your truth. Live your brand.",
//       "Where clarity becomes culture.",
//       "Born to stand out. Built to last."
//     ]
//   } = data || {};

//   return (
//     <div className="page-bg">
//       <div className="a4-scrollable font-inter">
//         {/* Decorative blurred background */}
//         <div className="a4-blur-bg">
//           <div className="blur-circle cyan-light" style={{ top: 160, left: 450, width: 100, height: 100 }} />
//           <div className="blur-circle blue" style={{ top: 360, left: 520, width: 92, height: 92 }} />
//         </div>
//         <div className="main-content">
//           <h2 className="title-centered section-blue">Emotional Connection</h2>
//           <div className="emotional-table">
//             <div className="emotional-table-col">
//               <h3 className="box-heading">Before Our Brand</h3>
//               <p className="box-body">{emotionalConnectionBefore}</p>
//             </div>
//             <div className="emotional-table-divider"></div>
//             <div className="emotional-table-col">
//               <h3 className="box-heading">After Our Brand</h3>
//               <p className="box-body">{emotionalConnectionAfter}</p>
//             </div>
//           </div>
//           <div className="section-divider"></div>
 
//           {/* Differentiation Statement */}
//           <h2 className="differentiation-title section-blue">Differentiation Statement</h2>
//           <p className="differentiation-desc">{differentiationStatement}</p>
 
//           {/* Brand Style & Tone & Visual Mood Banner */}
//           <div className="two-col-banner">
//             <p className="diff-left">{differentiationHighlight}</p>
//             <h2 className="diff-right section-blue">
//               Brand Style & Tone <br />& Visual Mood
//             </h2>
//           </div>

//           {/* Brand Style & Tone & Visual Mood Three Columns */}
//           <div className="style-tone-three-col">
//             <div className="style-tone-col">
//               <div className="style-tone-label">Tone of Voice</div>
//               <div className="style-tone-value">{toneOfVoice}</div>
//             </div>
//             <div className="style-tone-sep"></div>
//             <div className="style-tone-col">
//               <div className="style-tone-label">Visual Mood</div>
//               <div className="style-tone-value">{visualMood}</div>
//             </div>  
//             <div className="style-tone-sep"></div>
//             <div className="style-tone-col">
//               <div className="style-tone-label">Design Style</div>
//               <div className="style-tone-value">{designStyle}</div>
//             </div>
//           </div>
    
//           {/* Brand Tagline Drafts */}
//           <section className="promise-section">
//             <h2 className="promise-title section-blue">Brand Tagline Drafts</h2>
//             <div className="tagline-list">
//               {taglines.map((tagline, index) => (
//                 <p key={index} className="tagline-row">{index + 1}. {tagline}</p>
//               ))}
//             </div>
//           </section>

//           <footer className="footer-quote">
//             <span>"This is just the beginning. Let's turn your brand's truth into action."</span>
//           </footer>
//         </div>
//       </div>
//     </div>
//   );
// }


import React from "react";
import "../components/ManifestoPage2.css";
 
export default function ManifestoSecondPage({ data }) {
  const {
    emotionalConnectionBefore = "Lorem ipsum...",
    emotionalConnectionAfter = "Lorem ipsum...",
    differentiationStatement = "Lorem ipsum...",
    differentiationHighlight = "Unlike competitors, bata distinguishes itself through its unwavering commitment to innovation and customer satisfaction.",
    toneOfVoice = "Confident, Warm, Honest",
    visualMood = "Deep blue, soft glow accents",
    designStyle = "Modern, Emotional, Authentic",
    taglines = [
      "Build your truth. Live your brand.",
      "Where clarity becomes culture.",
      "Born to stand out. Built to last."
    ]
  } = data || {};
 
  return (
    <div className="page-bg">
      <div className="a4-scrollable font-inter">
        {/* Decorative blurred background */}
        <div className="a4-blur-bg">
          <div
            className="blur-circle cyan-light"
            style={{ top: 160, left: 450, width: 100, height: 100 }}
          />
          <div
            className="blur-circle blue"
            style={{ top: 360, left: 520, width: 92, height: 92 }}
          />
        </div>
 
        <div className="main-content">
 
          {/* SECTION 1 — Emotional Connection */}
          <div className="section-block">
            <h2 className="title-centered section-blue">Emotional Connection</h2>
 
            <div className="emotional-table">
              <div className="emotional-table-col">
                <h3 className="box-heading">Before Our Brand</h3>
                <p className="box-body">{emotionalConnectionBefore}</p>
              </div>
 
              <div className="emotional-table-col">
                <h3 className="box-heading">After Our Brand</h3>
                <p className="box-body">{emotionalConnectionAfter}</p>
              </div>
            </div>
          </div>
 
          {/* SECTION 2 — Differentiation Statement */}
          <div className="section-block">
            <h2 className="differentiation-title section-blue">
              Differentiation Statement
            </h2>
            <p className="differentiation-desc">{differentiationStatement}</p>
          </div>
 
          {/* SECTION 3 — Brand Style, Tone & Visual Mood Banner */}
          <div className="section-block">
            <div className="two-col-banner">
              <p className="diff-left">{differentiationHighlight}</p>
 
              <h2 className="diff-right section-blue">
                Brand Style & Tone <br /> & Visual Mood
              </h2>
            </div>
          </div>
 
          {/* SECTION 4 — 3 Columns Style/Tone/Visual */}
          <div className="section-block">
            <div className="style-tone-three-col">
              <div className="style-tone-col">
                <div className="style-tone-label">Tone of Voice</div>
                <div className="style-tone-value">{toneOfVoice}</div>
              </div>
 
              <div className="style-tone-col">
                <div className="style-tone-label">Visual Mood</div>
                <div className="style-tone-value">{visualMood}</div>
              </div>
 
              <div className="style-tone-col">
                <div className="style-tone-label">Design Style</div>
                <div className="style-tone-value">{designStyle}</div>
              </div>
            </div>
          </div>
 
          {/* SECTION 5 — Taglines */}
          <div className="section-block">
            <section className="promise-section">
              <h2 className="promise-title section-blue">
                Brand Tagline Drafts
              </h2>
 
              <div className="tagline-list">
                {taglines.map((tagline, index) => (
                  <p key={index} className="tagline-row">
                    {index + 1}. {tagline}
                  </p>
                ))}
              </div>
            </section>
          </div>
 
          {/* Footer */}
          <footer className="footer-quote">
            <span>
              "This is just the beginning. Let's turn your brand's truth into
              action."
            </span>
          </footer>
        </div>
      </div>
    </div>
  );
}
 
 