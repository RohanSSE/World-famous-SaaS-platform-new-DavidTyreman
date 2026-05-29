import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import React from "react";
import ReactDOM from "react-dom/client";

const EXPORT_WIDTH = 932;
const EXPORT_HEIGHT = 768;

function renderInlineFormatted(text, keyPrefix = "i") {
  if (!text || typeof text !== "string") return text;
  const parts = [];
  let lastIndex = 0;
  const re = /\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_/g;
  let match;
  let key = 0;
  while ((match = re.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<React.Fragment key={`${keyPrefix}-${key++}`}>{text.slice(lastIndex, match.index)}</React.Fragment>);
    }
    if (match[1]) parts.push(<strong key={`${keyPrefix}-${key++}`}>{match[1]}</strong>);
    else if (match[2]) parts.push(<em key={`${keyPrefix}-${key++}`}>{match[2]}</em>);
    else if (match[3]) parts.push(<em key={`${keyPrefix}-${key++}`}>{match[3]}</em>);
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(<React.Fragment key={`${keyPrefix}-${key++}`}>{text.slice(lastIndex)}</React.Fragment>);
  }
  return parts.length > 0 ? parts : text;
}

function RenderElement({ el, dropCap = false }) {
  if (el.type === "heading") {
    return <h3 className="bsp-section-title">{renderInlineFormatted(el.text, `h-${el.key}`)}</h3>;
  }
  if (el.type === "subsection") {
    return <h4 className="bsp-subsection-title">{renderInlineFormatted(el.text, `sub-${el.key}`)}</h4>;
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
  return <p className={`bsp-body-text ${dropCap ? "bsp-drop-cap" : ""}`}>{renderInlineFormatted(el.text, `p-${el.key}`)}</p>;
}

function RailTitleWords({ text }) {
  return String(text || "Brand Book")
    .split(/\s+/)
    .filter(Boolean)
    .map((word, idx) => (
      <span className="bsp-pdf-rail-word" key={`${word}-${idx}`}>
        {word}
      </span>
    ));
}

function ExportBrandBookPage({
  activePage,
  brandName,
  contentDensity,
  currentPage,
  elements,
  heading,
  sidebarTitle,
  subheading,
  title,
}) {
  const activeElements = Array.isArray(activePage) ? activePage : activePage?.elements || [];
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

  return (
    <div className="bsp-book-screen bsp-pdf-capture-page">
      <div className="bsp-book-frame">
        <aside className="bsp-book-rail">
          <div className="bsp-rail-title-wrap">
            <span className="bsp-rail-watermark"><RailTitleWords text={sidebarTitle} /></span>
            <span className="bsp-rail-title"><RailTitleWords text={sidebarTitle} /></span>
          </div>
        </aside>

        <main className="bsp-book-content">
          {renderMetaFields && (
            <section className="bsp-overview">
              <h2>{activePage?.title || "Brand Overview"}</h2>
              <div className="bsp-meta-grid">
                {(activePage?.overview_fields || [
                  { label: "Brand Name", value: brandName || "Example Brand" },
                  { label: "Industry/Category", value: getMeta("industry") },
                  { label: "Core Belief (1-line Purpose)", value: getMeta("belief") },
                ]).map((field, idx) => (
                  <div key={`meta-${idx}`}>
                    <p className="bsp-meta-label">{field.label}</p>
                    <p className="bsp-meta-value">{field.value}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className={`bsp-content-flow bsp-density-${contentDensity}`}>
            {currentPage === 0 && !activePage?.title && title && <h3 className="bsp-main-title">{title}</h3>}
            {currentPage === 0 && !activePage?.title && heading && <h4 className="bsp-main-heading">{heading}</h4>}
            {currentPage === 0 && !activePage?.title && subheading && <h5 className="bsp-main-subheading">{subheading}</h5>}

            {Array.isArray(activePage?.sections) &&
              activePage.sections.map((sec, idx) => (
                <article key={`section-${idx}`} className="bsp-structured-section">
                  <h3 className="bsp-section-title">{sec.title}</h3>
                  <p className="bsp-body-text">{sec.content}</p>
                </article>
              ))}

            {Array.isArray(activePage?.dna_points) && activePage.dna_points.length > 0 && (
              <article className="bsp-structured-section">
                <h3 className="bsp-section-title">{activePage.title || "Brand DNA"}</h3>
                <ul className="bsp-dna-list">
                  {activePage.dna_points.map((point, idx) => <li key={`dna-${idx}`} className="bsp-list-item">{point}</li>)}
                </ul>
              </article>
            )}

            {activePage?.emotional_connection && (
              <article className="bsp-structured-section">
                <h3 className="bsp-section-title">{activePage.emotional_connection.title}</h3>
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
                <h3 className="bsp-section-title">{activePage.style_tone.title}</h3>
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
                <h3 className="bsp-section-title">Brand Tagline Drafts</h3>
                <ol className="bsp-tagline-list">
                  {activePage.taglines.map((tagline, idx) => <li key={`tag-${idx}`} className="bsp-list-item">{tagline}</li>)}
                </ol>
              </article>
            )}

            {!activePage?.sections &&
              activeElements.map((el, idx) => {
                const isFirstBody = el.type === "body" && activeElements.findIndex((item) => item.type === "body") === idx;
                return <RenderElement key={el.key} el={el} dropCap={isFirstBody} />;
              })}
          </section>
        </main>
      </div>
    </div>
  );
}

function safeFileName(value) {
  return String(value || "brand-book")
    .trim()
    .replace(/[^a-z0-9-_]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase() || "brand-book";
}

export async function downloadBrandBookScreenPdf({
  brandName,
  contentDensity,
  elements,
  heading,
  pages,
  sidebarTitle,
  subheading,
  title,
}) {
  const container = document.createElement("div");
  container.className = "bsp-pdf-export-host";
  container.style.position = "fixed";
  container.style.left = "-10000px";
  container.style.top = "0";
  container.style.width = `${EXPORT_WIDTH}px`;
  container.style.background = "#01092a";
  container.style.pointerEvents = "none";
  document.body.appendChild(container);

  const root = ReactDOM.createRoot(container);
  root.render(
    <>
      {(pages || []).map((page, idx) => (
        <ExportBrandBookPage
          key={`pdf-page-${idx}`}
          activePage={page}
          brandName={brandName}
          contentDensity={contentDensity}
          currentPage={idx}
          elements={elements || []}
          heading={heading}
          sidebarTitle={sidebarTitle || "Brand Book"}
          subheading={subheading}
          title={title}
        />
      ))}
    </>,
  );

  try {
    if (document.fonts?.ready) await document.fonts.ready;
    await new Promise((resolve) => setTimeout(resolve, 400));

    const pageNodes = Array.from(container.querySelectorAll(".bsp-pdf-capture-page"));
    if (pageNodes.length === 0) throw new Error("No brand book pages available for export");

    const pdf = new jsPDF({ orientation: "landscape", unit: "px", format: [EXPORT_WIDTH, EXPORT_HEIGHT] });
    for (let idx = 0; idx < pageNodes.length; idx += 1) {
      const canvas = await html2canvas(pageNodes[idx], {
        scale: 2,
        useCORS: true,
        backgroundColor: "#01092a",
        width: EXPORT_WIDTH,
        height: EXPORT_HEIGHT,
        windowWidth: 1200,
        windowHeight: EXPORT_HEIGHT,
        scrollX: 0,
        scrollY: 0,
      });
      const img = canvas.toDataURL("image/png");
      if (idx > 0) pdf.addPage([EXPORT_WIDTH, EXPORT_HEIGHT], "landscape");
      pdf.addImage(img, "PNG", 0, 0, EXPORT_WIDTH, EXPORT_HEIGHT);
    }
    pdf.save(`${safeFileName(brandName)}-brand-book.pdf`);
  } finally {
    root.unmount();
    document.body.removeChild(container);
  }
}