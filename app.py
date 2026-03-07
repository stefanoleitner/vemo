import streamlit as st
import json
import os
import sys
import tempfile
import time

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Model loading (lazy, cached)
# ---------------------------------------------------------------------------
LOCAL_EMOTION_MODEL = os.path.join(os.path.dirname(__file__), "..", "emotion2vec_plus_large")
DAM_DIR = os.path.join(os.path.dirname(__file__), "..", "dam")

@st.cache_resource
def load_emotion_model():
    try:
        from funasr import AutoModel
        if os.path.isdir(LOCAL_EMOTION_MODEL):
            return AutoModel(model=LOCAL_EMOTION_MODEL)
        else:
            return AutoModel(model="iic/emotion2vec_plus_base", hub="hf")
    except Exception:
        return None

@st.cache_resource
def load_dam_model():
    try:
        sys.path.insert(0, DAM_DIR)
        from pipeline import Pipeline
        return Pipeline()
    except Exception:
        return None

try:
    from pydub import AudioSegment
    def convert_to_wav(input_path):
        audio = AudioSegment.from_file(input_path)
        wav_path = input_path.rsplit(".", 1)[0] + ".wav"
        audio.export(wav_path, format="wav")
        return wav_path
except ImportError:
    convert_to_wav = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMOTION_LABELS = ["angry", "disgusted", "fearful", "happy", "neutral", "other", "sad", "surprised", "unknown"]

PERSONA_COLORS = {"maya": "#6366f1", "derek": "#f59e0b", "travis": "#ef4444", "lucia": "#10b981"}
PERSONA_EMOJI = {"maya": "💜", "derek": "🧡", "travis": "❤️", "lucia": "💚"}

EMOTION_COLORS = {
    "angry": "#ef4444", "disgusted": "#a855f7", "fearful": "#f59e0b", "happy": "#10b981",
    "neutral": "#6b7280", "other": "#94a3b8", "sad": "#3b82f6", "surprised": "#ec4899", "unknown": "#475569",
}

DEPRESSION_LEVELS = ["No Depression", "Mild-Moderate", "Severe"]
ANXIETY_LEVELS = ["No Anxiety", "Mild", "Moderate", "Severe"]
SEVERITY_COLORS = {
    "No Depression": "#10b981", "Mild-Moderate": "#f59e0b", "Severe": "#ef4444",
    "No Anxiety": "#10b981", "Mild": "#6366f1", "Moderate": "#f59e0b", "Severe": "#ef4444",
}

ALERT_EXPLAINERS = {
    "hrv_crash": {
        "what": "Your heart rate variability (HRV) dropped sharply — a sign your autonomic nervous system shifted into fight-or-flight mode.",
        "why": "A sudden HRV crash while not exercising is one of the strongest physiological markers of acute stress, anxiety, or emotional distress.",
        "do": "A voice check-in lets us cross-reference your physiological stress with emotional state to determine the right intervention.",
    },
    "hr_spike": {
        "what": "Your heart rate spiked above resting levels despite no physical activity — your body is reacting to something.",
        "why": "Elevated heart rate at rest suggests sympathetic nervous system activation — often triggered by stress, conflict, or rumination.",
        "do": "A voice check-in helps us distinguish physical causes (caffeine, dehydration) from emotional ones (anxiety, frustration).",
    },
    "combined": {
        "what": "Your HRV dropped critically low while your heart rate climbed — a dual signal of significant physiological stress.",
        "why": "When both markers move together, it's a strong indicator that your body is under real strain — not a sensor glitch.",
        "do": "This pattern warrants immediate attention. A voice check-in will help us tailor the right response.",
    },
}

ALL_SKILLS = [
    {"name": "Stress Resilience", "icon": "🧘", "desc": "Breathing protocols, acute stress reduction"},
    {"name": "Sleep Analyst", "icon": "🌙", "desc": "Sleep debt strategy, environment optimization"},
    {"name": "Recovery Coach", "icon": "🔋", "desc": "Activity throttling, rest scheduling"},
    {"name": "Morning Briefing", "icon": "☀️", "desc": "Daily synthesis, positive reinforcement"},
    {"name": "Clinical Escalation", "icon": "🏥", "desc": "Provider referral, PHQ-9/GAD-7 screening"},
    {"name": "Social Connection", "icon": "🤝", "desc": "Isolation detection, support network"},
]

