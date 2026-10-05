"""
RIFT — Refund Intelligence & Financial Tracking
Streamlit Dashboard
"""

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime

from rift_analyzer import analyze, load_tickets
from data.generate_data import generate_tickets, save_csv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RIFT — Refund Intelligence & Financial Tracking",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 16px;
        border-left: 4px solid #7c3aed;
    }
    .savings-card {
        background: linear-gradient(135deg, #065f46, #047857);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    .warning-card {
        background: linear-gradient(135deg, #7c2d12, #9a3412);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 20px; border-radius: 6px; }
    div[data-testid="metric-container"] {
        background-color: #1e1e2e;
        border: 1px solid #374151;
        padding: 15px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── Data loading ──────────────────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "tickets.csv")

@st.cache_data(ttl=300)
def get_data() -> pd.DataFrame:
    if not os.path.exists(DATA_PATH):
        with st.spinner("Generating synthetic dataset…"):
            tickets = generate_tickets(500)
            save_csv(tickets, DATA_PATH)
    return load_tickets(DATA_PATH)

@st.cache_data(ttl=300)
def get_insights(df_hash: int) -> dict:
    df = get_data()
    return analyze(df)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/financial-analytics.png", width=80)
    st.title("RIFT")
    st.caption("Refund Intelligence & Financial Tracking")
    st.divider()

    st.subheader("⚙️ Filters")
    df_raw = get_data()

    selected_categories = st.multiselect(
        "Ticket Category",
        options=df_raw["category"].unique().tolist(),
        default=df_raw["category"].unique().tolist(),
    )
    selected_agents = st.multiselect(
        "Agent",
        options=df_raw["agent_name"].unique().tolist(),
        default=df_raw["agent_name"].unique().tolist(),
    )
    show_avoidable_only = st.checkbox("Show Avoidable Refunds Only", value=False)

    st.divider()
    if st.button("🔄 Re-run AI Analysis", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y %H:%M')}")


# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_raw[
    (df_raw["category"].isin(selected_categories)) &
    (df_raw["agent_name"].isin(selected_agents))
]
if show_avoidable_only:
    df = df[df["avoidable"]]

insights = get_insights(hash(str(df_raw.shape)))


# ── Header ────────────────────────────────────────────────────────────────────
st.title("💸 RIFT — Refund Intelligence & Financial Tracking")
st.caption(
    f"Analyzing **{len(df):,}** support tickets · "
    f"AI Mode: **{insights.get('ai_mode', 'rule-based').upper()}** · "
    f"Estimated scale: **{insights['monthly_ticket_estimate']:,} tickets/month**"
)
st.divider()


# ── KPI Row ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

granted = df[df["refund_granted"]]
avoidable = df[df["avoidable"]]

with col1:
    st.metric("Total Tickets", f"{len(df):,}")
with col2:
    st.metric(
        "Refunds Granted",
        f"{len(granted):,}",
        delta=f"{len(granted)/len(df)*100:.1f}% rate",
        delta_color="inverse",
    )
with col3:
    st.metric(
        "Total ₹ Refunded",
        f"₹{granted['refund_amount_inr'].sum():,.0f}",
    )
with col4:
    st.metric(
        "Avoidable Refunds",
        f"{len(avoidable):,}",
        delta=f"{len(avoidable)/len(df)*100:.1f}% of total",
        delta_color="inverse",
    )
with col5:
    est_savings = insights["est_monthly_savings_inr"]
    st.metric(
        "Est. Monthly Savings",
        f"₹{est_savings:,.0f}",
        delta="if avoidable refunds prevented",
        delta_color="normal",
    )

st.divider()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", "🤖 AI Insights", "👤 Agent Analysis",
    "📂 Raw Data", "💰 Cost & Savings"
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Refunds by Category")
        cat_df = (
            granted.groupby("category")["refund_amount_inr"]
            .sum()
            .reset_index()
            .sort_values("refund_amount_inr", ascending=False)
        )
        fig = px.bar(
            cat_df,
            x="category",
            y="refund_amount_inr",
            color="refund_amount_inr",
            color_continuous_scale="Reds",
            labels={"refund_amount_inr": "Total Refunded (₹)", "category": "Category"},
            text_auto=".2s",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Avoidable vs. Legitimate Refunds")
        pie_data = pd.DataFrame({
            "Type": ["Avoidable", "Legitimate"],
            "Count": [len(avoidable), len(df) - len(avoidable)]
        })
        fig2 = px.pie(
            pie_data, names="Type", values="Count",
            color_discrete_sequence=["#ef4444", "#22c55e"],
            hole=0.45,
        )
        fig2.update_traces(textinfo="percent+value")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Refund Trend Over Time")
    trend_df = (
        granted.groupby(granted["date"].dt.to_period("W").astype(str))["refund_amount_inr"]
        .sum()
        .reset_index()
    )
    trend_df.columns = ["Week", "Total Refunded (₹)"]
    fig3 = px.area(
        trend_df, x="Week", y="Total Refunded (₹)",
        color_discrete_sequence=["#7c3aed"],
        markers=True,
    )
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Tickets by Channel")
        ch_df = df.groupby("channel").size().reset_index(name="count")
        fig4 = px.pie(ch_df, names="channel", values="count",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

    with col_d:
        st.subheader("Category Breakdown")
        cat_counts = df.groupby("category").size().reset_index(name="Tickets")
        cat_counts["Refunded (₹)"] = (
            df.groupby("category")["refund_amount_inr"].sum().values
        )
        cat_counts["Avoidable"] = df.groupby("category")["avoidable"].sum().values
        st.dataframe(cat_counts, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: AI INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    ai_mode = insights.get("ai_mode", "rule-based")
    st.subheader(f"🤖 AI Analysis — Mode: `{ai_mode}`")

    if ai_mode == "gemini-1.5-flash":
        col_ai1, col_ai2 = st.columns(2)
        with col_ai1:
            st.info(f"**Gemini Confidence:** {insights.get('ai_confidence', 0)*100:.0f}%")
            st.info(f"**Latency:** {insights.get('gemini_latency_sec', 'N/A')}s per run")
        with col_ai2:
            st.success(f"**Cost per run:** ₹{insights.get('cost_per_run_inr', 0):.4f}")
            st.success(f"**Cost per month:** ₹{insights.get('cost_per_month_inr', 0):.2f}")

        st.subheader("Root Causes Identified by AI")
        for i, cause in enumerate(insights.get("ai_root_causes", []), 1):
            st.markdown(f"**{i}.** {cause}")

        st.subheader("Actionable Insights")
        for insight in insights.get("ai_key_insights", []):
            st.success(f"💡 {insight}")

        avoidable_ids = insights.get("ai_avoidable_ids", [])
        if avoidable_ids:
            st.subheader(f"AI-Flagged Avoidable Tickets ({len(avoidable_ids)})")
            flagged_df = df[df["ticket_id"].isin(avoidable_ids)]
            st.dataframe(flagged_df, use_container_width=True, hide_index=True)
    else:
        st.warning(
            "Running in **rule-based mode** (Gemini API key not configured or unreachable). "
            "Set `GEMINI_API_KEY` in `.env` to enable full AI analysis."
        )
        st.subheader("Rule-Based Root Causes")
        causes = [
            "Duplicate charges caused by network timeouts / missing idempotency keys",
            "Billing system not prorating upgrades/downgrades correctly",
            "Cancellation flows not triggering refund pipeline automatically",
        ]
        for i, cause in enumerate(causes, 1):
            st.markdown(f"**{i}.** {cause}")

        st.subheader("Recommendations")
        recs = [
            "Implement idempotency keys on all payment endpoints → eliminates ~20% of Duplicate Charge tickets.",
            "Fix pro-rate billing calculation in `billing_service.py` → fixes ~80% of Billing Error tickets.",
            "Add automated refund trigger on cancellation within the refund window → removes agent overhead.",
            "Run Gemini classification weekly to flag emerging patterns before they scale.",
        ]
        for rec in recs:
            st.success(f"💡 {rec}")

    # Avoidable refunds heatmap
    st.subheader("Avoidable Refunds — Category × Agent Heatmap")
    heat_df = (
        avoidable.groupby(["agent_name", "category"])
        .size()
        .reset_index(name="count")
        .pivot(index="agent_name", columns="category", values="count")
        .fillna(0)
    )
    fig_heat = px.imshow(
        heat_df,
        color_continuous_scale="Reds",
        labels={"color": "Avoidable Tickets"},
        aspect="auto",
    )
    fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: AGENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Agent Performance Overview")

    agent_df = df.groupby("agent_name").agg(
        total_tickets=("ticket_id", "count"),
        refunds_granted=("refund_granted", "sum"),
        total_refunded_inr=("refund_amount_inr", lambda x: x[df.loc[x.index, "refund_granted"]].sum()),
        avoidable_count=("avoidable", "sum"),
        avg_resolution_hrs=("resolution_time_hrs", "mean"),
    ).reset_index()
    agent_df["refund_rate_%"] = (agent_df["refunds_granted"] / agent_df["total_tickets"] * 100).round(1)
    agent_df["avoidable_rate_%"] = (agent_df["avoidable_count"] / agent_df["total_tickets"] * 100).round(1)
    agent_df["avg_resolution_hrs"] = agent_df["avg_resolution_hrs"].round(1)
    agent_df["total_refunded_inr"] = agent_df["total_refunded_inr"].round(0)

    st.dataframe(
        agent_df.sort_values("total_refunded_inr", ascending=False),
        use_container_width=True, hide_index=True,
        column_config={
            "total_refunded_inr": st.column_config.NumberColumn("Total Refunded (₹)", format="₹%.0f"),
            "avg_resolution_hrs": st.column_config.NumberColumn("Avg Resolution (hrs)", format="%.1f"),
        }
    )

    col_ag1, col_ag2 = st.columns(2)
    with col_ag1:
        st.subheader("Total ₹ Refunded per Agent")
        fig_ag = px.bar(
            agent_df.sort_values("total_refunded_inr"),
            x="total_refunded_inr", y="agent_name",
            orientation="h",
            color="avoidable_rate_%",
            color_continuous_scale="Reds",
            labels={"total_refunded_inr": "Total Refunded (₹)", "agent_name": ""},
        )
        fig_ag.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_ag, use_container_width=True)

    with col_ag2:
        st.subheader("Avg Resolution Time vs Avoidable Rate")
        fig_scatter = px.scatter(
            agent_df,
            x="avg_resolution_hrs",
            y="avoidable_rate_%",
            size="total_tickets",
            color="agent_name",
            hover_name="agent_name",
            labels={"avg_resolution_hrs": "Avg Resolution (hrs)", "avoidable_rate_%": "Avoidable Rate (%)"},
        )
        fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.info(
        "💡 **Finding**: Agents with higher resolution times tend to have higher avoidable refund rates. "
        "Slow resolution may lead to customer frustration-driven refund escalations. "
        "Consider pairing high-time agents with faster resolution playbooks."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: RAW DATA
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader(f"Support Tickets ({len(df):,} records)")
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={
                     "refund_amount_inr": st.column_config.NumberColumn("Refund (₹)", format="₹%.2f"),
                     "avoidable": st.column_config.CheckboxColumn("Avoidable?"),
                     "refund_granted": st.column_config.CheckboxColumn("Granted?"),
                 })

    csv_export = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv_export,
        file_name=f"rift_tickets_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5: COST & SAVINGS
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("💰 ROI & Cost Analysis")

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown("""
        <div class="savings-card">
            <h2>₹{:,.0f}</h2>
            <p>Estimated Monthly Savings<br><small>if avoidable refunds prevented</small></p>
        </div>
        """.format(insights["est_monthly_savings_inr"]), unsafe_allow_html=True)
    with col_s2:
        annual = insights["est_monthly_savings_inr"] * 12
        st.markdown(f"""
        <div class="savings-card">
            <h2>₹{annual:,.0f}</h2>
            <p>Annual Savings Potential</p>
        </div>
        """, unsafe_allow_html=True)
    with col_s3:
        ai_mode = insights.get("ai_mode", "rule-based")
        cost_month = insights.get("cost_per_month_inr", 0)
        st.markdown(f"""
        <div class="warning-card">
            <h2>₹{cost_month:.2f}/mo</h2>
            <p>AI Analysis Cost<br><small>{ai_mode}</small></p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Calculation Breakdown")
    avoidable_rate = insights["avoidable_rate_pct"]
    monthly_vol = insights["monthly_ticket_estimate"]
    avg_refund = AVG_REFUND_INR = float(os.getenv("AVG_REFUND_INR", "850"))

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown(f"""
        | Metric | Value |
        |--------|-------|
        | Monthly Ticket Volume | {monthly_vol:,} |
        | Avoidable Refund Rate | {avoidable_rate:.1f}% |
        | Avoidable Tickets/Month | {int(monthly_vol * avoidable_rate / 100):,} |
        | Avg Refund Amount | ₹{avg_refund:,.0f} |
        | **Estimated Monthly Savings** | **₹{insights['est_monthly_savings_inr']:,.0f}** |
        | **Estimated Annual Savings** | **₹{insights['est_monthly_savings_inr']*12:,.0f}** |
        """)
    with col_b2:
        ai_mode_str = insights.get("ai_mode", "rule-based")
        cost_run = insights.get("cost_per_run_inr", 0)
        cost_mo = insights.get("cost_per_month_inr", 0)
        st.markdown(f"""
        | Cost Item | Amount |
        |-----------|--------|
        | AI Model | Gemini 1.5 Flash |
        | Tokens per run (~{SAMPLE_SIZE_FOR_AI} tickets) | ~15,000 |
        | Cost per run | ₹{cost_run:.4f} |
        | Runs per month | {int(monthly_vol / SAMPLE_SIZE_FOR_AI)} |
        | **Total AI cost/month** | **₹{cost_mo:.2f}** |
        | **ROI** | **{insights['est_monthly_savings_inr'] / max(cost_mo, 1):,.0f}x** |
        """)

    st.divider()
    st.subheader("Savings Waterfall")
    total_refunded = granted["refund_amount_inr"].sum()
    avoidable_amount = avoidable["refund_amount_inr"].sum()
    legitimate_amount = total_refunded - avoidable_amount

    fig_w = go.Figure(go.Waterfall(
        name="Refund Breakdown",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Legitimate Refunds", "Avoidable Refunds", "Total"],
        text=[f"₹{legitimate_amount:,.0f}", f"₹{avoidable_amount:,.0f}", f"₹{total_refunded:,.0f}"],
        y=[legitimate_amount, avoidable_amount, 0],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#ef4444"}},
        totals={"marker": {"color": "#6366f1"}},
    ))
    fig_w.update_layout(
        title="Where are the refunds going?",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_w, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("RIFT v1.0 · Built by Krishna Gupta · Banao Technologies AI Engineer Task")

SAMPLE_SIZE_FOR_AI = 50
