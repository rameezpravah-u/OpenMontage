# What to type while recording

Type these **exactly as written**, mistakes and all. Each one is built to make
TypeBetter do something visible, and each maps to a concept in
`viral/concepts/`.

## How to record (this part matters more than the sentences)

1. **Start recording with the field already empty**, keyboard up.
2. **Type the sentence at normal speed.** Don't slow down for the camera — the
   pipeline speeds typing up 2× anyway.
3. **Pause ~1 second** after the last character before you tap. This gives the
   beat detector a clean edge and gives the edit a breath.
4. **Tap the tool.** Let the "Generating Text" spinner run — do not cut it
   short. It gets sped up 2.4×, not removed, because the wait is what makes it
   look real.
5. **Let the result sit ~2 seconds** before you tap Apply.
6. **After Apply, hold ~2 seconds** on the corrected text. This is the payoff
   frame; everything before it exists to earn it.
7. **One fix per recording.** Stop, start a new one for the next sentence.
8. **Don't trim anything.** Dead air is free — the pipeline removes it.

Dark mode and light mode both work. Keep one mode per batch so cuts don't flip.

---

## Set 1 — Fix Grammar
*For: `mistake-reveal`, `typo-autopsy`, `pov`*

These contain the mistakes people genuinely make, not invented ones. Invented
typos look invented on camera.

| # | Type this exactly | The mistakes | Should become roughly |
|---|---|---|---|
| 1.1 | `i has send the report yesterday, please check it and revert me back` | `has send`, no caps, `revert me back` | I sent the report yesterday — could you take a look and let me know? |
| 1.2 | `Their going to there office because they forget there laptop` | `Their/there/there`, `forget` | They're going to their office because they forgot their laptop. |
| 1.3 | `she dont know weather the meeting is on monday or tuesday` | `dont`, `weather/whether`, no caps | She doesn't know whether the meeting is on Monday or Tuesday. |
| 1.4 | `your going to love this, its the best app ive used all year` | `your/you're`, `its/it's`, `ive` | You're going to love this — it's the best app I've used all year. |
| 1.5 | `me and him was discussing about the new project yesterday` | `me and him was`, `discussing about` | He and I were discussing the new project yesterday. |
| 1.6 | `could of been better but their was alot of issues` | `could of`, `their/there`, `alot` | It could have been better, but there were a lot of issues. |

**Best for a 3-mistake hook** (`typo-autopsy`): use **1.2** or **1.6** — both
have exactly three findable errors, which makes the "can you spot them all?"
hook literally true.

---

## Set 2 — Change Tone
*For: `boss-text`, `before-after`*

Type something you'd regret sending, then switch the tone. The draft has to be
plausible, not cartoonish.

| # | Type this exactly | Tone to pick | Why it works on camera |
|---|---|---|---|
| 2.1 | `am waiting since one hour, your delivery boy still not came` | Casual | Universally relatable; the rewrite is a visible personality change. |
| 2.2 | `this is the third time im asking about the invoice. please pay` | Polite / Professional | Real stakes. Everyone has written this and hesitated. |
| 2.3 | `no i cant do that by friday thats not realistic` | Diplomatic | Shows it can soften a refusal without reversing it. |
| 2.4 | `hey so i basically need the thing we talked about asap thanks` | Professional | Vague → precise is a dramatic visual jump. |
| 2.5 | `your design is wrong and the colors dont work at all` | Empathetic | Hard feedback made sendable — strong for a work audience. |

**Strongest single take:** 2.2. "Third time asking about the invoice" is
instantly legible and the Professional rewrite reads like a different person
sent it.

---

## Set 3 — Shorten / Expand
*For: `speed-run`*

| # | Type this exactly | Tool | Payoff |
|---|---|---|---|
| 3.1 | `Can you please do the needful and share me the invoice till friday` | Shorten | Long and awkward collapses to one clean line. |
| 3.2 | `i just wanted to quickly reach out and check in to see whether or not you might possibly have had a chance to look at the document i sent over last week` | Shorten | The best one for this set — a visibly absurd wall of text collapsing is the whole gag. |
| 3.3 | `ok` | Expand | Inverts the pattern: two letters become a full sentence. Great as the last beat in a sequence. |
| 3.4 | `cant make it` | Expand | Short and rude becomes short and polite. |

---

## Set 4 — Voice
*For: any concept; strongest as a second beat*

Speak these rather than type them. Deliberately include the disfluency — the
product's pitch is that it cleans them up.

| # | Say this | What should land |
|---|---|---|
| 4.1 | "um so like, tell Riya I'll be, uh, ten minutes late, sorry" | Tell Riya I'll be 10 minutes late. Sorry! |
| 4.2 | "hey can you um send me the, the file when you get a sec" | Hey, could you send me the file when you get a second? |
| 4.3 | "so basically the meeting is moved to uh Thursday I think" | The meeting has been moved to Thursday. |

---

## Priority order

If you only record a few, record these, in this order:

1. **1.2** — `Their going to there office...` → three clear errors, the hook writes itself
2. **2.2** — `this is the third time im asking about the invoice...` → highest stakes
3. **3.2** — the rambling wall of text → most satisfying collapse
4. **1.4** — `your going to love this, its...` → the two most common errors in English
5. **4.1** — the voice one with the ums
6. **3.3** — `ok` → Expand, as a closer

That's six recordings, one per concept, and a week of content.

---

## Theme notes applied to the engine

- **No blue.** Sampled the iOS app directly: it is black, white and warm
  off-white only. The blue used earlier came off the website's *Android* card
  and does not exist in the iPhone product. Removed.
- The only colours the product uses are the **correction green `#21C165`**
  (the ✓Applied tick) and a **muted error red `#A04641`** (strikethrough).
  Captions now highlight the active word in the correction green, which also
  reads semantically: green means fixed.
- **Offer is now 2,000 AI words**, not 5,000. Updated in every concept, the
  engine default, and the CTA.
- iPhone only — no Google Play or Android reference in any frame.
