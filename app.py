import streamlit as st
import json
import os
import time
import random

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMOTION_LABELS = ["angry", "disgusted", "fearful", "happy", "neutral", "other", "sad", "surprised", "unknown"]

EMOTION_COLORS = {
    "angry": "#ef4444", "disgusted": "#a855f7", "fearful": "#f59e0b", "happy": "#10b981",
    "neutral": "#6b7280", "other": "#94a3b8", "sad": "#3b82f6", "surprised": "#ec4899", "unknown": "#475569",
}

PERSONA_COLORS = {"maya": "#6366f1", "derek": "#f59e0b", "travis": "#ef4444", "lucia": "#10b981"}

DEPRESSION_LEVELS = ["No Depression", "Mild-Moderate", "Severe"]
ANXIETY_LEVELS = ["No Anxiety", "Mild", "Moderate", "Severe"]
SEVERITY_COLORS = {
    "No Depression": "#10b981", "Mild-Moderate": "#f59e0b", "Severe": "#ef4444",
    "No Anxiety": "#10b981", "Mild": "#6366f1", "Moderate": "#f59e0b", "Severe": "#ef4444",
}

MEETING_COLORS = {
    "standup": "#6366f1",
    "review": "#f59e0b",
    "1on1": "#ec4899",
    "planning": "#8b5cf6",
    "external": "#ef4444",
    "sync": "#06b6d4",
    "workshop": "#10b981",
    "allhands": "#f97316",
}

# ---------------------------------------------------------------------------
# Employee profiles (replaces personas)
# ---------------------------------------------------------------------------
EMPLOYEES = {
    "maya": {
        "name": "Maya Chen",
        "role": "Senior Software Engineer",
        "team": "Platform Engineering",
        "age": 34,
        "bio": "Remote since 2020. Carries heavy meeting load — 6-7 meetings/day. Tends to internalize stress. HRV shows chronic low recovery.",
        "label": "High Meeting Load",
        "emoji": "💜",
        "meetings": [
            {"title": "Team Standup", "start": "08:00", "end": "08:30", "type": "standup", "participants": ["Alex", "Jordan", "Sam", "PM"]},
            {"title": "Architecture Review", "start": "09:30", "end": "11:00", "type": "review", "participants": ["VP Eng", "Tech Lead", "Platform Team"]},
            {"title": "1:1 with Manager", "start": "11:30", "end": "12:00", "type": "1on1", "participants": ["Engineering Manager"]},
            {"title": "Sprint Planning", "start": "13:00", "end": "14:30", "type": "planning", "participants": ["Full Platform Team"]},
            {"title": "Client Integration Call", "start": "15:00", "end": "16:00", "type": "external", "participants": ["Client CTO", "Solutions Eng", "Account Mgr"]},
            {"title": "Eng Sync", "start": "16:30", "end": "17:00", "type": "sync", "participants": ["Backend Team"]},
        ],
    },
    "derek": {
        "name": "Derek Okafor",
        "role": "Product Manager",
        "team": "Growth",
        "age": 41,
        "bio": "Startup PM. Back-to-back meetings, constant context switching. Anxiety peaks during stakeholder presentations and deadlines.",
        "label": "Context Switching",
        "emoji": "🧡",
        "meetings": [
            {"title": "Leadership Standup", "start": "08:00", "end": "08:30", "type": "standup", "participants": ["CEO", "CTO", "Head of Design"]},
            {"title": "Stakeholder Review", "start": "09:00", "end": "10:30", "type": "review", "participants": ["Board Advisor", "VP Sales", "CEO"]},
            {"title": "Design Critique", "start": "11:00", "end": "12:00", "type": "workshop", "participants": ["Design Team", "UX Research"]},
            {"title": "1:1 with CEO", "start": "13:00", "end": "13:30", "type": "1on1", "participants": ["CEO"]},
            {"title": "Customer Discovery", "start": "14:00", "end": "15:00", "type": "external", "participants": ["Enterprise Prospect", "Sales Rep"]},
            {"title": "Sprint Retro", "start": "15:30", "end": "16:30", "type": "planning", "participants": ["Eng Team", "Design"]},
            {"title": "Metrics Review", "start": "17:00", "end": "17:30", "type": "sync", "participants": ["Data Analyst", "Growth Lead"]},
        ],
    },
    "travis": {
        "name": "Travis Kim",
        "role": "Engineering Manager",
        "team": "Infrastructure",
        "age": 29,
        "bio": "New manager, still adjusting. Frustration builds during cross-team conflicts and unclear requirements. Skips breaks to attend more meetings.",
        "label": "New Manager Stress",
        "emoji": "❤️",
        "meetings": [
            {"title": "Eng Leads Sync", "start": "08:30", "end": "09:00", "type": "sync", "participants": ["Other Eng Managers", "VP Eng"]},
            {"title": "Incident Postmortem", "start": "09:30", "end": "10:30", "type": "review", "participants": ["SRE Team", "On-call Eng", "VP Eng"]},
            {"title": "1:1 with Report", "start": "11:00", "end": "11:30", "type": "1on1", "participants": ["Junior Engineer"]},
            {"title": "1:1 with Report", "start": "11:30", "end": "12:00", "type": "1on1", "participants": ["Senior Engineer"]},
            {"title": "Cross-team Alignment", "start": "13:30", "end": "14:30", "type": "planning", "participants": ["Product", "Design", "QA", "Infra"]},
            {"title": "Hiring Debrief", "start": "15:00", "end": "15:30", "type": "review", "participants": ["Recruiter", "Interview Panel"]},
            {"title": "All-Hands", "start": "16:00", "end": "17:00", "type": "allhands", "participants": ["Entire Company"]},
        ],
    },
    "lucia": {
        "name": "Lucia Vargas",
        "role": "Head of Customer Success",
        "team": "Customer Success",
        "age": 52,
        "bio": "Experienced leader with strong emotional regulation. Takes walking breaks between meetings. Models healthy remote work habits.",
        "label": "Balanced Leader",
        "emoji": "💚",
        "meetings": [
            {"title": "CS Team Standup", "start": "09:00", "end": "09:30", "type": "standup", "participants": ["CS Team"]},
            {"title": "Escalation Review", "start": "10:00", "end": "10:30", "type": "review", "participants": ["Support Lead", "Account Mgr"]},
            {"title": "1:1 with Report", "start": "11:00", "end": "11:30", "type": "1on1", "participants": ["CS Manager"]},
            {"title": "Customer QBR", "start": "13:30", "end": "14:30", "type": "external", "participants": ["Enterprise Customer", "Account Exec"]},
            {"title": "Team Workshop", "start": "15:00", "end": "16:00", "type": "workshop", "participants": ["CS Team", "Product Mgr"]},
        ],
    },
}

