import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from styles import dark_chart_layout
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from api import api_get


@st.cache_data(ttl=60, show_spinner=False)
def fetch_burnout(uid):
    res = api_get(f"/employees/{uid}/burnout")
    if res.status_code != 200:
        return None
    return res.json()


def show(uid):
    st.markdown('<div class="page-title">🔥 Burnout Risk Detection</div>',
                unsafe_allow_html=True)

    data = fetch_burnout(uid)
    if data is None:
        st.error("Data not found")
        return

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    risk  = data["risk_level"]
    color = {"Low":"#2ecc71","Medium":"#f39c12","High":"#e74c3c"}.get(risk,"#888")

    # ── Row 1: Badge + Gauge + Probability ────────────────────
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{color}18,{color}08);
                    border:2px solid {color}; padding:24px 16px;
                    border-radius:14px; text-align:center; height:220px;
                    display:flex; flex-direction:column;
                    align-items:center; justify-content:center;">
            <div style="font-size:42px;">
                {"🟢" if risk=="Low" else "🟡" if risk=="Medium" else "🔴"}
            </div>
            <div style="font-size:22px; font-weight:800; color:{color}; margin-top:10px;">
                {risk} Risk
            </div>
            <div style="font-size:12px; color:#888; margin-top:6px;">
                Burnout Prediction
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        prob = data["probabilities"]
        low_val = prob.get("Low", 0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=100 - low_val,
            number={"suffix": "%", "font": {"color": color, "size": 28}},
            title={"text": "Risk Level", "font": {"color": "#888", "size": 11}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#555"},
                "bar":  {"color": color},
                "bgcolor": "#1a1a2e",
                "steps": [
                    {"range": [0,  40],  "color": "rgba(46,204,113,0.15)"},
                    {"range": [40, 70],  "color": "rgba(243,156,18,0.15)"},
                    {"range": [70, 100], "color": "rgba(231,76,60,0.15)"},
                ]
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor="#1a1a2e", height=220,
            margin=dict(l=10,r=10,t=30,b=10),
            font=dict(color="#ccc")
        )
        st.plotly_chart(fig_gauge, width="stretch")

    with col3:
        df_prob = pd.DataFrame({
            "Risk Level": list(prob.keys()),
            "Probability (%)": list(prob.values())
        })
        fig1 = px.bar(df_prob, x="Risk Level", y="Probability (%)",
                      color="Risk Level", text="Probability (%)",
                      color_discrete_map={
                          "Low":"#2ecc71","Medium":"#f39c12","High":"#e74c3c"
                      })
        fig1.update_layout(dark_chart_layout("Risk Probability Breakdown"), showlegend=False,title_x=0.5,title_xanchor="center", height=220)
        st.plotly_chart(fig1, width="stretch")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Row 2: You vs Employee Average ────────────────────────
    st.markdown('<div class="section-title">You vs Employee Average</div>',
                unsafe_allow_html=True)

    comp = data.get("company_comparison", {})
    your_score = comp.get("your_risk_score", 0)
    avg_score  = comp.get("avg_risk_score", 0)
    dist       = comp.get("risk_distribution", {"Low": 0, "Medium": 0, "High": 0})
    total_emp  = comp.get("total_employees", 0)

    col5, col6 = st.columns([1, 2])

    with col5:
        diff = round(your_score - avg_score, 2)
        st.metric(
            "Your Risk Score", f"{your_score}",
            delta=f"{diff:+.2f} vs employee avg ({avg_score})"
        )
        st.markdown(
            f'<div style="font-size:11px; color:#888; margin-top:4px;">'
            f'Compared against {total_emp} employee(s) with recorded data</div>',
            unsafe_allow_html=True
        )

    with col6:
        score_df = pd.DataFrame({
            "Who":   ["You", "Employee Avg"],
            "Score": [your_score, avg_score]
        })
        fig_cmp = px.bar(score_df, x="Who", y="Score", color="Who", text="Score",
                         color_discrete_sequence=["#e94560", "#3498db"])
        fig_cmp.update_layout(dark_chart_layout("Risk Score Comparison"), showlegend=False, height=220)
        st.plotly_chart(fig_cmp, width="stretch")

    st.markdown('<div class="section-title">Company-Wide Risk Distribution</div>',
                unsafe_allow_html=True)
    dist_df = pd.DataFrame({
        "Risk Level": list(dist.keys()),
        "Share of Employees (%)": list(dist.values())
    })
    fig_dist = px.bar(dist_df, x="Risk Level", y="Share of Employees (%)",
                      color="Risk Level", text="Share of Employees (%)",
                      color_discrete_map={"Low":"#2ecc71","Medium":"#f39c12","High":"#e74c3c"})
    fig_dist.update_layout(dark_chart_layout(""), showlegend=False, height=240)
    st.plotly_chart(fig_dist, width="stretch")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Row 3: Features in 3x3 grid ──────────────────────────
    st.markdown('<div class="section-title">Features Used for Prediction</div>',
                unsafe_allow_html=True)
    feats = data["input_features"]
    f1,f2,f3 = st.columns(3)
    f1.metric("Avg Working Hours",  f"{feats['avgHours']}h")
    f2.metric("Total Hours",        f"{feats['totalHours']}h")
    f3.metric("Attendance %",       f"{feats['attendance']}%")
    f4,f5,f6 = st.columns(3)
    f4.metric("Late Arrivals",      feats["lateArrivals"])
    f5.metric("Missed Checkouts",   feats["missedCheckouts"])
    f6.metric("Idle Warning Days",  feats["idleWarningDays"])
    f7,f8,f9 = st.columns(3)
    f7.metric("Geo Out of Range",   feats["geoOutOfRange"])
    f8.metric("Pending Tasks",      feats["pendingTasks"])
    f9.metric("Overdue Tasks",      feats["overdueTasks"])

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Row 4: Feature radar (fills empty space) ──────────────
    st.markdown('<div class="section-title">Risk Factor Analysis</div>',
                unsafe_allow_html=True)
    col_r, col_tip = st.columns([2, 1])

    with col_r:
        norm_vals = [
            min(feats["avgHours"] / 13 * 100, 100),
            min(feats["lateArrivals"] / 15 * 100, 100),
            min(feats["idleWarningDays"] / 20 * 100, 100),
            min(feats["pendingTasks"] / 30 * 100, 100),
            min(feats["missedCheckouts"] / 10 * 100, 100),
        ]
        labels = ["Long Hours","Late Arrivals","Idle Days","Pending Tasks","Missed Checkouts"]
        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(
            r=norm_vals + [norm_vals[0]],
            theta=labels + [labels[0]],
            fill="toself",
            line_color=color,
            fillcolor=f"rgba(233,69,96,0.15)"
        ))
        fig_r.update_layout(
            dark_chart_layout(""),
            polar=dict(
                bgcolor="#1a1a2e",
                radialaxis=dict(visible=True, range=[0,100], color="#555"),
                angularaxis=dict(color="#666")
            ),
            showlegend=False, height=280,
            margin=dict(l=20,r=20,t=10,b=10)
        )
        st.plotly_chart(fig_r, width="stretch")

    with col_tip:
        st.markdown('<div class="section-title">Recommendations</div>',
                    unsafe_allow_html=True)
        tips = {
            "Low":    ["✅ Great work-life balance","✅ Keep up the consistency","✅ You're on track"],
            "Medium": ["⚠️ Monitor working hours","⚠️ Reduce idle time","⚠️ Clear pending tasks"],
            "High":   ["🚨 Take a break soon","🚨 Talk to your manager","🚨 Reduce workload"]
        }
        for tip in tips.get(risk, []):
            st.markdown(f"""
            <div style="background:#16213e; border:1px solid #2a2a4a;
                        border-radius:8px; padding:10px 12px;
                        margin-bottom:8px; font-size:12px; color:#ccc;">
                {tip}
            </div>
            """, unsafe_allow_html=True)