# Vemo — Handoff Document

## What This Is
Workplace wellbeing AI agent for remote workers. Analyzes voice biomarkers from meeting recordings (emotion2vec+ and Kintsugi DAM) overlaid on simulated wearable biometric data (Whoop). Claude agent delivers real-time interventions with streaming responses.

## Location
`/Users/stefanoleitner/vibecode/longevity-hackathon/betterness/`

## Repo
https://github.com/stefanoleitner/vemo

## How to Run
```bash
cd /Users/stefanoleitner/vibecode/longevity-hackathon/betterness
export ANTHROPIC_BASE_URL="https://api.yacine.xyz"
export ANTHROPIC_AUTH_TOKEN="ff_ba1636cc368d4021"
export ANTHROPIC_MODEL="claude-opus-4-6"
streamlit run app.py
```

## Architecture
- `app.py` — single-file Streamlit app, ~940 lines
- `persona_data.json` — 4 base biometric profiles × 288 readings (5-min intervals, 24h)
- `skills/` — 4 markdown skill files
- `.streamlit/config.toml` — dark theme
- `streamlit-autorefresh` — used for smooth play mode (client-side JS timer)

## 6 Employee Personas
1. **Maya Chen** (💜) — Sr Engineer, meeting overload, uses `maya` biometrics
2. **Derek Okafor** (🧡) — PM, context switching anxiety, uses `derek` biometrics
3. **Jordan Torres** (🔥) — Sr SDR, cold call burnout, maps to `derek` biometrics
4. **Travis Kim** (❤️) — Eng Manager, new manager stress, uses `travis` biometrics
5. **Priya Mehta** (🌏) — Global Ops, timezone burnout (7am–10pm), maps to `maya` biometrics
6. **Lucia Vargas** (💚) — CS Head, balanced leader (healthy benchmark), uses `lucia` biometrics

New personas (Jordan, Priya) map to existing biometric data via `BIOMETRIC_MAP` dict.

## App Flow (4 screens)
1. **Employee Select** — 2×3 grid with recovery/meetings/hours stats
2. **Day View** — Play mode (autorefresh), biometric chart with meeting overlays appearing as day progresses. Each persona has a `trigger_meeting` that fires an alert when reached. Meeting list shows status (upcoming/in-progress/done) with emotion scores revealed after completion. Also has Week view toggle.
3. **Meeting Detail** — Emotion radar chart + clinical gauges (PHQ-9/GAD-7) + biometrics. Streaming agent response.
4. **Daily Summary** — Emotional arc across all meetings, biometric overlay, streaming end-of-day briefing, weekly trend chart.

## Trigger System
- Each employee has a `trigger_meeting` index (except Lucia who is None)
- When play mode reaches the end of that meeting, playback stops
- Pulsing red alert appears with meeting name + dominant emotion
- 5-step animated "thinking" sequence plays out
- Agent response streams in real-time with glowing green card
- Quick action buttons: Start Breathing, Block Calendar, Walking Break, Full Analysis

## Agent Architecture
- Uses raw Anthropic API with streaming (`client.messages.stream`)
- Two prompt types: `build_meeting_system_prompt` (per-meeting) and `build_daily_system_prompt` (end-of-day)
- Agent is framed as AGENTIC — takes actions, not just advises
- Streaming gives real-time typewriter effect

## Mock Data
- Emotion scores: `get_meeting_emotions()` — seeded random per employee+meeting, meeting-type-aware
- Clinical scores: `get_meeting_clinical()` — fixed per employee+meeting-type
- Weekly data: `get_week_daily_scores()` — seeded random stress/happiness per day
- No real models running — all mock for demo speed

## Key Dependencies
- streamlit, streamlit-autorefresh, anthropic, plotly

## What Works
- All 4 screens functional
- Play mode with autorefresh (smooth, no sleep blocking)
- Trigger alerts with animated agent sequence
- Streaming agent responses
- Quick action buttons with toast feedback
- Week view with stress trends
- Meeting-by-meeting navigation

## Things to Improve / Known Issues
- Play mode can sometimes double-tick on first rerun
- Priya's late-night meetings (21:00–22:00) extend beyond the default chart x-axis range — chart clips to 19:00 by default
- Quick action buttons are cosmetic only (toast notifications, no real calendar integration)
- Could add monthly view / longer-term trends
- Could add comparison between employees
- Audio recording/upload was removed in the pivot — could bring back for live demo
- The "Continue Day" button after a trigger works but resets the trigger state
