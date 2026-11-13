# Motion-design prompt libraries

Five libraries of Claude Opus 5.5 motion-graphics work, each published **with the prompts
behind them**. Sourced from [@ux.robin's post](https://www.instagram.com/p/DfCG01WiB-Y/)
(28 Oct 2026). All URLs checked and live on 13 Nov 2026.

These are reference material for the Type Better reels — places to pull a look, a motion
idiom, or a working prompt rather than inventing one from scratch.

| # | Library | URL | What it is |
|---|---|---|---|
| 1 | **Skillry** | https://skillry.com | Gallery of Opus 5.5 videos where each clip sits **next to a live remake** you can compare. Browse, open a clip, copy the prompt. The compare-view is the useful part — you see what the prompt actually produced. |
| 2 | **Prompt Motion** | https://prompt-motion.com | Free library of AI motion-graphics videos, each shown with the prompt *or skill* that made it. Filter by either, then copy. |
| 3 | **Claude Video** | https://claudevideo.org · [all videos](https://claudevideo.org/videos) | The big index: **1,276 videos from 1,007 creators**, searchable and sortable by type. 457 of them carry the full copyable prompt. Best for "what has anyone done in this genre." |
| 4 | **Prompt Motion (.org)** | https://promptmotion.org · [prompts](https://promptmotion.org/prompts) | Separate site, same idea — leans toward **showreels, launch films and UI motion**, which is the closest category to an app promo. |
| 5 | **JasonZhu.AI** | [Claude 5.5 prompt library](https://jasonzhu.ai/en/prompts/claude-opus-5-5) · [motion graphics](https://jasonzhu.ai/en/prompts/claude-opus-5-5/motion-graphics) | Ranked by views — every entry has **5,000+ views on X**. The motion-graphics section alone has 324 ranked examples with full prompts. Ranking by performance is what makes this one worth starting with. |

Also relevant: the upstream GitHub collection behind Skillry —
`github.com/yihui-dev/awesome-opus5-5-videos` (returns 403 through this session's proxy;
reachable via `gh api` or a normal browser).

## Caveats worth knowing before relying on a prompt

- **Counts drift.** Different sources report different totals for the same library (Skillry's
  companion repo has been cited at anything from 475 to 853 prompts). The sites are updated
  continuously; treat any number as a snapshot.
- **Not every prompt is complete.** Some creators published only part of a prompt, or a
  description of the result rather than the prompt itself.
- **Some results are unreproducible from the prompt alone.** JasonZhu.AI flags entries where
  the creator also supplied images, video, audio, documents or a codebase that aren't hosted
  with the prompt — the text on its own won't recreate those.
- **These are community indexes, not Anthropic publications.** No official announcement backs
  any of them.

## How these fit the Type Better work

The four reels built so far are all hand-authored Remotion under
`composition_mode: "atelier"`. These libraries are useful in two specific ways:

1. **Motion idioms to steal mechanically** — easing curves, stagger patterns, transition
   families. Reuse the *technique*, never the look (per `skills/meta/bespoke-composition.md`:
   reuse engine knowledge, never creative components).
2. **Category reconnaissance** — Prompt Motion (.org)'s launch-film section and
   JasonZhu.AI's view-ranked list are the fastest way to see what app-promo motion is
   actually performing, which is the same question the earlier competitor research answered
   for format rather than motion.

Sources: [@ux.robin on Instagram](https://www.instagram.com/p/DfCG01WiB-Y/) ·
[Awesome Opus 5.5 Videos](https://aiidelist.com/blog/awesome-opus-5-5-videos) ·
[Prompt Motion overview](https://toolfolio.com/articles/what-is-prompt-motion-how-to-use-the-free-claude-motion-prompt-library-step-by-step) ·
[Claude Video index](https://claudevideo.org/)
