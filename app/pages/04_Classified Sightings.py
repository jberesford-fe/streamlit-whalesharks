import streamlit as st
from datetime import datetime, timedelta
from utils import get_file_from_s3, mapUpdateClassified, filter_df_on_dates

st.set_page_config(layout="wide")

st.title("All Classified Sightings")
st.write(
    """This page shows all sightings that have been through the classifier
      form. It includes duplicates and unusable sightings."""
)

mapping_file = get_file_from_s3(
    bucket_name="mada-whales-python",
    object_key="files/mapping_testset.parquet",
)

shark_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="sharks/sightings.parquet"
)

form_selection = st.radio(
    "Select a dataset", ["Classified sightings", "Unusable sightings"], index=0
)

one_year_ago = datetime.now() - timedelta(days=365)
start_date = st.date_input("Start date", value=one_year_ago)
end_date = st.date_input("End date", value="today", min_value=start_date)

if form_selection == "Classified sightings":
    df = mapUpdateClassified(shark_sightings, mapping_file)
elif form_selection == "Unusable sightings":
    st.write("Unusable sightings")
else:
    st.write("No data available")


df = filter_df_on_dates(df, start_date, end_date)

st.dataframe(df.reset_index(drop=True))
