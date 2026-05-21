import React from "react";
import "../components/ManifestoPage1.css";

export default function ManifestoPage1({ data }) {
  const {
    brandName = "Example Brand",
    industryCategory = "Example Industry/Category",
    coreBelief = "Example Core Belief (1-line Purpose)",
    assumptions = [],
    originStory = "Lorem ipsum dolor sit amet...",
    brandDNA = ["Bold", "Purposeful", "Artistic"],
    brandPromise = "Lorem ipsum dolor sit amet..."
  } = data || {};

  return (
    <div className="a4-scrollable">
      {/* gradient balls */}
      <div className="background-bubbles">
        <div className="bubble-cff4ff" />
        <div className="bubble-3c73ff" />
      </div>
      <div className="main-content">
        <div className="manifesto-title">
          "Now the real work begins — living this brand, every single day."
        </div>
        <h1 className="brand-manifesto-heading">BRAND MANIFESTO</h1>
        <div className="brand-overview-section">
          <div className="overview-box">
            <div>
              <span className="label">Brand Name</span><br />
              <span className="value">{brandName}</span>
            </div>
            <div>
              <span className="label">Industry/Category</span><br />
              <span className="value">{industryCategory}</span>
            </div>
            <div>
              <span className="label">Core Belief (1-line Purpose)</span><br />
              <span className="value">{coreBelief}</span>
            </div>
          </div>
        </div>
        {/* Assumptions Section */}
        {assumptions && assumptions.length > 0 && (
          <div className="assumptions-section">
            <span className="section-title">Assumptions</span>
            <div className="assumptions-list">
              {assumptions.map((assumption, idx) => (
                <div className="assumption-item" key={idx}>{assumption}</div>
              ))}
            </div>
          </div>
        )}
        {/* Two-column: Brand Origin Story + Brand DNA */}
        <div className="two-col-row">
          <div>
            <span className="section-title">Brand Origin Story</span>
            <div className="origin-value">{originStory}</div>
          </div>
          <div>
            <span className="section-title">Brand's DNA</span>
            <div className="dna-list">
              {brandDNA.map((dna, idx) => (
                <div className="dna-item" key={idx}>{dna}</div>
              ))}
            </div>
          </div>
        </div>
        <div className="brand-promise-section">
          <span className="section-title">Brand’s Promise</span>
          <div className="promise-value">{brandPromise}</div>
        </div>
      </div>
    </div>
  );
}
