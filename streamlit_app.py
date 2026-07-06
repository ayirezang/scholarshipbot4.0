"""
Streamlit UI for GlobalEdu Bridge scholarship chatbot.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from main import (
    StudentProfile, RagMatcher, match_scholarships, GRADING_SYSTEMS,
)

st.set_page_config(page_title="GlobalEdu Bridge", page_icon="🎓", layout="wide")

# ─── Styles ────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .landing-page { min-height: 100vh; display: flex; flex-direction: column; justify-content: center; }
    .hero { text-align: center; padding: 1rem 0; }
    .hero h1 { font-size: 2.8rem; margin-bottom: 0.3rem; }
    .hero p { font-size: 1.1rem; color: #666; max-width: 600px; margin: auto; }
    .feature-card {
        background: #f0f2f6; border-radius: 12px; padding: 1.5rem;
        text-align: center; margin-bottom: 1rem;
    }
    .feature-card h3 { margin-bottom: 0.5rem; }
    .feature-card p { font-size: 0.9rem; color: #555; }
    .steps { display: flex; justify-content: center; gap: 1rem; margin: 1.5rem 0; }
    .scholar-card {
        background: #f8f9fb; border-radius: 10px; padding: 1.2rem; margin-bottom: 0.8rem;
        border-left: 4px solid #4CAF50;
    }
    .scholar-card.need { border-left-color: #FF9800; }
    .footer { text-align: center; color: #999; font-size: 0.8rem; margin-top: 3rem; }
    .form-container { max-width: 720px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────

if "profile" not in st.session_state:
    st.session_state.profile = StudentProfile()
    st.session_state.step = "landing"
    st.session_state.results_shown = False

profile = st.session_state.profile

# ─── LANDING PAGE ─────────────────────────────────────────────────────

if st.session_state.step == "landing":
    st.markdown('<div class="landing-page">', unsafe_allow_html=True)
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("# 🎓 GlobalEdu Bridge")
    st.markdown("### AI Scholarship Assistant")
    st.markdown(
        "Find fully-funded and partial scholarships matched to your profile. "
        "Built for students from Africa and underserved regions worldwide."
    )
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 Smart Matching")
        st.markdown("Search 39+ scholarships using semantic AI matching")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 🌍 Global Coverage")
        st.markdown("Scholarships across Africa, Europe, Asia, and the Americas")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown("### 📝 Full Guidance")
        st.markdown("Personal statement help, document checklists, and tips")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### How it works")
    st.markdown("""
    1. **Tell us about yourself** — country, level, field of study
    2. **Enter your grades** — we convert them to GPA automatically
    3. **Get matched** — AI finds the best scholarships for you
    """)

    if st.button("🚀 Get Started", use_container_width=True, type="primary"):
        st.session_state.step = "country"
        st.rerun()

    st.markdown(
        '<div class="footer">GlobalEdu Bridge v1.0 — RAG-powered scholarship discovery</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ─── PROFILE FORM ─────────────────────────────────────────────────────

else:
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    steps = ["Country", "Level", "Field", "Grades", "Need"]
    step_index = [
        "country", "level", "field", "grades", "grades_input", "financial_need"
    ]
    current = step_index.index(st.session_state.step) if st.session_state.step in step_index else 0

    st.markdown("### 🎓 GlobalEdu Bridge")
    cols = st.columns(len(steps))
    for i, (label, col) in enumerate(zip(steps, cols)):
        done = i < current
        active = i == current
        emoji = "✅" if done else ("●" if active else "○")
        col.markdown(f"**{emoji} {label}**", help=f"Step {i+1}: {label}")

    st.divider()

    with st.form("profile_form"):
        if st.session_state.step == "country":
            st.markdown("**Where are you from?**")
            country = st.text_input("Country", value=profile.country, placeholder="e.g. Ghana, Nigeria, Kenya")
            submitted = st.form_submit_button("Next →", use_container_width=True)
            if submitted and country:
                profile.country = country
                st.session_state.step = "level"
                st.rerun()

        elif st.session_state.step == "level":
            st.markdown("**What level are you currently at?**")
            level = st.radio(
                "Level",
                ["Still in secondary/high school",
                 "Finished secondary, looking for undergraduate",
                 "Currently in university, looking for postgraduate",
                 "Looking for PhD"],
                index=None, label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Next →", use_container_width=True)
            if submitted and level:
                profile.level = {
                    "Still in secondary/high school": "secondary",
                    "Finished secondary, looking for undergraduate": "undergraduate",
                    "Currently in university, looking for postgraduate": "postgraduate",
                    "Looking for PhD": "phd",
                }[level]
                st.session_state.step = "field"
                st.rerun()

        elif st.session_state.step == "field":
            st.markdown("**What field would you like to study?**")
            field = st.text_input("Field", value=profile.field, placeholder="e.g. Engineering, Medicine, Computer Science")
            submitted = st.form_submit_button("Next →", use_container_width=True)
            if submitted and field:
                profile.field = field
                st.session_state.step = "grades"
                st.rerun()

        elif st.session_state.step == "grades":
            st.markdown("**What grading system does your school use?**")
            sys_choices = {v["name"]: k for k, v in GRADING_SYSTEMS.items()}
            sys_name = st.radio("Grading system", list(sys_choices.keys()), index=None, label_visibility="collapsed")
            submitted = st.form_submit_button("Next →", use_container_width=True)
            if submitted and sys_name:
                choice = sys_choices[sys_name]
                profile.grading_system = GRADING_SYSTEMS[choice]["name"]
                st.session_state.grade_handler = GRADING_SYSTEMS[choice]["handler"]
                st.session_state.grade_choice = choice
                st.session_state.step = "grades_input"
                st.rerun()

        elif st.session_state.step == "grades_input":
            examples = {
                "1": "A1, B2, C4, B3", "2": "1, 2, 3", "3": "A*, A, B, C",
                "4": "A, B+, B, A-", "5": "3.5", "6": "280", "7": "85",
                "8": "16", "9": "38", "10": "1.5",
            }
            example = examples.get(st.session_state.grade_choice, "")
            st.markdown(f"**Enter your grades** ({profile.grading_system})")
            if example:
                st.caption(f"Example: {example}")
            raw = st.text_input("Grades", key="grades_input",
                                placeholder=example)
            submitted = st.form_submit_button("Next →", use_container_width=True)
            if submitted and raw:
                gpa = st.session_state.grade_handler(raw)
                if gpa is not None and 0 <= gpa <= 4.0:
                    profile.gpa = max(0.0, min(4.0, gpa))
                    st.success(f"Your converted GPA: **{profile.gpa:.2f}** / 4.0")
                    st.session_state.step = "financial_need"
                    st.rerun()
                else:
                    st.error("Could not parse those grades. Try again.")

        elif st.session_state.step == "financial_need":
            st.markdown("**Do you have financial need?**")
            need = st.radio("Financial need", ["Yes", "No"], index=None, label_visibility="collapsed")
            submitted = st.form_submit_button("🔍 Find Scholarships", use_container_width=True, type="primary")
            if submitted and need:
                profile.financial_need = (need == "Yes")
                st.session_state.step = "results"
                st.rerun()

    if st.session_state.step not in ("landing", "results"):
        if st.button("← Back to home"):
            st.session_state.profile = StudentProfile()
            st.session_state.step = "landing"
            st.session_state.results_shown = False
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ─── RESULTS ──────────────────────────────────────────────────────────

if st.session_state.step == "results" and not st.session_state.results_shown:
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    st.session_state.results_shown = True
    with st.spinner("Searching scholarships across our database..."):
        matched = match_scholarships(profile)

    st.divider()
    st.markdown("## Your Results")

    if not matched:
        st.warning("No scholarships matched your current profile. Try different criteria.")
    else:
        st.success(f"We found **{len(matched)} scholarship(s)** you may qualify for!")

        col1, col2, col3 = st.columns(3)
        total = len(matched)
        funded = sum(1 for s in matched if s.fully_funded)
        partial = total - funded
        col1.metric("Total Matched", total)
        col2.metric("Fully Funded", funded)
        col3.metric("Partial Funding", partial)

        st.markdown("### Matched Scholarships")
        for i, s in enumerate(matched, 1):
            css_class = "scholar-card need" if s.financial_need_based else "scholar-card"
            funding = "✅ Fully funded" if s.fully_funded else "💰 Partial funding"
            badge = f"{funding}" + (" · 🎯 Need-based" if s.financial_need_based else "")
            link_html = f"<br>🔗 <a href='{s.link}' target='_blank'>Apply here</a>" if s.link else ""

            st.markdown(
                f'<div class="{css_class}">'
                f'<strong>{i}. {s.name}</strong><br>'
                f'{s.description}<br>'
                f'<span style="font-size:0.9rem">{badge} · 📅 {s.deadline}</span>'
                f'{link_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

    col1, col2 = st.columns(2)
    if col1.button("🔄 Start Over", use_container_width=True):
        st.session_state.profile = StudentProfile()
        st.session_state.step = "landing"
        st.session_state.results_shown = False
        st.rerun()
    if col2.button("📋 New Search", use_container_width=True):
        st.session_state.profile = StudentProfile()
        st.session_state.step = "country"
        st.session_state.results_shown = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