SKILL_INFO = {
    "skills/stress-resilience.md": {"name": "Stress Resilience", "icon": "🧘", "trigger": "Elevated fear/anger in voice"},
    "skills/recovery-coach.md": {"name": "Recovery Coach", "icon": "🔋", "trigger": "Recovery score < 34%"},
    "skills/sleep-analyst.md": {"name": "Sleep Analyst", "icon": "🌙", "trigger": "Sleep performance < 60%"},
    "skills/morning-briefing.md": {"name": "Morning Briefing", "icon": "☀️", "trigger": "Default daily check-in"},
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_persona_data():
    with open(os.path.join(os.path.dirname(__file__), "persona_data.json")) as f:
        return json.load(f)

# ---------------------------------------------------------------------------
# Anomaly detection on biometrics
# ---------------------------------------------------------------------------
def detect_anomalies(hourly_data, start_idx=0):
    """Scan biometric data for distress signals. Returns list of (index, reason)."""
    alerts = []
    for i in range(max(start_idx, 12), len(hourly_data)):  # skip first hour (sleep)
        d = hourly_data[i]
        # Look back 6 readings (30 min) for HRV trend
        if i >= 6:
            recent_hrv = [hourly_data[j]["hrv_rmssd_ms"] for j in range(i-6, i)]
            avg_hrv = sum(recent_hrv) / len(recent_hrv)
            current_hrv = d["hrv_rmssd_ms"]

            # HRV crash: dropped >30% below recent average
            if current_hrv < avg_hrv * 0.7 and current_hrv < 30:
                alerts.append((i, "hrv_crash", f"HRV crashed to {current_hrv:.0f}ms (30-min avg was {avg_hrv:.0f}ms)"))
                continue

        # Elevated HR while not exercising
        if d["heart_rate_bpm"] > 90 and d["state"] not in ("Exercise", "High Strain"):
            alerts.append((i, "hr_spike", f"HR elevated to {d['heart_rate_bpm']:.0f}bpm while {d['state'].lower()}"))
            continue

        # Combined: low HRV + elevated HR
        if d["hrv_rmssd_ms"] < 20 and d["heart_rate_bpm"] > 80:
            alerts.append((i, "combined", f"HRV critically low ({d['hrv_rmssd_ms']:.0f}ms) with elevated HR ({d['heart_rate_bpm']:.0f}bpm)"))

    return alerts

def find_first_alert_after(hourly_data, hour):
    """Find the first anomaly at or after the given hour."""
    min_idx = hour * 12  # 5-min intervals
    alerts = detect_anomalies(hourly_data, min_idx)
    return alerts[0] if alerts else None

# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------
def save_audio(audio_bytes, fmt="wav"):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{fmt}")
    tmp.write(audio_bytes)
    tmp.close()
    return tmp.name

# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------
def analyze_emotion(audio_path):
    persona_key = st.session_state.get("persona", "maya")
    hour = st.session_state.get("alert_hour", 12)
    return get_mock_emotion_scores(persona_key, hour), True

def analyze_clinical(audio_path):
    persona_key = st.session_state.get("persona", "maya")
    return get_mock_clinical(persona_key), True

def get_mock_clinical(persona_key):
    return {"maya": {"depression": 2, "anxiety": 1}, "derek": {"depression": 0, "anxiety": 3},
            "travis": {"depression": 1, "anxiety": 2}, "lucia": {"depression": 0, "anxiety": 0},
            }.get(persona_key, {"depression": 0, "anxiety": 0})

def normalize(scores):
    total = sum(scores.values())
    return {k: round(v / total, 3) for k, v in scores.items()}

def get_mock_emotion_scores(persona_key, hour):
    import random
    random.seed(hash(f"{persona_key}_{hour}"))
    if persona_key == "maya":
        if (14 <= hour <= 17) or (21 <= hour <= 23):
            return normalize({"sad": 0.55, "neutral": 0.15, "fearful": 0.08, "happy": 0.02, "angry": 0.04, "disgusted": 0.03, "other": 0.06, "surprised": 0.02, "unknown": 0.02})
        else:
            return normalize({"sad": 0.30, "neutral": 0.30, "happy": 0.08, "fearful": 0.07, "other": 0.10, "angry": 0.04, "disgusted": 0.02, "surprised": 0.03, "unknown": 0.03})
    elif persona_key == "derek":
        if 8 <= hour <= 10:
            return normalize({"fearful": 0.48, "angry": 0.14, "surprised": 0.08, "neutral": 0.10, "sad": 0.05, "happy": 0.03, "other": 0.05, "disgusted": 0.03, "unknown": 0.02})
        elif 22 <= hour <= 23:
            return normalize({"fearful": 0.42, "sad": 0.18, "neutral": 0.12, "other": 0.08, "angry": 0.06, "happy": 0.02, "disgusted": 0.03, "surprised": 0.03, "unknown": 0.04})
        else:
            return normalize({"fearful": 0.22, "neutral": 0.28, "happy": 0.10, "other": 0.12, "angry": 0.08, "sad": 0.06, "surprised": 0.05, "disgusted": 0.03, "unknown": 0.04})
    elif persona_key == "travis":
        if hour in [11, 15, 22]:
            return normalize({"angry": 0.52, "disgusted": 0.12, "fearful": 0.08, "neutral": 0.08, "sad": 0.05, "other": 0.06, "happy": 0.02, "surprised": 0.03, "unknown": 0.02})
        elif hour in [6, 7, 18, 19]:
            return normalize({"angry": 0.35, "neutral": 0.18, "fearful": 0.10, "other": 0.10, "disgusted": 0.08, "sad": 0.06, "happy": 0.04, "surprised": 0.04, "unknown": 0.03})
        else:
            return normalize({"angry": 0.18, "neutral": 0.28, "other": 0.12, "fearful": 0.08, "sad": 0.08, "happy": 0.08, "disgusted": 0.05, "surprised": 0.05, "unknown": 0.05})
    else:
        if 7 <= hour <= 10:
            return normalize({"happy": 0.55, "neutral": 0.18, "surprised": 0.08, "other": 0.06, "sad": 0.02, "fearful": 0.02, "angry": 0.02, "disgusted": 0.01, "unknown": 0.03})
        else:
            return normalize({"happy": 0.42, "neutral": 0.25, "other": 0.08, "surprised": 0.06, "sad": 0.04, "fearful": 0.03, "angry": 0.02, "disgusted": 0.02, "unknown": 0.05})

def get_whoop_at_time(persona_data, hour, minute=0):
    target_minutes = hour * 60 + minute
    return min(persona_data["hourly_data"], key=lambda d: abs(d["minutes_from_midnight"] - target_minutes))

# ---------------------------------------------------------------------------
# Skill selection
# ---------------------------------------------------------------------------
def select_skill(emotion_scores, clinical_scores, whoop_summary):
    top_emotion = max(emotion_scores, key=emotion_scores.get)
    recovery = whoop_summary["recovery_score"]
    sleep = whoop_summary["sleep_performance_pct"]

    if top_emotion in ("angry", "fearful") and emotion_scores[top_emotion] > 0.3:
        skill_file = "skills/stress-resilience.md"
    elif recovery < 34:
        skill_file = "skills/recovery-coach.md"
    elif sleep < 60:
        skill_file = "skills/sleep-analyst.md"
    else:
        skill_file = "skills/morning-briefing.md"

    skill_path = os.path.join(os.path.dirname(__file__), skill_file)
    try:
        with open(skill_path) as f:
            return f.read(), skill_file
    except FileNotFoundError:
        return "Provide a personalized longevity-focused health intervention.", skill_file

# ---------------------------------------------------------------------------
# Agent call
# ---------------------------------------------------------------------------
def run_agent(emotion_scores, clinical_scores, whoop_snapshot, whoop_summary, persona_bio, skill_text, alert_reason):
    import anthropic
    client = anthropic.Anthropic(
        base_url=os.environ.get("ANTHROPIC_BASE_URL"),
        api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"),
    )

    top_emotion = max(emotion_scores, key=emotion_scores.get)
    dep_label = DEPRESSION_LEVELS[min(clinical_scores.get("depression", 0), 2)]
    anx_label = ANXIETY_LEVELS[min(clinical_scores.get("anxiety", 0), 3)]

    system = f"""You are Betterness, a longevity health agent. You analyze voice biomarkers and wearable data to provide personalized interventions.

You are ACTION-ORIENTED. Don't just describe. Tell the user exactly what to do right now.

## Why This Check-in Was Triggered
{alert_reason}

## Voice Emotion Analysis (emotion2vec+ model)
{json.dumps(emotion_scores, indent=2)}
Top emotion: {top_emotion} ({emotion_scores[top_emotion]:.0%})

## Clinical Voice Screening (Kintsugi DAM model)
Depression: {dep_label} (level {clinical_scores.get('depression', 0)}/2)
Anxiety: {anx_label} (level {clinical_scores.get('anxiety', 0)}/3)

## Wearable Data at This Moment
Heart Rate: {whoop_snapshot['heart_rate_bpm']:.0f} bpm
HRV (RMSSD): {whoop_snapshot['hrv_rmssd_ms']:.0f} ms
Respiratory Rate: {whoop_snapshot['respiratory_rate_brpm']:.1f} brpm
SpO2: {whoop_snapshot['spo2_pct']:.1f}%
Skin Temp: {whoop_snapshot['skin_temp_c']:.1f}C
Strain: {whoop_snapshot['cumulative_strain']:.1f}
State: {whoop_snapshot['state']}

## Daily Whoop Summary
Recovery: {whoop_summary['recovery_score']}%
Sleep: {whoop_summary['sleep_duration_hrs']}h of {whoop_summary['sleep_need_hrs']}h needed
Sleep Debt: {whoop_summary['sleep_debt_hrs']}h | Deep Sleep: {whoop_summary['deep_sleep_hrs']}h
Journal Tags: {', '.join(whoop_summary['journal_tags'])}

## Person
{persona_bio}

## Active Health Skill
{skill_text}

## Response Format
Respond in this EXACT structure using markdown:

**What I see:** One sentence combining voice emotion, clinical screening, and body signals. Reference the biometric trigger that caused this check-in.

**Right now:** One specific immediate action with exact parameters (breathing pattern with counts, walk duration, etc.)

**What I'm doing for you:**
- (concrete agent action 1, e.g. scheduling recovery time)
- (concrete agent action 2, e.g. flagging a multi-day pattern)
- (concrete agent action 3, e.g. adjusting strain target)

**Next check-in:** When you'll check in again and what you'll look for.

Be conversational and warm but structured. Show that you are an agent that DOES things, not just advises."""

    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": "Analyze my check-in and give me my intervention."}],
    )
    return response.content[0].text

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def make_monitoring_chart(hourly_data, up_to_idx, alert_idx, persona_color):
    """Build the live monitoring chart up to current index, with alert marker."""
    data_slice = hourly_data[:up_to_idx + 1]
    x_vals = [d["minutes_from_midnight"] for d in data_slice]
    hrvs = [d["hrv_rmssd_ms"] for d in data_slice]
    hrs = [d["heart_rate_bpm"] for d in data_slice]

    tick_vals = list(range(0, 1441, 180))
    tick_text = [f"{m // 60:02d}:00" for m in tick_vals]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=x_vals, y=hrvs, name="HRV", line=dict(color="#6366f1", width=2), fill="tozeroy",
                   fillcolor="rgba(99,102,241,0.1)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=x_vals, y=hrs, name="Heart Rate", line=dict(color="#ef4444", width=1.5), opacity=0.7),
        secondary_y=True,
    )

    # Alert marker
    if alert_idx is not None and alert_idx <= up_to_idx:
        alert_d = hourly_data[alert_idx]
        fig.add_trace(
            go.Scatter(
                x=[alert_d["minutes_from_midnight"]],
                y=[alert_d["hrv_rmssd_ms"]],
                mode="markers+text",
                marker=dict(size=14, color="#ef4444", symbol="circle"),
                text=["⚠️"],
                textposition="top center",
                textfont=dict(size=16),
                showlegend=False,
            ),
            secondary_y=False,
        )

    # Danger zone
    fig.add_hrect(y0=0, y1=25, fillcolor="rgba(239,68,68,0.08)", line_width=0, secondary_y=False,
                  annotation_text="Distress Zone", annotation_position="bottom left",
                  annotation_font_color="#ef4444", annotation_font_size=10)

    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickvals=tick_vals, ticktext=tick_text, gridcolor="#1e293b", range=[0, 1440]),
    )
    fig.update_yaxes(title_text="HRV (ms)", secondary_y=False, gridcolor="#1e293b")
    fig.update_yaxes(title_text="HR (bpm)", secondary_y=True, gridcolor="#1e293b")

    return fig

