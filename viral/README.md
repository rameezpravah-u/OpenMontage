# TypeBetter viral video system

Raw screen recording in, publishable vertical video out, one command:

```bash
python viral/pipeline.py --recording raw/type-fix.mov --concept mistake-reveal
```

No timeline. No manual trimming. The only thing you author per video is a
**concept JSON** — a hook, four lines of script, a few dials.

---

## 1. The problem this solves

A raw TypeBetter recording is ~80% dead air. Someone thinks, a caret blinks, a
spinner spins. The three seconds that sell the product — the mistake, the tap,
the correction landing — are buried at unpredictable timestamps.

Hand-editing that is ~30 minutes per video. At 100 videos a month it is a job.
So the system's whole design goal is: **find the interesting frames
automatically, and make every other decision once, in code.**

---

## 2. Architecture

```
  recording.mov
       │
       ├─► beats.py ─────────► change signal ─► speed plan + beat times
       │                        (frame diff)      │
       │                                          │
       ├─► ffmpeg ────────────► conformed footage │  1080×1920, ramped
       │                                          │
  concept.json                                    │
       │                                          │
       ├─► Piper TTS ─────────► narration.wav ────┤
       │                            │             │
       │                            ▼             │
       │                    faster-whisper ───────┤  word-level captions
       │                                          │
       └─► sound.py ──────────► music + SFX ──────┤  hits land on beats
                                                  │
                                                  ▼
                                            props.json
                                                  │
                                                  ▼
                                      Remotion ──► final.mp4
```

### The one non-obvious decision

**Captions do not come from the recording.** The recordings are silent — there
is no speech to transcribe. Nearly every "auto-caption" tutorial assumes
otherwise and breaks here.

Instead we generate narration with TTS, then run Whisper **on our own
generated audio** to get word timings that are exact against the track we are
actually going to play. Those feed `@remotion/captions` to drive karaoke-style
word highlighting.

```
script line → Piper → narration.wav → Whisper → word timestamps → captions
```

### Beat detection, in one paragraph

Decode the video at 15fps, 96×171, greyscale. Take the mean absolute
difference between consecutive frames. That signal reads cleanly:

| signal | meaning | policy |
|---|---|---|
| flat near zero | nothing happening | **6× speed** |
| low, sustained | typing | **2× speed** |
| single large spike | a state change | **1× + zoom punch** |

No ML, no API, deterministic, ~2 seconds per clip.

**Validated:** run on `type-fix.mov` it independently identified `18.00s` as
the moment the correction applies — the exact frame found earlier by manual
inspection — and compressed 48.8s → 15.9s while keeping every decision at 1×.

---

## 3. Repositories and why each one

