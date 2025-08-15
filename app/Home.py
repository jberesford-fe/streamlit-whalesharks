import streamlit as st
from utils import (
    check_password,
    convert_json_to_dataframe,
    import_data_from_api,
    import_tablet_ids_from_csv,
    push_df_to_s3,
    split_sightings_shark_megaf,
)

st.set_page_config(layout="wide")


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

    # Get data #

    results = import_data_from_api()
    tablet_ids = import_tablet_ids_from_csv()
    all_sightings, trips = convert_json_to_dataframe(results, tablet_ids)
    shark_sightings, megaf_sightings = split_sightings_shark_megaf(
        all_sightings
    )
    push_df_to_s3(
        "mada-whales-python", "sharks/sightings.parquet", shark_sightings
    )
    push_df_to_s3(
        "mada-whales-python", "megaf/sightings.parquet", megaf_sightings
    )
    push_df_to_s3("mada-whales-python", "sharks/trips.parquet", trips)


if __name__ == "__main__":
    main()
