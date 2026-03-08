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
    "maya": "#6366f1", "derek": "#f59e0b", "lucia": "#10b981",
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
    "maya": "maya", "derek": "derek", "lucia": "lucia",
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
# Monthly trend data (6 months)
# ---------------------------------------------------------------------------
MONTHS = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def get_monthly_trends(employee_key):
    random.seed(hash(f"{employee_key}_monthly_v1"))
    trajectories = {
        "maya": {
            "stress": [0.25, 0.30, 0.38, 0.48, 0.55, 0.62],
            "recovery": [72, 65, 55, 42, 35, 28],
            "meeting_hours": [4.2, 4.5, 5.0, 5.5, 5.8, 6.2],
            "mood": [0.65, 0.55, 0.42, 0.30, 0.22, 0.18],
        },
        "derek": {
            "stress": [0.30, 0.42, 0.35, 0.50, 0.58, 0.65],
            "recovery": [68, 55, 62, 48, 40, 35],
            "meeting_hours": [5.0, 5.5, 5.2, 6.0, 6.5, 7.0],
            "mood": [0.50, 0.38, 0.45, 0.30, 0.25, 0.18],
        },
        "lucia": {
            "stress": [0.15, 0.12, 0.18, 0.14, 0.10, 0.12],
            "recovery": [78, 82, 75, 80, 85, 82],
            "meeting_hours": [3.5, 3.8, 3.5, 3.2, 3.5, 3.0],
            "mood": [0.72, 0.75, 0.68, 0.78, 0.80, 0.82],
        },
    }
    t = trajectories.get(employee_key, trajectories["lucia"])
    data = []
    for i, month in enumerate(MONTHS):
        data.append({
            "month": month,
            "stress": min(1, max(0, t["stress"][i] + random.uniform(-0.03, 0.03))),
            "recovery": max(10, min(100, t["recovery"][i] + random.randint(-3, 3))),
            "meeting_hours": max(1, t["meeting_hours"][i] + random.uniform(-0.2, 0.2)),
            "mood": min(1, max(0, t["mood"][i] + random.uniform(-0.03, 0.03))),
        })
    return data

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_persona_data():
    with open(os.path.join(os.path.dirname(__file__), "persona_data.json")) as f:
        return json.load(f)

@st.cache_data
def load_skills():
    skills_dir = os.path.join(os.path.dirname(__file__), "skills")
    skills = {}
    for f in sorted(os.listdir(skills_dir)):
        if f.endswith(".md"):
            with open(os.path.join(skills_dir, f)) as fh:
                skills[f.replace(".md", "")] = fh.read()
    return skills

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
# Intervention system — skills, voice input, interactive trigger
# ---------------------------------------------------------------------------
SKILL_ICONS = {
    "stress-resilience": "🧘", "recovery-coach": "💚", "sleep-analyst": "😴",
    "heart-health-scorecard": "❤️", "inflammation-tracker": "🔬",
    "longevity-protocol": "🧬", "morning-briefing": "🌅",
}
SKILL_LABELS = {
    "stress-resilience": "Stress Resilience", "recovery-coach": "Recovery Coach",
    "sleep-analyst": "Sleep Analyst", "heart-health-scorecard": "Heart Health",
    "inflammation-tracker": "Inflammation Tracker", "longevity-protocol": "Longevity Protocol",
    "morning-briefing": "Morning Briefing",
}

VOICE_SUGGESTIONS = {
    "maya": [
        "I'm exhausted. Back to back meetings all day and I can't get any actual coding done. That client call was really intense and I feel completely drained.",
        "I feel like I'm drowning. Every meeting adds more tasks but I never get time to do the actual work. My head is pounding.",
    ],
    "derek": [
        "That stakeholder review was brutal. I feel like I'm being pulled in ten directions and nothing I present is good enough. My heart was racing the whole time.",
        "I'm so anxious about the board metrics. I keep switching between projects and I can't think deeply about anything anymore.",
    ],
    "lucia": [
        "I'm actually feeling pretty good today. The team is performing well and I managed to take my walking breaks between meetings.",
    ],
}

def select_skills(employee_key, emotions, clinical, biometric_snap, skills_dict):
    """Select 2-4 relevant skills based on trigger context."""
    selected = []
    top_emo = max(emotions, key=emotions.get)

    if top_emo in ("angry", "fearful", "sad", "disgusted"):
        selected.append("stress-resilience")

    hr = biometric_snap.get("heart_rate_bpm", 70)
    hrv = biometric_snap.get("hrv_rmssd_ms", 50)
    if hr > 80 or hrv < 40:
        selected.append("heart-health-scorecard")

    if clinical.get("depression", 0) >= 1 or clinical.get("anxiety", 0) >= 2:
        selected.append("recovery-coach")

    if clinical.get("anxiety", 0) >= 2 or clinical.get("depression", 0) >= 2:
        selected.append("inflammation-tracker")

    selected.append("sleep-analyst")

    if clinical.get("depression", 0) >= 2 and clinical.get("anxiety", 0) >= 2:
        selected.append("longevity-protocol")

    seen = set()
    unique = []
    for s in selected:
        if s not in seen and s in skills_dict:
            seen.add(s)
            unique.append(s)
    return unique[:4]