| Repo | Stars | Role | Why this over alternatives |
|---|---|---|---|
| **[remotion-dev/remotion](https://github.com/remotion-dev/remotion)** | 73k | Renderer | Video as React. The only mature tool where a video is a *function of props* — which is what makes one composition serve 100 videos. After Effects + scripting can't be driven from a JSON file in CI. |
| **[remotion-dev/template-tiktok](https://github.com/remotion-dev/template-tiktok)** | 308 | Caption pattern | The canonical word-highlight implementation. We follow its per-token `active` idiom rather than reinventing it. |
| **[SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper)** | 27k | Word timings | CTranslate2 reimplementation — ~4× faster than `openai-whisper` on CPU at equal accuracy, and it exposes `word_timestamps` directly. Matters because this runs once per video. |
| **[ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp)** | 55k | Alt. transcription | Use when you want the toolchain entirely inside Node — Remotion ships `@remotion/install-whisper-cpp` to manage it. Chosen *against* here only because the pipeline is already Python. |
| **[OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl)** | 6.3k | TTS | What `pip install piper-tts` (v1.8.0) actually installs today — Piper's current home. Runs locally, offline, free, ~0.5s for a 15s line. The economics of 100 videos/month don't survive a per-character API. Swap to ElevenLabs for hero pieces via `TB_TTS`. |
| **[rhasspy/piper](https://github.com/rhasspy/piper)** | 11.3k | Voice models | The original project. Still where the voices live — `rhasspy/piper-voices` on HuggingFace. We use `en_US-ryan-high`. |
| **[Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect)** | 5.5k | Shot detection | Worth adding when recordings contain hard app-switches. Our frame-diff is deliberately simpler because screen recordings have *no shot cuts* — only UI state changes, which PySceneDetect's content detector is not tuned for. |
| **[WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor)** | 5.9k | Silence trimming | The obvious off-the-shelf answer, and the right tool if your recordings have **audio**. Ours are silent, so its audio-loudness heuristic has nothing to work with — hence `beats.py`. |
| **[FFmpeg](https://github.com/FFmpeg/FFmpeg)** | — | Everything else | Conform, speed-ramp, mix, duck, encode. |

> Star counts checked via the GitHub API on 15 Nov 2026. Note `piper-tts` on
> PyPI points at `OHF-Voice/piper1-gpl`, **not** the older `rhasspy/piper` —
> an easy thing to get wrong when citing from memory.

Also in the stack but not a repo: **`@remotion/captions`** (in the Remotion
monorepo) for `createTikTokStyleCaptions`, which turns a flat word list into
paged karaoke captions with sane line breaks.

---

## 4. The craft decisions, made once

These live in code and apply to every video, which is the point.

| Decision | Setting | Reasoning |
|---|---|---|
| Hook timing | lands on **frame 1**, no fade | A hook that fades in loses its first 6 frames. 3-second play rate is the delivery signal on both platforms. |
| Dead air | 6× | Below ~4× it still reads as waiting. |
| Typing | 2× | Fast enough to compress, slow enough to still read as typing. |
| Decision moments | **1×, never cut** | Including the loading spinner. Removing the wait makes it look fake; speeding it 2.4× keeps it honest and watchable. |
| Zoom | 1.12–1.14 on each beat, ease out over 1.25s | Measured ceiling before phone UI clips. |
| Captions | ~1.2s per page, 3–5 words | Readable at thumb distance; faster reads as a subtitle track. |
| Caption style | white, 14px ink stroke, accent on active word | Survives any background without a box. |
| Music | ducked 8:1 under VO via sidechain | Voice always wins. |
| SFX | whoosh 0.16s *before* each beat, ding *on* it | Anticipation before payoff — the thing that makes a cut feel intentional. |

---

## 5. Concepts

Each is a JSON file in `viral/concepts/`. Add a file, get a video.

### A. Mistake Reveal — `mistake-reveal.json` *(built)*
> **"I type like this. On purpose."** → *Watch what happens next.*

Self-deprecating, pattern-interrupting, and it makes the viewer wait for the
payoff. The strongest default because the hook creates an open loop in four
words.

### B. Speed Run
> **"How fast can you fix a broken sentence?"**

Timer in the corner. Types garbage, taps, fixed — under 2 seconds. Competitive
framing invites "I could do that faster" comments, which is engagement.

### C. The Boss Text
> **"You do NOT send this to your boss."**

Shows an aggressive draft, then the Professional tone rewrite. Stakes are
instantly legible; everyone has written that message.

### D. Typo Autopsy
> **"Three mistakes in one sentence. Can you find them?"**

Holds on the bad sentence for 2s — viewers hunt, which is watch time — then the
fix highlights all three at once.

### E. POV
> **"POV: you type like you talk."**

Native-format framing. Lowest production polish, often highest reach.

### F. Before/After Split
> **"Same message. Two senders."**

Split screen, unfixed vs fixed. Most explicit value demonstration; best for
paid placement rather than organic.

**Rotation strategy:** 2 proven cores × 3–5 fresh hooks weekly. Hooks are cheap
to produce (one line in a JSON file), cores are expensive. Test hooks, keep
cores.

---

## 6. Running it

```bash
# one video
python viral/pipeline.py --recording raw/clip.mov --concept mistake-reveal

# fast draft while iterating on a concept
python viral/pipeline.py --recording raw/clip.mov --concept pov --scale 0.5

# inspect what the detector sees, without rendering
python viral/steps/beats.py raw/clip.mov
```

**Batch — a week of content from one shoot:**

```bash
for c in viral/concepts/*.json; do
  python viral/pipeline.py --recording raw/clip.mov --concept "$c"
done
```

One recording × six concepts = six genuinely different videos, because the
hook, script, captions, pacing dials and music style all change.

### Recording guidance

The better the input, the less the system has to compensate:

1. **Make real mistakes** — the ones people actually make (`their/there`,
   `i has send`, missing apostrophes). Invented typos look invented.
2. **Pause ~1s before tapping** the fix. Gives the detector a clean boundary
   and gives the edit a breath.
3. **Let the correction sit ~2s** before touching anything.
4. **One fix per recording.** Two cycles in one clip (as in `type-fix.mov`)
   works, but one is tighter.
5. **Don't trim anything.** Dead air is free — the pipeline removes it.

---

## 7. What is deliberately not automated

- **Which recording to shoot.** The concept decides the footage, not the
  reverse.
- **Whether a cut is good.** Every render gets eyeballed before posting.
- **Trending audio.** Attach it natively in the app at upload — platform-native
  sound is favoured by both algorithms, and it beats any bed we ship.

---

## 8. Known gaps

| Gap | Status |
|---|---|
| ElevenLabs voice | Scripted and wired behind `TB_TTS=elevenlabs`; blocked in this environment (connector 502s, no API key set). Piper is the working default. |
| Real music | Synth bed is on by default. Drop any `.mp3` into `music_library/` and `sound.bed()` uses it instead. |
| App icon | Reconstructed from the App Store listing. Replace `projects/viral-engine/public/app_icon_1024.png` with the original. |
| Auto-publishing | Not wired. Postiz/Metricool connectors exist for multi-account scheduling if you want it. |