# ---------------------------------------------------------------------------
# Mock emotion scores per meeting
# ---------------------------------------------------------------------------
def normalize(scores):
    total = sum(scores.values())
    return {k: round(v / total, 3) for k, v in scores.items()}

def get_meeting_emotions(employee_key, meeting_idx):
    """Generate persona-aware mock emotion scores for a specific meeting."""
    random.seed(hash(f"{employee_key}_{meeting_idx}_v2"))
    meetings = EMPLOYEES[employee_key]["meetings"]
    m = meetings[meeting_idx]
    mtype = m["type"]

    if employee_key == "maya":
        if mtype == "external":
            base = {"sad": 0.35, "fearful": 0.22, "neutral": 0.15, "angry": 0.08, "happy": 0.04, "disgusted": 0.03, "other": 0.06, "surprised": 0.03, "unknown": 0.02}
        elif mtype == "1on1":
            base = {"sad": 0.42, "neutral": 0.20, "fearful": 0.10, "happy": 0.06, "other": 0.08, "angry": 0.04, "disgusted": 0.02, "surprised": 0.03, "unknown": 0.03}
        elif mtype == "planning":
            base = {"neutral": 0.28, "sad": 0.25, "fearful": 0.12, "happy": 0.08, "other": 0.10, "angry": 0.06, "disgusted": 0.02, "surprised": 0.04, "unknown": 0.03}
        else:
            base = {"neutral": 0.30, "sad": 0.22, "happy": 0.12, "fearful": 0.08, "other": 0.10, "angry": 0.05, "disgusted": 0.03, "surprised": 0.05, "unknown": 0.03}
    elif employee_key == "derek":
        if mtype in ("review", "external"):
            base = {"fearful": 0.40, "angry": 0.15, "neutral": 0.12, "surprised": 0.08, "sad": 0.06, "happy": 0.04, "other": 0.06, "disgusted": 0.04, "unknown": 0.03}
        elif mtype == "1on1":
            base = {"fearful": 0.35, "neutral": 0.18, "sad": 0.12, "angry": 0.10, "other": 0.08, "happy": 0.04, "surprised": 0.04, "disgusted": 0.04, "unknown": 0.03}
        else:
            base = {"neutral": 0.25, "fearful": 0.22, "happy": 0.10, "other": 0.12, "angry": 0.08, "sad": 0.06, "surprised": 0.06, "disgusted": 0.04, "unknown": 0.05}
    elif employee_key == "travis":
        if mtype in ("review", "planning"):
            base = {"angry": 0.45, "disgusted": 0.12, "fearful": 0.10, "neutral": 0.10, "sad": 0.06, "other": 0.06, "happy": 0.03, "surprised": 0.04, "unknown": 0.02}
        elif mtype == "1on1":
            base = {"neutral": 0.28, "angry": 0.18, "happy": 0.14, "other": 0.10, "fearful": 0.08, "sad": 0.06, "disgusted": 0.04, "surprised": 0.06, "unknown": 0.04}
        else:
            base = {"angry": 0.25, "neutral": 0.22, "fearful": 0.12, "other": 0.10, "disgusted": 0.08, "sad": 0.06, "happy": 0.06, "surprised": 0.05, "unknown": 0.04}
    else:  # lucia
        if mtype == "external":
            base = {"happy": 0.38, "neutral": 0.25, "surprised": 0.08, "other": 0.08, "fearful": 0.05, "sad": 0.04, "angry": 0.03, "disgusted": 0.02, "unknown": 0.04}
        else:
            base = {"happy": 0.45, "neutral": 0.22, "surprised": 0.08, "other": 0.06, "sad": 0.04, "fearful": 0.04, "angry": 0.02, "disgusted": 0.02, "unknown": 0.04}

    # Add slight randomness
    for k in base:
        base[k] += random.uniform(-0.03, 0.03)
        base[k] = max(0.01, base[k])
    return normalize(base)

