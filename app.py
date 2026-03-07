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

PERSONA_COLORS = {
    "maya": "#6366f1", "derek": "#f59e0b", "travis": "#ef4444",
    "lucia": "#10b981", "jordan": "#ec4899", "priya": "#06b6d4",
}

DEPRESSION_LEVELS = ["No Depression", "Mild-Moderate", "Severe"]
ANXIETY_LEVELS = ["No Anxiety", "Mild", "Moderate", "Severe"]
SEVERITY_COLORS = {
    "No Depression": "#10b981", "Mild-Moderate": "#f59e0b", "Severe": "#ef4444",
    "No Anxiety": "#10b981", "Mild": "#6366f1", "Moderate": "#f59e0b", "Severe": "#ef4444",
}

MEETING_COLORS = {
    "standup": "#6366f1", "review": "#f59e0b", "1on1": "#ec4899",
    "planning": "#8b5cf6", "external": "#ef4444", "sync": "#06b6d4",
    "workshop": "#10b981", "allhands": "#f97316", "sales": "#ef4444",
    "coldcall": "#f97316", "demo": "#a855f7", "latenight": "#475569",
}

# Map new employees to existing biometric data keys
BIOMETRIC_MAP = {
    "maya": "maya", "derek": "derek", "travis": "travis", "lucia": "lucia",
    "jordan": "derek",  # anxiety pattern
    "priya": "maya",    # exhaustion pattern
}

