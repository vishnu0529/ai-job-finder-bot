"""
Vishnu's AI Job Finder Bot
──────────────────────────
Searches LinkedIn, Remotive, and Arbeitnow for AI Engineer roles,
scores each job against your profile, generates tailored cover letters,
and tracks every application in a local SQLite database.
"""

import os
import sys
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime, date

# ── env setup ─────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import streamlit as st

# ── project imports ───────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from config import CANDIDATE, SOURCES
from db.tracker import (init_db, upsert_job, get_all_jobs, get_job,
                        get_application, save_application, update_status, get_stats)
from searchers.base import Job
from searchers import remotive, arbeitnow, linkedin
from agents import scorer, writer
from sponsor import register as sponsor_register

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Job Finder · Vishnu",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── init db ───────────────────────────────────────────────────────────────────
init_db()

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #0f1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 44px; padding: 0 20px;
        background: #1e2130; border-radius: 8px;
        font-weight: 600; color: #aaa;
    }
    .stTabs [aria-selected="true"] {
        background: #003366 !important; color: white !important;
    }
    .job-card {
        background: #1e2130; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 12px;
        border-left: 4px solid #0066cc;
    }
    .score-badge {
        display: inline-block; padding: 2px 10px;
        border-radius: 20px; font-weight: 700; font-size: 13px;
    }
    .score-high   { background: #004d20; color: #00e676; }
    .score-mid    { background: #3d2e00; color: #ffca28; }
    .score-low    { background: #3d0000; color: #ff5252; }
    .status-pill  {
        display: inline-block; padding: 2px 10px;
        border-radius: 20px; font-size: 12px; font-weight: 600;
    }
    .tag-remote { background: #0d3349; color: #40c4ff; }
    .tag-uk     { background: #0d3323; color: #69f0ae; }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "saved":     "#555",
    "applied":   "#0066cc",
    "interview": "#9c27b0",
    "offer":     "#00897b",
    "rejected":  "#c62828",
}

STATUS_EMOJI = {
    "saved":     "📌",
    "applied":   "📤",
    "interview": "💬",
    "offer":     "🎉",
    "rejected":  "❌",
}

def score_badge(score: float) -> str:
    cls = "score-high" if score >= 7 else ("score-mid" if score >= 5 else "score-low")
    return f'<span class="score-badge {cls}">{score:.0f}/10</span>'


def status_pill(status: str) -> str:
    color = STATUS_COLORS.get(status, "#555")
    emoji = STATUS_EMOJI.get(status, "")
    return (f'<span class="status-pill" style="background:{color}22;color:{color};">'
            f'{emoji} {status.capitalize()}</span>')


def sponsor_badge(sponsor_licensed) -> str:
    """sponsor_licensed is 1/0/None from SQLite (see db/tracker.py)."""
    if sponsor_licensed == 1:
        return '<span class="status-pill" style="background:#16653422;color:#16a34a;">🛂 Sponsor-licensed</span>'
    if sponsor_licensed == 0:
        return '<span class="status-pill" style="background:#7c2d1222;color:#dc2626;">🛂 Not on register</span>'
    return ""


def render_job_card(job: dict, show_status: bool = False):
    score = job.get("match_score", 0) or 0
    status = job.get("status")
    remote_tag = '<span class="status-pill tag-remote">🌐 Remote</span>' if job.get("remote") else ""
    status_tag = status_pill(status) if show_status and status else ""
    salary_tag = f"<small>💷 {job['salary']}</small>  " if job.get("salary") else ""
    sponsor_tag = sponsor_badge(job.get("sponsor_licensed"))
    st.markdown(f"""
    <div class="job-card">
      <b style="font-size:15px;">{job['title']}</b>
      &nbsp;&nbsp;{score_badge(score)}
      &nbsp;{remote_tag}&nbsp;{status_tag}&nbsp;{sponsor_tag}<br>
      <span style="color:#aaa;">🏢 {job['company']} &nbsp;·&nbsp; 📍 {job['location']}</span><br>
      {salary_tag}<small style="color:#888;">🔗 {job['source'].capitalize()} &nbsp;·&nbsp;
      {"📅 " + job['posted_date'] if job.get('posted_date') else ""}</small>
    </div>
    """, unsafe_allow_html=True)
    if job.get("sponsor_note"):
        st.caption(f"🛂 {job['sponsor_note']}")
    if job.get("visa_note") and job["visa_note"] != "unclear":
        st.caption(f"🤖 AI visa read: {job['visa_note']}")


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🤖 AI Job Finder")
    st.markdown(f"**{CANDIDATE['name']}**")
    st.markdown(f"_{CANDIDATE['availability']}_")
    st.divider()

    stats = get_stats()
    st.markdown("### 📊 Quick Stats")
    cols = st.columns(2)
    cols[0].metric("Jobs Found", stats["total_jobs"])
    cols[1].metric("Avg Match", f"{stats['avg_score']}/10")

    by_status = stats.get("by_status", {})
    if by_status:
        st.markdown("**Applications**")
        for s, n in by_status.items():
            st.markdown(f"{STATUS_EMOJI.get(s, '')} {s.capitalize()}: **{n}**")

    st.divider()
    st.markdown("### ⚙️ API Keys")
    st.markdown("Unlock more sources:")
    reed_key   = st.text_input("Reed API Key (free)", type="password",
                               help="Get free key at reed.co.uk/developers/jobseeker")
    adzuna_id  = st.text_input("Adzuna App ID (free)", type="password",
                               help="Get free key at developer.adzuna.com")
    adzuna_key = st.text_input("Adzuna App Key (free)", type="password")

    if reed_key:
        SOURCES["reed"]["enabled"] = True
        SOURCES["reed"]["key"] = reed_key
    if adzuna_id and adzuna_key:
        SOURCES["adzuna"]["enabled"] = True
        SOURCES["adzuna"]["id"] = adzuna_id
        SOURCES["adzuna"]["key"] = adzuna_key


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_search, tab_jobs, tab_apply, tab_tracker, tab_dash = st.tabs([
    "🔍  Search",
    "📋  Job Board",
    "✍️  Apply",
    "📌  Tracker",
    "📊  Dashboard",
])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — SEARCH
# ──────────────────────────────────────────────────────────────────────────────
with tab_search:
    st.markdown("## 🔍 Search for AI Engineer Jobs")
    st.markdown("Searches LinkedIn, Remotive, and Arbeitnow simultaneously. AI scores each result against your profile.")

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keywords = st.text_input("Keywords", value="AI Engineer",
                                 placeholder="AI Engineer, NLP Engineer, LLM Engineer…")
    with col2:
        location = st.selectbox("Location", ["United Kingdom", "London", "Remote", "Hybrid"])
    with col3:
        limit = st.selectbox("Max results", [25, 50, 75, 100], index=1)

    sources_enabled = ["LinkedIn", "Remotive", "Arbeitnow"]
    if SOURCES["reed"]["enabled"]:
        sources_enabled.append("Reed")

    selected_sources = st.multiselect("Sources", sources_enabled, default=sources_enabled)
    score_jobs_toggle = st.toggle("AI-score each job (uses Gemini API — slower but ranks results)", value=True)

    if st.button("🚀 Search Jobs", type="primary", use_container_width=True):
        all_jobs: list[Job] = []
        progress = st.progress(0, text="Searching job boards…")
        status_msg = st.empty()

        # Search each enabled source
        step = 0
        total_steps = len(selected_sources)

        if "LinkedIn" in selected_sources:
            status_msg.info("🔗 Searching LinkedIn…")
            lj = linkedin.search(keywords, limit=min(limit, 50))
            all_jobs.extend(lj)
            step += 1
            progress.progress(step / total_steps, text=f"LinkedIn: {len(lj)} jobs found")

        if "Remotive" in selected_sources:
            status_msg.info("🌐 Searching Remotive (remote jobs)…")
            rj = remotive.search(keywords, limit=min(limit, 40))
            all_jobs.extend(rj)
            step += 1
            progress.progress(step / total_steps, text=f"Remotive: {len(rj)} remote jobs found")

        if "Arbeitnow" in selected_sources:
            status_msg.info("🌍 Searching Arbeitnow…")
            aj = arbeitnow.search(keywords, limit=min(limit, 40))
            all_jobs.extend(aj)
            step += 1
            progress.progress(step / total_steps, text=f"Arbeitnow: {len(aj)} jobs found")

        if "Reed" in selected_sources and SOURCES["reed"]["enabled"]:
            from searchers import reed
            status_msg.info("🌿 Searching Reed (UK)…")
            loc_str = location if location not in ["Remote", "Hybrid"] else "London"
            rj2 = reed.search(SOURCES["reed"]["key"], keywords, loc_str, limit)
            all_jobs.extend(rj2)
            step += 1
            progress.progress(1.0, text=f"Reed: {len(rj2)} jobs found")

        progress.progress(1.0, text=f"✅ Found {len(all_jobs)} total jobs")
        status_msg.empty()

        if not all_jobs:
            st.warning("No jobs found. LinkedIn may be rate-limiting — try again in a minute, or add Reed/Adzuna API keys.")
        else:
            # AI scoring
            if score_jobs_toggle and os.getenv("GOOGLE_API_KEY"):
                st.info(f"🧠 AI-scoring {len(all_jobs)} jobs against your profile…")
                score_bar = st.progress(0)
                for i, job in enumerate(all_jobs):
                    if job.description:
                        job.match_score, job.match_reason, job.visa_note = scorer.score_job(job)
                    else:
                        job.match_score = 5.0
                        job.match_reason = "No description available"
                        job.visa_note = "unclear"
                    score_bar.progress((i + 1) / len(all_jobs))
                    time.sleep(0.05)
                all_jobs.sort(key=lambda j: j.match_score, reverse=True)
                score_bar.empty()

            # Real UK sponsor-register check (not an LLM guess — see sponsor/register.py)
            st.info("🛂 Checking companies against the UK sponsor register…")
            sponsor_bar = st.progress(0)
            for i, job in enumerate(all_jobs):
                try:
                    result = sponsor_register.check_company(job.company)
                    job.sponsor_licensed = result.licensed
                    job.sponsor_note = (
                        f"Licensed as '{result.matched_name}' ({', '.join(result.routes)})"
                        if result.licensed
                        else "Not found on register under this name — verify manually"
                    )
                except Exception as e:
                    job.sponsor_licensed = None
                    job.sponsor_note = f"Could not check register: {e}"
                sponsor_bar.progress((i + 1) / len(all_jobs))
            sponsor_bar.empty()

            # Save to DB
            for job in all_jobs:
                upsert_job(job)

            st.success(f"✅ {len(all_jobs)} jobs saved to your board. Switch to **📋 Job Board** to review them.")
            st.balloons()

            # Preview top 5
            st.markdown("### 🏆 Top matches")
            for job in all_jobs[:5]:
                render_job_card(vars(job))


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — JOB BOARD
# ──────────────────────────────────────────────────────────────────────────────
with tab_jobs:
    st.markdown("## 📋 Job Board")

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        filter_source = st.selectbox("Source", ["All", "linkedin", "remotive", "arbeitnow", "reed", "adzuna"])
    with col2:
        filter_status = st.selectbox("Status", ["All", "new", "saved", "applied", "interview", "offer", "rejected"])
    with col3:
        min_score_filter = st.slider("Min match score", 0, 10, 5)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh")

    sponsor_only = st.checkbox(
        "🛂 Sponsor-licensed only (real UK Home Office register check)"
    )

    all_db_jobs = get_all_jobs(min_score=min_score_filter)

    if filter_source != "All":
        all_db_jobs = [j for j in all_db_jobs if j["source"] == filter_source]
    if filter_status != "All":
        all_db_jobs = [j for j in all_db_jobs if j.get("status") == filter_status]
    if sponsor_only:
        all_db_jobs = [j for j in all_db_jobs if j.get("sponsor_licensed") == 1]

    st.markdown(f"**{len(all_db_jobs)} jobs** matching filters")

    if not all_db_jobs:
        st.info("No jobs found. Run a search first from the 🔍 Search tab.")
    else:
        for job in all_db_jobs:
            render_job_card(job, show_status=True)

            c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
            with c1:
                if st.button("✍️ Generate Application", key=f"gen_{job['id']}"):
                    st.session_state["apply_job_id"] = job["id"]
                    st.session_state["active_tab"] = "apply"
                    st.info("Switch to the ✍️ Apply tab to see your generated materials.")
            with c2:
                if st.button("🔗 Open Job URL", key=f"open_{job['id']}"):
                    webbrowser.open(job["url"])
                    st.success("Opened in browser!")
            with c3:
                new_status = st.selectbox(
                    "Update status", ["saved", "applied", "interview", "offer", "rejected"],
                    key=f"status_{job['id']}",
                    index=["saved","applied","interview","offer","rejected"].index(
                        job.get("status") or "saved"
                    ) if job.get("status") in ["saved","applied","interview","offer","rejected"] else 0
                )
                if st.button("Save status", key=f"save_status_{job['id']}"):
                    if get_application(job["id"]):
                        update_status(job["id"], new_status)
                    else:
                        save_application(job["id"], status=new_status)
                    st.success("Status updated!")
                    st.rerun()
            with c4:
                if job.get("match_reason"):
                    st.caption(f"💡 {job['match_reason']}")

            st.divider()


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — APPLY
# ──────────────────────────────────────────────────────────────────────────────
with tab_apply:
    st.markdown("## ✍️ Generate Application Materials")
    st.markdown("Select a job to generate a tailored cover letter, ATS keyword analysis, and interview prep questions.")

    all_db_jobs_apply = get_all_jobs()
    if not all_db_jobs_apply:
        st.info("No jobs found yet. Search first from the 🔍 Search tab.")
    else:
        job_options = {
            f"{j['title']} @ {j['company']} [{j['source']}]": j["id"]
            for j in all_db_jobs_apply
        }
        # Pre-select if coming from Job Board
        default_label = None
        if "apply_job_id" in st.session_state:
            for label, jid in job_options.items():
                if jid == st.session_state["apply_job_id"]:
                    default_label = label
                    break

        selected_label = st.selectbox(
            "Select job",
            list(job_options.keys()),
            index=list(job_options.keys()).index(default_label) if default_label else 0,
        )
        selected_id = job_options[selected_label]
        job_data = get_job(selected_id)

        if job_data:
            st.markdown(f"**{job_data['title']}** at **{job_data['company']}** · {job_data['location']}")
            if job_data.get("url"):
                st.markdown(f"🔗 [{job_data['url'][:60]}...]({job_data['url']})")

            with st.expander("📄 Job Description"):
                st.text(job_data.get("description", "No description available") or "No description available")

            existing_app = get_application(selected_id)

            st.divider()
            col_a, col_b, col_c = st.columns(3)

            # ── Cover Letter ──────────────────────────────────────────────────
            with col_a:
                st.markdown("### 📝 Cover Letter")
                if existing_app and existing_app.get("cover_letter"):
                    st.success("Cover letter already generated")
                    cover_letter = existing_app["cover_letter"]
                else:
                    cover_letter = ""

                if st.button("⚡ Generate Cover Letter", type="primary"):
                    with st.spinner("Gemini is writing your cover letter…"):
                        desc = job_data.get("description", "") or ""
                        if not desc and job_data.get("url"):
                            # Try fetching description from LinkedIn
                            if "linkedin" in job_data.get("source", ""):
                                desc = linkedin.fetch_description(job_data["url"])
                        cover_letter = writer.generate_cover_letter(
                            title=job_data["title"],
                            company=job_data["company"],
                            location=job_data["location"],
                            description=desc,
                        )
                        save_application(selected_id, cover_letter=cover_letter, status="saved")
                        st.success("Cover letter saved!")

                if cover_letter:
                    edited_cl = st.text_area("Edit before copying:", value=cover_letter, height=400)
                    if st.button("📋 Copy to Clipboard", key="copy_cl"):
                        st.code(edited_cl, language="text")
                        st.info("Select all and copy from the box above.")
                    if st.button("💾 Save edits"):
                        save_application(selected_id, cover_letter=edited_cl)
                        st.success("Saved!")

            # ── CV / ATS Notes ────────────────────────────────────────────────
            with col_b:
                st.markdown("### 🎯 ATS Keywords")
                if st.button("⚡ Analyse ATS Keywords", type="primary"):
                    with st.spinner("Analysing job description…"):
                        desc = job_data.get("description", "") or ""
                        notes = writer.generate_cv_notes(
                            title=job_data["title"],
                            company=job_data["company"],
                            description=desc,
                        )
                    if notes:
                        ats_score = notes.get("ats_score_estimate", "?")
                        score_color = "green" if ats_score >= 70 else ("orange" if ats_score >= 50 else "red")
                        st.markdown(f"**ATS Match Estimate:** :{score_color}[{ats_score}%]")

                        st.markdown("**✅ Keywords your CV already has:**")
                        for kw in notes.get("ats_keywords_present", []):
                            st.markdown(f"  - `{kw}`")

                        st.markdown("**⚠️ Missing keywords to add:**")
                        for kw in notes.get("ats_keywords_missing", []):
                            st.markdown(f"  - `{kw}`")

                        st.markdown("**📌 Top 3 role requirements:**")
                        for r in notes.get("top_3_requirements", []):
                            st.markdown(f"  - {r}")

                        st.markdown("**💡 CV tailoring tips:**")
                        for tip in notes.get("tailoring_tips", []):
                            st.info(tip)

                        notes_str = str(notes)
                        save_application(selected_id, cv_notes=notes_str)
                    else:
                        st.warning("Could not analyse — check your Gemini API key.")

            # ── Interview Prep ────────────────────────────────────────────────
            with col_c:
                st.markdown("### 💬 Interview Prep")
                if st.button("⚡ Generate Interview Questions", type="primary"):
                    with st.spinner("Generating likely questions…"):
                        desc = job_data.get("description", "") or ""
                        questions = writer.generate_interview_prep(
                            title=job_data["title"],
                            company=job_data["company"],
                            description=desc,
                        )
                    if questions:
                        for i, qa in enumerate(questions, 1):
                            with st.expander(f"Q{i}: {qa.get('question', '')}"):
                                st.markdown(f"**💡 Hint:** {qa.get('hint', '')}")
                    else:
                        st.warning("Could not generate questions.")

            st.divider()
            st.markdown("### 🚀 One-Click Apply")
            col_apply1, col_apply2 = st.columns(2)
            with col_apply1:
                if st.button("🔗 Open Application URL", use_container_width=True, type="primary"):
                    webbrowser.open(job_data["url"])
                    update_status(selected_id, "applied")
                    st.success("Opened in browser. Status updated to Applied.")
                    st.rerun()
            with col_apply2:
                if st.button("📌 Mark as Applied", use_container_width=True):
                    save_application(selected_id, status="applied")
                    st.success("Marked as applied!")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — TRACKER
# ──────────────────────────────────────────────────────────────────────────────
with tab_tracker:
    st.markdown("## 📌 Application Tracker")

    tracked = get_all_jobs()
    tracked = [j for j in tracked if j.get("status")]

    if not tracked:
        st.info("No applications tracked yet. Apply to jobs from the 📋 Job Board or ✍️ Apply tabs.")
    else:
        # Group by status
        for status_key in ["offer", "interview", "applied", "saved", "rejected"]:
            group = [j for j in tracked if j.get("status") == status_key]
            if not group:
                continue
            st.markdown(f"### {STATUS_EMOJI.get(status_key, '')} {status_key.capitalize()} ({len(group)})")
            for job in group:
                with st.expander(f"{job['title']} @ {job['company']} · {job['location']}"):
                    render_job_card(job, show_status=False)
                    app = get_application(job["id"])
                    if app:
                        if app.get("applied_date"):
                            st.caption(f"Applied: {app['applied_date'][:10]}")
                        if app.get("notes"):
                            st.markdown(f"**Notes:** {app['notes']}")
                        if app.get("cover_letter"):
                            with st.expander("View cover letter"):
                                st.text(app["cover_letter"])

                    col1, col2 = st.columns(2)
                    with col1:
                        new_s = st.selectbox(
                            "Status",
                            ["saved", "applied", "interview", "offer", "rejected"],
                            index=["saved","applied","interview","offer","rejected"].index(status_key),
                            key=f"tracker_status_{job['id']}",
                        )
                    with col2:
                        note = st.text_input("Add note", key=f"tracker_note_{job['id']}")

                    if st.button("Update", key=f"tracker_update_{job['id']}"):
                        update_status(job["id"], new_s, note)
                        st.success("Updated!")
                        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
with tab_dash:
    st.markdown("## 📊 Dashboard")

    stats = get_stats()
    all_scored = [j for j in get_all_jobs() if j.get("match_score", 0) >= 7]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Jobs Found",    stats["total_jobs"])
    c2.metric("High Match (7+/10)", len(all_scored))
    c3.metric("Avg Match Score",     f"{stats['avg_score']}/10")
    c4.metric("Applied",             stats["by_status"].get("applied", 0))
    c5.metric("Interviews",          stats["by_status"].get("interview", 0))

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🏆 Top 10 Matched Jobs")
        top_jobs = sorted(get_all_jobs(), key=lambda j: j.get("match_score", 0), reverse=True)[:10]
        if top_jobs:
            import pandas as pd
            df = pd.DataFrame([{
                "Score": f"{j.get('match_score', 0):.0f}/10",
                "Title": j["title"][:40],
                "Company": j["company"][:25],
                "Source": j["source"],
                "Status": j.get("status") or "—",
            } for j in top_jobs])
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.info("No jobs scored yet.")

    with col_right:
        st.markdown("### 📈 Application Funnel")
        funnel_data = {
            "Found":     stats["total_jobs"],
            "Saved":     stats["by_status"].get("saved", 0),
            "Applied":   stats["by_status"].get("applied", 0),
            "Interview": stats["by_status"].get("interview", 0),
            "Offer":     stats["by_status"].get("offer", 0),
        }
        if any(funnel_data.values()):
            import pandas as pd
            df2 = pd.DataFrame(list(funnel_data.items()), columns=["Stage", "Count"])
            st.bar_chart(df2.set_index("Stage"))
        else:
            st.info("Start applying to see your funnel.")

    st.divider()
    st.markdown("### 🎯 Your Job Search Action Plan")
    st.markdown("""
    | Priority | Action | Status |
    |---|---|---|
    | 🔴 Critical | Switch LinkedIn 'Open to Work' to **All Members** (green badge) | Do today |
    | 🔴 Critical | Add 4 projects to LinkedIn profile | Do today |
    | 🟡 High | Post one technical post on LinkedIn about your AI Resume Matcher | This week |
    | 🟡 High | Get 2 free certifications (DeepLearning.AI: LangChain, Building with ChatGPT) | This week |
    | 🟢 Normal | Apply to 5–10 jobs per day using this bot | Daily |
    | 🟢 Normal | Add Reed.co.uk free API key in sidebar for more UK jobs | When ready |
    """)

    st.markdown("### 🔑 Missing Gemini API Key?")
    if not os.getenv("GOOGLE_API_KEY"):
        st.warning("Add your Google Gemini API key to the `.env` file to enable AI scoring and cover letter generation.")
        st.code('GOOGLE_API_KEY=your_key_here', language="bash")
    else:
        st.success("✅ Gemini API connected — AI scoring and cover letter generation active.")
