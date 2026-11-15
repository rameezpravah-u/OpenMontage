import React, { useMemo } from "react";
import {
  AbsoluteFill,
  Audio,
  CalculateMetadataFunction,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Caption, createTikTokStyleCaptions, TikTokPage } from "@remotion/captions";

// ---------------------------------------------------------------------------
// VIRAL ENGINE — one composition, driven entirely by props.json.
//
// Nothing here is specific to a single video. The Python pipeline hands it:
//   - a speed-ramped screen recording
//   - detected beat times (where to punch in)
//   - word-level captions from the narration
//   - a hook, a CTA, an audio track
// Swap the props, get a different video. That is what makes 100/month work.
// ---------------------------------------------------------------------------

const CREAM = "#F2F1EB";
const INK = "#0B0B10";
const ACCENT = "#2B59FF";

const SERIF = "'TB Playfair', Georgia, serif";
const SANS = "'TB Inter', system-ui, sans-serif";

const fontFace = (family: string, file: string, weight: number) =>
  `@font-face{font-family:'${family}';font-style:normal;font-weight:${weight};font-display:block;src:url(${staticFile(
    `fonts/${file}.woff2`
  )}) format('woff2');}`;

const FontFaces: React.FC = () => (
  <style
    dangerouslySetInnerHTML={{
      __html: [
        fontFace("TB Playfair", "playfair500", 500),
        fontFace("TB Playfair", "playfair600", 600),
        fontFace("TB Inter", "inter500", 500),
        fontFace("TB Inter", "inter600", 600),
      ].join(""),
    }}
  />
);

export interface Hook {
  /** Big line that must land in the first 2 seconds. */
  text: string;
  sub?: string;
  durationInFrames: number;
}

export interface ZoomBeat {
  /** seconds into the composition */
  t: number;
  scale: number;
}

export interface SceneProps {
  video: string;
  videoDurationInFrames: number;
  hook: Hook;
  captions: Caption[];
  zooms: ZoomBeat[];
  audio?: string | null;
  cta: {
    durationInFrames: number;
    wordmark: string;
    line: string;
    store: string;
    icon: string;
  };
  fps: number;
}

/* ------------------------------ hook card ------------------------------ */