# ---------------------------------------------------------------------------
# Employee profiles
# ---------------------------------------------------------------------------
EMPLOYEES = {
    "maya": {
        "name": "Maya Chen",
        "role": "Senior Software Engineer",
        "team": "Platform Engineering",
        "bio": "Remote since 2020. 6-7 meetings/day. Internalizes stress. Chronic low recovery from meeting overload.",
        "label": "Meeting Overload",
        "emoji": "💜",
        "trigger_meeting": 4,  # Client Integration Call triggers alert
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
        "bio": "Startup PM. Constant context switching. Anxiety peaks during stakeholder presentations and board interactions.",
        "label": "Context Switching",
        "emoji": "🧡",
        "trigger_meeting": 1,  # Stakeholder Review triggers alert
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
    "jordan": {
        "name": "Jordan Torres",
        "role": "Senior SDR",
        "team": "Sales Development",
        "bio": "8-12 cold calls/day plus demos. Constant rejection. Competitive pressure from leaderboard. Skips lunch for pipeline reviews.",
        "label": "Sales Burnout",
        "emoji": "🔥",
        "trigger_meeting": 4,  # Rejection-heavy cold call block triggers
        "meetings": [
            {"title": "Sales Standup", "start": "08:00", "end": "08:30", "type": "standup", "participants": ["Sales Team", "VP Sales"]},
            {"title": "Cold Call Block #1", "start": "09:00", "end": "10:30", "type": "coldcall", "participants": ["Prospect A", "Prospect B", "Prospect C"]},
            {"title": "Demo: Acme Corp", "start": "11:00", "end": "11:45", "type": "demo", "participants": ["Acme VP Ops", "AE Partner"]},
            {"title": "Pipeline Review", "start": "12:00", "end": "12:30", "type": "review", "participants": ["Sales Manager", "RevOps"]},
            {"title": "Cold Call Block #2", "start": "13:30", "end": "15:00", "type": "coldcall", "participants": ["Prospect D", "Prospect E", "Prospect F", "Prospect G"]},
            {"title": "1:1 with Manager", "start": "15:30", "end": "16:00", "type": "1on1", "participants": ["Sales Manager"]},
            {"title": "Deal Strategy", "start": "16:30", "end": "17:00", "type": "planning", "participants": ["AE", "Solutions Eng"]},
        ],
    },
    "travis": {
        "name": "Travis Kim",
        "role": "Engineering Manager",
        "team": "Infrastructure",
        "bio": "New manager. Frustration builds during cross-team conflicts. Skips breaks. Takes on too much.",
        "label": "New Manager Stress",
        "emoji": "❤️",
        "trigger_meeting": 4,  # Cross-team alignment triggers
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
    "priya": {
        "name": "Priya Mehta",
        "role": "Global Ops Lead",
        "team": "Operations",
        "bio": "Manages teams across US, EU, and APAC. First call at 7am, last at 10pm. Chronic exhaustion. Never truly off.",
        "label": "Timezone Burnout",
        "emoji": "🌏",
        "trigger_meeting": 5,  # Late evening call triggers
        "meetings": [
            {"title": "APAC Handoff", "start": "07:00", "end": "07:45", "type": "sync", "participants": ["Singapore Team", "Tokyo Lead"]},
            {"title": "Global Standup", "start": "09:00", "end": "09:30", "type": "standup", "participants": ["All Regions", "COO"]},
            {"title": "Vendor Negotiation", "start": "10:30", "end": "11:30", "type": "external", "participants": ["Vendor CEO", "Legal", "Finance"]},
            {"title": "1:1 with COO", "start": "13:00", "end": "13:30", "type": "1on1", "participants": ["COO"]},
            {"title": "EU Ops Review", "start": "15:00", "end": "16:00", "type": "review", "participants": ["London Team", "Berlin Lead"]},
            {"title": "APAC Planning", "start": "21:00", "end": "22:00", "type": "latenight", "participants": ["Singapore PM", "India Ops"]},
        ],
    },
    "lucia": {
        "name": "Lucia Vargas",
        "role": "Head of Customer Success",
        "team": "Customer Success",
        "bio": "Experienced leader. Walking breaks between meetings. Strong emotional regulation. Models healthy remote work.",
        "label": "Balanced Leader",
        "emoji": "💚",
        "trigger_meeting": None,  # No trigger — she's the healthy benchmark
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
    random.seed(hash(f"{employee_key}_{meeting_idx}_v3"))
    m = EMPLOYEES[employee_key]["meetings"][meeting_idx]
    mtype = m["type"]

    base_profiles = {
        "maya": {
            "external": {"sad": 0.35, "fearful": 0.22, "neutral": 0.15, "angry": 0.08, "happy": 0.04, "disgusted": 0.03, "other": 0.06, "surprised": 0.03, "unknown": 0.02},
            "1on1": {"sad": 0.42, "neutral": 0.20, "fearful": 0.10, "happy": 0.06, "other": 0.08, "angry": 0.04, "disgusted": 0.02, "surprised": 0.03, "unknown": 0.03},
            "planning": {"neutral": 0.28, "sad": 0.25, "fearful": 0.12, "happy": 0.08, "other": 0.10, "angry": 0.06, "disgusted": 0.02, "surprised": 0.04, "unknown": 0.03},
            "_default": {"neutral": 0.30, "sad": 0.22, "happy": 0.12, "fearful": 0.08, "other": 0.10, "angry": 0.05, "disgusted": 0.03, "surprised": 0.05, "unknown": 0.03},
        },
        "derek": {
            "review": {"fearful": 0.40, "angry": 0.15, "neutral": 0.12, "surprised": 0.08, "sad": 0.06, "happy": 0.04, "other": 0.06, "disgusted": 0.04, "unknown": 0.03},
            "external": {"fearful": 0.40, "angry": 0.15, "neutral": 0.12, "surprised": 0.08, "sad": 0.06, "happy": 0.04, "other": 0.06, "disgusted": 0.04, "unknown": 0.03},
            "1on1": {"fearful": 0.35, "neutral": 0.18, "sad": 0.12, "angry": 0.10, "other": 0.08, "happy": 0.04, "surprised": 0.04, "disgusted": 0.04, "unknown": 0.03},
            "_default": {"neutral": 0.25, "fearful": 0.22, "happy": 0.10, "other": 0.12, "angry": 0.08, "sad": 0.06, "surprised": 0.06, "disgusted": 0.04, "unknown": 0.05},
        },
        "jordan": {
            "coldcall": {"fearful": 0.30, "angry": 0.22, "sad": 0.15, "neutral": 0.10, "disgusted": 0.06, "other": 0.06, "happy": 0.03, "surprised": 0.04, "unknown": 0.02},
            "demo": {"happy": 0.25, "fearful": 0.20, "neutral": 0.18, "surprised": 0.10, "angry": 0.06, "other": 0.08, "sad": 0.04, "disgusted": 0.03, "unknown": 0.04},
            "review": {"fearful": 0.35, "angry": 0.18, "sad": 0.12, "neutral": 0.10, "disgusted": 0.06, "other": 0.06, "happy": 0.04, "surprised": 0.04, "unknown": 0.03},
            "1on1": {"sad": 0.28, "fearful": 0.22, "neutral": 0.18, "angry": 0.08, "happy": 0.06, "other": 0.06, "disgusted": 0.04, "surprised": 0.04, "unknown": 0.02},
            "_default": {"neutral": 0.22, "fearful": 0.20, "angry": 0.15, "happy": 0.10, "other": 0.10, "sad": 0.08, "surprised": 0.05, "disgusted": 0.04, "unknown": 0.04},
        },
        "travis": {
            "review": {"angry": 0.45, "disgusted": 0.12, "fearful": 0.10, "neutral": 0.10, "sad": 0.06, "other": 0.06, "happy": 0.03, "surprised": 0.04, "unknown": 0.02},
            "planning": {"angry": 0.45, "disgusted": 0.12, "fearful": 0.10, "neutral": 0.10, "sad": 0.06, "other": 0.06, "happy": 0.03, "surprised": 0.04, "unknown": 0.02},
            "1on1": {"neutral": 0.28, "angry": 0.18, "happy": 0.14, "other": 0.10, "fearful": 0.08, "sad": 0.06, "disgusted": 0.04, "surprised": 0.06, "unknown": 0.04},
            "_default": {"angry": 0.25, "neutral": 0.22, "fearful": 0.12, "other": 0.10, "disgusted": 0.08, "sad": 0.06, "happy": 0.06, "surprised": 0.05, "unknown": 0.04},
        },
        "priya": {
            "latenight": {"sad": 0.38, "fearful": 0.18, "neutral": 0.14, "angry": 0.10, "disgusted": 0.06, "other": 0.05, "happy": 0.02, "surprised": 0.03, "unknown": 0.02},
            "external": {"fearful": 0.28, "neutral": 0.22, "angry": 0.12, "sad": 0.10, "happy": 0.08, "other": 0.08, "surprised": 0.04, "disgusted": 0.04, "unknown": 0.02},
            "1on1": {"neutral": 0.25, "sad": 0.20, "fearful": 0.15, "happy": 0.10, "other": 0.10, "angry": 0.06, "disgusted": 0.04, "surprised": 0.04, "unknown": 0.04},
            "_default": {"neutral": 0.28, "sad": 0.18, "happy": 0.15, "fearful": 0.10, "other": 0.10, "angry": 0.06, "disgusted": 0.03, "surprised": 0.05, "unknown": 0.03},
        },
        "lucia": {
            "external": {"happy": 0.38, "neutral": 0.25, "surprised": 0.08, "other": 0.08, "fearful": 0.05, "sad": 0.04, "angry": 0.03, "disgusted": 0.02, "unknown": 0.04},
            "_default": {"happy": 0.45, "neutral": 0.22, "surprised": 0.08, "other": 0.06, "sad": 0.04, "fearful": 0.04, "angry": 0.02, "disgusted": 0.02, "unknown": 0.04},
        },
    }

    profiles = base_profiles.get(employee_key, base_profiles["lucia"])
    base = dict(profiles.get(mtype, profiles["_default"]))

    for k in base:
        base[k] += random.uniform(-0.03, 0.03)
        base[k] = max(0.01, base[k])
    return normalize(base)

def get_meeting_clinical(employee_key, meeting_idx):
    m = EMPLOYEES[employee_key]["meetings"][meeting_idx]
    mtype = m["type"]
    clinicals = {
        "maya": {"external": {"depression": 2, "anxiety": 2}, "1on1": {"depression": 2, "anxiety": 1}, "_default": {"depression": 1, "anxiety": 1}},
        "derek": {"review": {"depression": 0, "anxiety": 3}, "external": {"depression": 0, "anxiety": 2}, "1on1": {"depression": 0, "anxiety": 2}, "_default": {"depression": 0, "anxiety": 1}},
        "jordan": {"coldcall": {"depression": 1, "anxiety": 3}, "review": {"depression": 1, "anxiety": 2}, "1on1": {"depression": 1, "anxiety": 1}, "_default": {"depression": 0, "anxiety": 2}},
        "travis": {"review": {"depression": 1, "anxiety": 2}, "planning": {"depression": 1, "anxiety": 2}, "_default": {"depression": 0, "anxiety": 1}},
        "priya": {"latenight": {"depression": 2, "anxiety": 2}, "external": {"depression": 1, "anxiety": 1}, "_default": {"depression": 1, "anxiety": 0}},
        "lucia": {"_default": {"depression": 0, "anxiety": 0}},
    }
    emp_clinicals = clinicals.get(employee_key, {"_default": {"depression": 0, "anxiety": 0}})
    return emp_clinicals.get(mtype, emp_clinicals["_default"])

# ---------------------------------------------------------------------------
# Weekly mock data
# ---------------------------------------------------------------------------
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

def get_week_daily_scores(employee_key):
    random.seed(hash(f"{employee_key}_week_v2"))
    days = []
    for day_idx, day_name in enumerate(WEEKDAYS):
        profiles = {
            "maya":   (0.3 + day_idx * 0.08, max(0.05, 0.25 - day_idx * 0.04)),
            "derek":  (0.35 + (0.15 if day_idx in (1, 3) else 0), 0.12),
            "jordan": (0.4 + day_idx * 0.06, max(0.03, 0.15 - day_idx * 0.03)),
            "travis": (0.25 + (0.2 if day_idx == 2 else 0.05 * day_idx), 0.1),
            "priya":  (0.35 + day_idx * 0.05, max(0.08, 0.20 - day_idx * 0.03)),
            "lucia":  (0.1, 0.45),
        }
        base_stress, base_happy = profiles.get(employee_key, (0.2, 0.3))
        stress = base_stress + random.uniform(-0.05, 0.05)
        happy = base_happy + random.uniform(-0.05, 0.05)
        days.append({
            "day": day_name,
            "stress_level": min(1, max(0, stress)),
            "happy": min(1, max(0, happy)),
            "meeting_count": len(EMPLOYEES[employee_key]["meetings"]) + random.randint(-1, 1),
            "recovery": max(15, min(95, int(70 - stress * 60 + random.randint(-5, 5)))),
        })
    return days

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_persona_data():
    with open(os.path.join(os.path.dirname(__file__), "persona_data.json")) as f:
        return json.load(f)

def time_to_minutes(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)

# ---------------------------------------------------------------------------
# Agent calls
# ---------------------------------------------------------------------------
def get_anthropic_client():
    import anthropic
    return anthropic.Anthropic(
        base_url=os.environ.get("ANTHROPIC_BASE_URL"),
        api_key=os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"),
    )

def stream_agent_response(system, user_msg, max_tokens=600):
    """Stream response for that real-time agentic feel."""
    client = get_anthropic_client()
    with client.messages.stream(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        for text in stream.text_stream:
            yield text

def build_meeting_system_prompt(employee, meeting, emotions, clinical, whoop_snap):
    top = max(emotions, key=emotions.get)
    dep_label = DEPRESSION_LEVELS[min(clinical.get("depression", 0), 2)]
    anx_label = ANXIETY_LEVELS[min(clinical.get("anxiety", 0), 3)]

    return f"""You are Vemo, a workplace wellbeing AI agent. You just detected a concerning emotional pattern in a meeting recording and are intervening in real-time.

You are AGENTIC. You don't just advise — you take actions. You have access to the employee's calendar, wellness tools, and notification system.

## Employee
{employee['name']}, {employee['role']} on {employee['team']} team
{employee['bio']}

## Meeting Analyzed
{meeting['title']} ({meeting['start']}–{meeting['end']})
Type: {meeting['type']}
Participants: {', '.join(meeting['participants'])}

## Voice Biomarkers (emotion2vec+ large)
{json.dumps(emotions, indent=2)}
Dominant: {top} ({emotions[top]:.0%})

## Clinical Screening (Kintsugi DAM 3.1)
Depression: {dep_label} | Anxiety: {anx_label}

## Biometrics During Meeting
HR: {whoop_snap['heart_rate_bpm']:.0f} bpm | HRV: {whoop_snap['hrv_rmssd_ms']:.0f} ms | Resp: {whoop_snap['respiratory_rate_brpm']:.1f}

## Response Format — Be SPECIFIC and AGENTIC:

**DETECTED:** One punchy sentence about what the voice + body signals reveal about this meeting. Name the emotion and the physiological confirmation.

**EXECUTING NOW:**
- [Action 1 with specific details — e.g. "Blocking 15 min on your calendar before your next meeting at 16:30"]
- [Action 2 — e.g. "Starting 4-7-8 breathing protocol (inhale 4s, hold 7s, exhale 8s, 3 cycles)"]
- [Action 3 — e.g. "Lowering your strain target for the rest of the day from 14 to 8"]

**PATTERN ALERT:** One sentence about what this means in the context of their week/role. Reference their specific situation.

**NEXT:** What Vemo will monitor for in the next meeting.

Be direct. Be warm. Show agency — you are DOING things, not suggesting them."""

def build_daily_system_prompt(employee, meetings_with_emotions, whoop_summary, biometric_at_worst):
    meeting_summaries = []
    for m in meetings_with_emotions:
        top = max(m["emotions"], key=m["emotions"].get)
        dep_label = DEPRESSION_LEVELS[min(m["clinical"].get("depression", 0), 2)]
        anx_label = ANXIETY_LEVELS[min(m["clinical"].get("anxiety", 0), 3)]
        meeting_summaries.append(
            f"- {m['start']}-{m['end']} **{m['title']}** ({m['type']}): "
            f"{top} ({m['emotions'][top]:.0%}), D: {dep_label}, A: {anx_label}"
        )

    return f"""You are Vemo, a workplace wellbeing AI agent delivering an end-of-day briefing. You've monitored this employee's entire day through voice biomarkers and wearable data.

You are AGENTIC. You take actions, set up tomorrow, and flag patterns.

## Employee
{employee['name']}, {employee['role']} on {employee['team']} team
{employee['bio']}

## Today's Meeting Analysis
{chr(10).join(meeting_summaries)}

## Wearable Summary
Recovery: {whoop_summary['recovery_score']}% | Sleep: {whoop_summary['sleep_duration_hrs']}h / {whoop_summary['sleep_need_hrs']}h needed
Sleep Debt: {whoop_summary['sleep_debt_hrs']}h

## Biometrics at Worst Meeting
HR: {biometric_at_worst['heart_rate_bpm']:.0f} bpm | HRV: {biometric_at_worst['hrv_rmssd_ms']:.0f} ms

## Response Format:

**TODAY'S ARC:** 2-3 sentences mapping the emotional journey across meetings. Name specific meetings and transitions.

**ACTIONS TAKEN:**
- [What Vemo already did today in response to patterns — be specific]
- [Calendar changes made for tomorrow]
- [Notifications or flags set]

**TONIGHT:** 2-3 specific recovery actions with exact details (not generic).

**TOMORROW — ALREADY SCHEDULED:**
- [Specific calendar modification for tomorrow]
- [Buffer blocks added]
- [Meeting format changes suggested]

**WEEKLY TREND:** One observation about the pattern this week and what Vemo is doing about it.

Reference actual meeting names. Be specific, not generic."""

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def make_day_chart(hourly_data, meetings, pcolor, up_to_minutes=None, selected_meeting_idx=None, trigger_meeting_idx=None):
    x_vals = [d["minutes_from_midnight"] for d in hourly_data]
    hrvs = [d["hrv_rmssd_ms"] for d in hourly_data]
    hrs = [d["heart_rate_bpm"] for d in hourly_data]

    work_start = 6 * 60
    work_end = 23 * 60  # extended for Priya's late meetings

    # Clip data if playing
    if up_to_minutes is not None:
        clip_idx = next((i for i, x in enumerate(x_vals) if x > up_to_minutes), len(x_vals))
        x_vals = x_vals[:clip_idx]
        hrvs = hrvs[:clip_idx]
        hrs = hrs[:clip_idx]

    tick_vals = list(range(work_start, min(work_end, 19 * 60) + 1, 60))
    tick_text = [f"{m // 60:02d}:00" for m in tick_vals]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=x_vals, y=hrvs, name="HRV", line=dict(color="#6366f1", width=2),
                   fill="tozeroy", fillcolor="rgba(99,102,241,0.08)"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=x_vals, y=hrs, name="Heart Rate", line=dict(color="#ef4444", width=1.5), opacity=0.6),
        secondary_y=True,
    )

    # Meeting blocks — only show if time has passed them (or if not playing)
    for i, m in enumerate(meetings):
        start_min = time_to_minutes(m["start"])
        end_min = time_to_minutes(m["end"])

        if up_to_minutes is not None and start_min > up_to_minutes:
            continue  # haven't reached this meeting yet

        mcolor = MEETING_COLORS.get(m["type"], "#64748b")
        is_selected = selected_meeting_idx == i
        is_trigger = trigger_meeting_idx == i

        if is_trigger:
            opacity = 0.35
            line_w = 3
            mcolor = "#ef4444"
        elif is_selected:
            opacity = 0.25
            line_w = 2
        else:
            opacity = 0.1
            line_w = 1

        fig.add_vrect(
            x0=start_min, x1=end_min,
            fillcolor=mcolor, opacity=opacity,
            line=dict(color=mcolor, width=line_w),
            annotation_text=m["title"] if (end_min - start_min) >= 45 else m["title"][:15],
            annotation_position="top left",
            annotation_font_size=9,
            annotation_font_color=mcolor,
            secondary_y=False,
        )

    fig.update_layout(
        height=350, margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(tickvals=tick_vals, ticktext=tick_text, gridcolor="#1e293b", range=[work_start, min(work_end, 19 * 60)]),
    )
    fig.update_yaxes(title_text="HRV (ms)", secondary_y=False, gridcolor="#1e293b")
    fig.update_yaxes(title_text="HR (bpm)", secondary_y=True, gridcolor="#1e293b")
    return fig

def make_emotion_radar(scores):
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
        fillcolor=f"rgba({int(fill_color[1:3], 16)},{int(fill_color[3:5], 16)},{int(fill_color[5:7], 16)},0.25)",
        line=dict(color=fill_color, width=2.5),
        hovertemplate="%{theta}: %{r:.0%}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0f172a",
            radialaxis=dict(visible=True, range=[0, max(values) * 1.2], showticklabels=False, gridcolor="#1e293b"),
            angularaxis=dict(gridcolor="#1e293b", linecolor="#1e293b"),
        ),
        height=300, margin=dict(l=40, r=40, t=20, b=20),
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8", size=11),
        showlegend=False,
    )
    return fig

def make_week_chart(week_data, employee_key):
    days = [d["day"][:3] for d in week_data]
    stress = [d["stress_level"] for d in week_data]
    happy = [d["happy"] for d in week_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=stress, name="Stress", line=dict(color="#ef4444", width=3),
                             fill="tozeroy", fillcolor="rgba(239,68,68,0.1)"))
    fig.add_trace(go.Scatter(x=days, y=happy, name="Positive", line=dict(color="#10b981", width=3),
                             fill="tozeroy", fillcolor="rgba(16,185,129,0.1)"))
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
    @keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 50% { box-shadow: 0 0 20px 10px rgba(239,68,68,0.15); } }
    @keyframes glow { 0%, 100% { box-shadow: 0 0 5px rgba(16,185,129,0.3); } 50% { box-shadow: 0 0 20px rgba(16,185,129,0.6); } }
    @keyframes scan { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
    .metric-card { background: #1e293b; border-radius: 8px; padding: 12px 16px; text-align: center; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #e2e8f0; }
    .metric-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
    .model-badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px;
    }
    .agent-card {
        background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
        border-radius: 12px; padding: 20px 24px; border: 1px solid #10b981; line-height: 1.7;
        animation: glow 3s ease-in-out infinite;
    }
    .alert-box {
        background: linear-gradient(135deg, #451a03 0%, #0f172a 100%);
        border: 2px solid #ef4444; border-radius: 16px; padding: 24px 32px; text-align: center;
        animation: pulse 2s ease-in-out infinite;
    }
    .severity-gauge { border-radius: 8px; padding: 16px; text-align: center; background: #1e293b; }
    .screen-header { text-align: center; padding: 20px 0 10px 0; }
    .agent-step {
        background: #1e293b; border-radius: 8px; padding: 12px 16px; margin: 6px 0;
        border-left: 3px solid #334155; transition: all 0.3s;
    }
    .agent-step.active { border-left-color: #10b981; background: #10b98110; }
    .agent-step.done { border-left-color: #6366f1; }
    .action-btn {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 10px; padding: 14px 18px;
        text-align: center; transition: all 0.2s; cursor: pointer;
    }
    .action-btn:hover { border-color: #10b981; background: #10b98110; }
    .scan-bar {
        height: 3px; background: linear-gradient(90deg, transparent 0%, #10b981 50%, transparent 100%);
        background-size: 200% 100%; animation: scan 1.5s linear infinite;
        border-radius: 2px; margin: 8px 0;
    }
    .vemo-active {
        display: inline-flex; align-items: center; gap: 8px;
        background: #10b98120; border: 1px solid #10b981; border-radius: 20px;
        padding: 4px 14px; font-size: 0.8rem; color: #10b981; font-weight: 600;
    }
    .vemo-dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: pulse 1.5s infinite; }
    div[data-testid="stHorizontalBlock"] > div { min-width: 0; }
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# SESSION STATE
# ===========================================================================
defaults = {
    "screen": "select", "employee": None, "selected_meeting": None,
    "view_mode": "day", "playing": False, "play_minutes": 7 * 60,
    "triggered": False, "agent_done": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

all_data = load_persona_data()

def go_to(screen):
    st.session_state.screen = screen

# ===========================================================================
# SCREEN 1: EMPLOYEE SELECTION
# ===========================================================================
if st.session_state.screen == "select":
    st.markdown('<div class="screen-header">', unsafe_allow_html=True)
    st.markdown("# 🎙️ Vemo")
    st.markdown("**Workplace Wellbeing Intelligence**")
    st.markdown("Voice biomarkers from meeting recordings + wearable data → real-time interventions")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")

    # 2 rows of 3
    emp_keys = list(EMPLOYEES.keys())
    for row_start in range(0, len(emp_keys), 3):
        cols = st.columns(3, gap="large")
        for i, key in enumerate(emp_keys[row_start:row_start + 3]):
            emp = EMPLOYEES[key]
            bio_key = BIOMETRIC_MAP[key]
            persona_data = all_data[bio_key]
            pcolor = PERSONA_COLORS[key]
            recovery = persona_data["daily_summary"]["recovery_score"]
            rec_color = "#ef4444" if recovery < 34 else "#f59e0b" if recovery < 67 else "#10b981"
            n_meetings = len(emp["meetings"])
            total_mins = sum(time_to_minutes(m["end"]) - time_to_minutes(m["start"]) for m in emp["meetings"])

            with cols[i]:
                st.markdown(f"""
                <div style="background: #0f172a; border: 2px solid #1e293b; border-radius: 16px; padding: 24px; text-align: center; min-height: 320px;">
                    <div style="font-size: 2.5rem; margin-bottom: 4px;">{emp['emoji']}</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: #e2e8f0;">{emp['name']}</div>
                    <div style="font-size: 0.8rem; color: {pcolor}; font-weight: 600; margin: 2px 0;">{emp['role']}</div>
                    <div style="display: inline-block; background: {pcolor}15; color: {pcolor}; padding: 2px 10px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; margin: 4px 0;">{emp['label'].upper()}</div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin: 8px 0; line-height: 1.4;">{emp['bio']}</div>
                    <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #1e293b; display: flex; justify-content: space-around;">
                        <div><span style="font-size: 1.2rem; font-weight: 700; color: {rec_color};">{recovery}%</span><div style="font-size: 0.6rem; color: #64748b;">RECOVERY</div></div>
                        <div><span style="font-size: 1.2rem; font-weight: 700; color: #e2e8f0;">{n_meetings}</span><div style="font-size: 0.6rem; color: #64748b;">MEETINGS</div></div>
                        <div><span style="font-size: 1.2rem; font-weight: 700; color: #e2e8f0;">{total_mins / 60:.1f}h</span><div style="font-size: 0.6rem; color: #64748b;">ON CALLS</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Monitor {emp['name'].split()[0]}", key=f"sel_{key}", use_container_width=True):
                    st.session_state.employee = key
                    st.session_state.selected_meeting = None
                    st.session_state.playing = False
                    st.session_state.play_minutes = 7 * 60
                    st.session_state.triggered = False
                    st.session_state.agent_done = False
                    go_to("day")
                    st.rerun()
        st.markdown("")

# ===========================================================================
# SCREEN 2: DAY VIEW (with play mode)
# ===========================================================================
elif st.session_state.screen == "day":
    from streamlit_autorefresh import st_autorefresh

    emp_key = st.session_state.employee
    emp = EMPLOYEES[emp_key]
    bio_key = BIOMETRIC_MAP[emp_key]
    persona_data = all_data[bio_key]
    summary = persona_data["daily_summary"]
    hourly_data = persona_data["hourly_data"]
    pcolor = PERSONA_COLORS[emp_key]
    meetings = emp["meetings"]
    trigger_idx = emp.get("trigger_meeting")

    # Header
    col_hdr, col_status, col_back = st.columns([3, 1, 1])
    with col_hdr:
        st.markdown(f"## {emp['emoji']} {emp['name']}")
        st.caption(f"{emp['role']} · {emp['team']}")
    with col_status:
        if st.session_state.playing:
            st.markdown('<div class="vemo-active"><span class="vemo-dot"></span> MONITORING</div>', unsafe_allow_html=True)
    with col_back:
        if st.button("← Back"):
            st.session_state.playing = False
            go_to("select")
            st.rerun()

    # View toggle
    col_view, col_play, col_speed = st.columns([2, 1, 1])
    with col_view:
        view = st.segmented_control("View", ["Day", "Week"], default="Day" if st.session_state.view_mode == "day" else "Week", label_visibility="collapsed")
        if view:
            st.session_state.view_mode = view.lower()

    # ---- WEEK VIEW ----
    if st.session_state.view_mode == "week":
        week_data = get_week_daily_scores(emp_key)
        fig_week = make_week_chart(week_data, emp_key)
        st.plotly_chart(fig_week, use_container_width=True)

        day_cols = st.columns(5)
        for i, day in enumerate(week_data):
            with day_cols[i]:
                stress_color = "#ef4444" if day["stress_level"] > 0.5 else "#f59e0b" if day["stress_level"] > 0.3 else "#10b981"
                is_today = (i == 4)
                border = "border: 2px solid #6366f1;" if is_today else "border: 1px solid #1e293b;"
                st.markdown(f"""
                <div style="background: #1e293b; border-radius: 10px; padding: 14px; text-align: center; {border}">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #e2e8f0;">{day['day']}{'  ← today' if is_today else ''}</div>
                    <div style="font-size: 1.4rem; font-weight: 700; color: {stress_color}; margin: 6px 0;">{day['stress_level']:.0%}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">STRESS</div>
                    <div style="margin-top: 6px; font-size: 0.8rem; color: #94a3b8;">{day['meeting_count']} meetings</div>
                    <div style="font-size: 0.8rem; color: #94a3b8;">Recovery: {day['recovery']}%</div>
                </div>
                """, unsafe_allow_html=True)

    # ---- DAY VIEW ----
    else:
        with col_play:
            play_label = "▶ Play Day" if not st.session_state.playing else "⏸ Pause"
            if st.button(play_label, use_container_width=True, type="primary"):
                if not st.session_state.playing:
                    st.session_state.playing = True
                    if st.session_state.triggered:
                        # Reset if replaying
                        st.session_state.play_minutes = 7 * 60
                        st.session_state.triggered = False
                        st.session_state.agent_done = False
                else:
                    st.session_state.playing = False
                st.rerun()
        with col_speed:
            speed_map = {"1x": 15, "2x": 30, "4x": 60, "8x": 120}
            speed_label = st.select_slider("Speed", options=list(speed_map.keys()), value="4x")

        # Summary row
        m1, m2, m3, m4 = st.columns(4)
        rec_color = "#ef4444" if summary["recovery_score"] < 34 else "#f59e0b" if summary["recovery_score"] < 67 else "#10b981"
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{rec_color}">{summary["recovery_score"]}%</div><div class="metric-label">Recovery</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{summary["sleep_duration_hrs"]}h</div><div class="metric-label">Sleep ({summary["sleep_performance_pct"]}%)</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(meetings)}</div><div class="metric-label">Meetings</div></div>', unsafe_allow_html=True)
        with m4:
            total_mins = sum(time_to_minutes(mt["end"]) - time_to_minutes(mt["start"]) for mt in meetings)
            st.markdown(f'<div class="metric-card"><div class="metric-value">{total_mins / 60:.1f}h</div><div class="metric-label">On Calls</div></div>', unsafe_allow_html=True)

        # Current time display
        play_min = st.session_state.play_minutes
        current_h = play_min // 60
        current_m = play_min % 60
        current_time = f"{current_h:02d}:{current_m:02d}"

        # Check if trigger meeting has been reached
        trigger_reached = False
        if trigger_idx is not None and not st.session_state.triggered:
            trigger_end = time_to_minutes(meetings[trigger_idx]["end"])
            if play_min >= trigger_end:
                trigger_reached = True

        # Determine which meetings are "in progress" or "done"
        current_meeting_label = ""
        for mt in meetings:
            ms = time_to_minutes(mt["start"])
            me = time_to_minutes(mt["end"])
            if ms <= play_min < me:
                current_meeting_label = f"In: {mt['title']}"
                break

        st.markdown(f"""
        <div style="text-align: center; padding: 8px 0;">
            <span style="font-size: 2.5rem; font-weight: 700; color: #e2e8f0; letter-spacing: 2px;">{current_time}</span>
            <span style="font-size: 0.9rem; color: #64748b; margin-left: 16px;">{current_meeting_label}</span>
        </div>
        """, unsafe_allow_html=True)

        # Chart
        trigger_show = trigger_idx if st.session_state.triggered else None
        fig = make_day_chart(hourly_data, meetings, pcolor,
                            up_to_minutes=play_min if st.session_state.playing or play_min < 18 * 60 else None,
                            trigger_meeting_idx=trigger_show)
        st.plotly_chart(fig, use_container_width=True, key="day_chart")

        # Meeting timeline below chart
        st.markdown("### Meetings")
        for i, mt in enumerate(meetings):
            ms = time_to_minutes(mt["start"])
            me = time_to_minutes(mt["end"])
            mcolor = MEETING_COLORS.get(mt["type"], "#64748b")

            if play_min < ms:
                status = "upcoming"
                status_icon = "⏳"
                opacity = "0.4"
            elif ms <= play_min < me:
                status = "in-progress"
                status_icon = "🔴"
                opacity = "1"
            else:
                status = "done"
                status_icon = "✅"
                opacity = "1"

            emotions = get_meeting_emotions(emp_key, i) if status == "done" else None
            top_emo = max(emotions, key=emotions.get) if emotions else ""
            top_score = emotions[top_emo] if emotions else 0
            emo_color = EMOTION_COLORS.get(top_emo, "#64748b")

            is_trigger = (i == trigger_idx and st.session_state.triggered)

            col_time, col_name, col_emotion, col_btn = st.columns([1.5, 3, 2, 1])
            with col_time:
                st.markdown(f'<div style="opacity:{opacity};padding:6px 0;font-size:0.85rem;color:#94a3b8;">{status_icon} {mt["start"]}–{mt["end"]}</div>', unsafe_allow_html=True)
            with col_name:
                highlight = "color:#ef4444;font-weight:700;" if is_trigger else f"color:#e2e8f0;"
                st.markdown(f"""
                <div style="padding:6px 0;opacity:{opacity};">
                    <span style="font-size:0.65rem;background:{mcolor}22;color:{mcolor};padding:1px 6px;border-radius:3px;font-weight:600;">{mt['type'].upper()}</span>
                    <span style="font-size:0.95rem;margin-left:8px;{highlight}">{mt['title']}</span>
                    {'<span style="font-size:0.7rem;color:#ef4444;margin-left:6px;">⚠️ ALERT</span>' if is_trigger else ''}
                </div>
                """, unsafe_allow_html=True)
            with col_emotion:
                if emotions:
                    st.markdown(f'<div style="padding:6px 0;text-align:center;"><span style="font-weight:700;color:{emo_color};">{top_emo.upper()}</span> <span style="color:#64748b;">{top_score:.0%}</span></div>', unsafe_allow_html=True)
            with col_btn:
                if status == "done":
                    if st.button("→", key=f"mtg_{i}", use_container_width=True):
                        st.session_state.selected_meeting = i
                        st.session_state.playing = False
                        go_to("meeting")
                        st.rerun()

        # TRIGGER ALERT
        if trigger_reached and not st.session_state.triggered:
            st.session_state.playing = False
            st.session_state.triggered = True
            st.rerun()

        if st.session_state.triggered and not st.session_state.agent_done:
            tm = meetings[trigger_idx]
            emotions = get_meeting_emotions(emp_key, trigger_idx)
            top_emo = max(emotions, key=emotions.get)
            emo_color = EMOTION_COLORS.get(top_emo, "#ef4444")

            st.markdown("---")
            st.markdown(f"""
            <div class="alert-box">
                <div style="font-size: 2.5rem; margin-bottom: 8px;">⚠️</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #ef4444;">Emotional Distress Detected</div>
                <div style="font-size: 1.1rem; color: #fbbf24; margin: 8px 0; font-weight: 600;">{tm['title']} — {top_emo.upper()} at {emotions[top_emo]:.0%}</div>
                <div style="font-size: 0.9rem; color: #94a3b8;">Voice biomarkers from this meeting recording show significant emotional strain.</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            # Agent thinking steps
            st.markdown("### Vemo Responding...")
            st.markdown('<div class="scan-bar"></div>', unsafe_allow_html=True)

            steps = [
                ("🎙️", "Analyzing voice biomarkers", "emotion2vec+ processing meeting audio..."),
                ("🧠", "Clinical screening", "Kintsugi DAM evaluating depression/anxiety markers..."),
                ("📊", "Correlating biometrics", "Cross-referencing HR, HRV, respiratory rate..."),
                ("⚡", "Selecting intervention", "Matching patterns to skill library..."),
                ("🚀", "Executing actions", "Deploying personalized intervention..."),
            ]

            step_placeholder = st.empty()
            for j, (icon, title, desc) in enumerate(steps):
                with step_placeholder.container():
                    for k in range(j + 1):
                        cls = "agent-step done" if k < j else "agent-step active"
                        si, st_title, sd = steps[k]
                        check = "✓" if k < j else "..."
                        st.markdown(f'<div class="{cls}"><strong>{si} {st_title}</strong> {check}<div style="font-size:0.8rem;color:#64748b;">{sd}</div></div>', unsafe_allow_html=True)
                time.sleep(0.6)

            # Now stream the agent response
            st.markdown("---")
            st.markdown('<div class="vemo-active" style="margin-bottom:12px;"><span class="vemo-dot"></span> VEMO INTERVENING</div>', unsafe_allow_html=True)

            clinical = get_meeting_clinical(emp_key, trigger_idx)
            mid_min = (time_to_minutes(tm["start"]) + time_to_minutes(tm["end"])) // 2
            snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - mid_min))
            system_prompt = build_meeting_system_prompt(emp, tm, emotions, clinical, snap)

            api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
            if api_key:
                response_placeholder = st.empty()
                full_response = ""
                for chunk in stream_agent_response(system_prompt, "Intervene now. What are you doing?"):
                    full_response += chunk
                    response_placeholder.markdown(f'<div class="agent-card">\n\n{full_response}\n\n</div>', unsafe_allow_html=True)

                # Action buttons
                st.markdown("")
                st.markdown("### Quick Actions")
                a1, a2, a3, a4 = st.columns(4)
                with a1:
                    if st.button("🧘 Start Breathing", use_container_width=True, type="primary"):
                        st.toast("4-7-8 breathing protocol started. Follow the rhythm.", icon="🧘")
                with a2:
                    if st.button("📅 Block Calendar", use_container_width=True):
                        st.toast("15-min recovery block added before your next meeting.", icon="📅")
                with a3:
                    if st.button("🚶 Walking Break", use_container_width=True):
                        st.toast("10-min walking break scheduled. Your next meeting will get a 5-min late start notification.", icon="🚶")
                with a4:
                    if st.button("📊 Full Analysis", use_container_width=True):
                        st.session_state.selected_meeting = trigger_idx
                        st.session_state.agent_done = True
                        go_to("meeting")
                        st.rerun()

                st.session_state.agent_done = True

        elif st.session_state.triggered and st.session_state.agent_done:
            # Already triggered and handled — show summary nav
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📊 Generate Daily Insights", use_container_width=True, type="primary"):
                    go_to("summary")
                    st.rerun()
            with c2:
                if st.button("▶ Continue Day", use_container_width=True):
                    st.session_state.playing = True
                    st.session_state.play_minutes = time_to_minutes(meetings[trigger_idx]["end"]) + 30
                    st.session_state.triggered = False
                    st.session_state.agent_done = False
                    st.rerun()

        # Auto-play tick
        if st.session_state.playing and not trigger_reached:
            st_autorefresh(interval=400, limit=None, key="play_tick")
            advance = speed_map[speed_label]
            st.session_state.play_minutes = min(play_min + advance, 23 * 60)
            if play_min >= 18 * 60:
                st.session_state.playing = False

# ===========================================================================
# SCREEN 3: MEETING DETAIL
# ===========================================================================
elif st.session_state.screen == "meeting":
    emp_key = st.session_state.employee
    emp = EMPLOYEES[emp_key]
    bio_key = BIOMETRIC_MAP[emp_key]
    persona_data = all_data[bio_key]
    hourly_data = persona_data["hourly_data"]
    meeting_idx = st.session_state.selected_meeting
    m = emp["meetings"][meeting_idx]
    pcolor = PERSONA_COLORS[emp_key]

    emotions = get_meeting_emotions(emp_key, meeting_idx)
    clinical = get_meeting_clinical(emp_key, meeting_idx)
    top_emo = max(emotions, key=emotions.get)
    emo_color = EMOTION_COLORS.get(top_emo, "#94a3b8")

    mid_minutes = (time_to_minutes(m["start"]) + time_to_minutes(m["end"])) // 2
    snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - mid_minutes))

    # Header
    mcolor = MEETING_COLORS.get(m["type"], "#64748b")
    st.markdown(f"""
    <div style="text-align:center;padding:16px 0;">
        <span style="font-size:0.75rem;background:{mcolor}22;color:{mcolor};padding:3px 12px;border-radius:6px;font-weight:600;">{m['type'].upper()}</span>
        <div style="font-size:1.8rem;font-weight:700;color:#e2e8f0;margin:8px 0;">🎙️ {m['title']}</div>
        <div style="font-size:0.95rem;color:#94a3b8;">{m['start']}–{m['end']} · {', '.join(m['participants'])}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    emo_col, clin_col = st.columns(2)

    with emo_col:
        st.markdown('<div class="model-badge" style="background:#10b98122;color:#10b981;border:1px solid #10b981;">ANALYZED</div>', unsafe_allow_html=True)
        st.markdown("#### Voice Emotion Profile")
        st.caption("**emotion2vec+ large** — 9-class speech emotion recognition")

        st.markdown(f"""
        <div style="background:{emo_color}22;border:1px solid {emo_color};border-radius:12px;padding:12px;text-align:center;margin-bottom:8px;">
            <span style="font-size:1.6rem;font-weight:700;color:{emo_color};">{top_emo.upper()}</span>
            <span style="font-size:1.2rem;color:#94a3b8;margin-left:8px;">{emotions[top_emo]:.0%}</span>
        </div>
        """, unsafe_allow_html=True)
        fig_radar = make_emotion_radar(emotions)
        st.plotly_chart(fig_radar, use_container_width=True)

    with clin_col:
        st.markdown('<div class="model-badge" style="background:#10b98122;color:#10b981;border:1px solid #10b981;">ANALYZED</div>', unsafe_allow_html=True)
        st.markdown("#### Clinical Screening")
        st.caption("**Kintsugi DAM 3.1** — PHQ-9 depression & GAD-7 anxiety")

        dep_idx = min(clinical.get("depression", 0), 2)
        anx_idx = min(clinical.get("anxiety", 0), 3)
        dep_label = DEPRESSION_LEVELS[dep_idx]
        anx_label = ANXIETY_LEVELS[anx_idx]
        dep_color = SEVERITY_COLORS[dep_label]
        anx_color = SEVERITY_COLORS[anx_label]

        dep_c, anx_c = st.columns(2)
        with dep_c:
            st.markdown(f'<div class="severity-gauge"><div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;">Depression (PHQ-9)</div><div style="font-size:1.3rem;font-weight:700;color:{dep_color};margin-top:4px;">{dep_label}</div><div style="background:#0f172a;border-radius:4px;height:8px;margin-top:8px;"><div style="background:{dep_color};width:{max(dep_idx/2*100,10)}%;height:100%;border-radius:4px;"></div></div></div>', unsafe_allow_html=True)
        with anx_c:
            st.markdown(f'<div class="severity-gauge"><div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;">Anxiety (GAD-7)</div><div style="font-size:1.3rem;font-weight:700;color:{anx_color};margin-top:4px;">{anx_label}</div><div style="background:#0f172a;border-radius:4px;height:8px;margin-top:8px;"><div style="background:{anx_color};width:{max(anx_idx/3*100,10)}%;height:100%;border-radius:4px;"></div></div></div>', unsafe_allow_html=True)

        st.markdown("")
        st.markdown("**Biometrics During Meeting**")
        bv1, bv2, bv3 = st.columns(3)
        with bv1:
            st.metric("HR", f"{snap['heart_rate_bpm']:.0f} bpm")
        with bv2:
            st.metric("HRV", f"{snap['hrv_rmssd_ms']:.0f} ms")
        with bv3:
            st.metric("Resp", f"{snap['respiratory_rate_brpm']:.1f}")

    # Agent
    st.markdown("---")
    st.markdown('<div class="vemo-active" style="margin-bottom:12px;"><span class="vemo-dot"></span> VEMO ANALYSIS</div>', unsafe_allow_html=True)

    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        system_prompt = build_meeting_system_prompt(emp, m, emotions, clinical, snap)
        response_placeholder = st.empty()
        full_response = ""
        for chunk in stream_agent_response(system_prompt, "Analyze this meeting and intervene.", max_tokens=400):
            full_response += chunk
            response_placeholder.markdown(f'<div class="agent-card">\n\n{full_response}\n\n</div>', unsafe_allow_html=True)

    # Navigation
    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("← Day View", use_container_width=True):
            go_to("day")
            st.rerun()
    with n2:
        if meeting_idx < len(emp["meetings"]) - 1:
            if st.button(f"Next: {emp['meetings'][meeting_idx + 1]['title']} →", use_container_width=True):
                st.session_state.selected_meeting = meeting_idx + 1
                st.rerun()
    with n3:
        if st.button("📊 Daily Insights", use_container_width=True):
            go_to("summary")
            st.rerun()

# ===========================================================================
# SCREEN 4: DAILY SUMMARY
# ===========================================================================
elif st.session_state.screen == "summary":
    emp_key = st.session_state.employee
    emp = EMPLOYEES[emp_key]
    bio_key = BIOMETRIC_MAP[emp_key]
    persona_data = all_data[bio_key]
    summary = persona_data["daily_summary"]
    hourly_data = persona_data["hourly_data"]
    meetings = emp["meetings"]
    pcolor = PERSONA_COLORS[emp_key]

    st.markdown(f"## 📊 End-of-Day — {emp['name']}")
    st.caption(f"{emp['role']} · {len(meetings)} meetings · {sum(time_to_minutes(m['end']) - time_to_minutes(m['start']) for m in meetings) / 60:.1f}h on calls")

    meetings_with_emotions = []
    for i, m in enumerate(meetings):
        meetings_with_emotions.append({**m, "emotions": get_meeting_emotions(emp_key, i), "clinical": get_meeting_clinical(emp_key, i)})

    worst_idx = max(range(len(meetings_with_emotions)), key=lambda i: max(
        meetings_with_emotions[i]["emotions"].get("angry", 0),
        meetings_with_emotions[i]["emotions"].get("fearful", 0),
        meetings_with_emotions[i]["emotions"].get("sad", 0),
    ))

    # Emotional arc
    st.markdown("### Emotional Arc")
    n_cols = min(len(meetings), 7)
    arc_cols = st.columns(n_cols)
    for i, m in enumerate(meetings_with_emotions):
        with arc_cols[i % n_cols]:
            top = max(m["emotions"], key=m["emotions"].get)
            emo_color = EMOTION_COLORS.get(top, "#94a3b8")
            is_worst = i == worst_idx
            border = "border:2px solid #ef4444;" if is_worst else "border:1px solid #1e293b;"
            st.markdown(f"""
            <div style="background:#0f172a;border-radius:10px;padding:10px;text-align:center;margin-bottom:6px;{border}">
                <div style="font-size:0.65rem;color:#64748b;">{m['start']}</div>
                <div style="font-size:0.75rem;font-weight:600;color:#e2e8f0;margin:2px 0;">{m['title'][:18]}</div>
                <div style="font-size:1rem;font-weight:700;color:{emo_color};">{top.upper()}</div>
                <div style="font-size:0.75rem;color:#94a3b8;">{m['emotions'][top]:.0%}</div>
                {'<div style="font-size:0.6rem;color:#ef4444;margin-top:2px;">⚠ CONCERN</div>' if is_worst else ''}
            </div>
            """, unsafe_allow_html=True)

    # Chart
    st.markdown("---")
    fig = make_day_chart(hourly_data, meetings, pcolor, selected_meeting_idx=worst_idx)
    st.plotly_chart(fig, use_container_width=True)

    # Agent briefing
    st.markdown("---")
    st.markdown('<div class="vemo-active" style="margin-bottom:12px;"><span class="vemo-dot"></span> END-OF-DAY BRIEFING</div>', unsafe_allow_html=True)

    worst_snap_min = (time_to_minutes(meetings[worst_idx]["start"]) + time_to_minutes(meetings[worst_idx]["end"])) // 2
    worst_snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - worst_snap_min))

    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        system_prompt = build_daily_system_prompt(emp, meetings_with_emotions, summary, worst_snap)
        response_placeholder = st.empty()
        full_response = ""
        for chunk in stream_agent_response(system_prompt, "Give me my end-of-day briefing.", max_tokens=800):
            full_response += chunk
            response_placeholder.markdown(f'<div class="agent-card">\n\n{full_response}\n\n</div>', unsafe_allow_html=True)

    # Weekly preview
    st.markdown("---")
    st.markdown("### Weekly Trend")
    week_data = get_week_daily_scores(emp_key)
    fig_week = make_week_chart(week_data, emp_key)
    st.plotly_chart(fig_week, use_container_width=True)

    # Navigation
    st.markdown("---")
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("← Day View", use_container_width=True):
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
