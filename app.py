import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Wine Dashboard", page_icon="🍷", layout="wide")
st.title("🍷 Wine Dataset Dashboard")

@st.cache_data
def load_data():
    return pd.read_csv("Wine dataset.csv")

df=load_data()
classes=sorted(df["class"].unique())
selected=st.sidebar.multiselect("Pilih Class",classes,default=classes)
filtered=df[df["class"].isin(selected)]
st.dataframe(filtered,use_container_width=True)
st.write(filtered.describe())
num=filtered.select_dtypes(include="number").columns.tolist()
x=st.selectbox("X",num,0)
y=st.selectbox("Y",num,1)
fig,ax=plt.subplots()
for c in filtered["class"].unique():
    d=filtered[filtered["class"]==c]
    ax.scatter(d[x],d[y],label=str(c))
ax.legend()
st.pyplot(fig)
