import streamlit as st
import pandas as pd

st.set_page_config(page_title="Amazon Echo Reviews Dashboard", layout="wide")

st.title("📊 Amazon Echo Reviews Dashboard")

uploaded_file = st.file_uploader("Upload CSV Review Amazon Echo", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Preview Data")
    st.dataframe(df.head())

    st.subheader("Informasi Dataset")
    col1, col2 = st.columns(2)
    col1.metric("Jumlah Baris", len(df))
    col2.metric("Jumlah Kolom", len(df.columns))

    st.subheader("Filter Rating")
    if "Rating" in df.columns:
        rating = st.multiselect(
            "Pilih Rating",
            sorted(df["Rating"].dropna().unique()),
            default=sorted(df["Rating"].dropna().unique())
        )

        filtered_df = df[df["Rating"].isin(rating)]

        st.dataframe(filtered_df)

        st.subheader("Distribusi Rating")
        st.bar_chart(filtered_df["Rating"].value_counts().sort_index())
    else:
        st.warning("Kolom Rating tidak ditemukan.")

    st.download_button(
        label="Download Data Filter",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="filtered_reviews.csv",
        mime="text/csv"
    )
else:
    st.info("Silakan upload file CSV untuk memulai.")
