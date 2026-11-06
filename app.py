import streamlit as st

st.set_page_config(page_title="Cotizador Inteligente", layout="wide")

pg = st.navigation([
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
])
pg.run()