def get_meeting_clinical(employee_key, meeting_idx):
    """Mock clinical scores per meeting."""
    meetings = EMPLOYEES[employee_key]["meetings"]
    m = meetings[meeting_idx]
    mtype = m["type"]

    clinicals = {
        "maya": {"external": {"depression": 2, "anxiety": 2}, "1on1": {"depression": 2, "anxiety": 1}, "_default": {"depression": 1, "anxiety": 1}},
        "derek": {"review": {"depression": 0, "anxiety": 3}, "external": {"depression": 0, "anxiety": 2}, "1on1": {"depression": 0, "anxiety": 2}, "_default": {"depression": 0, "anxiety": 1}},
        "travis": {"review": {"depression": 1, "anxiety": 2}, "planning": {"depression": 1, "anxiety": 2}, "_default": {"depression": 0, "anxiety": 1}},
        "lucia": {"_default": {"depression": 0, "anxiety": 0}},
    }
    emp_clinicals = clinicals.get(employee_key, {"_default": {"depression": 0, "anxiety": 0}})
    return emp_clinicals.get(mtype, emp_clinicals["_default"])

# ---------------------------------------------------------------------------
# Weekly mock data
# ---------------------------------------------------------------------------
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def get_week_daily_scores(employee_key):
    """Generate 5 days of aggregated emotion scores for weekly view."""
    random.seed(hash(f"{employee_key}_week_v1"))
    days = []
    for day_idx, day_name in enumerate(WEEKDAYS):
        if employee_key == "maya":
            stress = 0.3 + day_idx * 0.08 + random.uniform(-0.05, 0.05)  # builds through week
            base_happy = max(0.05, 0.25 - day_idx * 0.04)
        elif employee_key == "derek":
            stress = 0.35 + (0.15 if day_idx in (1, 3) else 0) + random.uniform(-0.05, 0.05)
            base_happy = 0.12 + random.uniform(-0.03, 0.03)
        elif employee_key == "travis":
            stress = 0.25 + (0.2 if day_idx == 2 else 0.05 * day_idx) + random.uniform(-0.05, 0.05)
            base_happy = 0.1 + random.uniform(-0.03, 0.05)
        else:
            stress = 0.1 + random.uniform(-0.03, 0.05)
            base_happy = 0.45 + random.uniform(-0.05, 0.05)

        days.append({
            "day": day_name,
            "stress_level": min(1, max(0, stress)),
            "happy": min(1, max(0, base_happy)),
            "meeting_count": len(EMPLOYEES[employee_key]["meetings"]) + random.randint(-1, 1),
            "recovery": max(15, min(95, int(70 - stress * 60 + random.randint(-5, 5)))),
        })
    return days

# ---------------------------------------------------------------------------
# Data loading (biometric data)
# ---------------------------------------------------------------------------
@st.cache_data
def load_persona_data():
    with open(os.path.join(os.path.dirname(__file__), "persona_data.json")) as f:
        return json.load(f)

def time_to_minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)

# ---------------------------------------------------------------------------
# Agent call
# ---------------------------------------------------------------------------
def run_daily_agent(employee, meetings_with_emotions, whoop_summary, biometric_at_worst):
    """Generate end-of-day insights from all meetings."""
    import anthropic
    client = anthropic.Anthropic(
        base_url=os.environ.get("ANTHROPIC_BASE_URL"),
        api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"),
    )

    meeting_summaries = []
    for i, m in enumerate(meetings_with_emotions):
        top = max(m["emotions"], key=m["emotions"].get)
        dep_label = DEPRESSION_LEVELS[min(m["clinical"].get("depression", 0), 2)]
        anx_label = ANXIETY_LEVELS[min(m["clinical"].get("anxiety", 0), 3)]
        meeting_summaries.append(
            f"- {m['start']}-{m['end']} **{m['title']}** ({m['type']}): "
            f"Top emotion: {top} ({m['emotions'][top]:.0%}), Depression: {dep_label}, Anxiety: {anx_label}"
        )

    system = f"""You are Vemo, a workplace wellbeing AI agent. You analyze voice biomarkers from meeting recordings and wearable data to help remote workers manage their emotional health.

You are ACTION-ORIENTED. You provide specific, practical interventions — not generic wellness advice.

## Employee
{employee['name']}, {employee['role']} on {employee['team']} team
{employee['bio']}

## Today's Meetings (voice emotion analysis from recordings)
{chr(10).join(meeting_summaries)}

## Wearable Summary
Recovery: {whoop_summary['recovery_score']}%
Sleep: {whoop_summary['sleep_duration_hrs']}h of {whoop_summary['sleep_need_hrs']}h needed
Sleep Debt: {whoop_summary['sleep_debt_hrs']}h

## Biometric Snapshot at Highest-Stress Meeting
HR: {biometric_at_worst['heart_rate_bpm']:.0f} bpm | HRV: {biometric_at_worst['hrv_rmssd_ms']:.0f} ms

## Response Format
Respond in this EXACT structure using markdown:

**Today's pattern:** 2-3 sentences about the emotional arc across the day's meetings. Name specific meetings. Be specific about what happened emotionally.

**Highest concern:** Name the specific meeting and why it's the most concerning from a wellbeing perspective. Reference the emotion + clinical data.

**Tonight:** 2-3 specific actions for this evening to recover (not generic — tailored to what happened today).

**Tomorrow:** 2-3 specific recommendations for tomorrow's schedule based on today's patterns (e.g. "block 30 min after your stakeholder review — your stress peaks in high-stakes meetings").

**This week:** One observation about the weekly trend if patterns are emerging.

Be direct, warm, and specific. Reference actual meeting names and data."""

    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": "Analyze my day and give me my end-of-day briefing."}],
    )
    return response.content[0].text

