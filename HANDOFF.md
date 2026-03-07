# Vemo — Handoff Document

## What This Is
Workplace wellbeing AI agent for remote workers. Analyzes voice biomarkers from meeting recordings (emotion2vec+ and Kintsugi DAM) overlaid on simulated wearable biometric data (Whoop). Claude agent delivers real-time interventions with streaming responses, powered by a skill protocol library.

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
- `app.py` — single-file Streamlit app, ~1100 lines
- `persona_data.json` — 4 base biometric profiles x 288 readings (5-min intervals, 24h)
- `skills/` — 7 markdown skill files (stress-resilience, recovery-coach, sleep-analyst, morning-briefing, heart-health-scorecard, inflammation-tracker, longevity-protocol)
- `.streamlit/config.toml` — dark theme
- `streamlit-autorefresh` — used for smooth play mode (client-side JS timer)

## 3 Employee Personas
1. **Maya Chen** (depressed) — Sr Engineer, meeting overload, sadness-dominant voice, declining 6-month trajectory, uses `maya` biometrics
2. **Derek Okafor** (anxious) — PM, context switching anxiety, fear-dominant voice, spiking stress, uses `derek` biometrics
3. **Lucia Vargas** (healthy) — CS Head, balanced leader, happy-dominant voice, stable trajectory, uses `lucia` biometrics

Each persona has distinct emotion profiles, clinical scores, weekly patterns, and 6-month trend trajectories.

## App Flow (4 screens)
1. **Employee Select** — 1x3 grid with recovery/meetings/hours stats
2. **Day View** — Three sub-views via segmented control:
   - **Day**: Play mode (autorefresh), biometric chart with meeting overlays, meeting timeline with status (upcoming/in-progress/done), emotion scores revealed after completion
   - **Week**: Stress/positive chart + daily cards
   - **Trends**: 6-month trajectory chart (stress, mood, recovery) + monthly cards + auto-generated DECLINING/STABLE/IMPROVING label
3. **Meeting Detail** — Emotion radar chart + clinical gauges (PHQ-9/GAD-7) + biometrics. Streaming agent response.
4. **Daily Summary** — Emotional arc across all meetings, biometric overlay, streaming end-of-day briefing, weekly trend chart.

## Trigger + Intervention System (the core demo flow)
Each employee has a `trigger_meeting` index (except Lucia who is None). When play mode reaches the end of that meeting:

1. **Alert** — Playback stops, pulsing red alert with meeting name + dominant emotion
2. **Analysis animation** — 5-step animated sequence (emotion2vec+, Kintsugi DAM, biometric correlation, skill matching, voice channel)
3. **Voice input** — User can record live audio via `st.audio_input` OR upload a pre-saved audio file (.wav/.mp3/.m4a/.ogg/.webm)
4. **Model processing animation** — Shows emotion2vec+, Kintsugi DAM, biometric correlation, skill matching steps
5. **Results display** — Three cards showing dominant emotion, depression score (PHQ-9), anxiety score (GAD-7)
6. **Skills activated** — Auto-selected based on trigger data (emotions, clinical, biometrics). Displayed as green pills. 2-4 skills per trigger.
7. **Agent streams** — Intervention response referencing skill protocols by name, with biometric data
8. **Quick actions** — Start Breathing, Block Calendar, Walking Break, Full Analysis buttons

### Skill Selection Logic (`select_skills`)
- Negative emotion (angry/fearful/sad/disgusted) -> stress-resilience
- High HR (>80) or low HRV (<40) -> heart-health-scorecard
- Depression >=1 or anxiety >=2 -> recovery-coach
- Anxiety >=2 or depression >=2 -> inflammation-tracker
- Always includes sleep-analyst
- Severe (depression >=2 AND anxiety >=2) -> longevity-protocol

### Intervention State Machine
`st.session_state.intervention_step`: "alert" -> "listening" -> "processing" -> "responding"

## Agent Architecture
- Uses raw Anthropic API with streaming (`client.messages.stream`)
- Three prompt types:
  - `build_meeting_system_prompt` — per-meeting analysis
  - `build_daily_system_prompt` — end-of-day briefing
  - `build_intervention_prompt` — trigger intervention with skills (references voice biomarkers, clinical screening, biometrics, and skill protocols)
- Agent is framed as AGENTIC — takes actions, not just advises
- Streaming gives real-time typewriter effect

## Mock Data
- Emotion scores: `get_meeting_emotions()` — seeded random per employee+meeting, meeting-type-aware base profiles
- Clinical scores: `get_meeting_clinical()` — fixed per employee+meeting-type
- Weekly data: `get_week_daily_scores()` — seeded random stress/happiness per day
- Monthly trends: `get_monthly_trends()` — 6-month trajectories (Oct-Mar), different per persona
- No real models running — all mock for demo speed. Audio input is for visual credibility only.

## Key Dependencies
- streamlit, streamlit-autorefresh, anthropic, plotly

## What Works
- All 4 screens functional
- Play mode with autorefresh (smooth, no sleep blocking)
- Trigger alerts with voice recording/upload -> model processing animation -> results + skills + agent
- Streaming agent responses with skill protocol references
- 6-month trend view with trajectory analysis
- Quick action buttons with toast feedback
- Week view with stress trends
- Meeting-by-meeting navigation

## Known Issues / Things to Improve
- Play mode can sometimes double-tick on first rerun
- Quick action buttons are cosmetic only (toast notifications, no real calendar integration)
- Audio input is visual only — not actually processed through models (mock data used)
- Could add comparison between employees on trends view
- Could add actual speech-to-text transcription of recorded audio
- The "Continue Day" button after a trigger works but resets the trigger state
- Trigger content requires scrolling down — could benefit from a modal/popup approach
