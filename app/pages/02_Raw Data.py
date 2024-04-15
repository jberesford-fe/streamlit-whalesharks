import streamlit as st
from datetime import datetime, timedelta

from utils import (
    import_data_from_api,
    import_tablet_ids_from_csv,
    convert_json_to_dataframe,
    split_sightings_shark_megaf,
    filter_df_on_dates,
)

# Get data #
results = import_data_from_api()

tablet_ids = import_tablet_ids_from_csv()

all_sightings = convert_json_to_dataframe(results, tablet_ids)

shark_sightings, megaf_sightings = split_sightings_shark_megaf(all_sightings)


st.title("About Page")
st.write(
    """This is the About Page.
    Here you can share information about your app or project."""
)

one_year_ago = datetime.now() - timedelta(days=365)
start_date = st.date_input("Start date", value=one_year_ago)
end_date = st.date_input("End date", value="today", min_value=start_date)

raw_select = st.selectbox("Select a dataset", ["Sharks", "Megafauna"])
if raw_select == "Sharks":
    st.dataframe(filter_df_on_dates(shark_sightings, start_date, end_date))
elif raw_select == "Megafauna":
    st.dataframe(filter_df_on_dates(megaf_sightings, start_date, end_date))