def build_intervention_prompt(employee, meeting, emotions, clinical, whoop_snap, voice_input, skills_text):
    top = max(emotions, key=emotions.get)
    dep_label = DEPRESSION_LEVELS[min(clinical.get("depression", 0), 2)]
    anx_label = ANXIETY_LEVELS[min(clinical.get("anxiety", 0), 3)]
    first_name = employee['name'].split()[0]

    return f"""You are Vemo, a workplace wellbeing AI agent. You detected concerning emotional patterns in a meeting recording. The employee has just spoken to you about how they're feeling.

You are AGENTIC. You don't just advise — you take actions. You have access to the employee's calendar, wellness tools, and notification system.

## Employee
{employee['name']}, {employee['role']} on {employee['team']} team
{employee['bio']}

## Meeting Just Analyzed
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

## Voice Sample Analysis
You just analyzed a live voice sample from {first_name}. The emotion and clinical results above were extracted from their voice patterns.

## Your Skill Protocols (USE THESE — reference them by name)
{skills_text}

## Response Format — Be SPECIFIC, WARM, and AGENTIC:

**HEY {first_name.upper()}, I NEED TO FLAG SOMETHING.** 2 sentences about what the voice analysis revealed. Be direct but warm — name what the models detected and why it matters.

**WHAT YOUR BODY IS TELLING ME:** 2 sentences connecting the voice biomarkers + wearable biometrics. Make the data human — e.g., "Your voice carried 40% fearful markers while your heart rate hit 95 and HRV dropped to 28 — your body was in fight-or-flight the entire call."

**ACTIVATING NOW:**
- [Specific action from a named skill protocol — e.g., "Per **Stress Resilience Protocol**: Starting 4-7-8 breathing — inhale 4s, hold 7s, exhale 8s, 3 cycles"]
- [Calendar action — e.g., "Blocking your next 30 minutes as recovery time"]
- [Another skill-based action — e.g., "Per **Recovery Coach**: Lowering your strain target from 14 to 8 for today"]

**TONIGHT — YOUR RECOVERY PROTOCOL:**
- [2 specific recovery actions drawn from the skills, personalized to their situation]

**PATTERN WATCH:** One sentence about what Vemo will monitor going forward this week.

Be direct, warm, and human. You're talking to someone whose voice just revealed distress. Name the skill protocols you're using. Reference specific numbers from the biomarkers."""

# ---------------------------------------------------------------------------
# Action dialogs (modals)
# ---------------------------------------------------------------------------
@st.dialog("🧘 Breathing Exercise", width="large")
def show_breathing_dialog():
    import streamlit.components.v1 as components
    breathing_html = """
    <div id="breathe-app" style="text-align:center;padding:40px 20px;background:linear-gradient(135deg,#0c1222 0%,#1a1a2e 100%);border-radius:16px;border:1px solid #6366f1;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
        <div style="font-size:0.7rem;color:#6366f1;letter-spacing:0.15em;font-weight:700;margin-bottom:6px;">STRESS RESILIENCE PROTOCOL</div>
        <div style="font-size:1.1rem;color:#e2e8f0;font-weight:600;margin-bottom:24px;">4-7-8 Breathing Exercise</div>
        <div id="circle-wrap" style="position:relative;width:180px;height:180px;margin:0 auto 24px auto;">
            <div id="breathe-circle" style="width:180px;height:180px;border-radius:50%;background:radial-gradient(circle,#6366f140,#6366f110);border:3px solid #6366f1;display:flex;align-items:center;justify-content:center;transition:transform 4s ease-in-out, border-color 0.5s;transform:scale(0.6);">
                <div>
                    <div id="phase-text" style="font-size:1.4rem;font-weight:700;color:#e2e8f0;">Ready</div>
                    <div id="count-text" style="font-size:2.5rem;font-weight:800;color:#6366f1;line-height:1;margin-top:4px;"></div>
                </div>
            </div>
        </div>
        <div id="cycle-info" style="font-size:0.85rem;color:#94a3b8;margin-bottom:16px;">3 cycles — press Start to begin</div>
        <button id="start-btn" onclick="startBreathing()" style="background:linear-gradient(135deg,#4f46e5,#6366f1);color:white;border:none;padding:12px 36px;border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;letter-spacing:0.03em;">Start</button>
    </div>
    <script>
    const phases = [
        {name:"Inhale", duration:4, scale:1.0, color:"#6366f1"},
        {name:"Hold", duration:7, scale:1.0, color:"#f59e0b"},
        {name:"Exhale", duration:8, scale:0.6, color:"#10b981"}
    ];
    const totalCycles = 3;
    let running = false;
    function startBreathing() {
        if (running) return;
        running = true;
        document.getElementById("start-btn").style.display = "none";
        runCycle(0);
    }
    function runCycle(cycle) {
        if (cycle >= totalCycles) {
            document.getElementById("phase-text").textContent = "Complete";
            document.getElementById("count-text").textContent = "\\u2713";
            document.getElementById("breathe-circle").style.borderColor = "#10b981";
            document.getElementById("breathe-circle").style.transform = "scale(0.8)";
            document.getElementById("cycle-info").textContent = "Great work. Your nervous system is resetting.";
            running = false;
            return;
        }
        document.getElementById("cycle-info").textContent = "Cycle " + (cycle+1) + " of " + totalCycles;
        runPhase(0, cycle);
    }
    function runPhase(pi, cycle) {
        if (pi >= phases.length) { runCycle(cycle+1); return; }
        const p = phases[pi];
        const circle = document.getElementById("breathe-circle");
        const phaseEl = document.getElementById("phase-text");
        const countEl = document.getElementById("count-text");
        phaseEl.textContent = p.name;
        circle.style.borderColor = p.color;
        circle.style.transition = "transform " + (p.name==="Hold"?"0.3":p.duration) + "s ease-in-out, border-color 0.5s";
        circle.style.transform = "scale(" + p.scale + ")";
        let sec = p.duration;
        countEl.textContent = sec;
        countEl.style.color = p.color;
        const iv = setInterval(()=>{
            sec--;
            if(sec<=0){clearInterval(iv);runPhase(pi+1,cycle);}
            else{countEl.textContent=sec;}
        },1000);
    }
    </script>
    """
    components.html(breathing_html, height=420)

