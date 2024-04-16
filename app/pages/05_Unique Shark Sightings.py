import streamlit as st
from utils import get_file_from_s3, mapUpdateKnownSharks, check_password

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.set_page_config(layout="wide")

st.title("Shark Sightings")
st.write("Merged and cleaned shark sightings.")


selected_merge = st.selectbox(
    label="Select Dataset",
    options=["Known sharks", "Merged yearly", "Merged weekly", "Merged daily"],
)

mapping_file = get_file_from_s3(
    bucket_name="mada-whales-python",
    object_key="files/mapping_testset.parquet",
)

shark_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="sharks/sightings.parquet"
)

if selected_merge == "Known sharks":
    df = mapUpdateKnownSharks(shark_sightings, mapping_file)
elif selected_merge == "Merged yearly":
    st.write("Merged yearly")
elif selected_merge == "Merged weekly":
    st.write("Merged weekly")
elif selected_merge == "Merged daily":
    st.write("Merged daily")
else:
    st.write("No data available")

st.dataframe(df.reset_index(drop=True))