const HookCard: React.FC<{ hook: Hook; fps: number }> = ({ hook, fps }) => {
  const frame = useCurrentFrame();
  // No fade-in: frame 1 already carries the message. A hook that fades is a
  // hook that lost its first 6 frames.
  const pop = spring({ frame, fps, config: { damping: 200, mass: 0.5, stiffness: 220 } });
  const out = interpolate(
    frame,
    [hook.durationInFrames - 7, hook.durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );
  return (
    <AbsoluteFill style={{ opacity: out }}>
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 700,
          background: `linear-gradient(180deg, ${CREAM} 0%, ${CREAM} 68%, ${CREAM}00 100%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 150,
          left: 64,
          right: 64,
          textAlign: "center",
          transform: `scale(${0.96 + pop * 0.04})`,
        }}
      >
        <div
          style={{
            fontFamily: SERIF,
            fontWeight: 600,
            fontSize: 92,
            lineHeight: 1.0,
            letterSpacing: "-0.02em",
            color: INK,
            whiteSpace: "pre-line",
          }}
        >
          {hook.text}
        </div>
        {hook.sub ? (
          <div
            style={{
              marginTop: 24,
              fontFamily: SANS,
              fontWeight: 500,
              fontSize: 36,
              color: INK,
              opacity: 0.62,
            }}
          >
            {hook.sub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

/* ---------------------------- karaoke captions ---------------------------- */

const CaptionLayer: React.FC<{ pages: TikTokPage[]; fps: number }> = ({ pages, fps }) => {
  const frame = useCurrentFrame();
  const ms = (frame / fps) * 1000;
  const page = pages.find((p) => ms >= p.startMs && ms < p.startMs + p.durationMs);
  if (!page) return null;

  const enter = spring({
    frame: frame - (page.startMs / 1000) * fps,
    fps,
    config: { damping: 200, mass: 0.4, stiffness: 240 },
  });

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          // Sits in the empty chat field, above the text input and clear of
          // the keyboard. At bottom:330 the captions covered the keys — never
          // put the caption layer over the interface the ad is demonstrating.
          bottom: 830,
          left: 56,
          right: 56,
          textAlign: "center",
          transform: `translateY(${(1 - enter) * 18}px) scale(${0.96 + enter * 0.04})`,
        }}
      >
        <span
          style={{
            fontFamily: SANS,
            fontWeight: 600,
            fontSize: 62,
            lineHeight: 1.18,
            color: "#FFFFFF",
            WebkitTextStroke: `14px ${INK}`,
            paintOrder: "stroke",
          }}
        >
          {page.tokens.map((t, i) => {
            const active = ms >= t.fromMs && ms < t.toMs;
            return (
              <span key={i} style={{ whiteSpace: "pre", color: active ? ACCENT : "#FFFFFF" }}>
                {t.text}
              </span>
            );
          })}
        </span>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------------ the footage ------------------------------ */

const Footage: React.FC<{ src: string; zooms: ZoomBeat[]; fps: number }> = ({ src, zooms, fps }) => {
  const frame = useCurrentFrame();
  const t = frame / fps;

  // Punch in briefly on each detected beat, then ease back. This is the
  // "editor noticed something happened" move, applied automatically.
  let scale = 1.0;
  for (const z of zooms) {
    const d = t - z.t;
    if (d >= -0.18 && d <= 1.25) {
      const p =
        d < 0
          ? interpolate(d, [-0.18, 0], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })
          : interpolate(d, [0, 0.35, 1.25], [1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
      scale = Math.max(scale, 1 + (z.scale - 1) * p);
    }
  }

  return (
    <AbsoluteFill style={{ background: INK, overflow: "hidden" }}>
      <OffthreadVideo
        src={staticFile(src)}
        style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }}
        muted
      />
    </AbsoluteFill>
  );
};

/* --------------------------------- CTA --------------------------------- */

const Cta: React.FC<{ cta: SceneProps["cta"]; fps: number }> = ({ cta, fps }) => {
  const frame = useCurrentFrame();
  const s = spring({ frame, fps, config: { damping: 13, mass: 0.7, stiffness: 160 } });
  const fade = (a: number, b: number) =>
    interpolate(frame, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{ background: CREAM, alignItems: "center", justifyContent: "center", flexDirection: "column" }}
    >
      <Img
        src={staticFile(cta.icon)}
        style={{
          width: 272,
          height: 272,
          borderRadius: 61,
          transform: `scale(${0.86 + s * 0.14})`,
          opacity: Math.min(1, s * 1.6),
          marginTop: -70,
        }}
      />
      <div
        style={{
          marginTop: 48,
          fontFamily: SERIF,
          fontWeight: 600,
          fontSize: 96,
          letterSpacing: "-0.02em",
          color: INK,
          opacity: fade(6, 18),
          transform: `translateY(${(1 - fade(6, 18)) * 20}px)`,
        }}
      >
        {cta.wordmark}
      </div>
      <div style={{ marginTop: 26, fontFamily: SANS, fontWeight: 600, fontSize: 38, color: ACCENT, opacity: fade(16, 30) }}>
        {cta.line}
      </div>
      <div
        style={{
          marginTop: 36,
          fontFamily: SANS,
          fontWeight: 500,
          fontSize: 29,
          letterSpacing: "0.04em",
          color: INK,
          opacity: 0.5 * fade(28, 44),
        }}
      >
        {cta.store}
      </div>
    </AbsoluteFill>
  );
};

/* -------------------------------- scene -------------------------------- */

export const Scene: React.FC<SceneProps> = ({
  video, videoDurationInFrames, hook, captions, zooms, audio, cta, fps,
}) => {
  const { pages } = useMemo(
    () =>
      createTikTokStyleCaptions({
        captions: captions ?? [],
        // ~1.2s per page keeps 3-5 words on screen: readable at thumb distance,
        // still fast enough to feel native rather than like a subtitle track.
        combineTokensWithinMilliseconds: 1200,
      }),
    [captions]
  );

  return (
    <AbsoluteFill style={{ background: INK }}>
      <FontFaces />
      {audio ? <Audio src={staticFile(audio)} /> : null}

      <Sequence from={0} durationInFrames={videoDurationInFrames} name="footage">
        <Footage src={video} zooms={zooms ?? []} fps={fps} />
      </Sequence>

      <Sequence from={0} durationInFrames={hook.durationInFrames} name="hook">
        <HookCard hook={hook} fps={fps} />
      </Sequence>

      <Sequence from={0} durationInFrames={videoDurationInFrames} name="captions">
        <CaptionLayer pages={pages} fps={fps} />
      </Sequence>

      <Sequence from={videoDurationInFrames} durationInFrames={cta.durationInFrames} name="cta">
        <Cta cta={cta} fps={fps} />
      </Sequence>
    </AbsoluteFill>
  );
};

export const calculateMetadata: CalculateMetadataFunction<SceneProps> = async ({ props }) => ({
  durationInFrames: (props.videoDurationInFrames ?? 0) + (props.cta?.durationInFrames ?? 0) || 600,
  fps: props.fps ?? 30,
  width: 1080,
  height: 1920,
});
