import streamlit as st
from controller import run_pipeline

st.set_page_config(layout="wide")
st.title("📈 AI Stock Market Decision System")

stock = st.text_input("Enter Stock Symbol (NSE/BSE/US)", value="RELIANCE.NS")

if st.button("Get Latest Forecast"):
    with st.spinner("Analyzing market..."):
        result = run_pipeline(stock)

    if result is None:
        st.error("Invalid stock symbol or no data.")
    else:
        st.metric("Decision", result["decision"])
        st.metric("Confidence", f"{result['confidence']:.2f}")
        st.info(result["explanation"])

st.caption("Educational project. Not financial advice.")
