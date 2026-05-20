/**
 * PDF Template Styling Configuration
 * Extracted from template: utils/My Brand_Brand_Manifesto.pdf
 * 
 * This file contains the styling configuration that matches the PDF template
 */

export const pdfTemplateStyles = {
  // Colors
  colors: {
    background: {
      primary: "#0a1727",        // Main dark blue background
      secondary: "#101e35",        // Secondary dark blue for boxes
      gradient: "linear-gradient(90deg, rgba(6,25,35,1) 0%, rgba(6,25,35,1) 78%, rgba(12,47,62,1) 100%)",
      accent: "linear-gradient(270deg, rgba(134, 227, 255, 0.3) 0%, rgba(134, 227, 255, 0) 100%)"
    },
    text: {
      primary: "#FFFFFF",          // Main white text
      secondary: "#e4fafd",        // Light cyan for body text
      heading: "#D4FBFF",          // Cyan for headings
      accent: "#86E3FF",           // Bright cyan for section titles
      label: "#c1deff",            // Light blue for labels
      muted: "#8EE5FF",            // Muted cyan
      subheading: "rgba(255, 255, 255, 0.75)", // Softer color for subheading
      quote: "#e4fafd"             // Quote text color
    },
    borders: {
      primary: "#8EE5FF",           // Cyan border
      secondary: "#34D6DC",         // Teal border for DNA items
      subtle: "rgba(134, 227, 255, 0.3)",
      quote: "#86E3FF"              // Quote left border
    },
    highlights: {
      dnaBackground: "#D9FBFF",     // Light cyan for DNA items
      dnaText: "#001A32",            // Dark blue text on DNA items
      quoteBackground: "rgba(134, 227, 255, 0.05)" // Quote background
    }
  },

  // Typography - Magazine Style
  typography: {
    fontFamily: {
      primary: "'Inter', Arial, sans-serif",
      heading: "'Inter', Arial, sans-serif"
    },
    sizes: {
      title: "3.5rem",              // Large editorial-style title (56px)
      heading: "2rem",              // Medium-large heading (32px)
      subheading: "1.25rem",        // Subheading (20px)
      quote: "1.15rem",             // Quote text (18.4px)
      manifestoTitle: "14px",       // Italic quote at top
      mainHeading: "36px",          // "BRAND MANIFESTO"
      sectionTitle: "12px",          // Section headings
      label: "14px",                 // Labels
      body: "11px",                  // Body text
      value: "12px",                  // Values in boxes
      dna: "12px"                    // DNA items
    },
    weights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800                // For title
    },
    lineHeight: {
      tight: 1.1,                   // For title
      normal: 1.3,                  // For heading
      relaxed: 1.5,                 // For subheading
      quote: 1.7,                   // For quote
      body: 1.6                    // For body text
    },
    letterSpacing: {
      title: "0.02em",              // For title
      heading: "0.01em",            // For heading
      subheading: "0.005em",       // For subheading
      normal: "0.01em"
    }
  },

  // Spacing
  spacing: {
    page: {
      padding: {
        top: "24px",
        sides: "30px",
        bottom: "20px"
      }
    },
    sections: {
      between: "18px",               // Space between major sections
      small: "6px",                  // Small spacing
      medium: "12px"                 // Medium spacing
    },
    elements: {
      headingMargin: "18px",         // Margin below main heading
      sectionTitleMargin: "4px",     // Margin below section title
      itemSpacing: "4px",             // Spacing between list items
      boxPadding: "14px 19px",        // Padding inside boxes
      boxGap: "8px"                   // Gap between items in box
    }
  },

  // Layout
  layout: {
    page: {
      width: "595px",                // A4 width at 72dpi
      height: "842px",               // A4 height
      maxWidth: "100%"
    },
    borderRadius: {
      box: "11px",                   // Border radius for boxes
      item: "6px"                    // Border radius for items
    },
    borders: {
      box: "1px solid #8EE5FF",      // Box border
      item: "1px solid #34D6DC"      // Item border
    }
  },

  // Effects
  effects: {
    boxShadow: "none",                // Typically no shadow in PDF
    transitions: "none"               // No transitions in PDF
  }
};

/**
 * Get CSS custom properties object for use in styled components
 */
export const getCSSVariables = () => {
  return {
    '--pdf-bg-primary': pdfTemplateStyles.colors.background.primary,
    '--pdf-bg-secondary': pdfTemplateStyles.colors.background.secondary,
    '--pdf-text-primary': pdfTemplateStyles.colors.text.primary,
    '--pdf-text-secondary': pdfTemplateStyles.colors.text.secondary,
    '--pdf-text-heading': pdfTemplateStyles.colors.text.heading,
    '--pdf-text-accent': pdfTemplateStyles.colors.text.accent,
    '--pdf-border-primary': pdfTemplateStyles.colors.borders.primary,
    '--pdf-font-size-body': pdfTemplateStyles.typography.sizes.body,
    '--pdf-font-size-heading': pdfTemplateStyles.typography.sizes.mainHeading,
    '--pdf-font-size-section': pdfTemplateStyles.typography.sizes.sectionTitle,
    '--pdf-spacing-section': pdfTemplateStyles.spacing.sections.between,
    '--pdf-spacing-small': pdfTemplateStyles.spacing.sections.small
  };
};