def run_meeting_agent(employee, meeting, emotions, clinical, whoop_snap):
    """Generate intervention for a specific meeting."""
    import anthropic
    client = anthropic.Anthropic(
        base_url=os.environ.get("ANTHROPIC_BASE_URL"),
        api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"),
    )

    top = max(emotions, key=emotions.get)
    dep_label = DEPRESSION_LEVELS[min(clinical.get("depression", 0), 2)]
    anx_label = ANXIETY_LEVELS[min(clinical.get("anxiety", 0), 3)]

    system = f"""You are Vemo, a workplace wellbeing AI agent. You just analyzed voice biomarkers from a specific meeting recording.

## Employee
{employee['name']}, {employee['role']}

## Meeting Just Analyzed
{meeting['title']} ({meeting['start']}–{meeting['end']})
Type: {meeting['type']}
Participants: {', '.join(meeting['participants'])}

## Voice Analysis (emotion2vec+)
{json.dumps(emotions, indent=2)}
Top emotion: {top} ({emotions[top]:.0%})

## Clinical Screening (Kintsugi DAM)
Depression: {dep_label} | Anxiety: {anx_label}

## Biometrics During Meeting
HR: {whoop_snap['heart_rate_bpm']:.0f} bpm | HRV: {whoop_snap['hrv_rmssd_ms']:.0f} ms

## Response Format
Respond in this EXACT structure:

**What I heard:** One sentence about the emotional signature of this meeting. Be specific — reference the meeting type and participants.

**Right now:** One specific 2-5 minute action before the next meeting (breathing exercise with counts, desk stretch, quick walk, journaling prompt).

**For next time:** One specific suggestion for how to approach this type of meeting differently.

Keep it to 3-4 sentences total. Be concise and actionable."""

    response = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": "What should I do right now?"}],
    )
    return response.content[0].text

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def make_day_chart(hourly_data, meetings, pcolor, selected_meeting_idx=None):
    """Biometric chart with meeting blocks overlaid."""
    x_vals = [d["minutes_from_midnight"] for d in hourly_data]
    hrvs = [d["hrv_rmssd_ms"] for d in hourly_data]
    hrs = [d["heart_rate_bpm"] for d in hourly_data]

    # Only show working hours
    work_start = 7 * 60  # 07:00
    work_end = 18 * 60   # 18:00

    tick_vals = list(range(work_start, work_end + 1, 60))
    tick_text = [f"{m // 60:02d}:00" for m in tick_vals]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # HRV trace
    fig.add_trace(
        go.Scatter(x=x_vals, y=hrvs, name="HRV", line=dict(color="#6366f1", width=2),
                   fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"),
        secondary_y=False,
    )
    # HR trace
    fig.add_trace(
        go.Scatter(x=x_vals, y=hrs, name="Heart Rate", line=dict(color="#ef4444", width=1.5), opacity=0.6),
        secondary_y=True,
    )

    # Meeting blocks as shaded rectangles
    for i, m in enumerate(meetings):
        start_min = time_to_minutes(m["start"])
        end_min = time_to_minutes(m["end"])
        mcolor = MEETING_COLORS.get(m["type"], "#64748b")

        is_selected = selected_meeting_idx == i
        opacity = 0.25 if is_selected else 0.1

        fig.add_vrect(
            x0=start_min, x1=end_min,
            fillcolor=mcolor, opacity=opacity,
            line=dict(color=mcolor, width=2 if is_selected else 1),
            annotation_text=m["title"] if (end_min - start_min) >= 45 else m["title"][:15],
            annotation_position="top left",
            annotation_font_size=9,
            annotation_font_color=mcolor,
            secondary_y=False,
        )

    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickvals=tick_vals, ticktext=tick_text, gridcolor="#1e293b", range=[work_start, work_end]),
    )
    fig.update_yaxes(title_text="HRV (ms)", secondary_y=False, gridcolor="#1e293b")
    fig.update_yaxes(title_text="HR (bpm)", secondary_y=True, gridcolor="#1e293b")

    return fig

def make_emotion_radar(scores):
    """Radar chart for emotion scores."""
    labels = list(scores.keys())
    values = list(scores.values())
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
        hovertemplate="%{theta}: %{r:.0%}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0f172a",
            radialaxis=dict(visible=True, range=[0, max(values) * 1.2], showticklabels=False, gridcolor="#1e293b"),
            angularaxis=dict(gridcolor="#1e293b", linecolor="#1e293b"),
        ),
        height=280, margin=dict(l=40, r=40, t=20, b=20),
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        showlegend=False,
    )
    return fig

