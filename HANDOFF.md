# Betterness App — Handoff for Next Session

## What This Is
A multi-screen Streamlit app for a longevity hackathon demo. Voice biomarkers (emotion2vec+ and Kintsugi DAM) overlaid on simulated Whoop biometric data, with an LLM agent delivering personalized interventions.

## Location
`/Users/stefanoleitner/vibecode/longevity-hackathon/betterness/`

## How to Run
```bash
cd /Users/stefanoleitner/vibecode/longevity-hackathon/betterness
export ANTHROPIC_BASE_URL="https://api.yacine.xyz"
export ANTHROPIC_AUTH_TOKEN="ff_ba1636cc368d4021"
export ANTHROPIC_MODEL="claude-opus-4-6"
streamlit run app.py
```

## Architecture
- `app.py` — single-file Streamlit app, ~700 lines
- `persona_data.json` — 4 personas × 288 readings (5-min intervals, 24h), converted from Excel
- `skills/` — 4 markdown skill files (stress, sleep, recovery, morning briefing)
- `.streamlit/config.toml` — dark theme
- `../emotion2vec_plus_large/` — local emotion2vec+ large model (1.8GB, loaded via funasr)
- `../dam/` — Kintsugi DAM 3.1 model (depression/anxiety clinical screening via pipeline.py)

## App Flow (4 screens)
1. **Persona Selection** — 4 cards (Maya/Derek/Travis/Lucia) with recovery scores
2. **Live Monitoring** — Play button auto-advances through 24h biometric data. Chart shows HRV + HR with distress zone. When anomaly detected (HRV crash, HR spike), auto-navigates to check-in
3. **Voice Check-in** — Record or upload audio (.wav, .mp3, .m4a). Runs both models
4. **Results + Intervention** — Side-by-side: emotion2vec+ (9 emotions) and Kintsugi DAM (PHQ-9 depression + GAD-7 anxiety). Signal correlation panel. Claude agent with skill bar and structured intervention

## Two Voice Models
- **emotion2vec+ large** — 9-class speech emotion recognition (angry, sad, fearful, happy, neutral, etc.)
- **Kintsugi DAM 3.1** — Clinical-grade depression (PHQ-9) and anxiety (GAD-7) screening from acoustic properties only
- Both have LIVE/SIMULATED badges. Falls back to persona-matched mock scores if models fail to load
- Models are lazy-loaded and cached via `@st.cache_resource`

## Key Dependencies
- streamlit, audio-recorder-streamlit, anthropic, plotly, torch, torchaudio, funasr, pydub
- ffmpeg (installed via homebrew)
- peft, transformers (for DAM model)

## What Works
- Persona selection screen
- Play button with speed control (1x/2x/4x/8x) and reset
- Biometric anomaly detection triggers auto-navigation to check-in
- Audio upload + conversion (m4a→wav via pydub)
- Dual model analysis with badges
- Claude agent intervention with skill selection and structured output
- Navigation between all 4 screens

## Known Issues / Things to Improve
- emotion2vec+ model takes ~30-60s to load on first run (cached after)
- DAM model may need `peft` and `transformers` installed: `pip install peft transformers`
- The play animation uses `time.sleep(0.3)` + `st.rerun()` which can feel janky in Streamlit
- No audio playback preview before analysis
- Could add a progress indicator during model loading
- The "What this agent can do" capabilities grid could be interactive
- Could add longitudinal tracking across multiple check-ins in one session
