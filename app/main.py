import streamlit as st
from utils import (
    check_password,
    import_data_from_api,
    import_tablet_ids_from_csv,
    convert_json_to_dataframe,
    split_sightings_shark_megaf,
)


def main():

    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    results = import_data_from_api()

    tablet_ids = import_tablet_ids_from_csv()

    all_sightings = convert_json_to_dataframe(results, tablet_ids)

    shark_sightings, megaf_sightings = split_sightings_shark_megaf(
        all_sightings
    )

    st.title("Whalesharks Dashboard")

    st.write("Raw shark data")
    st.dataframe(shark_sightings)

    st.write("Raw Megafauna data")
    st.dataframe(megaf_sightings)


if __name__ == "__main__":
    main()
