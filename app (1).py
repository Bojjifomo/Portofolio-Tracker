"""
Net Worth Portfolio Tracker
Streamlit app — yield diinput harian, diakumulasikan otomatis per bulan.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import calendar
from datetime import datetime

# ============================================================
# KONFIGURASI
# ============================================================
st.set_page_config(
    page_title="Networth Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "portfolio_data.json"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
          "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

CATEGORIES = [
    {"key": "saham",     "label": "Saham",     "color": "#22c55e", "yield_label": "Dividen"},
    {"key": "crypto",    "label": "Crypto",    "color": "#f59e0b", "yield_label": "Staking/Airdrop"},
    {"key": "deposito",  "label": "Deposito",  "color": "#3b82f6", "yield_label": "Bunga"},
    {"key": "reksadana", "label": "Reksadana", "color": "#8b5cf6", "yield_label": "Return"},
    {"key": "emas",      "label": "Emas",      "color": "#eab308", "yield_label": "Yield"},
    {"key": "cash",      "label": "Cash",      "color": "#6b7280", "yield_label": "Bunga"},
    {"key": "properti",  "label": "Properti",  "color": "#ec4899", "yield_label": "Sewa/Yield"},
    {"key": "lainnya",   "label": "Lainnya",   "color": "#14b8a6", "yield_label": "Yield"},
]

st.markdown("""
<style>
    .main { background-color: #020617; }
    .stApp { background-color: #020617; color: #e2e8f0; }
    h1, h2, h3, h4 { color: #e2e8f0 !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem; }
    [data-testid="stSidebar"] { background-color: #0f172a; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# UTILITIES
# ============================================================
def fmt_rp(v):
    try:
        return f"Rp {int(v):,}".replace(",", ".")
    except Exception:
        return "Rp 0"

def fmt_short(v):
    try:
        v = float(v)
        if v >= 1e9: return f"Rp{v/1e9:.1f}B"
        if v >= 1e6: return f"Rp{v/1e6:.1f}M"
        if v >= 1e3: return f"Rp{v/1e3:.0f}K"
        return f"Rp{int(v)}"
    except Exception:
        return "Rp0"

def days_in(year, month_idx):
    """Jumlah hari di bulan tertentu (month_idx 0=Jan)."""
    return calendar.monthrange(int(year), int(month_idx) + 1)[1]

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            return [migrate_entry(e) for e in data]
        except Exception:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def migrate_entry(e):
    """Migrate data lama: yields bulanan -> yields_daily harian."""
    if "yields_daily" not in e:
        days = days_in(e["year"], e["month"])
        old_monthly = e.get("yields", {})
        e["yields_daily"] = {k: (v / days if days else 0) for k, v in old_monthly.items()}
    return e

def monthly_yield(e, category_key):
    """Hitung yield bulanan dari yield harian × jumlah hari di bulan itu."""
    daily = e.get("yields_daily", {}).get(category_key, 0)
    return daily * days_in(e["year"], e["month"])

def total_monthly_yield(e):
    return sum(monthly_yield(e, c["key"]) for c in CATEGORIES)

def entry_timestamp(year, month):
    return datetime(year, month + 1, 1).timestamp()

def sort_entries(entries):
    return sorted(entries, key=lambda e: e["ts"])

# ============================================================
# INIT STATE
# ============================================================
if "entries" not in st.session_state:
    st.session_state.entries = load_data()
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "page" not in st.session_state:
    st.session_state.page = "📈 Dashboard"

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("# 📊 NETWORTH TRACKER")
st.sidebar.caption("Portfolio · Daily Yield · Passive Income")
st.sidebar.markdown("---")

PAGES = ["📈 Dashboard", "➕ Tambah / Edit Data", "📜 Riwayat", "🔍 Analisis"]
current_idx = PAGES.index(st.session_state.page) if st.session_state.page in PAGES else 0
selected = st.sidebar.radio("Menu", PAGES, index=current_idx, label_visibility="collapsed")
if selected != st.session_state.page:
    st.session_state.page = selected
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Total entries: **{len(st.session_state.entries)}**")

if st.sidebar.button("🗑️ Reset All Data", use_container_width=True):
    st.session_state.entries = []
    save_data([])
    st.session_state.edit_idx = None
    st.rerun()

with st.sidebar.expander("💾 Backup / Restore"):
    if st.session_state.entries:
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(st.session_state.entries, indent=2),
            file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )
    uploaded = st.file_uploader("⬆️ Upload JSON", type=["json"])
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            st.session_state.entries = [migrate_entry(e) for e in data]
            save_data(st.session_state.entries)
            st.success("Data berhasil diimpor!")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal impor: {e}")

# ============================================================
# DASHBOARD
# ============================================================
def render_dashboard():
    st.title("Dashboard")
    entries = sort_entries(st.session_state.entries)

    if not entries:
        st.info("Belum ada data. Silakan tambahkan data bulanan pertama di menu **Tambah Data**.")
        if st.button("➕ Tambah Data Pertama", type="primary"):
            st.session_state.page = "➕ Tambah / Edit Data"
            st.rerun()
        return

    latest = entries[-1]
    prev = entries[-2] if len(entries) > 1 else None

    latest_monthly_yield = total_monthly_yield(latest)
    latest_days = days_in(latest["year"], latest["month"])
    latest_daily_yield = latest_monthly_yield / latest_days if latest_days else 0

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Net Worth", fmt_rp(latest["total"]), help=f"Data per {latest['label']}")
    with col2:
        if prev:
            delta = latest["total"] - prev["total"]
            pct = (delta / prev["total"] * 100) if prev["total"] else 0
            st.metric("Perubahan Bulan Ini", f"{pct:+.2f}%", delta=fmt_short(delta))
        else:
            st.metric("Perubahan Bulan Ini", "—")
    with col3:
        yield_pa = (latest_monthly_yield / latest["total"] * 100 * 12) if latest["total"] else 0
        st.metric(
            f"💰 Passive Income ({latest['label']})",
            fmt_rp(latest_monthly_yield),
            delta=f"≈ {fmt_short(latest_daily_yield)}/hari · {yield_pa:.1f}% p.a.",
            delta_color="off",
        )
    with col4:
        total_pi = sum(total_monthly_yield(e) for e in entries)
        avg_pi = total_pi / len(entries) if entries else 0
        st.metric("Avg Yield / Bulan", fmt_rp(round(avg_pi)),
                  delta=f"Total: {fmt_short(total_pi)}", delta_color="off")

    st.markdown("---")

    # Chart data
    df = pd.DataFrame([
        {"bulan": e["label"],
         "Net Worth": e["total"],
         "Yield": total_monthly_yield(e),
         **{c["key"]: e["values"].get(c["key"], 0) for c in CATEGORIES}}
        for e in entries
    ])

    # Main chart
    st.subheader("Net Worth & Passive Income")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=df["bulan"], y=df["Net Worth"],
        mode="lines+markers", name="Net Worth",
        line=dict(color="#22c55e", width=3),
        fill="tozeroy", fillcolor="rgba(34,197,94,0.15)",
        marker=dict(size=8),
    ), secondary_y=False)
    fig.add_trace(go.Bar(
        x=df["bulan"], y=df["Yield"],
        name="Yield Bulanan", marker_color="#f59e0b", opacity=0.7,
    ), secondary_y=True)
    fig.update_layout(
        height=380, template="plotly_dark",
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=0, r=0, t=20, b=0),
    )
    fig.update_yaxes(title_text="Net Worth (Rp)", secondary_y=False, gridcolor="#1e293b")
    fig.update_yaxes(title_text="Yield (Rp)", secondary_y=True, gridcolor="#1e293b")
    fig.update_xaxes(gridcolor="#1e293b")
    st.plotly_chart(fig, use_container_width=True)

    # MoM Change
    if len(entries) > 1:
        st.subheader("Perubahan Bulanan (%)")
        changes = []
        for i in range(1, len(entries)):
            prev_t = entries[i-1]["total"]
            cur_t = entries[i]["total"]
            ch = (cur_t - prev_t) / prev_t * 100 if prev_t else 0
            changes.append({"bulan": entries[i]["label"], "change": ch})
        df_ch = pd.DataFrame(changes)
        fig = go.Figure(go.Bar(
            x=df_ch["bulan"], y=df_ch["change"],
            marker_color=["#22c55e" if v >= 0 else "#ef4444" for v in df_ch["change"]],
            text=[f"{v:+.1f}%" for v in df_ch["change"]],
            textposition="outside",
        ))
        fig.update_layout(
            height=300, template="plotly_dark",
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            yaxis_title="Perubahan (%)", showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        fig.update_yaxes(gridcolor="#1e293b")
        fig.update_xaxes(gridcolor="#1e293b")
        st.plotly_chart(fig, use_container_width=True)

    # Allocation + Yield
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Alokasi Aset")
        alloc_data = [(c["label"], latest["values"].get(c["key"], 0), c["color"])
                      for c in CATEGORIES if latest["values"].get(c["key"], 0) > 0]
        if alloc_data:
            labels, values, colors = zip(*alloc_data)
            fig = go.Figure(go.Pie(
                labels=labels, values=values,
                marker=dict(colors=colors), hole=0.5,
                textinfo="percent", textposition="inside",
            ))
            fig.update_layout(
                height=360, template="plotly_dark",
                plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                margin=dict(l=0, r=0, t=20, b=0),
                legend=dict(orientation="v", x=1.05, y=0.5),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada alokasi aset.")

    with col2:
        st.subheader("Yield Bulanan per Kategori")
        yield_data = []
        for c in CATEGORIES:
            my = monthly_yield(latest, c["key"])
            if my > 0:
                yield_data.append((c["label"], my, c["color"]))
        if yield_data:
            labels, values, colors = zip(*yield_data)
            fig = go.Figure(go.Bar(
                x=values, y=labels, orientation="h",
                marker_color=colors,
                text=[fmt_short(v) for v in values],
                textposition="outside",
            ))
            fig.update_layout(
                height=360, template="plotly_dark",
                plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
                xaxis_title=f"Yield ({latest_days} hari)", showlegend=False,
                margin=dict(l=0, r=0, t=20, b=0),
            )
            fig.update_yaxes(gridcolor="#1e293b")
            fig.update_xaxes(gridcolor="#1e293b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada yield.")

    # Stacked composition
    if len(entries) > 1:
        st.subheader("Komposisi Aset Over Time")
        fig = go.Figure()
        for c in CATEGORIES:
            fig.add_trace(go.Scatter(
                x=df["bulan"], y=df[c["key"]],
                mode="lines", stackgroup="one", name=c["label"],
                line=dict(width=0.5, color=c["color"]),
                fillcolor=c["color"],
            ))
        fig.update_layout(
            height=320, template="plotly_dark",
            plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation="h", y=-0.2),
        )
        fig.update_yaxes(gridcolor="#1e293b")
        fig.update_xaxes(gridcolor="#1e293b")
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# INPUT
# ============================================================
def render_input():
    is_edit = st.session_state.edit_idx is not None
    st.title("✏️ Edit Data" if is_edit else "➕ Tambah Data Bulanan")

    if is_edit:
        edit_entry = st.session_state.entries[st.session_state.edit_idx]
        default_year = edit_entry["year"]
        default_month = edit_entry["month"]
        default_desc = edit_entry.get("description", "")
        default_values = {c["key"]: edit_entry["values"].get(c["key"], 0) for c in CATEGORIES}
        default_daily = {c["key"]: edit_entry.get("yields_daily", {}).get(c["key"], 0) for c in CATEGORIES}
    else:
        now = datetime.now()
        default_year = now.year
        default_month = now.month - 1
        default_desc = ""
        default_values = {c["key"]: 0 for c in CATEGORIES}
        default_daily = {c["key"]: 0 for c in CATEGORIES}

    # Year & month PICKERS OUTSIDE form biar days_in_month live-update
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Tahun", min_value=2000, max_value=2100,
                               value=default_year, step=1, key="input_year")
    with col2:
        month = st.selectbox("Bulan", options=list(range(12)),
                             format_func=lambda x: MONTHS[x], index=default_month,
                             key="input_month")

    days = days_in(year, month)
    st.info(f"📅 **{MONTHS[month]} {year}** punya **{days} hari** — yield harian akan dikali {days} untuk total bulan ini.")

    with st.form("input_form", clear_on_submit=False):
        description = st.text_area(
            "📝 Deskripsi / Catatan",
            value=default_desc,
            placeholder="Contoh: Bulan ini dapat dividen BBCA, top up crypto, staking USDT di exchange...",
            height=80,
        )

        st.markdown("##### Detail Aset & Yield Harian")
        st.caption(f"Isi nilai aset + **yield per hari** per kategori. Sistem akan mengalikan dengan {days} hari untuk total bulan ini.")

        values = {}
        daily_yields = {}
        for c in CATEGORIES:
            cols = st.columns([1.2, 2, 2, 1.5])
            with cols[0]:
                st.markdown(
                    f"<div style='padding-top:28px;'>"
                    f"<span style='color:{c['color']}; font-size:18px;'>●</span> "
                    f"<b>{c['label']}</b></div>",
                    unsafe_allow_html=True,
                )
            with cols[1]:
                values[c["key"]] = st.number_input(
                    "Nilai Aset (Rp)",
                    min_value=0.0, value=float(default_values[c["key"]]),
                    step=1_000_000.0, format="%.0f",
                    key=f"val_{c['key']}",
                )
            with cols[2]:
                daily_yields[c["key"]] = st.number_input(
                    f"{c['yield_label']} / hari (Rp)",
                    min_value=0.0, value=float(default_daily[c["key"]]),
                    step=10_000.0, format="%.0f",
                    key=f"dly_{c['key']}",
                )
            with cols[3]:
                monthly = daily_yields[c["key"]] * days
                st.markdown(
                    f"<div style='padding-top:28px;'>"
                    f"<small style='color:#64748b;'>= {days} hari</small><br>"
                    f"<b style='color:#f59e0b;'>{fmt_short(monthly)}</b>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        total_asset = sum(values.values())
        total_daily_yield = sum(daily_yields.values())
        total_monthly_yld = total_daily_yield * days

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Aset", fmt_rp(total_asset))
        with col2:
            st.metric("Yield / Hari", fmt_rp(total_daily_yield))
        with col3:
            st.metric(f"Total Yield Bulan Ini ({days} hari)", fmt_rp(total_monthly_yld),
                     delta=f"≈ {(total_monthly_yld/total_asset*100*12):.1f}% p.a." if total_asset else None,
                     delta_color="off")

        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button(
                "💾 Simpan & Lihat Dashboard" if not is_edit else "✅ Update & Lihat Dashboard",
                use_container_width=True, type="primary",
            )
        with col2:
            cancel = st.form_submit_button("❌ Batal", use_container_width=True) if is_edit else False

        if cancel:
            st.session_state.edit_idx = None
            st.session_state.page = "📈 Dashboard"
            st.rerun()

        if submit:
            entry = {
                "year": int(year),
                "month": int(month),
                "label": f"{MONTHS[month]} {year}",
                "ts": entry_timestamp(int(year), int(month)),
                "description": description,
                "values": {k: float(v) for k, v in values.items()},
                "yields_daily": {k: float(v) for k, v in daily_yields.items()},
                "total": float(total_asset),
            }
            if is_edit:
                st.session_state.entries[st.session_state.edit_idx] = entry
                st.session_state.edit_idx = None
            else:
                existing_idx = None
                for i, e in enumerate(st.session_state.entries):
                    if e["year"] == entry["year"] and e["month"] == entry["month"]:
                        existing_idx = i
                        break
                if existing_idx is not None:
                    st.session_state.entries[existing_idx] = entry
                else:
                    st.session_state.entries.append(entry)

            st.session_state.entries = sort_entries(st.session_state.entries)
            save_data(st.session_state.entries)
            st.session_state.page = "📈 Dashboard"
            st.toast(f"✅ Data {entry['label']} berhasil disimpan!", icon="🎉")
            st.rerun()


# ============================================================
# HISTORY
# ============================================================
def render_history():
    st.title("📜 Riwayat Data")
    entries = sort_entries(st.session_state.entries)

    if not entries:
        st.info("Belum ada data.")
        return

    for i, e in enumerate(entries):
        prev_t = entries[i-1]["total"] if i > 0 else None
        ch_pct = ((e["total"] - prev_t) / prev_t * 100) if prev_t else None
        my = total_monthly_yield(e)
        days = days_in(e["year"], e["month"])

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1.5])
            with col1:
                st.markdown(f"**{e['label']}** · _{days} hari_")
                if e.get("description"):
                    st.caption(f"📝 {e['description']}")
            with col2:
                st.metric("Net Worth", fmt_short(e["total"]),
                         delta=f"{ch_pct:+.2f}%" if ch_pct is not None else None)
            with col3:
                st.metric(f"💰 Yield ({days} hari)", fmt_short(my),
                         delta=f"{fmt_short(my/days if days else 0)}/hari", delta_color="off")
            with col4:
                real_idx = st.session_state.entries.index(e)
                if st.button("✏️ Edit", key=f"edit_{i}", use_container_width=True):
                    st.session_state.edit_idx = real_idx
                    st.session_state.page = "➕ Tambah / Edit Data"
                    st.rerun()
                if st.button("🗑️ Hapus", key=f"del_{i}", use_container_width=True):
                    st.session_state.entries.pop(real_idx)
                    save_data(st.session_state.entries)
                    st.rerun()

            with st.expander("Detail per kategori"):
                detail_cols = st.columns(4)
                shown = 0
                for c in CATEGORIES:
                    val = e["values"].get(c["key"], 0)
                    daily = e.get("yields_daily", {}).get(c["key"], 0)
                    month_val = daily * days
                    if val or month_val:
                        with detail_cols[shown % 4]:
                            html = (
                                f"<div style='border-left:3px solid {c['color']}; padding-left:8px; margin-bottom:8px;'>"
                                f"<small>{c['label']}</small><br>"
                                f"<b>{fmt_short(val)}</b>"
                            )
                            if month_val:
                                html += (
                                    f"<br><small style='color:#f59e0b;'>"
                                    f"{fmt_short(daily)}/hari × {days} = {fmt_short(month_val)}"
                                    f"</small>"
                                )
                            html += "</div>"
                            st.markdown(html, unsafe_allow_html=True)
                        shown += 1


