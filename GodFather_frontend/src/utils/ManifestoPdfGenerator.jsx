import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import React from "react";
import ReactDOM from "react-dom/client";
import ManifestoPage1 from "../pages/ManifestoPage1";
import ManifestoPage2 from "../pages/ManifestoPage2";

export async function downloadManifestoPdf(manifestoData, sessionTitle = "Brand Manifesto") {
  const container = document.createElement("div");
  container.style.position = "fixed";
  container.style.left = "-200vw";
  container.style.top = "0";
  container.style.width = "595px";
  container.style.height = "842px";
  container.style.background = "#0a1727";
  container.style.margin = "0";
  container.style.padding = "0";
  container.style.overflow = "hidden";
  document.body.appendChild(container);

  // PAGE 1
  const pageDiv1 = document.createElement("div");
  pageDiv1.style.width = "595px";
  pageDiv1.style.height = "842px";
  pageDiv1.style.margin = "0";
  pageDiv1.style.padding = "0";
  container.appendChild(pageDiv1);
  const root1 = ReactDOM.createRoot(pageDiv1);
  root1.render(React.createElement(ManifestoPage1, { data: manifestoData }));

  await new Promise(r => setTimeout(r, 600));
  const canvas1 = await html2canvas(pageDiv1, {
    scale: 2,
    useCORS: true,
    backgroundColor: "#0a1727",
    x: 0,
    y: 0,
    width: 595,
    height: 842,
    windowWidth: 595,
    windowHeight: 842,
    scrollX: 0,
    scrollY: 0
  });

  const img1 = canvas1.toDataURL("image/png");

  // PAGE 2
  const pageDiv2 = document.createElement("div");
  pageDiv2.style.width = "595px";
  pageDiv2.style.height = "842px";
  pageDiv2.style.margin = "0";
  pageDiv2.style.padding = "0";
  container.appendChild(pageDiv2);
  const root2 = ReactDOM.createRoot(pageDiv2);
  root2.render(React.createElement(ManifestoPage2, { data: manifestoData }));

  await new Promise(r => setTimeout(r, 600));
  const canvas2 = await html2canvas(pageDiv2, {
    scale: 2,
    useCORS: true,
    backgroundColor: "#0a1727",
    x: 0,
    y: 0,
    width: 595,
    height: 842,
    windowWidth: 595,
    windowHeight: 842,
    scrollX: 0,
    scrollY: 0
  });

  const img2 = canvas2.toDataURL("image/png");

  const pdf = new jsPDF("p", "mm", "a4");
  pdf.addImage(img1, "PNG", 0, 0, 210, 297);
  pdf.addPage();
  pdf.addImage(img2, "PNG", 0, 0, 210, 297);
  pdf.save(`${sessionTitle}_Brand_Manifesto.pdf`);
  document.body.removeChild(container);
}
