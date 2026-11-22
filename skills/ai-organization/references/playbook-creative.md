# Creative, video and design playbook

## Video

1. **Creative brief:** audience, one key message, tone, length, aspect ratio (16:9, 9:16 or 1:1) and platform.
2. **Script:** a hook in the first 2–3 seconds, one idea per scene, written for the ear. Read it aloud and time it.
3. **Storyboard / shot list:** scene → visuals → on-screen text → motion → duration → audio cue.
4. **Design system:** palette, type scale, motion principles (easing, durations, stagger) and safe areas.
5. **Build** with the installed video skill (for example Remotion's `remotion-dev/skills` or HyperFrames): compositions, sequences, spring/interpolate animation, audio sync and captions.
6. **Render** test stills at key frames first, then the full render (H.264, correct fps and resolution).
7. **Review:** extract a frame every second (`ffmpeg -i out.mp4 -vf fps=1 frames/%03d.png`), look at each one for overflow, contrast, typos, timing and jank, and check the specs with `ffprobe`. Fix and re-render.

**Quality bar:** no text outside safe areas; readable on a phone; captions present; one consistent motion language; balanced sound; exact duration and specs.

## Design / UI

Use `frontend-design` (from `anthropics/skills`) or the installed equivalent. Commit to a clear aesthetic direction, a type scale and spacing tokens, design mobile-first, and meet WCAG AA contrast. Screenshot every key screen at mobile (375px) and desktop widths for review.
