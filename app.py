import streamlit as st

st.set_page_config(page_title="Cotizador Inteligente", layout="wide")

pg = st.navigation([
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/2_admin.py", title="Admin", icon="⚙️"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
])
pg.run()
