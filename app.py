"""
Net Worth Portfolio Tracker — v5
- Input di bulan yang sama = AKUMULASI (ditambahkan, bukan ditimpa)
- Edit = replace (dari halaman Riwayat)
- Yield input harian, auto-akumulasi per bulan
- Auto-redirect ke Dashboard setelah submit
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
    if "yields_daily" not in e:
        days = days_in(e["year"], e["month"])
        old_monthly = e.get("yields", {})
        e["yields_daily"] = {k: (v / days if days else 0) for k, v in old_monthly.items()}
    if "descriptions" not in e:
        old_desc = e.get("description", "")
        e["descriptions"] = [old_desc] if old_desc else []
    return e

def monthly_yield(e, category_key):
    daily = e.get("yields_daily", {}).get(category_key, 0)
    return daily * days_in(e["year"], e["month"])

def total_monthly_yield(e):
    return sum(monthly_yield(e, c["key"]) for c in CATEGORIES)

def entry_timestamp(year, month):
    return datetime(year, month + 1, 1).timestamp()

def sort_entries(entries):
    return sorted(entries, key=lambda e: e["ts"])

def next_month_after_latest(entries):
    if not entries:
        now = datetime.now()
        return now.year, now.month - 1
    latest = sort_entries(entries)[-1]
    y, m = latest["year"], latest["month"]
    m += 1
    if m > 11:
        m = 0
        y += 1
    return y, m

def find_entry_idx(entries, year, month):
    """Cari index entry di bulan tertentu, return None kalau ga ada."""
    for i, e in enumerate(entries):
        if e["year"] == year and e["month"] == month:
            return i
    return None

def accumulate_entry(existing, new_values, new_daily_yields, new_desc):
    """Tambahkan data baru ke entry yang udah ada (AKUMULASI)."""
    for c in CATEGORIES:
        k = c["key"]
        existing["values"][k] = existing["values"].get(k, 0) + new_values.get(k, 0)
        existing["yields_daily"][k] = existing["yields_daily"].get(k, 0) + new_daily_yields.get(k, 0)
    existing["total"] = sum(existing["values"].get(c["key"], 0) for c in CATEGORIES)
    if new_desc.strip():
        existing.setdefault("descriptions", [])
        existing["descriptions"].append(new_desc.strip())
    return existing

# ============================================================
# INIT STATE
# ============================================================
if "entries" not in st.session_state:
    st.session_state.entries = load_data()
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None
if "page" not in st.session_state:
    st.session_state.page = "📈 Dashboard"
if "form_iter" not in st.session_state:
    st.session_state.form_iter = 0
if "flash" not in st.session_state:
    st.session_state.flash = None

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("# 📊 NETWORTH TRACKER")
st.sidebar.caption("Portfolio · Daily Yield · Passive Income")
st.sidebar.markdown("---")

PAGES = ["📈 Dashboard", "➕ Tambah Data", "✏️ Edit (via Riwayat)", "📜 Riwayat", "🔍 Analisis"]
VISIBLE_PAGES = ["📈 Dashboard", "➕ Tambah Data", "📜 Riwayat", "🔍 Analisis"]
current_idx = VISIBLE_PAGES.index(st.session_state.page) if st.session_state.page in VISIBLE_PAGES else 0
selected = st.sidebar.radio("Menu", VISIBLE_PAGES, index=current_idx, label_visibility="collapsed")
if selected != st.session_state.page:
    st.session_state.page = selected
    st.session_state.edit_idx = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Total entries: **{len(st.session_state.entries)}**")

if st.sidebar.button("🗑️ Reset All Data", use_container_width=True):
    st.session_state.entries = []
    save_data([])
    st.session_state.edit_idx = None
    st.session_state.form_iter += 1
    st.rerun()

with st.sidebar.expander("💾 Backup / Restore"):
    st.caption("⚠️ Download backup JSON secara berkala!")
    if st.session_state.entries:
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(st.session_state.entries, indent=2),
            file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
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
    st.title("📈 Dashboard")

    if st.session_state.flash:
        msg, level = st.session_state.flash
        getattr(st, level, st.info)(msg)
        st.session_state.flash = None

    entries = sort_entries(st.session_state.entries)

    if not entries:
        st.info("Belum ada data. Silakan tambahkan data bulanan pertama.")
        if st.button("➕ Tambah Data Pertama", type="primary"):
            st.session_state.page = "➕ Tambah Data"
            st.rerun()
        return

    latest = entries[-1]
    prev = entries[-2] if len(entries) > 1 else None

    latest_my = total_monthly_yield(latest)
    latest_days = days_in(latest["year"], latest["month"])
    latest_daily = latest_my / latest_days if latest_days else 0

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
        yield_pa = (latest_my / latest["total"] * 100 * 12) if latest["total"] else 0
        st.metric(
            f"💰 Passive Income ({latest['label']})",
            fmt_rp(latest_my),
            delta=f"≈ {fmt_short(latest_daily)}/hari · {yield_pa:.1f}% p.a.",
            delta_color="off",
        )
    with col4:
        total_pi = sum(total_monthly_yield(e) for e in entries)
        avg_pi = total_pi / len(entries)
        st.metric("Avg Yield / Bulan", fmt_rp(round(avg_pi)),
                  delta=f"Total: {fmt_short(total_pi)}", delta_color="off")

    # Latest descriptions
    descs = latest.get("descriptions", [])
    if descs:
        with st.expander(f"📝 Catatan {latest['label']} ({len(descs)} input)", expanded=False):
            for idx, d in enumerate(descs, 1):
                st.markdown(f"**#{idx}:** {d}")

    st.markdown("---")

    df = pd.DataFrame([
        {"bulan": e["label"],
         "Net Worth": e["total"],
         "Yield": total_monthly_yield(e),
         **{c["key"]: e["values"].get(c["key"], 0) for c in CATEGORIES}}
        for e in entries
    ])

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

    with col2:
        st.subheader("Yield per Kategori")
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
# TAMBAH DATA (AKUMULASI kalau bulan sama)
# ============================================================
def render_add():
    st.title("➕ Tambah Data")

    s = st.session_state.form_iter
    key_suffix = f"{s}_add"

    # Default ke bulan yang sama (biar bisa akumulasi) atau bulan berikutnya
    now = datetime.now()
    default_year, default_month = now.year, now.month - 1

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Tahun", min_value=2000, max_value=2100,
                               value=default_year, step=1, key=f"yr_{key_suffix}")
    with col2:
        month = st.selectbox("Bulan", options=list(range(12)),
                             format_func=lambda x: MONTHS[x], index=default_month,
                             key=f"mo_{key_suffix}")

    days = days_in(year, month)

    # Check existing
    existing_idx = find_entry_idx(st.session_state.entries, year, month)
    if existing_idx is not None:
        existing = st.session_state.entries[existing_idx]
        st.success(
            f"📦 **{MONTHS[month]} {year}** sudah ada data sebelumnya "
            f"(Net Worth: {fmt_rp(existing['total'])}, "
            f"Yield/hari: {fmt_rp(sum(existing.get('yields_daily', {}).values()))}). "
            f"Data yang kamu input sekarang akan **DITAMBAHKAN** ke data yang udah ada."
        )
    else:
        st.info(f"📅 **{MONTHS[month]} {year}** — entry baru ({days} hari). Yield harian × {days} = total bulan ini.")

    with st.form(f"add_form_{key_suffix}", clear_on_submit=False):
        description = st.text_area(
            "📝 Catatan input ini",
            value="",
            placeholder="Contoh: Tambah saham BBCA 10 lot, staking ETH mulai hari ini...",
            height=80,
            key=f"desc_{key_suffix}",
        )

        st.markdown("##### Nilai Aset & Yield Harian yang Ditambahkan")
        if existing_idx is not None:
            st.caption(f"⚡ Nilai yang kamu isi akan **ditambahkan** ke data {MONTHS[month]} {year} yang sudah ada.")
        else:
            st.caption(f"Isi nilai aset + yield per hari. Sistem akan × {days} hari untuk total bulan.")

        values = {}
        daily_yields = {}
        for c in CATEGORIES:
            cols = st.columns([1.2, 2, 2, 1.5])
            with cols[0]:
                existing_val = 0
                existing_daily = 0
                if existing_idx is not None:
                    existing_val = existing["values"].get(c["key"], 0)
                    existing_daily = existing.get("yields_daily", {}).get(c["key"], 0)

                label_html = (
                    f"<div style='padding-top:28px;'>"
                    f"<span style='color:{c['color']}; font-size:18px;'>●</span> "
                    f"<b>{c['label']}</b>"
                )
                if existing_idx is not None and (existing_val or existing_daily):
                    label_html += f"<br><small style='color:#64748b;'>Saat ini: {fmt_short(existing_val)}</small>"
                label_html += "</div>"
                st.markdown(label_html, unsafe_allow_html=True)

            with cols[1]:
                values[c["key"]] = st.number_input(
                    "Tambah Aset (Rp)",
                    min_value=0.0, value=0.0,
                    step=1_000_000.0, format="%.0f",
                    key=f"val_{c['key']}_{key_suffix}",
                )
            with cols[2]:
                daily_yields[c["key"]] = st.number_input(
                    f"Tambah {c['yield_label']} / hari (Rp)",
                    min_value=0.0, value=0.0,
                    step=10_000.0, format="%.0f",
                    key=f"dly_{c['key']}_{key_suffix}",
                )
            with cols[3]:
                new_monthly = daily_yields[c["key"]] * days
                if existing_idx is not None:
                    old_monthly = existing.get("yields_daily", {}).get(c["key"], 0) * days
                    total_m = old_monthly + new_monthly
                    new_total_val = existing["values"].get(c["key"], 0) + values[c["key"]]
                    st.markdown(
                        f"<div style='padding-top:18px;'>"
                        f"<small style='color:#64748b;'>+ {fmt_short(new_monthly)}</small><br>"
                        f"<b style='color:#22c55e;'>Total: {fmt_short(new_total_val)}</b><br>"
                        f"<small style='color:#f59e0b;'>Yield: {fmt_short(total_m)}/bln</small>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='padding-top:28px;'>"
                        f"<small style='color:#64748b;'>= {days} hari</small><br>"
                        f"<b style='color:#f59e0b;'>{fmt_short(new_monthly)}</b>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        total_new_asset = sum(values.values())
        total_new_daily = sum(daily_yields.values())
        total_new_monthly = total_new_daily * days

        st.markdown("---")

        if existing_idx is not None:
            grand_asset = existing["total"] + total_new_asset
            grand_daily = sum(existing.get("yields_daily", {}).values()) + total_new_daily
            grand_monthly = grand_daily * days
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Yang Ditambahkan", fmt_rp(total_new_asset))
            with col2:
                st.metric("TOTAL Aset Setelah Akumulasi", fmt_rp(grand_asset))
            with col3:
                st.metric(f"TOTAL Yield/bulan ({days} hari)", fmt_rp(grand_monthly),
                         delta=f"+{fmt_short(total_new_monthly)} baru", delta_color="off")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Aset", fmt_rp(total_new_asset))
            with col2:
                st.metric("Yield / Hari", fmt_rp(total_new_daily))
            with col3:
                st.metric(f"Yield Bulan Ini ({days} hari)", fmt_rp(total_new_monthly),
                         delta=f"≈ {(total_new_monthly/total_new_asset*100*12):.1f}% p.a." if total_new_asset else None,
                         delta_color="off")

        submit = st.form_submit_button(
            "💾 Simpan & Lihat Dashboard",
            use_container_width=True, type="primary",
        )

        if submit:
            if existing_idx is not None:
                # AKUMULASI ke entry yang udah ada
                accumulate_entry(
                    st.session_state.entries[existing_idx],
                    values, daily_yields, description,
                )
                action = "diakumulasikan"
                final_total = st.session_state.entries[existing_idx]["total"]
                final_yield = total_monthly_yield(st.session_state.entries[existing_idx])
            else:
                # Buat entry baru
                entry = {
                    "year": int(year),
                    "month": int(month),
                    "label": f"{MONTHS[month]} {year}",
                    "ts": entry_timestamp(int(year), int(month)),
                    "descriptions": [description.strip()] if description.strip() else [],
                    "values": {k: float(v) for k, v in values.items()},
                    "yields_daily": {k: float(v) for k, v in daily_yields.items()},
                    "total": float(total_new_asset),
                }
                st.session_state.entries.append(entry)
                action = "ditambahkan"
                final_total = total_new_asset
                final_yield = total_new_monthly

            st.session_state.entries = sort_entries(st.session_state.entries)
            save_data(st.session_state.entries)
            st.session_state.form_iter += 1

            st.session_state.flash = (
                f"✅ Data **{MONTHS[month]} {year}** berhasil **{action}**! "
                f"Total aset: {fmt_rp(final_total)} · Yield bulan ini: {fmt_rp(final_yield)}",
                "success",
            )
            st.session_state.page = "📈 Dashboard"
            st.rerun()


# ============================================================
# EDIT (REPLACE — dari Riwayat)
# ============================================================
def render_edit():
    if st.session_state.edit_idx is None:
        st.warning("Tidak ada data yang dipilih. Klik ✏️ Edit dari halaman Riwayat.")
        return

    st.title("✏️ Edit Data (Replace)")
    st.caption("⚠️ Mode edit: data akan **di-replace** sepenuhnya, bukan diakumulasi.")

    edit_entry = st.session_state.entries[st.session_state.edit_idx]

    s = st.session_state.form_iter
    key_suffix = f"{s}_edit_{st.session_state.edit_idx}"

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Tahun", min_value=2000, max_value=2100,
                               value=edit_entry["year"], step=1, key=f"yr_{key_suffix}")
    with col2:
        month = st.selectbox("Bulan", options=list(range(12)),
                             format_func=lambda x: MONTHS[x], index=edit_entry["month"],
                             key=f"mo_{key_suffix}")

    days = days_in(year, month)
    st.info(f"📅 **{MONTHS[month]} {year}** — {days} hari.")

    with st.form(f"edit_form_{key_suffix}", clear_on_submit=False):
        all_descs = edit_entry.get("descriptions", [])
        desc_combined = "\n".join(all_descs) if all_descs else ""
        description = st.text_area(
            "📝 Deskripsi / Catatan",
            value=desc_combined,
            height=80,
            key=f"desc_{key_suffix}",
        )

        st.markdown("##### Detail Aset & Yield Harian")

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
                    min_value=0.0,
                    value=float(edit_entry["values"].get(c["key"], 0)),
                    step=1_000_000.0, format="%.0f",
                    key=f"val_{c['key']}_{key_suffix}",
                )
            with cols[2]:
                daily_yields[c["key"]] = st.number_input(
                    f"{c['yield_label']} / hari (Rp)",
                    min_value=0.0,
                    value=float(edit_entry.get("yields_daily", {}).get(c["key"], 0)),
                    step=10_000.0, format="%.0f",
                    key=f"dly_{c['key']}_{key_suffix}",
                )
            with cols[3]:
                m = daily_yields[c["key"]] * days
                st.markdown(
                    f"<div style='padding-top:28px;'>"
                    f"<small style='color:#64748b;'>= {days} hari</small><br>"
                    f"<b style='color:#f59e0b;'>{fmt_short(m)}</b>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        total_asset = sum(values.values())
        total_daily = sum(daily_yields.values())
        total_m = total_daily * days

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Aset", fmt_rp(total_asset))
        with col2:
            st.metric("Yield / Hari", fmt_rp(total_daily))
        with col3:
            st.metric(f"Yield Bulan ({days} hari)", fmt_rp(total_m))

        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            submit = st.form_submit_button("✅ Update", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Batal", use_container_width=True)

        if cancel:
            st.session_state.edit_idx = None
            st.session_state.form_iter += 1
            st.session_state.page = "📈 Dashboard"
            st.rerun()

        if submit:
            new_descs = [d.strip() for d in description.split("\n") if d.strip()]
            st.session_state.entries[st.session_state.edit_idx] = {
                "year": int(year),
                "month": int(month),
                "label": f"{MONTHS[month]} {year}",
                "ts": entry_timestamp(int(year), int(month)),
                "descriptions": new_descs,
                "values": {k: float(v) for k, v in values.items()},
                "yields_daily": {k: float(v) for k, v in daily_yields.items()},
                "total": float(total_asset),
            }
            st.session_state.entries = sort_entries(st.session_state.entries)
            save_data(st.session_state.entries)
            st.session_state.edit_idx = None
            st.session_state.form_iter += 1
            st.session_state.flash = (
                f"✅ Data **{MONTHS[month]} {year}** berhasil diupdate (replaced).",
                "success",
            )
            st.session_state.page = "📈 Dashboard"
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

    st.caption(f"Total **{len(entries)}** entry tersimpan.")

    for i, e in enumerate(entries):
        prev_t = entries[i-1]["total"] if i > 0 else None
        ch_pct = ((e["total"] - prev_t) / prev_t * 100) if prev_t else None
        my = total_monthly_yield(e)
        d = days_in(e["year"], e["month"])
        descs = e.get("descriptions", [])
        num_inputs = len(descs) if descs else 1

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1.5])
            with col1:
                st.markdown(f"**{e['label']}** · _{d} hari_ · 📥 {num_inputs} input")
                if descs:
                    for idx, desc in enumerate(descs, 1):
                        if desc:
                            st.caption(f"📝 #{idx}: {desc}")
            with col2:
                st.metric("Net Worth", fmt_short(e["total"]),
                         delta=f"{ch_pct:+.2f}%" if ch_pct is not None else None)
            with col3:
                st.metric(f"💰 Yield ({d} hari)", fmt_short(my),
                         delta=f"{fmt_short(my/d if d else 0)}/hari", delta_color="off")
            with col4:
                real_idx = st.session_state.entries.index(e)
                if st.button("✏️ Edit", key=f"edit_{i}", use_container_width=True):
                    st.session_state.edit_idx = real_idx
                    st.session_state.form_iter += 1
                    st.session_state.page = "✏️ Edit (via Riwayat)"
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
                    month_val = daily * d
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
                                    f"{fmt_short(daily)}/hari × {d} = {fmt_short(month_val)}"
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

    years_diff = (entries[-1]["ts"] - entries[0]["ts"]) / (60*60*24*365.25)
    cagr = ((entries[-1]["total"] / entries[0]["total"]) ** (1/years_diff) - 1) * 100 if years_diff > 0 and entries[0]["total"] > 0 else 0

    total_pi = sum(total_monthly_yield(e) for e in entries)
    avg_pi = total_pi / len(entries)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("📈 Bulan Terbaik", best["label"], delta=f"+{best['change']:.2f}%")
    with col2: st.metric("📉 Bulan Terburuk", worst["label"], delta=f"{worst['change']:.2f}%")
    with col3: st.metric("📊 Avg Growth/bln", f"{avg_growth:+.2f}%")
    with col4: st.metric("🎯 CAGR", f"{cagr:.2f}%", delta="Annualized", delta_color="off")

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

    st.subheader("Detail per Kategori")
    latest_d = days_in(latest["year"], latest["month"])
    cat_cols = st.columns(4)
    shown = 0
    for c in CATEGORIES:
        cur = latest["values"].get(c["key"], 0)
        prv = prev["values"].get(c["key"], 0)
        daily = latest.get("yields_daily", {}).get(c["key"], 0)
        my = daily * latest_d
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
                    st.markdown(f"<small style='color:#f59e0b;'>{fmt_short(daily)}/hari → {fmt_short(my)}/bln</small>", unsafe_allow_html=True)
                st.markdown(f"<small style='color:#64748b;'>Alokasi: {alloc:.1f}%</small>", unsafe_allow_html=True)
        shown += 1

    st.markdown("---")
    st.subheader("Skor Diversifikasi")
    active = [latest["values"].get(c["key"], 0) for c in CATEGORIES if latest["values"].get(c["key"], 0) > 0]
    if active:
        total = sum(active)
        hhi = sum((v / total) ** 2 for v in active)
        score = round((1 - hhi) * 100)
        level = "Baik" if score > 70 else ("Cukup" if score > 40 else "Perlu perbaikan")
        color = "#22c55e" if score > 70 else ("#f59e0b" if score > 40 else "#ef4444")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"<div style='text-align:center; font-size:60px; color:{color}; font-weight:bold;'>{score}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"### <span style='color:{color};'>{level}</span>", unsafe_allow_html=True)
            st.caption(f"{len(active)} kategori aktif · HHI: {hhi*10000:.0f}")

    st.markdown("---")
    df_export = pd.DataFrame([
        {"Periode": e["label"], "Hari": days_in(e["year"], e["month"]),
         "Total": e["total"], "Yield Bulanan": total_monthly_yield(e),
         "Deskripsi": " | ".join(e.get("descriptions", [])),
         **{c["label"]: e["values"].get(c["key"], 0) for c in CATEGORIES}}
        for e in entries
    ])
    st.download_button("📊 Download CSV", data=df_export.to_csv(index=False).encode("utf-8"),
                       file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv")


# ============================================================
# ROUTING
# ============================================================
page = st.session_state.page
if page == "📈 Dashboard":
    render_dashboard()
elif page == "➕ Tambah Data":
    render_add()
elif page == "✏️ Edit (via Riwayat)":
    render_edit()
elif page == "📜 Riwayat":
    render_history()
elif page == "🔍 Analisis":
    render_analysis()

st.sidebar.markdown("---")
st.sidebar.caption("💡 Jangan lupa backup JSON secara berkala!")