@st.dialog("📅 Calendar Block", width="large")
def show_calendar_dialog(emp, trigger_meeting, meetings):
    trigger_end = time_to_minutes(trigger_meeting["end"])
    next_meeting = None
    for mt_next in meetings:
        if time_to_minutes(mt_next["start"]) > trigger_end:
            next_meeting = mt_next
            break
    block_start_str = f"{trigger_end // 60:02d}:{trigger_end % 60:02d}"
    block_end_min = trigger_end + 15
    block_end_str = f"{block_end_min // 60:02d}:{block_end_min % 60:02d}"

    cal_placeholder = st.empty()
    steps_text = [
        "Connecting to Google Calendar...",
        "Creating recovery block...",
        f"Notifying attendees of {next_meeting['title'] if next_meeting else 'next meeting'} about 5-min late start...",
        "Calendar updated.",
    ]
    for si, step_msg in enumerate(steps_text):
        with cal_placeholder.container():
            prev_html = "".join(
                f'<div style="font-size:0.85rem;color:#64748b;padding:2px 0;">✓ {steps_text[k]}</div>'
                for k in range(si)
            )
            st.markdown(f"""
            <div style="background:#0f172a;border:1px solid #10b981;border-radius:12px;padding:20px 24px;">
                <div style="font-size:0.7rem;color:#10b981;letter-spacing:0.12em;font-weight:700;margin-bottom:12px;">VEMO CALENDAR ACTION</div>
                {prev_html}
                <div style="font-size:0.85rem;color:#e2e8f0;padding:2px 0;">⏳ {step_msg}</div>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(0.6)

    first_name = emp['name'].split()[0]
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1e293b,#0f172a);border:2px solid #10b981;border-radius:16px;padding:24px 28px;margin-top:12px;">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
            <div style="width:12px;height:40px;border-radius:3px;background:#10b981;"></div>
            <div>
                <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">Recovery Block — {first_name}</div>
                <div style="font-size:0.8rem;color:#94a3b8;">Added by Vemo Wellbeing Agent</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:#0f172a;border-radius:8px;padding:12px;">
                <div style="font-size:0.65rem;color:#64748b;text-transform:uppercase;">Time</div>
                <div style="font-size:1rem;font-weight:600;color:#e2e8f0;">{block_start_str} – {block_end_str}</div>
                <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px;">15 minutes</div>
            </div>
            <div style="background:#0f172a;border-radius:8px;padding:12px;">
                <div style="font-size:0.65rem;color:#64748b;text-transform:uppercase;">Before</div>
                <div style="font-size:1rem;font-weight:600;color:#e2e8f0;">{next_meeting['title'] if next_meeting else 'End of day'}</div>
                <div style="font-size:0.75rem;color:#f59e0b;margin-top:2px;">5-min late start sent</div>
            </div>
        </div>
        <div style="margin-top:14px;padding:10px 14px;background:#10b98112;border-radius:8px;border:1px solid #10b98130;">
            <div style="font-size:0.8rem;color:#10b981;font-weight:600;">Description</div>
            <div style="font-size:0.8rem;color:#cbd5e1;margin-top:4px;line-height:1.5;">
                Auto-scheduled recovery time after elevated stress detected in {trigger_meeting['title']}.
                Suggested: step away from screen, hydrate, 2-min stretch, or use Vemo breathing exercise.
            </div>
        </div>
        <div style="margin-top:12px;text-align:center;">
            <span style="font-size:0.7rem;color:#10b981;font-weight:600;letter-spacing:0.1em;">✓ CALENDAR UPDATED</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.dialog("🚶 Walking Break", width="large")
def show_walking_dialog():
    import streamlit.components.v1 as components
    walking_html = """
    <div style="text-align:center;padding:36px 20px;background:linear-gradient(135deg,#0c1222,#0f2a1a);border-radius:16px;border:1px solid #10b981;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
        <div style="font-size:0.7rem;color:#10b981;letter-spacing:0.15em;font-weight:700;margin-bottom:6px;">RECOVERY COACH PROTOCOL</div>
        <div style="font-size:1.1rem;color:#e2e8f0;font-weight:600;margin-bottom:20px;">10-Minute Walking Break</div>
        <div style="font-size:4rem;margin-bottom:8px;">🚶</div>
        <div id="walk-timer" style="font-size:3rem;font-weight:800;color:#10b981;letter-spacing:2px;margin-bottom:8px;">10:00</div>
        <div id="walk-status" style="font-size:0.85rem;color:#94a3b8;margin-bottom:20px;">Step away from your screen. Walk, stretch, breathe.</div>
        <div style="display:flex;justify-content:center;gap:20px;margin-bottom:20px;">
            <div style="text-align:center;">
                <div style="font-size:1.5rem;font-weight:700;color:#6366f1;" id="steps-count">0</div>
                <div style="font-size:0.65rem;color:#64748b;">EST. STEPS</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.5rem;font-weight:700;color:#f59e0b;" id="cal-count">0</div>
                <div style="font-size:0.65rem;color:#64748b;">EST. CAL</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:1.5rem;font-weight:700;color:#10b981;">+5</div>
                <div style="font-size:0.65rem;color:#64748b;">HRV BOOST</div>
            </div>
        </div>
        <div style="background:#1e293b;border-radius:8px;padding:10px 16px;max-width:340px;margin:0 auto;">
            <div style="font-size:0.75rem;color:#f59e0b;font-weight:600;">Next meeting notified</div>
            <div style="font-size:0.8rem;color:#94a3b8;">5-min late start notification sent</div>
        </div>
        <br/>
        <button id="walk-btn" onclick="startWalk()" style="background:linear-gradient(135deg,#065f46,#10b981);color:white;border:none;padding:12px 36px;border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;">Start Timer</button>
    </div>
    <script>
    let walkRunning = false;
    function startWalk() {
        if (walkRunning) return;
        walkRunning = true;
        document.getElementById("walk-btn").style.display = "none";
        let total = 600;
        const timerEl = document.getElementById("walk-timer");
        const stepsEl = document.getElementById("steps-count");
        const calEl = document.getElementById("cal-count");
        const statusEl = document.getElementById("walk-status");
        const iv = setInterval(()=>{
            total--;
            const m = Math.floor(total/60);
            const s = total%60;
            timerEl.textContent = m + ":" + (s<10?"0":"") + s;
            const elapsed = 600 - total;
            stepsEl.textContent = Math.floor(elapsed * 1.7);
            calEl.textContent = Math.floor(elapsed * 0.08);
            if(total<=0){
                clearInterval(iv);
                timerEl.textContent = "Done!";
                timerEl.style.color = "#10b981";
                statusEl.textContent = "Great break. Your recovery score is updating.";
            }
        }, 1000);
    }
    </script>
    """
    components.html(walking_html, height=440)

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

def make_monthly_chart(monthly_data):
    months = [d["month"] for d in monthly_data]
    stress = [d["stress"] for d in monthly_data]
    mood = [d["mood"] for d in monthly_data]
    recovery = [d["recovery"] / 100 for d in monthly_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=stress, name="Stress", line=dict(color="#ef4444", width=3),
                             fill="tozeroy", fillcolor="rgba(239,68,68,0.08)", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=mood, name="Mood", line=dict(color="#10b981", width=3),
                             fill="tozeroy", fillcolor="rgba(16,185,129,0.08)", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=recovery, name="Recovery", line=dict(color="#6366f1", width=2.5),
                             mode="lines+markers"))
    fig.update_layout(
        height=300, margin=dict(l=0, r=0, t=20, b=0),
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
    @keyframes mic-pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.5); } 50% { box-shadow: 0 0 30px 15px rgba(99,102,241,0.15); } }
    .mic-circle {
        width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #4f46e5, #6366f1);
        display: inline-flex; align-items: center; justify-content: center; font-size: 2rem;
        animation: mic-pulse 2s ease-in-out infinite; margin: 16px auto;
    }
    .voice-area {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 2px solid #6366f1; border-radius: 16px; padding: 28px 32px; text-align: center;
    }
    .voice-transcript {
        background: #0f172a; border: 1px solid #334155; border-radius: 12px;
        padding: 16px 20px; margin: 12px 0; text-align: left;
        font-style: italic; color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;
    }
    .skill-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: #10b98115; border: 1px solid #10b981; border-radius: 20px;
        padding: 6px 14px; font-size: 0.75rem; color: #10b981; font-weight: 600; margin: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# SESSION STATE
# ===========================================================================
defaults = {
    "screen": "intro", "employee": None, "selected_meeting": None,
    "view_mode": "day", "playing": False, "play_minutes": 7 * 60,
    "triggered": False, "agent_done": False,
    "intervention_step": "alert", "voice_input": "",
    "active_action": None, "intervention_response": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

all_data = load_persona_data()
all_skills = load_skills()

def go_to(screen):
    st.session_state.screen = screen

# ===========================================================================
# SCREEN 0: INTRO — TECH STACK & CLINICAL VALIDATION
# ===========================================================================
if st.session_state.screen == "intro":
    st.markdown("""
    <div style="text-align:center;padding:30px 0 10px 0;">
        <div style="font-size:2.8rem;font-weight:800;color:#e2e8f0;letter-spacing:-1px;">🎙️ Vemo</div>
        <div style="font-size:1.1rem;color:#94a3b8;margin-top:4px;">Workplace Wellbeing Intelligence for the Longevity Era</div>
    </div>
    """, unsafe_allow_html=True)

    # --- 5 Pillars of Longevity ---
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f172a,#1a1a2e);border:1px solid #6366f1;border-radius:16px;padding:24px 28px;margin:16px 0;">
        <div style="text-align:center;margin-bottom:16px;">
            <div style="font-size:0.7rem;color:#6366f1;letter-spacing:0.15em;font-weight:700;">THE FIVE PILLARS OF LONGEVITY</div>
            <div style="font-size:0.85rem;color:#94a3b8;margin-top:4px;">Work is where these pillars silently collapse. Vemo protects them.</div>
        </div>
        <div style="display:flex;justify-content:center;gap:16px;flex-wrap:wrap;">
            <div style="text-align:center;background:#1e293b;border-radius:12px;padding:16px 14px;min-width:120px;border:1px solid #334155;">
                <div style="font-size:1.8rem;">😴</div>
                <div style="font-size:0.85rem;font-weight:700;color:#6366f1;margin:4px 0;">Sleep</div>
                <div style="font-size:0.7rem;color:#94a3b8;line-height:1.4;">Work stress is the #1 driver of poor sleep quality</div>
            </div>
            <div style="text-align:center;background:#1e293b;border-radius:12px;padding:16px 14px;min-width:120px;border:1px solid #334155;">
                <div style="font-size:1.8rem;">🧘</div>
                <div style="font-size:0.85rem;font-weight:700;color:#ef4444;margin:4px 0;">Stress</div>
                <div style="font-size:0.7rem;color:#94a3b8;line-height:1.4;">Chronic cortisol from back-to-back meetings drives inflammation</div>
            </div>
            <div style="text-align:center;background:#1e293b;border-radius:12px;padding:16px 14px;min-width:120px;border:1px solid #334155;">
                <div style="font-size:1.8rem;">🏃</div>
                <div style="font-size:0.85rem;font-weight:700;color:#10b981;margin:4px 0;">Exercise</div>
                <div style="font-size:0.7rem;color:#94a3b8;line-height:1.4;">Meeting overload eliminates movement from the day</div>
            </div>
            <div style="text-align:center;background:#1e293b;border-radius:12px;padding:16px 14px;min-width:120px;border:1px solid #334155;">
                <div style="font-size:1.8rem;">🥗</div>
                <div style="font-size:0.85rem;font-weight:700;color:#f59e0b;margin:4px 0;">Nutrition</div>
                <div style="font-size:0.7rem;color:#94a3b8;line-height:1.4;">Stressed workers skip meals or stress-eat through the day</div>
            </div>
            <div style="text-align:center;background:#1e293b;border-radius:12px;padding:16px 14px;min-width:120px;border:1px solid #334155;">
                <div style="font-size:1.8rem;">🤝</div>
                <div style="font-size:0.85rem;font-weight:700;color:#ec4899;margin:4px 0;">Connection</div>
                <div style="font-size:0.7rem;color:#94a3b8;line-height:1.4;">7 calls/day yet more isolated than ever — digital loneliness</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Problem ---
    st.markdown("""
    <div style="background:linear-gradient(135deg,#451a0310,#0f172a);border:1px solid #ef4444;border-radius:16px;padding:22px 28px;margin:12px 0;">
        <div style="font-size:0.7rem;color:#ef4444;letter-spacing:0.12em;font-weight:700;margin-bottom:8px;">THE SILENT CRISIS</div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div style="flex:1;min-width:200px;">
                <div style="font-size:2.2rem;font-weight:800;color:#ef4444;">76%</div>
                <div style="font-size:0.8rem;color:#cbd5e1;">of workers report at least one symptom of a mental health condition</div>
            </div>
            <div style="flex:1;min-width:200px;">
                <div style="font-size:2.2rem;font-weight:800;color:#f59e0b;">6.5h</div>
                <div style="font-size:0.8rem;color:#cbd5e1;">average daily screen time on video calls for remote workers post-COVID</div>
            </div>
            <div style="flex:1;min-width:200px;">
                <div style="font-size:2.2rem;font-weight:800;color:#6366f1;">67%</div>
                <div style="font-size:0.8rem;color:#cbd5e1;">of burnout cases go undetected — these are the silent sufferers</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- How it works ---
    st.markdown("""
    <div style="background:linear-gradient(135deg,#064e3b10,#0f172a);border:1px solid #10b981;border-radius:16px;padding:22px 28px;margin:12px 0;">
        <div style="font-size:0.7rem;color:#10b981;letter-spacing:0.12em;font-weight:700;margin-bottom:10px;">HOW VEMO WORKS</div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <div style="flex:1;min-width:150px;background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.5rem;">📅</div>
                <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;margin:4px 0;">Connects</div>
                <div style="font-size:0.7rem;color:#94a3b8;">Syncs with your calendar. Silent. Passive. Always on.</div>
            </div>
            <div style="flex:1;min-width:150px;background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.5rem;">🎙️</div>
                <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;margin:4px 0;">Listens</div>
                <div style="font-size:0.7rem;color:#94a3b8;">Records every call. Analyzes voice as a vital sign.</div>
            </div>
            <div style="flex:1;min-width:150px;background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.5rem;">🧠</div>
                <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;margin:4px 0;">Detects</div>
                <div style="font-size:0.7rem;color:#94a3b8;">Acoustic models score emotion, depression, anxiety.</div>
            </div>
            <div style="flex:1;min-width:150px;background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.5rem;">⚡</div>
                <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;margin:4px 0;">Intervenes</div>
                <div style="font-size:0.7rem;color:#94a3b8;">Real-time agentic AI takes action when it matters.</div>
            </div>
            <div style="flex:1;min-width:150px;background:#1e293b;border-radius:10px;padding:14px;text-align:center;">
                <div style="font-size:1.5rem;">📊</div>
                <div style="font-size:0.8rem;font-weight:600;color:#e2e8f0;margin:4px 0;">Tracks</div>
                <div style="font-size:0.7rem;color:#94a3b8;">Daily, weekly, monthly reports across all 5 pillars.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Tech + Skills in two columns ---
    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.markdown("""
        <div style="background:#1e293b;border-radius:12px;padding:18px 22px;border:1px solid #334155;">
            <div style="font-size:0.7rem;color:#6366f1;letter-spacing:0.1em;font-weight:700;margin-bottom:10px;">VOICE ACOUSTIC MODELS</div>
            <div style="margin-bottom:12px;">
                <div style="font-size:0.9rem;font-weight:700;color:#e2e8f0;">emotion2vec+ large</div>
                <div style="font-size:0.75rem;color:#94a3b8;line-height:1.5;">9-class speech emotion recognition. Audio → spectrograms → emotion classification. Trained on 40,000+ hours.</div>
            </div>
            <div style="margin-bottom:12px;">
                <div style="font-size:0.9rem;font-weight:700;color:#e2e8f0;">Kintsugi DAM 3.1</div>
                <div style="font-size:0.75rem;color:#94a3b8;line-height:1.5;">Clinically validated voice biomarker analysis. Correlates with <strong style="color:#cbd5e1;">PHQ-9</strong> (depression) and <strong style="color:#cbd5e1;">GAD-7</strong> (anxiety). FDA Breakthrough Device Designation. 30-second voice sample → clinical-grade scores.</div>
            </div>
            <div>
                <div style="font-size:0.9rem;font-weight:700;color:#e2e8f0;">Whoop Biometrics</div>
                <div style="font-size:0.75rem;color:#94a3b8;line-height:1.5;">HR, HRV, respiratory rate, recovery, sleep. Cross-referenced with voice biomarkers for multi-modal validation.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        st.markdown("""
        <div style="background:#1e293b;border-radius:12px;padding:18px 22px;border:1px solid #334155;">
            <div style="font-size:0.7rem;color:#10b981;letter-spacing:0.1em;font-weight:700;margin-bottom:8px;">AGENTIC AI</div>
            <div style="font-size:0.75rem;color:#94a3b8;line-height:1.6;">
                Powered by <strong style="color:#cbd5e1;">Claude Opus</strong>. Streams real-time interventions with full biometric + voice context. Takes action — blocks calendars, starts breathing exercises, adjusts strain targets. References skill protocols by name with personalized data.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
        <div style="background:#1e293b;border-radius:12px;padding:18px 22px;border:1px solid #334155;">
            <div style="font-size:0.7rem;color:#10b981;letter-spacing:0.1em;font-weight:700;margin-bottom:10px;">BETTERNESS SKILLS — 7 LONGEVITY PROTOCOLS</div>
            <div style="display:flex;flex-direction:column;gap:8px;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">🧘</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Stress Resilience</span><br/><span style="font-size:0.7rem;color:#94a3b8;">Breathing protocols, nervous system regulation</span></div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">💚</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Recovery Coach</span><br/><span style="font-size:0.7rem;color:#94a3b8;">Strain management, workload balancing</span></div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">😴</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Sleep Analyst</span><br/><span style="font-size:0.7rem;color:#94a3b8;">Sleep debt tracking, circadian rhythm support</span></div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">❤️</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Heart Health Scorecard</span><br/><span style="font-size:0.7rem;color:#94a3b8;">HR/HRV analysis, cardiovascular strain alerts</span></div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">🔬</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Inflammation Tracker</span><br/><span style="font-size:0.7rem;color:#94a3b8;">Chronic stress markers, anti-inflammatory interventions</span></div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">🧬</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Longevity Protocol</span><br/><span style="font-size:0.7rem;color:#94a3b8;">Multi-pillar intervention for severe cases</span></div>
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">🌅</span>
                    <div><span style="font-size:0.85rem;font-weight:600;color:#e2e8f0;">Morning Briefing</span><br/><span style="font-size:0.7rem;color:#94a3b8;">Proactive daily planning from recovery + sleep data</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    if st.button("Enter Vemo →", type="primary", use_container_width=True):
        go_to("select")
        st.rerun()

# ===========================================================================
# SCREEN 1: EMPLOYEE SELECTION
# ===========================================================================
elif st.session_state.screen == "select":
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
                    st.session_state.intervention_step = "alert"
                    st.session_state.voice_input = ""
                    st.session_state.active_action = None
                    st.session_state.intervention_response = ""
                    st.session_state.view_mode = "trends"
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
            st.session_state.triggered = False
            st.session_state.agent_done = False
            st.session_state.intervention_step = "alert"
            st.session_state.voice_input = ""
            st.session_state.active_action = None
            st.session_state.intervention_response = ""
            go_to("select")
            st.rerun()

    # View toggle
    col_view, col_play, col_speed = st.columns([2, 1, 1])
    with col_view:
        view_options = ["Day", "Week", "Trends"]
        current_default = {"day": "Day", "week": "Week", "trends": "Trends"}.get(st.session_state.view_mode, "Day")
        view = st.segmented_control("View", view_options, default=current_default, label_visibility="collapsed")
        if view:
            st.session_state.view_mode = view.lower()

    # ---- TRENDS VIEW ----
    if st.session_state.view_mode == "trends":
        monthly = get_monthly_trends(emp_key)
        st.markdown("### 6-Month Trajectory")
        fig_monthly = make_monthly_chart(monthly)
        st.plotly_chart(fig_monthly, use_container_width=True)

        # Monthly cards
        month_cols = st.columns(6)
        for i, md in enumerate(monthly):
            with month_cols[i]:
                stress_color = "#ef4444" if md["stress"] > 0.5 else "#f59e0b" if md["stress"] > 0.3 else "#10b981"
                rec_color = "#ef4444" if md["recovery"] < 34 else "#f59e0b" if md["recovery"] < 67 else "#10b981"
                is_current = (i == len(monthly) - 1)
                border = "border: 2px solid #6366f1;" if is_current else "border: 1px solid #1e293b;"
                st.markdown(f"""
                <div style="background: #1e293b; border-radius: 10px; padding: 12px; text-align: center; {border}">
                    <div style="font-size: 0.8rem; font-weight: 600; color: #e2e8f0;">{md['month']}{'  ← now' if is_current else ''}</div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: {stress_color}; margin: 4px 0;">{md['stress']:.0%}</div>
                    <div style="font-size: 0.6rem; color: #64748b;">STRESS</div>
                    <div style="font-size: 0.85rem; color: {rec_color}; margin-top: 4px;">{md['recovery']}%</div>
                    <div style="font-size: 0.6rem; color: #64748b;">RECOVERY</div>
                    <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px;">{md['meeting_hours']:.1f}h/day</div>
                </div>
                """, unsafe_allow_html=True)

        # Trajectory insight
        first_stress = monthly[0]["stress"]
        last_stress = monthly[-1]["stress"]
        delta = last_stress - first_stress
        if delta > 0.15:
            trajectory = "DECLINING"
            traj_color = "#ef4444"
            traj_msg = f"Stress has increased {delta:.0%} over 6 months. Meeting hours up from {monthly[0]['meeting_hours']:.1f}h to {monthly[-1]['meeting_hours']:.1f}h/day. Recovery trending down. Intervention recommended."
        elif delta < -0.05:
            trajectory = "IMPROVING"
            traj_color = "#10b981"
            traj_msg = f"Positive trajectory. Stress down {abs(delta):.0%} over 6 months. Recovery stable at {monthly[-1]['recovery']}%. Healthy patterns sustained."
        else:
            trajectory = "STABLE"
            traj_color = "#6366f1"
            traj_msg = f"Metrics holding steady. Stress at {last_stress:.0%}, recovery at {monthly[-1]['recovery']}%. Continue monitoring."

        st.markdown(f"""
        <div style="background: {traj_color}10; border: 1px solid {traj_color}; border-radius: 12px; padding: 16px 20px; margin-top: 16px;">
            <span style="font-size: 0.7rem; font-weight: 700; color: {traj_color}; letter-spacing: 0.1em;">TRAJECTORY: {trajectory}</span>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 6px; line-height: 1.5;">{traj_msg}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---- WEEK VIEW ----
    elif st.session_state.view_mode == "week":
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
            st.session_state.intervention_step = "alert"
            st.rerun()

        if st.session_state.triggered and not st.session_state.agent_done:
            tm = meetings[trigger_idx]
            emotions = get_meeting_emotions(emp_key, trigger_idx)
            top_emo = max(emotions, key=emotions.get)
            emo_color = EMOTION_COLORS.get(top_emo, "#ef4444")
            clinical = get_meeting_clinical(emp_key, trigger_idx)
            mid_min = (time_to_minutes(tm["start"]) + time_to_minutes(tm["end"])) // 2
            snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - mid_min))

            # Always show alert box
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

            # --- STEP 1: ANIMATED THINKING ---
            if st.session_state.intervention_step == "alert":
                st.markdown("### Vemo Analyzing...")
                st.markdown('<div class="scan-bar"></div>', unsafe_allow_html=True)

                steps = [
                    ("🎙️", "Analyzing voice biomarkers", "emotion2vec+ processing meeting audio..."),
                    ("🧠", "Clinical screening", "Kintsugi DAM evaluating depression/anxiety markers..."),
                    ("📊", "Correlating biometrics", "Cross-referencing HR, HRV, respiratory rate..."),
                    ("📚", "Loading skill protocols", "Matching patterns to intervention library..."),
                    ("👂", "Opening voice channel", "Ready to listen..."),
                ]

                step_placeholder = st.empty()
                for j, (icon, title, desc) in enumerate(steps):
                    with step_placeholder.container():
                        for k in range(j + 1):
                            cls = "agent-step done" if k < j else "agent-step active"
                            si, st_title, sd = steps[k]
                            check = "✓" if k < j else "..."
                            st.markdown(f'<div class="{cls}"><strong>{si} {st_title}</strong> {check}<div style="font-size:0.8rem;color:#64748b;">{sd}</div></div>', unsafe_allow_html=True)
                    time.sleep(0.5)

                st.session_state.intervention_step = "listening"
                st.rerun()

            # --- STEP 2: VOICE INPUT (record or upload) ---
            elif st.session_state.intervention_step == "listening":
                st.markdown(f"""
                <div class="voice-area">
                    <div class="mic-circle">🎙️</div>
                    <div style="font-size: 1.2rem; font-weight: 600; color: #e2e8f0; margin-bottom: 4px;">Vemo needs a voice check-in</div>
                    <div style="font-size: 0.85rem; color: #94a3b8;">{emp['name'].split()[0]}, record a quick voice sample or upload a pre-saved one.</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("")
                rec_col, upload_col = st.columns(2)
                with rec_col:
                    st.markdown("**Record live**")
                    audio_recording = st.audio_input("Record a voice check-in", key="voice_rec")
                with upload_col:
                    st.markdown("**Upload audio**")
                    audio_upload = st.file_uploader("Upload a voice sample", type=["wav", "mp3", "m4a", "ogg", "webm"], key="voice_upload", label_visibility="collapsed")

                has_audio = audio_recording is not None or audio_upload is not None

                if has_audio:
                    st.markdown("")
                    if st.button("🔬 Analyze Voice Sample", type="primary", use_container_width=True, key="analyze_voice"):
                        st.session_state.voice_input = "(voice sample provided)"
                        st.session_state.intervention_step = "processing"
                        st.rerun()

            # --- STEP 2b: PROCESSING THROUGH MODELS ---
            elif st.session_state.intervention_step == "processing":
                st.markdown("### Processing Voice Sample...")
                st.markdown('<div class="scan-bar"></div>', unsafe_allow_html=True)

                model_steps = [
                    ("🎙️", "emotion2vec+ large", "9-class speech emotion recognition running..."),
                    ("🧠", "Kintsugi DAM 3.1", "PHQ-9 depression & GAD-7 anxiety screening..."),
                    ("📊", "Biometric correlation", "Cross-referencing Whoop HR, HRV, respiratory rate..."),
                    ("📚", "Skill protocol matching", "Selecting intervention protocols..."),
                ]

                model_placeholder = st.empty()
                for j, (icon, title, desc) in enumerate(model_steps):
                    with model_placeholder.container():
                        for k in range(j + 1):
                            cls = "agent-step done" if k < j else "agent-step active"
                            si, st_title, sd = model_steps[k]
                            check = "✓" if k < j else "..."
                            st.markdown(f'<div class="{cls}"><strong>{si} {st_title}</strong> {check}<div style="font-size:0.8rem;color:#64748b;">{sd}</div></div>', unsafe_allow_html=True)
                    time.sleep(0.6)

                st.session_state.intervention_step = "responding"
                st.rerun()

            # --- STEP 3: RESULTS + SKILL SELECTION + AGENT RESPONSE ---
            elif st.session_state.intervention_step == "responding":
                # Show voice analysis results
                dep_label = DEPRESSION_LEVELS[min(clinical.get("depression", 0), 2)]
                anx_label = ANXIETY_LEVELS[min(clinical.get("anxiety", 0), 3)]

                res_col1, res_col2, res_col3 = st.columns(3)
                with res_col1:
                    st.markdown(f"""
                    <div style="background:#0f172a;border:1px solid {emo_color};border-radius:10px;padding:12px;text-align:center;">
                        <div style="font-size:0.65rem;color:#64748b;">EMOTION2VEC+</div>
                        <div style="font-size:1.3rem;font-weight:700;color:{emo_color};margin:4px 0;">{top_emo.upper()}</div>
                        <div style="font-size:0.85rem;color:#94a3b8;">{emotions[top_emo]:.0%}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with res_col2:
                    dep_color = SEVERITY_COLORS[dep_label]
                    st.markdown(f"""
                    <div style="background:#0f172a;border:1px solid {dep_color};border-radius:10px;padding:12px;text-align:center;">
                        <div style="font-size:0.65rem;color:#64748b;">DEPRESSION (PHQ-9)</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{dep_color};margin:4px 0;">{dep_label}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with res_col3:
                    anx_color = SEVERITY_COLORS[anx_label]
                    st.markdown(f"""
                    <div style="background:#0f172a;border:1px solid {anx_color};border-radius:10px;padding:12px;text-align:center;">
                        <div style="font-size:0.65rem;color:#64748b;">ANXIETY (GAD-7)</div>
                        <div style="font-size:1.1rem;font-weight:700;color:{anx_color};margin:4px 0;">{anx_label}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("")

                # Select and display skills
                selected_skills = select_skills(emp_key, emotions, clinical, snap, all_skills)

                st.markdown("### Skills Activated")
                skills_html = "".join(
                    f'<span class="skill-pill">{SKILL_ICONS.get(s, "📋")} {SKILL_LABELS.get(s, s)}</span>'
                    for s in selected_skills
                )
                st.markdown(f'<div style="margin-bottom: 16px;">{skills_html}</div>', unsafe_allow_html=True)

                # Build skills text for prompt
                skills_text = "\n\n".join(
                    f"### {SKILL_LABELS.get(s, s)}\n{all_skills.get(s, '')}" for s in selected_skills
                )

                # Stream agent response (cache to avoid re-streaming on rerun)
                st.markdown("---")
                st.markdown('<div class="vemo-active" style="margin-bottom:12px;"><span class="vemo-dot"></span> VEMO INTERVENING</div>', unsafe_allow_html=True)

                api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
                if api_key:
                    response_placeholder = st.empty()
                    if "intervention_response" not in st.session_state or not st.session_state.intervention_response:
                        system_prompt = build_intervention_prompt(emp, tm, emotions, clinical, snap, "", skills_text)
                        full_response = ""
                        for chunk in stream_agent_response(system_prompt, f"You just analyzed a live voice sample from {emp['name'].split()[0]}. Based on the voice biomarkers, clinical screening, and biometrics, intervene now using your skill protocols.", max_tokens=800):
                            full_response += chunk
                            response_placeholder.markdown(f'<div class="agent-card">\n\n{full_response}\n\n</div>', unsafe_allow_html=True)
                        st.session_state.intervention_response = full_response
                    else:
                        response_placeholder.markdown(f'<div class="agent-card">\n\n{st.session_state.intervention_response}\n\n</div>', unsafe_allow_html=True)

                    # Action buttons — open dialogs (no rerun needed)
                    st.markdown("")
                    st.markdown("### Quick Actions")
                    a1, a2, a3, a4 = st.columns(4)
                    with a1:
                        if st.button("🧘 Start Breathing", use_container_width=True, type="primary"):
                            show_breathing_dialog()
                    with a2:
                        if st.button("📅 Block Calendar", use_container_width=True):
                            show_calendar_dialog(emp, tm, meetings)
                    with a3:
                        if st.button("🚶 Walking Break", use_container_width=True):
                            show_walking_dialog()
                    with a4:
                        if st.button("📊 Full Analysis", use_container_width=True):
                            st.session_state.selected_meeting = trigger_idx
                            st.session_state.agent_done = True
                            go_to("meeting")
                            st.rerun()

                    st.session_state.agent_done = True

        elif st.session_state.triggered and st.session_state.agent_done:
            # Already triggered and handled — show cached response + actions
            tm = meetings[trigger_idx]
            emotions = get_meeting_emotions(emp_key, trigger_idx)
            clinical = get_meeting_clinical(emp_key, trigger_idx)
            mid_min = (time_to_minutes(tm["start"]) + time_to_minutes(tm["end"])) // 2
            snap = min(hourly_data, key=lambda d: abs(d["minutes_from_midnight"] - mid_min))

            st.markdown("---")
            if st.session_state.intervention_response:
                st.markdown('<div class="vemo-active" style="margin-bottom:12px;"><span class="vemo-dot"></span> VEMO INTERVENING</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="agent-card">\n\n{st.session_state.intervention_response}\n\n</div>', unsafe_allow_html=True)

                st.markdown("")
                st.markdown("### Quick Actions")
                a1, a2, a3, a4 = st.columns(4)
                with a1:
                    if st.button("🧘 Start Breathing", use_container_width=True, type="primary"):
                        show_breathing_dialog()
                with a2:
                    if st.button("📅 Block Calendar", use_container_width=True):
                        show_calendar_dialog(emp, tm, meetings)
                with a3:
                    if st.button("🚶 Walking Break", use_container_width=True):
                        show_walking_dialog()
                with a4:
                    if st.button("📊 Full Analysis", use_container_width=True):
                        st.session_state.selected_meeting = trigger_idx
                        go_to("meeting")
                        st.rerun()

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
                    st.session_state.intervention_step = "alert"
                    st.session_state.voice_input = ""
                    st.session_state.active_action = None
                    st.session_state.intervention_response = ""
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
