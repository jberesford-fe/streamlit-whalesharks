import streamlit as st
from utils import (
    get_file_from_s3,
    get_summary_stats,
    mapUpdateKnownSharks,
    check_password,
)

if not check_password():
    st.stop()  # Do not continue if check_password is not True.


st.title("Summary Statistics")

mapping_file = get_file_from_s3(
    bucket_name="mada-whales-python",
    object_key="files/mapping_testset.parquet",
)

shark_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="sharks/sightings.parquet"
)

known_sharks = mapUpdateKnownSharks(shark_sightings, mapping_file)

summary_stats = get_summary_stats(known_sharks)

st.dataframe(summary_stats)
