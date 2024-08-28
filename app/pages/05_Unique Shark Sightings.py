import streamlit as st
from datetime import datetime, timedelta

from utils import get_file_from_s3, mapUpdateKnownSharks, check_password, filter_df_on_dates

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

st.set_page_config(layout="wide")

st.title("Shark Sightings")
st.write("Merged and cleaned shark sightings. This table will show one row per identified whaleshark.")


no_date_filter = st.toggle("Remove date fliters (show all time)")

mapping_file = get_file_from_s3(
    bucket_name="mada-whales-python",
    object_key="files/mapping_testset.parquet",
)

shark_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="sharks/sightings.parquet"
)

if no_date_filter:
    df = mapUpdateKnownSharks(shark_sightings, mapping_file)
else:

    one_week_ago = datetime.now() - timedelta(days=7)
    start_date = st.date_input("Start date", value=one_week_ago)
    end_date = st.date_input("End date", value="today", min_value=start_date)

    sightings_in_period = filter_df_on_dates(shark_sightings, start_date, end_date)

    df = mapUpdateKnownSharks(sightings_in_period, mapping_file)
    df = df[df["Total sightings"] > 0]

st.dataframe(df.reset_index(drop=True))