def make_week_chart(week_data, employee_key):
    """Weekly stress + happiness trend."""
    days = [d["day"][:3] for d in week_data]
    stress = [d["stress_level"] for d in week_data]
    happy = [d["happy"] for d in week_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days, y=stress, name="Stress", line=dict(color="#ef4444", width=3),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=happy, name="Positive", line=dict(color="#10b981", width=3),
        fill="tozeroy", fillcolor="rgba(16,185,129,0.1)",
    ))
    fig.update_layout(
        height=250, margin=dict(l=0, r=0, t=20, b=0),
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        yaxis=dict(range=[0, 1], tickformat=".0%", gridcolor="#1e293b"),
        xaxis=dict(gridcolor="#1e293b"),
    )
    return fig

# ===========================================================================
# PAGE CONFIG + STYLES
# ===========================================================================
st.set_page_config(page_title="Vemo", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
    .metric-card { background: #1e293b; border-radius: 8px; padding: 12px 16px; text-align: center; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #e2e8f0; }
    .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .meeting-card {
        background: #1e293b; border-radius: 12px; padding: 14px 18px; margin-bottom: 8px;
        border-left: 4px solid #334155; cursor: pointer; transition: all 0.2s;
    }
    .meeting-card:hover { background: #334155; }
    .meeting-card.selected { border-color: #10b981; background: #10b98110; }
    .model-badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px;
    }
    .agent-card {
        background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
        border-radius: 12px; padding: 20px 24px; border: 1px solid #10b981; line-height: 1.7;
    }
    .severity-gauge { border-radius: 8px; padding: 16px; text-align: center; background: #1e293b; }
    .screen-header { text-align: center; padding: 20px 0 10px 0; }
    .step-indicator { display: flex; justify-content: center; gap: 8px; margin: 16px 0; }
    .step-dot { width: 12px; height: 12px; border-radius: 50%; background: #334155; display: inline-block; }
    .step-dot.active { background: #10b981; }
    .step-dot.done { background: #6366f1; }
    .week-day-card {
        background: #1e293b; border-radius: 10px; padding: 14px; text-align: center;
        border: 2px solid transparent; transition: all 0.2s;
    }
    .week-day-card.today { border-color: #6366f1; }
    div[data-testid="stHorizontalBlock"] > div { min-width: 0; }
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# SESSION STATE
# ===========================================================================
if "screen" not in st.session_state:
    st.session_state.screen = "select"
if "employee" not in st.session_state:
    st.session_state.employee = None
if "selected_meeting" not in st.session_state:
    st.session_state.selected_meeting = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "day"  # day, week

all_data = load_persona_data()

def go_to(screen):
    st.session_state.screen = screen

# Step indicator
def render_steps(current):
    steps = ["select", "day", "meeting", "summary"]
    labels = ["Employee", "Day View", "Meeting", "Insights"]
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
# SCREEN 1: EMPLOYEE SELECTION
# ===========================================================================
if st.session_state.screen == "select":
    st.markdown('<div class="screen-header">', unsafe_allow_html=True)
    st.markdown("# 🎙️ Vemo")
    st.markdown("**Workplace Wellbeing from Voice Biomarkers**")
    st.markdown("Emotional intelligence from your meeting recordings + wearable data")
    st.markdown('</div>', unsafe_allow_html=True)
    render_steps("select")

    st.markdown("")
    cols = st.columns(4, gap="large")

    for i, key in enumerate(EMPLOYEES.keys()):
        emp = EMPLOYEES[key]
        persona_data = all_data[key]
        pcolor = PERSONA_COLORS[key]
        recovery = persona_data["daily_summary"]["recovery_score"]
        rec_color = "#ef4444" if recovery < 34 else "#f59e0b" if recovery < 67 else "#10b981"
        n_meetings = len(emp["meetings"])

        with cols[i]:
            st.markdown(f"""
            <div style="background: #0f172a; border: 2px solid #1e293b; border-radius: 16px; padding: 24px; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">{emp['emoji']}</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #e2e8f0;">{emp['name']}</div>
                <div style="font-size: 0.85rem; color: {pcolor}; font-weight: 600; margin: 4px 0;">{emp['role']}</div>
                <div style="font-size: 0.8rem; color: #64748b;">{emp['team']} · {emp['label']}</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin: 8px 0; line-height: 1.4;">{emp['bio']}</div>
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #1e293b; display: flex; justify-content: space-around;">
                    <div>
                        <span style="font-size: 1.3rem; font-weight: 700; color: {rec_color};">{recovery}%</span>
                        <div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase;">Recovery</div>
                    </div>
                    <div>
                        <span style="font-size: 1.3rem; font-weight: 700; color: #e2e8f0;">{n_meetings}</span>
                        <div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase;">Meetings</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"View {emp['name'].split()[0]}'s Day", key=f"sel_{key}", use_container_width=True):
                st.session_state.employee = key
                st.session_state.selected_meeting = None
                go_to("day")
                st.rerun()

# ===========================================================================
# SCREEN 2: DAY VIEW
# ===========================================================================
elif st.session_state.screen == "day":
    emp_key = st.session_state.employee
    emp = EMPLOYEES[emp_key]
    persona_data = all_data[emp_key]
    summary = persona_data["daily_summary"]
    hourly_data = persona_data["hourly_data"]
    pcolor = PERSONA_COLORS[emp_key]
    meetings = emp["meetings"]

    render_steps("day")

    # Header with view toggle
    col_hdr, col_toggle, col_back = st.columns([3, 1, 1])
    with col_hdr:
        st.markdown(f"## {emp['emoji']} {emp['name']} — {'Today' if st.session_state.view_mode == 'day' else 'This Week'}")
    with col_toggle:
        view = st.segmented_control("View", ["Day", "Week"], default="Day" if st.session_state.view_mode == "day" else "Week", label_visibility="collapsed")
        if view:
            st.session_state.view_mode = view.lower()
    with col_back:
        if st.button("← Change Employee"):
            go_to("select")
            st.rerun()

    # ---- WEEK VIEW ----
    if st.session_state.view_mode == "week":
        week_data = get_week_daily_scores(emp_key)

        # Weekly trend chart
        fig_week = make_week_chart(week_data, emp_key)
        st.plotly_chart(fig_week, use_container_width=True)

        # Day cards
        day_cols = st.columns(5)
        for i, day in enumerate(week_data):
            with day_cols[i]:
                stress_color = "#ef4444" if day["stress_level"] > 0.5 else "#f59e0b" if day["stress_level"] > 0.3 else "#10b981"
                is_today = (i == 4)  # Friday = today for demo
                card_cls = "week-day-card today" if is_today else "week-day-card"
                st.markdown(f"""
                <div class="{card_cls}">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">{day['day']}</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: {stress_color}; margin: 8px 0;">{day['stress_level']:.0%}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">STRESS</div>
                    <div style="margin-top: 8px; font-size: 0.8rem; color: #94a3b8;">{day['meeting_count']} meetings</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">Recovery: {day['recovery']}%</div>
                </div>
                """, unsafe_allow_html=True)

        # Weekly insight
        st.markdown("---")
        st.markdown("### Weekly Pattern")
        avg_stress = sum(d["stress_level"] for d in week_data) / len(week_data)
        worst_day = max(week_data, key=lambda d: d["stress_level"])
        best_day = min(week_data, key=lambda d: d["stress_level"])
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-left: 4px solid #f59e0b; border-radius: 8px; padding: 16px 20px; line-height: 1.6;">
            Average stress this week: <strong style="color: #e2e8f0;">{avg_stress:.0%}</strong><br>
            Highest stress: <strong style="color: #ef4444;">{worst_day['day']}</strong> ({worst_day['stress_level']:.0%})<br>
            Best day: <strong style="color: #10b981;">{best_day['day']}</strong> ({best_day['stress_level']:.0%})<br>
            Total meetings: <strong style="color: #e2e8f0;">{sum(d['meeting_count'] for d in week_data)}</strong>
        </div>
        """, unsafe_allow_html=True)

    # ---- DAY VIEW ----
    else:
        # Summary row
        m1, m2, m3, m4 = st.columns(4)
        rec_color = "#ef4444" if summary["recovery_score"] < 34 else "#f59e0b" if summary["recovery_score"] < 67 else "#10b981"
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{rec_color}">{summary["recovery_score"]}%</div><div class="metric-label">Recovery</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["sleep_duration_hrs"]}h</div><div class="metric-label">Sleep ({summary["sleep_performance_pct"]}%)</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(meetings)}</div><div class="metric-label">Meetings Today</div></div>', unsafe_allow_html=True)
        with m4:
            # Calculate total meeting hours
            total_mins = sum(time_to_minutes(m["end"]) - time_to_minutes(m["start"]) for m in meetings)
            st.markdown(f'<div class="metric-card"><div class="metric-value">{total_mins / 60:.1f}h</div><div class="metric-label">In Meetings</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Biometric chart with meeting overlays
        fig = make_day_chart(hourly_data, meetings, pcolor, st.session_state.selected_meeting)
        st.plotly_chart(fig, use_container_width=True)

        # Meeting cards
        st.markdown("### Meeting Emotion Analysis")
        st.caption("Voice biomarkers automatically extracted from meeting recordings")

        for i, m in enumerate(meetings):
            emotions = get_meeting_emotions(emp_key, i)
            top_emo = max(emotions, key=emotions.get)
            top_score = emotions[top_emo]
            emo_color = EMOTION_COLORS.get(top_emo, "#94a3b8")
            mcolor = MEETING_COLORS.get(m["type"], "#64748b")
            clinical = get_meeting_clinical(emp_key, i)
            dep_label = DEPRESSION_LEVELS[min(clinical.get("depression", 0), 2)]
            anx_label = ANXIETY_LEVELS[min(clinical.get("anxiety", 0), 3)]

            is_concerning = top_emo in ("angry", "fearful", "sad") and top_score > 0.3
            border_color = "#ef4444" if is_concerning else mcolor

            col_info, col_emo, col_clinical, col_action = st.columns([3, 2, 2, 1])
            with col_info:
                st.markdown(f"""
                <div style="padding: 8px 0;">
                    <span style="font-size: 0.7rem; background: {mcolor}22; color: {mcolor}; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{m['type'].upper()}</span>
                    <div style="font-size: 1rem; font-weight: 600; color: #e2e8f0; margin-top: 4px;">{m['title']}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">{m['start']}–{m['end']} · {', '.join(m['participants'][:3])}{'...' if len(m['participants']) > 3 else ''}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_emo:
                st.markdown(f"""
                <div style="padding: 8px 0; text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: {emo_color};">{top_emo.upper()}</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">{top_score:.0%}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_clinical:
                dep_color = SEVERITY_COLORS[dep_label]
                anx_color = SEVERITY_COLORS[anx_label]
                st.markdown(f"""
                <div style="padding: 8px 0; text-align: center;">
                    <span style="font-size: 0.75rem; color: {dep_color};">D: {dep_label}</span><br>
                    <span style="font-size: 0.75rem; color: {anx_color};">A: {anx_label}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_action:
                if st.button("Analyze", key=f"meeting_{i}", use_container_width=True):
                    st.session_state.selected_meeting = i
                    go_to("meeting")
                    st.rerun()

            st.markdown("<hr style='margin: 4px 0; border-color: #1e293b;'>", unsafe_allow_html=True)

        # Daily summary button
        st.markdown("")
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            if st.button("📊 Generate Daily Insights", use_container_width=True, type="primary"):
                go_to("summary")
                st.rerun()

# ===========================================================================
# SCREEN 3: MEETING DETAIL
# ===========================================================================
elif st.session_state.screen == "meeting":
    emp_key = st.session_state.employee
    emp = EMPLOYEES[emp_key]
    persona_data = all_data[emp_key]
    hourly_data = persona_data["hourly_data"]
    meeting_idx = st.session_state.selected_meeting
    m = emp["meetings"][meeting_idx]
    pcolor = PERSONA_COLORS[emp_key]

    emotions = get_meeting_emotions(emp_key, meeting_idx)
    clinical = get_meeting_clinical(emp_key, meeting_idx)
    top_emo = max(emotions, key=emotions.get)
    emo_color = EMOTION_COLORS.get(top_emo, "#94a3b8")

    # Get biometric snapshot at meeting midpoint
    mid_minutes = (time_to_minutes(m["start"]) + time_to_minutes(m["end"])) // 2
    snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - mid_minutes))

    render_steps("meeting")

    st.markdown(f"## 🎙️ {m['title']}")
    st.markdown(f"**{m['start']}–{m['end']}** · {m['type'].capitalize()} · {', '.join(m['participants'])}")

    st.markdown("---")

    # Two-column: radar + clinical
    emo_col, clin_col = st.columns(2)

    with emo_col:
        st.markdown('<div class="model-badge" style="background: #10b98122; color: #10b981; border: 1px solid #10b981;">ANALYZED</div>', unsafe_allow_html=True)
        st.markdown("#### Voice Emotion Profile")
        st.caption("**emotion2vec+ large** — 9-class speech emotion recognition from meeting audio")

        st.markdown(f"""
        <div style="background: {emo_color}22; border: 1px solid {emo_color}; border-radius: 12px; padding: 12px; text-align: center; margin-bottom: 8px;">
            <span style="font-size: 1.6rem; font-weight: 700; color: {emo_color};">{top_emo.upper()}</span>
            <span style="font-size: 1.2rem; color: #94a3b8; margin-left: 8px;">{emotions[top_emo]:.0%}</span>
        </div>
        """, unsafe_allow_html=True)
        fig_radar = make_emotion_radar(emotions)
        st.plotly_chart(fig_radar, use_container_width=True)

    with clin_col:
        st.markdown('<div class="model-badge" style="background: #10b98122; color: #10b981; border: 1px solid #10b981;">ANALYZED</div>', unsafe_allow_html=True)
        st.markdown("#### Clinical Screening")
        st.caption("**Kintsugi DAM 3.1** — PHQ-9 depression & GAD-7 anxiety from acoustics")

        dep_idx = min(clinical.get("depression", 0), 2)
        anx_idx = min(clinical.get("anxiety", 0), 3)
        dep_label = DEPRESSION_LEVELS[dep_idx]
        anx_label = ANXIETY_LEVELS[anx_idx]
        dep_color = SEVERITY_COLORS[dep_label]
        anx_color = SEVERITY_COLORS[anx_label]

        dep_c, anx_c = st.columns(2)
        with dep_c:
            st.markdown(f"""
            <div class="severity-gauge">
                <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Depression (PHQ-9)</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {dep_color}; margin-top: 4px;">{dep_label}</div>
                <div style="background: #0f172a; border-radius: 4px; height: 8px; margin-top: 8px;">
                    <div style="background: {dep_color}; width: {max(dep_idx / 2 * 100, 10)}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with anx_c:
            st.markdown(f"""
            <div class="severity-gauge">
                <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;">Anxiety (GAD-7)</div>
                <div style="font-size: 1.3rem; font-weight: 700; color: {anx_color}; margin-top: 4px;">{anx_label}</div>
                <div style="background: #0f172a; border-radius: 4px; height: 8px; margin-top: 8px;">
                    <div style="background: {anx_color}; width: {max(anx_idx / 3 * 100, 10)}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")

        # Biometrics during meeting
        st.markdown("**Biometrics During Meeting**")
        bv1, bv2, bv3 = st.columns(3)
        with bv1:
            st.metric("HR", f"{snap['heart_rate_bpm']:.0f} bpm")
        with bv2:
            st.metric("HRV", f"{snap['hrv_rmssd_ms']:.0f} ms")
        with bv3:
            st.metric("Resp", f"{snap['respiratory_rate_brpm']:.1f}")

    # Agent intervention
    st.markdown("---")
    st.markdown("### Vemo Intervention")

    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        with st.spinner("Generating meeting-specific intervention..."):
            time.sleep(1)
            agent_response = run_meeting_agent(emp, m, emotions, clinical, snap)
        st.markdown(f'<div class="agent-card">\n\n{agent_response}\n\n</div>', unsafe_allow_html=True)
    else:
        st.warning("Set `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY` to enable the agent.")

    # Navigation
    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("← Back to Day View", use_container_width=True):
            go_to("day")
            st.rerun()
    with n2:
        # Next/prev meeting
        if meeting_idx < len(emp["meetings"]) - 1:
            next_m = emp["meetings"][meeting_idx + 1]
            if st.button(f"Next: {next_m['title']} →", use_container_width=True):
                st.session_state.selected_meeting = meeting_idx + 1
                st.rerun()
    with n3:
        if st.button("📊 Daily Insights", use_container_width=True):
            go_to("summary")
            st.rerun()

# ===========================================================================
# SCREEN 4: DAILY SUMMARY + INSIGHTS
# ===========================================================================
elif st.session_state.screen == "summary":
    emp_key = st.session_state.employee
    emp = EMPLOYEES[emp_key]
    persona_data = all_data[emp_key]
    summary = persona_data["daily_summary"]
    hourly_data = persona_data["hourly_data"]
    meetings = emp["meetings"]
    pcolor = PERSONA_COLORS[emp_key]

    render_steps("summary")

    st.markdown(f"## 📊 Daily Insights — {emp['name']}")
    st.caption(f"{emp['role']} · {emp['team']} · {len(meetings)} meetings today")

    # Build meeting data with emotions
    meetings_with_emotions = []
    for i, m in enumerate(meetings):
        emotions = get_meeting_emotions(emp_key, i)
        clinical = get_meeting_clinical(emp_key, i)
        meetings_with_emotions.append({**m, "emotions": emotions, "clinical": clinical})

    # Find worst meeting
    worst_idx = max(range(len(meetings_with_emotions)), key=lambda i: max(
        meetings_with_emotions[i]["emotions"].get("angry", 0),
        meetings_with_emotions[i]["emotions"].get("fearful", 0),
        meetings_with_emotions[i]["emotions"].get("sad", 0),
    ))
    worst_meeting = meetings_with_emotions[worst_idx]
    worst_snap_min = (time_to_minutes(worst_meeting["start"]) + time_to_minutes(worst_meeting["end"])) // 2
    worst_snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - worst_snap_min))

    # Emotion timeline — small radar per meeting
    st.markdown("### Emotional Arc")
    meeting_cols = st.columns(min(len(meetings), 4))
    for i, m in enumerate(meetings_with_emotions):
        with meeting_cols[i % min(len(meetings), 4)]:
            top = max(m["emotions"], key=m["emotions"].get)
            emo_color = EMOTION_COLORS.get(top, "#94a3b8")
            is_worst = i == worst_idx
            border = f"border: 2px solid #ef4444;" if is_worst else "border: 1px solid #1e293b;"
            st.markdown(f"""
            <div style="background: #0f172a; border-radius: 10px; padding: 12px; text-align: center; margin-bottom: 8px; {border}">
                <div style="font-size: 0.7rem; color: #64748b;">{m['start']}–{m['end']}</div>
                <div style="font-size: 0.8rem; font-weight: 600; color: #e2e8f0; margin: 4px 0;">{m['title'][:20]}</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: {emo_color};">{top.upper()}</div>
                <div style="font-size: 0.8rem; color: #94a3b8;">{m['emotions'][top]:.0%}</div>
                {'<div style="font-size: 0.65rem; color: #ef4444; margin-top: 4px;">⚠ HIGHEST CONCERN</div>' if is_worst else ''}
            </div>
            """, unsafe_allow_html=True)

    # Biometric chart with all meetings
    st.markdown("---")
    st.markdown("### Biometrics + Meeting Overlay")
    fig = make_day_chart(hourly_data, meetings, pcolor, worst_idx)
    st.plotly_chart(fig, use_container_width=True)

    # Agent daily briefing
    st.markdown("---")
    st.markdown("### Vemo End-of-Day Briefing")

    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        with st.spinner("Analyzing full day and generating insights..."):
            agent_response = run_daily_agent(emp, meetings_with_emotions, summary, worst_snap)
        st.markdown(f'<div class="agent-card">\n\n{agent_response}\n\n</div>', unsafe_allow_html=True)
    else:
        st.warning("Set `ANTHROPIC_AUTH_TOKEN` or `ANTHROPIC_API_KEY` to enable the agent.")

    # Weekly view teaser
    st.markdown("---")
    st.markdown("### This Week")
    week_data = get_week_daily_scores(emp_key)
    fig_week = make_week_chart(week_data, emp_key)
    st.plotly_chart(fig_week, use_container_width=True)

    # Navigation
    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("← Back to Day View", use_container_width=True):
            go_to("day")
            st.rerun()
    with n2:
        if st.button("📅 Weekly View", use_container_width=True):
            st.session_state.view_mode = "week"
            go_to("day")
            st.rerun()
    with n3:
        if st.button("🏠 Change Employee", use_container_width=True):
            go_to("select")
            st.rerun()