# ============================================================
# ANALYSIS
# ============================================================
def render_analysis():
    st.title("🔍 Analisis Portfolio")
    entries = sort_entries(st.session_state.entries)

    if len(entries) < 2:
        st.warning("Butuh minimal 2 bulan data untuk analisis.")
        return

    latest = entries[-1]
    prev = entries[-2]

    changes = []
    for i in range(1, len(entries)):
        prev_t = entries[i-1]["total"]
        cur_t = entries[i]["total"]
        ch = (cur_t - prev_t) / prev_t * 100 if prev_t else 0
        changes.append({"label": entries[i]["label"], "change": ch})

    best = max(changes, key=lambda x: x["change"])
    worst = min(changes, key=lambda x: x["change"])
    avg_growth = sum(c["change"] for c in changes) / len(changes)

    years = (entries[-1]["ts"] - entries[0]["ts"]) / (60 * 60 * 24 * 365.25)
    cagr = ((entries[-1]["total"] / entries[0]["total"]) ** (1 / years) - 1) * 100 if years > 0 and entries[0]["total"] > 0 else 0

    total_pi = sum(total_monthly_yield(e) for e in entries)
    avg_pi = total_pi / len(entries)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📈 Bulan Terbaik", best["label"], delta=f"+{best['change']:.2f}%")
    with col2:
        st.metric("📉 Bulan Terburuk", worst["label"], delta=f"{worst['change']:.2f}%")
    with col3:
        st.metric("📊 Avg Growth/bln", f"{avg_growth:+.2f}%")
    with col4:
        st.metric("🎯 CAGR", f"{cagr:.2f}%", delta="Annualized", delta_color="off")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Passive Income", fmt_rp(total_pi),
                 delta=f"{len(entries)} bulan", delta_color="off")
    with col2:
        pi_pa = (avg_pi / latest["total"] * 100 * 12) if latest["total"] else 0
        st.metric("💰 Avg Yield/bulan", fmt_rp(round(avg_pi)),
                 delta=f"{pi_pa:.1f}% p.a.", delta_color="off")
    with col3:
        total_growth = entries[-1]["total"] - entries[0]["total"]
        st.metric("💎 Pertumbuhan Total", fmt_short(total_growth),
                 delta=f"{entries[0]['label']} → {entries[-1]['label']}", delta_color="off")
    with col4:
        st.metric("📅 Periode", f"{len(entries)} bulan")

    st.markdown("---")

    # Passive income trend
    st.subheader("Trend Passive Income Bulanan")
    df_pi = pd.DataFrame([{
        "bulan": e["label"],
        "yield": total_monthly_yield(e),
        "harian": total_monthly_yield(e) / days_in(e["year"], e["month"]),
    } for e in entries])
    fig = go.Figure(go.Bar(
        x=df_pi["bulan"], y=df_pi["yield"],
        marker_color="#f59e0b",
        text=[fmt_short(v) for v in df_pi["yield"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Bulanan: %{y:,.0f}<br>Harian avg: %{customdata:,.0f}<extra></extra>",
        customdata=df_pi["harian"],
    ))
    fig.update_layout(
        height=300, template="plotly_dark",
        plot_bgcolor="#0f172a", paper_bgcolor="#0f172a",
        yaxis_title="Yield Bulanan (Rp)", showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    fig.update_yaxes(gridcolor="#1e293b")
    fig.update_xaxes(gridcolor="#1e293b")
    st.plotly_chart(fig, use_container_width=True)

    # Per category detail
    st.subheader("Detail per Kategori (Latest vs Previous)")
    latest_days = days_in(latest["year"], latest["month"])
    cat_cols = st.columns(4)
    shown = 0
    for c in CATEGORIES:
        cur = latest["values"].get(c["key"], 0)
        prv = prev["values"].get(c["key"], 0)
        daily = latest.get("yields_daily", {}).get(c["key"], 0)
        my = daily * latest_days
        if not cur and not my:
            continue
        ch = ((cur - prv) / prv * 100) if prv else None
        alloc = (cur / latest["total"] * 100) if latest["total"] else 0
        with cat_cols[shown % 4]:
            with st.container(border=True):
                st.markdown(f"<small style='color:#94a3b8;'>{c['label']}</small>", unsafe_allow_html=True)
                st.markdown(f"**{fmt_short(cur)}**")
                if ch is not None:
                    color = "#22c55e" if ch >= 0 else "#ef4444"
                    st.markdown(f"<small style='color:{color};'>{ch:+.2f}%</small>", unsafe_allow_html=True)
                if my > 0:
                    st.markdown(
                        f"<small style='color:#f59e0b;'>"
                        f"{fmt_short(daily)}/hari → {fmt_short(my)}/bln"
                        f"</small>", unsafe_allow_html=True,
                    )
                st.markdown(f"<small style='color:#64748b;'>Alokasi: {alloc:.1f}%</small>", unsafe_allow_html=True)
        shown += 1

    # Diversification
    st.markdown("---")
    st.subheader("Skor Diversifikasi")
    alloc_values = [latest["values"].get(c["key"], 0) for c in CATEGORIES]
    active = [v for v in alloc_values if v > 0]
    if active:
        total = sum(active)
        hhi = sum((v / total) ** 2 for v in active)
        score = round((1 - hhi) * 100)
        if score > 70:
            level, color = "Baik", "#22c55e"
        elif score > 40:
            level, color = "Cukup", "#f59e0b"
        else:
            level, color = "Perlu perbaikan", "#ef4444"
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(
                f"<div style='text-align:center; font-size:60px; color:{color}; font-weight:bold;'>{score}</div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(f"### <span style='color:{color};'>{level}</span>", unsafe_allow_html=True)
            st.caption(f"{len(active)} kategori aktif · HHI: {hhi*10000:.0f}")
            if score <= 40:
                st.info("💡 Pertimbangkan untuk mendiversifikasi ke lebih banyak kelas aset.")

    # Export
    st.markdown("---")
    df_export = pd.DataFrame([
        {"Periode": e["label"],
         "Hari": days_in(e["year"], e["month"]),
         "Total": e["total"],
         "Yield Bulanan": total_monthly_yield(e),
         "Yield Harian": total_monthly_yield(e) / days_in(e["year"], e["month"]),
         "Deskripsi": e.get("description", ""),
         **{c["label"]: e["values"].get(c["key"], 0) for c in CATEGORIES}}
        for e in entries
    ])
    st.download_button(
        "📊 Download data sebagai CSV",
        data=df_export.to_csv(index=False).encode("utf-8"),
        file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# ============================================================
# ROUTING
# ============================================================
if st.session_state.page == "📈 Dashboard":
    render_dashboard()
elif st.session_state.page == "➕ Tambah / Edit Data":
    render_input()
elif st.session_state.page == "📜 Riwayat":
    render_history()
elif st.session_state.page == "🔍 Analisis":
    render_analysis()

st.sidebar.markdown("---")
st.sidebar.caption("💡 Data disimpan otomatis di `portfolio_data.json`")
