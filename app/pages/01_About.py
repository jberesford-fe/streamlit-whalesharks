import streamlit as st
from utils import check_password

if not check_password():
    st.stop()  # Do not continue if check_password is not True.


st.markdown("<h3>How to use this dashboard</h3>", unsafe_allow_html=True)
html_instructions = """
<ol>
    <li>While at sea, fill in
    <a href='https://ee.kobotoolbox.org/x/PME7pT8m'>the survey</a></li>
    <li>Check your sightings have appeared in <i>raw data</i>
    (Note: you can filter by your name, date, tablet etc).
     Results will take a few minutes to appear.</li>
    <li>Upload your photos to I&sup3;S and, where an ID available,
    make a note of the I&sup3;S ID for each of your sightings.</li>
    <li>Go to <i>classifier</i> and file each of your sightings as 'done',
    'advice needed' or 'unusablke.</li>
    <li>Check that your sighting information appears in the
    <i>classified sightings</i>
    tab as well as in the <i>clean data</i> tabs</li>
</ol>"""
st.markdown(html_instructions, unsafe_allow_html=True)

st.markdown("<h3>Definitions</h3>", unsafe_allow_html=True)
st.markdown(
    """+ A sighting is defined as any shark registered in the survey,
    regardless of whether a left ID is taken.""",
    unsafe_allow_html=True,
)
st.markdown(
    "+ A known shark is any shark to which we have assigned an I³S ID.",
    unsafe_allow_html=True,
)


st.markdown("<h3>How to access data backups</h3>", unsafe_allow_html=True)
st.markdown(
    """Raw data is available on the kobo server. All you need is a password,
    please contact [Stella] or [Amy].""",
    unsafe_allow_html=True,
)
st.markdown(
    """Clean data and mapping files are backed securly on Amazon S3.
    This data is accessible via API, please contact Justin Beresford.""",
    unsafe_allow_html=True,
)