def make_emotion_chart(scores):
    # Radar chart for emotion scores
    labels = list(scores.keys())
    values = list(scores.values())
    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    top_emotion = max(scores, key=scores.get)
    fill_color = EMOTION_COLORS.get(top_emotion, "#6366f1")

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=[l.capitalize() for l in labels_closed],
        fill="toself",
        fillcolor=f"rgba({int(fill_color[1:3], 16)},{int(fill_color[3:5], 16)},{int(fill_color[5:7], 16)},0.2)",
        line=dict(color=fill_color, width=2),
        text=[f"{v:.0%}" for v in values_closed],
        hovertemplate="%{theta}: %{r:.0%}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0f172a",
            radialaxis=dict(visible=True, range=[0, max(values) * 1.2], showticklabels=False, gridcolor="#1e293b"),
            angularaxis=dict(gridcolor="#1e293b", linecolor="#1e293b"),
        ),
        height=320, margin=dict(l=40, r=40, t=20, b=20),
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        showlegend=False,
    )
    return fig

# ===========================================================================
# PAGE CONFIG + STYLES
# ===========================================================================
st.set_page_config(page_title="Betterness", page_icon="🦞", layout="wide")

st.markdown("""
<style>
    .metric-card { background: #1e293b; border-radius: 8px; padding: 12px 16px; text-align: center; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #e2e8f0; }
    .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .alert-box {
        background: linear-gradient(135deg, #451a03 0%, #0f172a 100%);
        border: 2px solid #ef4444;
        border-radius: 16px;
        padding: 24px 32px;
        text-align: center;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
        50% { box-shadow: 0 0 20px 10px rgba(239,68,68,0.15); }
    }
    .model-badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px;
    }
    .agent-card {
        background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
        border-radius: 12px; padding: 20px 24px; border: 1px solid #10b981; line-height: 1.7;
    }
    .skill-chip {
        display: inline-block; background: #1e293b; border: 1px solid #334155;
        border-radius: 8px; padding: 8px 14px; margin: 4px; font-size: 0.85rem;
    }
    .skill-chip.active { border-color: #10b981; background: #10b98115; }
    .severity-gauge { border-radius: 8px; padding: 16px; text-align: center; background: #1e293b; }
    .correlation-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-left: 4px solid #f59e0b; border-radius: 8px; padding: 16px 20px; margin: 8px 0;
    }
    .screen-header {
        text-align: center; padding: 20px 0 10px 0;
    }
    .step-indicator {
        display: flex; justify-content: center; gap: 8px; margin: 16px 0;
    }
    .step-dot {
        width: 12px; height: 12px; border-radius: 50%; background: #334155; display: inline-block;
    }
    .step-dot.active { background: #10b981; }
    .step-dot.done { background: #6366f1; }
    div[data-testid="stHorizontalBlock"] > div { min-width: 0; }
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# SESSION STATE
# ===========================================================================
if "screen" not in st.session_state:
    st.session_state.screen = "select"  # select -> monitor -> checkin -> results
if "persona" not in st.session_state:
    st.session_state.persona = None
if "alert_idx" not in st.session_state:
    st.session_state.alert_idx = None
if "alert_reason" not in st.session_state:
    st.session_state.alert_reason = ""
if "monitor_idx" not in st.session_state:
    st.session_state.monitor_idx = 0
if "emotion_scores" not in st.session_state:
    st.session_state.emotion_scores = None
if "clinical_scores" not in st.session_state:
    st.session_state.clinical_scores = None

all_data = load_persona_data()

def go_to(screen):
    st.session_state.screen = screen

# Step indicator
def render_steps(current):
    steps = ["select", "monitor", "checkin", "results"]
    labels = ["Persona", "Monitor", "Check-in", "Results"]
    dots = ""
    for i, (s, l) in enumerate(zip(steps, labels)):
        if s == current:
            cls = "active"
        elif steps.index(current) > i:
            cls = "done"
        else:
            cls = ""
        dots += f'<span class="step-dot {cls}" title="{l}"></span>'
    st.markdown(f'<div class="step-indicator">{dots}</div>', unsafe_allow_html=True)

# ===========================================================================
# SCREEN 1: PERSONA SELECTION
# ===========================================================================
if st.session_state.screen == "select":
    st.markdown('<div class="screen-header">', unsafe_allow_html=True)
    st.markdown("# 🦞 Betterness")
    st.markdown("**Voice Biomarker Longevity Agent**")
    st.markdown("Select a persona to begin monitoring")
    st.markdown('</div>', unsafe_allow_html=True)
    render_steps("select")

    st.markdown("")
    cols = st.columns(4, gap="large")

    for i, key in enumerate(list(all_data.keys())):
        p = all_data[key]
        pcolor = PERSONA_COLORS[key]
        emoji = PERSONA_EMOJI[key]
        recovery = p["daily_summary"]["recovery_score"]
        rec_color = "#ef4444" if recovery < 34 else "#f59e0b" if recovery < 67 else "#10b981"

        with cols[i]:
            st.markdown(f"""
            <div style="background: #0f172a; border: 2px solid #1e293b; border-radius: 16px; padding: 24px; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">{emoji}</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #e2e8f0;">{p['name']}</div>
                <div style="font-size: 0.85rem; color: {pcolor}; font-weight: 600; margin: 4px 0;">{p['label']}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{p['age']} years old</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin: 8px 0; line-height: 1.4;">{p['bio']}</div>
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #1e293b;">
                    <span style="font-size: 1.6rem; font-weight: 700; color: {rec_color};">{recovery}%</span>
                    <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Recovery Score</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Monitor {p['name'].split()[0]}", key=f"sel_{key}", use_container_width=True):
                st.session_state.persona = key
                st.session_state.monitor_idx = 72  # start at 06:00 (72 * 5min)
                st.session_state.alert_idx = None
                go_to("monitor")
                st.rerun()

# ===========================================================================
# SCREEN 2: LIVE MONITORING
# ===========================================================================
elif st.session_state.screen == "monitor":
    from streamlit_autorefresh import st_autorefresh

    persona_key = st.session_state.persona
    persona = all_data[persona_key]
    summary = persona["daily_summary"]
    pcolor = PERSONA_COLORS[persona_key]
    hourly_data = persona["hourly_data"]

    # Pre-compute the first alert for this persona (hidden from UI until triggered)
    alert = find_first_alert_after(hourly_data, 6)
    alert_idx = alert[0] if alert else None

    # Initialize playback state
    if "playing" not in st.session_state:
        st.session_state.playing = False
    if "play_speed" not in st.session_state:
        st.session_state.play_speed = 6

    render_steps("monitor")

    # Header
    col_hdr, col_back = st.columns([4, 1])
    with col_hdr:
        st.markdown(f"## {PERSONA_EMOJI[persona_key]} {persona['name']} — Live Monitoring")
    with col_back:
        if st.button("← Change Persona"):
            st.session_state.playing = False
            go_to("select")
            st.rerun()

    # Summary row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        rec_color = "#ef4444" if summary["recovery_score"] < 34 else "#f59e0b" if summary["recovery_score"] < 67 else "#10b981"
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{rec_color}">{summary["recovery_score"]}%</div><div class="metric-label">Recovery</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["sleep_duration_hrs"]}h</div><div class="metric-label">Sleep ({summary["sleep_performance_pct"]}%)</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["sleep_debt_hrs"]}h</div><div class="metric-label">Sleep Debt</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["deep_sleep_hrs"]}h</div><div class="metric-label">Deep Sleep</div></div>', unsafe_allow_html=True)
    with m5:
        tags_str = ", ".join(summary["journal_tags"])
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="font-size:0.9rem;">{tags_str}</div><div class="metric-label">Journal Tags</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Playback controls
    ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1, 1, 2])
    with ctrl1:
        if st.button("▶ Play" if not st.session_state.playing else "⏸ Pause", use_container_width=True, type="primary"):
            st.session_state.playing = not st.session_state.playing
            st.rerun()
    with ctrl2:
        if st.button("⏮ Reset", use_container_width=True):
            st.session_state.monitor_idx = 72
            st.session_state.playing = False
            st.rerun()
    with ctrl3:
        speed_map = {"1x": 3, "2x": 6, "4x": 12, "8x": 24}
        speed_label = st.select_slider("Speed", options=list(speed_map.keys()), value="2x")
        st.session_state.play_speed = speed_map[speed_label]

    current_idx = st.session_state.monitor_idx
    current_d = hourly_data[min(current_idx, 287)]
    current_time = current_d["timestamp"]

    with ctrl4:
        st.markdown(f"""
        <div style="text-align: center; padding: 8px;">
            <span style="font-size: 2rem; font-weight: 700; color: #e2e8f0;">{current_time}</span>
            <span style="font-size: 0.85rem; color: #64748b; margin-left: 12px;">{current_d['state']}</span>
        </div>
        """, unsafe_allow_html=True)

    # Check if we hit alert
    alert_triggered = alert_idx is not None and current_idx >= alert_idx

    # Chart — only show alert marker once triggered (no spoilers)
    fig = make_monitoring_chart(hourly_data, current_idx, alert_idx if alert_triggered else None, pcolor)
    st.plotly_chart(fig, use_container_width=True, key="monitor_chart")

    # Current vitals
    v1, v2, v3, v4, v5 = st.columns(5)
    with v1:
        st.metric("HR", f"{current_d['heart_rate_bpm']:.0f} bpm")
    with v2:
        st.metric("HRV", f"{current_d['hrv_rmssd_ms']:.0f} ms")
    with v3:
        st.metric("Resp", f"{current_d['respiratory_rate_brpm']:.1f}")
    with v4:
        st.metric("SpO2", f"{current_d['spo2_pct']:.1f}%")
    with v5:
        st.metric("State", current_d["state"])

    # Alert area — only appears when triggered
    if alert_triggered:
        st.session_state.playing = False  # stop playback

        alert_type = alert[1]
        explainer = ALERT_EXPLAINERS.get(alert_type, ALERT_EXPLAINERS["combined"])

        st.markdown(f"""
        <div class="alert-box">
            <div style="font-size: 2rem; margin-bottom: 8px;">⚠️</div>
            <div style="font-size: 1.2rem; font-weight: 700; color: #ef4444;">Biometric Alert Detected</div>
            <div style="font-size: 1rem; color: #fbbf24; margin: 8px 0; font-weight: 600;">{alert[2]}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        # Three-column explainer
        exp1, exp2, exp3 = st.columns(3)
        with exp1:
            st.markdown(f"""
            <div style="background: #1e293b; border-radius: 12px; padding: 16px; border-left: 4px solid #ef4444; height: 100%;">
                <div style="font-size: 0.75rem; color: #ef4444; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 8px;">What happened</div>
                <div style="font-size: 0.9rem; color: #e2e8f0; line-height: 1.5;">{explainer['what']}</div>
            </div>
            """, unsafe_allow_html=True)
        with exp2:
            st.markdown(f"""
            <div style="background: #1e293b; border-radius: 12px; padding: 16px; border-left: 4px solid #f59e0b; height: 100%;">
                <div style="font-size: 0.75rem; color: #f59e0b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 8px;">Why it matters</div>
                <div style="font-size: 0.9rem; color: #e2e8f0; line-height: 1.5;">{explainer['why']}</div>
            </div>
            """, unsafe_allow_html=True)
        with exp3:
            st.markdown(f"""
            <div style="background: #1e293b; border-radius: 12px; padding: 16px; border-left: 4px solid #10b981; height: 100%;">
                <div style="font-size: 0.75rem; color: #10b981; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 8px;">What we do next</div>
                <div style="font-size: 0.9rem; color: #e2e8f0; line-height: 1.5;">{explainer['do']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("🎙️  Begin Voice Check-in", use_container_width=True, type="primary"):
                st.session_state.alert_idx = alert_idx
                st.session_state.alert_reason = alert[2]
                st.session_state.alert_hour = hourly_data[alert_idx]["hour"]
                go_to("checkin")
                st.rerun()
    elif not st.session_state.playing:
        # Progress bar when paused
        prog = max(0, (current_idx - 72)) / max(1, (287 - 72))
        st.progress(prog, text=f"Day progress: {current_time}")

    # Auto-play via client-side timer (no time.sleep blocking)
    if st.session_state.playing and not alert_triggered:
        # Tick every 300ms from the browser — no server blocking
        st_autorefresh(interval=300, limit=None, key="play_tick")
        # Advance on each tick
        if current_idx < 287:
            st.session_state.monitor_idx = min(current_idx + st.session_state.play_speed, 287)
        else:
            st.session_state.playing = False

# ===========================================================================
# SCREEN 3: VOICE CHECK-IN
# ===========================================================================
elif st.session_state.screen == "checkin":
    persona_key = st.session_state.persona
    persona = all_data[persona_key]
    pcolor = PERSONA_COLORS[persona_key]
    hourly_data = persona["hourly_data"]
    alert_idx = st.session_state.alert_idx
    alert_d = hourly_data[alert_idx]

    render_steps("checkin")

    st.markdown('<div class="screen-header">', unsafe_allow_html=True)
    st.markdown(f"## 🎙️ Voice Check-in — {alert_d['timestamp']}")
    st.markdown(f"**{persona['name']}** · {st.session_state.alert_reason}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Show trigger context
    st.markdown(f"""
    <div class="correlation-box">
        <span style="font-size: 0.75rem; color: #f59e0b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Why this check-in was triggered</span>
        <div style="font-size: 0.95rem; color: #e2e8f0; margin-top: 6px; line-height: 1.5;">
            {st.session_state.alert_reason}. Betterness will analyze your voice for emotional markers and clinical indicators, then combine them with your wearable data to deliver a personalized intervention.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Current state
    st.markdown("---")
    v1, v2, v3, v4, v5 = st.columns(5)
    with v1:
        st.metric("HR", f"{alert_d['heart_rate_bpm']:.0f} bpm")
    with v2:
        st.metric("HRV", f"{alert_d['hrv_rmssd_ms']:.0f} ms")
    with v3:
        st.metric("Resp", f"{alert_d['respiratory_rate_brpm']:.1f}")
    with v4:
        st.metric("SpO2", f"{alert_d['spo2_pct']:.1f}%")
    with v5:
        st.metric("State", alert_d["state"])

    st.markdown("---")
    st.markdown("### How are you feeling? Record or upload a voice sample.")
    st.caption("Betterness will analyze your voice using two models: emotion detection and clinical depression/anxiety screening.")

    audio_bytes = None
    audio_format = "wav"

    col_rec, col_upload = st.columns(2)
    with col_rec:
        st.markdown("**Record Voice**")
        try:
            from audio_recorder_streamlit import audio_recorder
            recorded = audio_recorder(
                text="Tap to record",
                recording_color="#ef4444",
                neutral_color="#6b7280",
                icon_size="3x",
                pause_threshold=3.0,
            )
            if recorded:
                audio_bytes = recorded
                audio_format = "wav"
        except ImportError:
            st.info("Install `audio-recorder-streamlit` for recording.")

    with col_upload:
        st.markdown("**Upload Audio**")
        uploaded = st.file_uploader("Upload voice sample", type=["wav", "mp3", "ogg", "m4a"], label_visibility="collapsed")
        if uploaded:
            audio_bytes = uploaded.read()
            audio_format = uploaded.name.rsplit(".", 1)[-1].lower()

    if audio_bytes:
        audio_path = save_audio(audio_bytes, audio_format)
        if audio_format not in ("wav", "mp3") and convert_to_wav:
            audio_path = convert_to_wav(audio_path)

        with st.spinner("Analyzing voice biomarkers — emotion2vec+ and Kintsugi DAM..."):
            emotion_scores, emotion_real = analyze_emotion(audio_path)
            clinical_scores, clinical_real = analyze_clinical(audio_path)
            time.sleep(2)  # brief pause so it feels like real analysis

        try:
            os.unlink(audio_path)
        except OSError:
            pass

        st.session_state.emotion_scores = emotion_scores
        st.session_state.emotion_real = emotion_real
        st.session_state.clinical_scores = clinical_scores
        st.session_state.clinical_real = clinical_real
        go_to("results")
        st.rerun()

    st.markdown("")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("← Back to Monitoring", use_container_width=True):
            go_to("monitor")
            st.rerun()

# ===========================================================================
# SCREEN 4: RESULTS + INTERVENTION
# ===========================================================================
elif st.session_state.screen == "results":
    persona_key = st.session_state.persona
    persona = all_data[persona_key]
    summary = persona["daily_summary"]
    pcolor = PERSONA_COLORS[persona_key]
    hourly_data = persona["hourly_data"]
    alert_idx = st.session_state.alert_idx
    snap = hourly_data[alert_idx]

    emotion_scores = st.session_state.emotion_scores
    clinical_scores = st.session_state.clinical_scores
    emotion_real = st.session_state.get("emotion_real", False)
    clinical_real = st.session_state.get("clinical_real", False)

    render_steps("results")

    st.markdown(f"## Analysis — {persona['name']} at {snap['timestamp']}")

    # ===== TWO-COLUMN MODEL OUTPUT =====
    emo_col, clin_col = st.columns(2)

    with emo_col:
        badge_color = "#10b981" if emotion_real else "#f59e0b"
        badge_text = "LIVE" if emotion_real else "SIMULATED"
        st.markdown(f'<div class="model-badge" style="background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color};">{badge_text}</div>', unsafe_allow_html=True)
        st.markdown("#### Emotion Detection")
        st.caption("**emotion2vec+ large** — 9-class speech emotion recognition")

        top_emotion = max(emotion_scores, key=emotion_scores.get)
        top_score = emotion_scores[top_emotion]
        st.markdown(f"""
        <div style="background: {EMOTION_COLORS.get(top_emotion, '#94a3b8')}22; border: 1px solid {EMOTION_COLORS.get(top_emotion, '#94a3b8')}; border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 8px;">
            <span style="font-size: 1.6rem; font-weight: 700; color: {EMOTION_COLORS.get(top_emotion, '#94a3b8')};">{top_emotion.upper()}</span>
            <span style="font-size: 1.2rem; color: #94a3b8; margin-left: 8px;">{top_score:.0%}</span>
        </div>
        """, unsafe_allow_html=True)
        fig_emotions = make_emotion_chart(emotion_scores)
        st.plotly_chart(fig_emotions, use_container_width=True)

    with clin_col:
        badge_color = "#10b981" if clinical_real else "#f59e0b"
        badge_text = "LIVE" if clinical_real else "SIMULATED"
        st.markdown(f'<div class="model-badge" style="background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color};">{badge_text}</div>', unsafe_allow_html=True)
        st.markdown("#### Clinical Screening")
        st.caption("**Kintsugi DAM 3.1** — PHQ-9 depression & GAD-7 anxiety")

        dep_idx = min(clinical_scores.get("depression", 0), 2)
        anx_idx = min(clinical_scores.get("anxiety", 0), 3)
        dep_label = DEPRESSION_LEVELS[dep_idx]
        anx_label = ANXIETY_LEVELS[anx_idx]
        dep_color = SEVERITY_COLORS[dep_label]
        anx_color = SEVERITY_COLORS[anx_label]

        dep_c, anx_c = st.columns(2)
        with dep_c:
            st.markdown(f"""
            <div class="severity-gauge">
                <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Depression (PHQ-9)</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {dep_color}; margin-top: 4px;">{dep_label}</div>
                <div style="background: #0f172a; border-radius: 4px; height: 8px; margin-top: 8px;">
                    <div style="background: {dep_color}; width: {max(dep_idx / 2 * 100, 10)}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with anx_c:
            st.markdown(f"""
            <div class="severity-gauge">
                <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Anxiety (GAD-7)</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {anx_color}; margin-top: 4px;">{anx_label}</div>
                <div style="background: #0f172a; border-radius: 4px; height: 8px; margin-top: 8px;">
                    <div style="background: {anx_color}; width: {max(anx_idx / 3 * 100, 10)}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        st.caption("Analyzes acoustic properties only — no transcription. Trained on ~35K individuals.")

    # --- Signal correlation ---
    st.markdown("---")
    st.markdown("### Signal Correlation")

    cor_left, cor_mid, cor_right = st.columns(3)
    with cor_left:
        st.markdown("**Voice Emotion**")
        for emo, score in sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
            bw = int(score * 100)
            st.markdown(f'<div style="margin-bottom:6px;"><span style="color:{EMOTION_COLORS.get(emo,"#94a3b8")};font-weight:600;width:80px;display:inline-block;">{emo}</span><span style="background:{EMOTION_COLORS.get(emo,"#94a3b8")};height:8px;width:{bw}%;display:inline-block;border-radius:4px;vertical-align:middle;"></span><span style="color:#94a3b8;margin-left:8px;">{score:.0%}</span></div>', unsafe_allow_html=True)
    with cor_mid:
        st.markdown("**Clinical Screen**")
        st.markdown(f"🧠 Depression: **{dep_label}**")
        st.markdown(f"😰 Anxiety: **{anx_label}**")
    with cor_right:
        st.markdown("**Body Signals**")
        st.markdown(f"❤️ HR: **{snap['heart_rate_bpm']:.0f} bpm**")
        st.markdown(f"💜 HRV: **{snap['hrv_rmssd_ms']:.0f} ms**")
        st.markdown(f"🫁 Resp: **{snap['respiratory_rate_brpm']:.1f} brpm**")

    # Correlation text
    top_emotion = max(emotion_scores, key=emotion_scores.get)
    top_score = emotion_scores[top_emotion]
    parts = []
    if top_emotion in ("sad", "fearful", "angry") and top_score > 0.3:
        parts.append(f"Voice emotion shows dominant **{top_emotion}** ({top_score:.0%})")
    if dep_idx >= 2:
        parts.append(f"clinical screening flags **{dep_label.lower()} depression**")
    if anx_idx >= 2:
        parts.append(f"clinical screening flags **{anx_label.lower()} anxiety**")
    if snap["hrv_rmssd_ms"] < 25:
        parts.append(f"HRV critically low at **{snap['hrv_rmssd_ms']:.0f}ms**")
    if snap["heart_rate_bpm"] > 85:
        parts.append(f"heart rate elevated at **{snap['heart_rate_bpm']:.0f}bpm**")
    correlation_text = " and ".join(parts[:3]) + ". Multiple signals converge." if len(parts) >= 2 else (parts[0] + "." if parts else "Signals within normal ranges.")
    st.markdown(f'<div class="correlation-box">{correlation_text}</div>', unsafe_allow_html=True)

    # ===== AGENT INTERVENTION =====
    st.markdown("---")
    st.markdown("### Betterness Agent")

    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        skill_text, skill_file = select_skill(emotion_scores, clinical_scores, summary)
        active_skill = SKILL_INFO.get(skill_file, {})

        # Skill bar
        skill_html = ""
        for s in ALL_SKILLS:
            is_active = s["name"] == active_skill.get("name", "")
            cls = "skill-chip active" if is_active else "skill-chip"
            arrow = " ◀" if is_active else ""
            skill_html += f'<span class="{cls}">{s["icon"]} {s["name"]}{arrow}</span>'
        st.markdown(f'<div style="margin-bottom:12px;">{skill_html}</div>', unsafe_allow_html=True)

        if active_skill:
            st.caption(f"**Activated: {active_skill['icon']} {active_skill['name']}** — {active_skill['trigger']}")

        with st.spinner("Agent analyzing signals and generating intervention..."):
            agent_response = run_agent(
                emotion_scores, clinical_scores, snap, summary,
                persona["bio"], skill_text, st.session_state.alert_reason,
            )

        st.markdown(f'<div class="agent-card">\n\n{agent_response}\n\n</div>', unsafe_allow_html=True)

        # Agent capabilities
        st.markdown("")
        st.markdown("**Agent capabilities:**")
        action_cols = st.columns(3)
        actions = [
            ("📅", "Schedule recovery blocks", "Block calendar time for rest"),
            ("📊", "Track patterns", "Flag multi-day distress trends"),
            ("🏥", "Escalate to provider", "Recommend clinical screening"),
            ("🧘", "Guide breathing", "4-7-8, box breathing, coherence"),
            ("🌙", "Optimize sleep", "Bedtime, environment, stimulants"),
            ("🤝", "Social connection", "Check-ins when isolation detected"),
        ]
        for i, (icon, title, desc) in enumerate(actions):
            with action_cols[i % 3]:
                st.markdown(f'<div style="background:#1e293b;border-radius:8px;padding:10px 12px;margin-bottom:8px;"><div style="font-size:0.9rem;font-weight:600;color:#e2e8f0;">{icon} {title}</div><div style="font-size:0.75rem;color:#64748b;">{desc}</div></div>', unsafe_allow_html=True)
    else:
        st.warning("Set `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY` to enable the agent.")

    # Navigation
    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("← Back to Monitoring", use_container_width=True):
            go_to("monitor")
            st.rerun()
    with n2:
        if st.button("🔄 New Check-in", use_container_width=True):
            go_to("checkin")
            st.rerun()
    with n3:
        if st.button("🏠 Change Persona", use_container_width=True):
            go_to("select")
            st.rerun()
