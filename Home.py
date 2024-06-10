import streamlit as st

# change browser tab icon and title
st.set_page_config(
    page_title="Chat-UI feedback visualization tool",
    page_icon="⛏️",
    layout="wide",
)

st.title("Welcome to Chat-UI feedback visualization tool👋")


st.markdown(
    """
    ## How to start?
    - Browse all the feedbacks on the `📈 Browse Feedbacks` page.
    - Search particular conversation records on the `🔎 Search Conversation` page.
    - View particular conversation details on the `💬 View Conversation` page.
    """
    )
