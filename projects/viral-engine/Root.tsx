import { Composition } from "remotion";
import { Scene, calculateMetadata, SceneProps } from "./Composition";

const fallback = {
  video: "", videoDurationInFrames: 300, captions: [], zooms: [], audio: null, fps: 30,
  hook: { text: "", durationInFrames: 66 },
  cta: { durationInFrames: 120, wordmark: "", line: "", store: "", icon: "" },
} as unknown as SceneProps;

export const Root: React.FC = () => (
  <Composition
    id="ViralEngine"
    component={Scene}
    durationInFrames={600}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={fallback}
    calculateMetadata={calculateMetadata}
  />
);
