import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
import re

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Amazon Echo 2 – Review Dashboard",
    page_icon="🔊",
    layout="wide",
)

# ── Load data ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Amazon_Echo_2_Reviews.csv")
    df["Review Date"] = pd.to_datetime(df["Review Date"], errors="coerce")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df["Review Useful Count"] = pd.to_numeric(df["Review Useful Count"], errors="coerce").fillna(0)
    df["Sentiment"] = df["Rating"].apply(
        lambda r: "Positif" if r >= 4 else ("Negatif" if r <= 2 else "Netral")
    )
    df["Review Length"] = df["Review Text"].astype(str).apply(len)
    return df

df = load_data()

# ── Header ──────────────────────────────────────────────────────────────────────
st.title("🔊 Amazon Echo 2 – Review Dashboard")
st.markdown("Analisis **6.855 ulasan** pelanggan dari Amazon · Data mencakup rating, sentimen, tren waktu, dan kata kunci.")
st.divider()

# ── Sidebar filters ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Filter Data")

    rating_filter = st.multiselect(
        "Rating",
        options=[1, 2, 3, 4, 5],
        default=[1, 2, 3, 4, 5],
        format_func=lambda x: "⭐" * x,
    )

    sentiment_filter = st.multiselect(
        "Sentimen",
        options=["Positif", "Netral", "Negatif"],
        default=["Positif", "Netral", "Negatif"],
    )

    verified_filter = st.selectbox(
        "Status Verifikasi",
        options=["Semua", "Verified", "Unverified"],
    )

    date_min = df["Review Date"].min()
    date_max = df["Review Date"].max()
    date_range = st.date_input(
        "Rentang Tanggal",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

# ── Apply filters ────────────────────────────────────────────────────────────────
filtered = df[
    df["Rating"].isin(rating_filter) &
    df["Sentiment"].isin(sentiment_filter)
].copy()

if verified_filter == "Verified":
    filtered = filtered[filtered["User Verified"].astype(str).str.lower() == "yes"]
elif verified_filter == "Unverified":
    filtered = filtered[filtered["User Verified"].astype(str).str.lower() != "yes"]

if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[
        (filtered["Review Date"] >= start) & (filtered["Review Date"] <= end)
    ]

# ── KPI Cards ────────────────────────────────────────────────────────────────────
st.subheader("📊 Ringkasan")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Ulasan", f"{len(filtered):,}")
k2.metric("Rata-rata Rating", f"{filtered['Rating'].mean():.2f} ⭐")
k3.metric("Ulasan Positif", f"{(filtered['Sentiment']=='Positif').sum():,}")
k4.metric("Ulasan Negatif", f"{(filtered['Sentiment']=='Negatif').sum():,}")
k5.metric("Helpful Votes", f"{int(filtered['Review Useful Count'].sum()):,}")

st.divider()

# ── Row 1: Rating distribution + Sentiment pie ──────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("⭐ Distribusi Rating")
    rating_counts = filtered["Rating"].value_counts().sort_index().reset_index()
    rating_counts.columns = ["Rating", "Jumlah"]
    rating_counts["Label"] = rating_counts["Rating"].apply(lambda x: "⭐" * int(x))
    fig_rating = px.bar(
        rating_counts,
        x="Rating", y="Jumlah",
        color="Rating",
        color_continuous_scale=["#d73027", "#fc8d59", "#fee08b", "#91cf60", "#1a9850"],
        text="Jumlah",
        labels={"Rating": "Bintang", "Jumlah": "Jumlah Ulasan"},
    )
    fig_rating.update_traces(textposition="outside")
    fig_rating.update_layout(coloraxis_showscale=False, showlegend=False)
    st.plotly_chart(fig_rating, use_container_width=True)

with col2:
    st.subheader("😊 Proporsi Sentimen")
    sentiment_counts = filtered["Sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["Sentimen", "Jumlah"]
    colors = {"Positif": "#2ecc71", "Netral": "#f39c12", "Negatif": "#e74c3c"}
    fig_pie = px.pie(
        sentiment_counts,
        names="Sentimen",
        values="Jumlah",
        color="Sentimen",
        color_discrete_map=colors,
        hole=0.4,
    )
    fig_pie.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Row 2: Tren ulasan per bulan ─────────────────────────────────────────────────
st.subheader("📅 Tren Ulasan Per Bulan")
monthly = (
    filtered.dropna(subset=["Review Date"])
    .set_index("Review Date")
    .resample("ME")
    .agg(Jumlah=("Rating", "count"), Rata_Rating=("Rating", "mean"))
    .reset_index()
)
fig_trend = go.Figure()
fig_trend.add_trace(go.Bar(
    x=monthly["Review Date"], y=monthly["Jumlah"],
    name="Jumlah Ulasan", marker_color="#3498db", yaxis="y1"
))
fig_trend.add_trace(go.Scatter(
    x=monthly["Review Date"], y=monthly["Rata_Rating"],
    name="Rata-rata Rating", mode="lines+markers",
    marker=dict(color="#e67e22", size=7), line=dict(width=2), yaxis="y2"
))
fig_trend.update_layout(
    yaxis=dict(title="Jumlah Ulasan"),
    yaxis2=dict(title="Rating Rata-rata", overlaying="y", side="right", range=[1, 5]),
    legend=dict(orientation="h"),
    hovermode="x unified",
)
st.plotly_chart(fig_trend, use_container_width=True)

# ── Row 3: Word Cloud + Review length ────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("☁️ Word Cloud Ulasan")
    tab_pos, tab_neg, tab_all = st.tabs(["Positif", "Negatif", "Semua"])

    def make_wc(texts, colormap="Greens"):
        combined = " ".join(texts.dropna().astype(str))
        # Remove stopwords simply
        combined = re.sub(r"\b(the|and|to|of|a|in|is|it|that|this|was|for|with|have|but|not|are|be|as|at|by|my|i|you|me|we|they|very|just|so|if|its|an|on|or|from|do|get|all|has|no|had|can|also|more|been|would|your|our|their|there|he|she|his|her|one|was|were|will|about|up|out|re|amazon|echo)\b", "", combined, flags=re.IGNORECASE)
        wc = WordCloud(width=600, height=350, background_color="white", colormap=colormap, max_words=100).generate(combined)
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        return fig

    with tab_pos:
        pos_texts = filtered[filtered["Sentiment"] == "Positif"]["Review Text"]
        if len(pos_texts) > 0:
            st.pyplot(make_wc(pos_texts, "Greens"))
        else:
            st.info("Tidak ada data positif.")

    with tab_neg:
        neg_texts = filtered[filtered["Sentiment"] == "Negatif"]["Review Text"]
        if len(neg_texts) > 0:
            st.pyplot(make_wc(neg_texts, "Reds"))
        else:
            st.info("Tidak ada data negatif.")

    with tab_all:
        if len(filtered) > 0:
            st.pyplot(make_wc(filtered["Review Text"], "Blues"))

with col4:
    st.subheader("📏 Panjang Ulasan vs Rating")
    fig_box = px.box(
        filtered,
        x="Rating", y="Review Length",
        color="Sentiment",
        color_discrete_map={"Positif": "#2ecc71", "Netral": "#f39c12", "Negatif": "#e74c3c"},
        labels={"Review Length": "Panjang Ulasan (karakter)", "Rating": "Rating"},
        points=False,
    )
    st.plotly_chart(fig_box, use_container_width=True)

# ── Row 4: Top helpful reviews ────────────────────────────────────────────────────
st.subheader("👍 Ulasan Paling Helpful")
top_helpful = (
    filtered[filtered["Review Useful Count"] > 0]
    .sort_values("Review Useful Count", ascending=False)
    .head(10)[["Title", "Rating", "Sentiment", "Review Useful Count", "Review Date", "Review Text"]]
    .reset_index(drop=True)
)
top_helpful.index += 1
st.dataframe(
    top_helpful.rename(columns={
        "Title": "Judul",
        "Review Useful Count": "Helpful Votes",
        "Review Date": "Tanggal",
        "Review Text": "Ulasan",
    }),
    use_container_width=True,
    hide_index=False,
)

# ── Row 5: Configuration breakdown ───────────────────────────────────────────────
if "Configuration Text" in filtered.columns:
    st.subheader("⚙️ Rata-rata Rating per Konfigurasi")
    config_avg = (
        filtered.dropna(subset=["Configuration Text"])
        .groupby("Configuration Text")
        .agg(Rata_Rating=("Rating", "mean"), Jumlah=("Rating", "count"))
        .reset_index()
        .sort_values("Rata_Rating", ascending=True)
        .tail(15)
    )
    if not config_avg.empty:
        fig_conf = px.bar(
            config_avg,
            x="Rata_Rating", y="Configuration Text",
            orientation="h",
            color="Rata_Rating",
            color_continuous_scale="RdYlGn",
            range_color=[1, 5],
            text=config_avg["Rata_Rating"].round(2),
            labels={"Configuration Text": "Konfigurasi", "Rata_Rating": "Rating Rata-rata"},
        )
        fig_conf.update_traces(textposition="outside")
        fig_conf.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig_conf, use_container_width=True)

# ── Raw data ──────────────────────────────────────────────────────────────────────
with st.expander("📋 Lihat Data Mentah"):
    st.dataframe(
        filtered[["Title", "Rating", "Sentiment", "Review Date", "User Verified", "Review Useful Count", "Review Text"]]
        .reset_index(drop=True),
        use_container_width=True,
    )
    csv_export = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV terfilter",
        data=csv_export,
        file_name="echo_reviews_filtered.csv",
        mime="text/csv",
    )

st.divider()
st.caption("Dashboard dibuat dengan Streamlit · Data: Amazon Echo 2 Reviews")
