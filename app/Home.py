import streamlit as st

from utils import (
    check_password,
)


def main():

    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    st.title("Madagascar Whale Shark Project")

    html_content = """
    This dashboard is designed to be used in conjunction with the
    <a href='https://ee.kobotoolbox.org/x/PME7pT8m'>this survey</a>.
    It has several use cases:
    <ul>
    <li>Raw survey outputs are available to view in near real-time.</li>
    <li>Summary statistics and data visualisation are automised and available
     to view in the <i>clean data</i> and <i>graphs</i> tabs.</li>
    <li>The 'classifier' lets users assign I³S ID's to shark sightings.
    </ul>
    Armed with this information, the dashboard automates the merging of
     shark sightings into known sharks.
    """

    st.markdown(html_content, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
