# Al principio del archivo, después de los imports:
if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
    st.error("Debés iniciar sesión para ver esta página.")
    st.stop()
