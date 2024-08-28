import streamlit as st
from datetime import datetime, timedelta

from utils import (
    get_file_from_s3,
    filter_df_on_dates,
    check_password,
)

if not check_password():
    st.stop()  # Do not continue if check_password is not True.


st.set_page_config(layout="wide")

# Get data #
shark_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="sharks/sightings.parquet"
)

megaf_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="megaf/sightings.parquet"
)


st.title("About Page")
st.write(
    """This is the About Page.
    Here you can share information about your app or project."""
)


raw_select = st.radio("Select a dataset", ["Sharks", "Megafauna"])


one_year_ago = datetime.now() - timedelta(days=365)
start_date = st.date_input("Start date", value=one_year_ago)
end_date = st.date_input("End date", value="today", min_value=start_date)

cols_sharks = [
'trip_id',
'survey_start',
'username',
'observer',
'operator',
'guide',
'day_type',
'meteo',
'sea_state',
'visibility',
'meduses',
'salpes',
'krill',
'trichodesmium',
'mise_a_leau',
'sst',
'second_observer',
'meteo_end',
'boats_total',
'boats_total_notes',
'gopro',
'third_party_date',
'sea_state_end',
'guide_other',
'start',
'end',
'deviceid',
'tablet_name',
'sighting_number',
'sighting_id',
'left_id',
'right_id',
'shark_geo',
'sex',
'sex_pic',
'size',
'scars',
'scar_number',
'localisation',
'taille_chasse',
'behaviour',
'code_of_conduct',
'boats_min',
'boats_max',
'end_encounter',
'biopsy',
'tag',
'drone',
'prey',
'tag_no',
'shark_name_known',
'sighting_start_time',
'surrounding_animals',
'surrounding_objects',
'taille_chasse_fish',
'compactness',
'avoidance_behaviour',
'fish_notes',
'avoidance_behaviour_other',
'biopsy_number',
'prey_tube_number',
'balise',
'nom_du_bateau_en_faute',
'chasse_id',
'chasse_geo',
'rb_in_chasse',
'sighting_observer',
'tag_deployed',
'prey_bio_tube_no',
]

cols_megaf = [
    'trip_id',
'survey_start',
'username',
'observer',
'operator',
'guide',
'day_type',
'meteo',
'sea_state',
'visibility',
'meduses',
'salpes',
'krill',
'trichodesmium',
'mise_a_leau',
'sst',
'second_observer',
'meteo_end',
'boats_total',
'boats_total_notes',
'gopro',
'third_party_date',
'sea_state_end',
'guide_other',
'start',
'end',
'deviceid',
'tablet_name',
'megaf_number',
'megaf_id',
'espece',
'megaf_count',
'megaf_notes',
'espece_other',
'megaf_geo',
'dauphin_notes',
'sighting_number',
'chasse_id',
'chasse_geo',
'rb_in_chasse',
]

if raw_select == "Sharks":
    st.dataframe(
        filter_df_on_dates(shark_sightings, start_date, end_date).reset_index(
            drop=True
        )[cols_sharks]
    )

elif raw_select == "Megafauna":
    st.dataframe(
        filter_df_on_dates(megaf_sightings, start_date, end_date).reset_index(
            drop=True
        )[cols_megaf]
    )
