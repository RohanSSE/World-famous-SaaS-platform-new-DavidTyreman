import "./BrandOrb.css";

const ORB_RING_VIDEO = "/GettyImages-925618798.mp4";
const ORB_CORE_VIDEO =
  "/magnific_i-want-to-remove-the-background-of-this-video-and-_auto_720p_24fps_96756.mp4";

/**
 * Brand Godfather ORB — particle ring + glowing core (transparent, no black disc).
 * @param {"lg"|"welcome"|"md"|"hero"|"sm"|"xs"|"corner"} size
 */
export default function BrandOrb({ size = "md", className = "" }) {
  return (
    <div
      className={`brand-orb brand-orb--${size} ${className}`.trim()}
      role="img"
      aria-label="Brand Godfather ORB"
    >
      <video
        className="brand-orb__ring"
        src={ORB_RING_VIDEO}
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        aria-hidden="true"
      />
      <div className="brand-orb__core">
        <video
          className="brand-orb__blob"
          src={ORB_CORE_VIDEO}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
