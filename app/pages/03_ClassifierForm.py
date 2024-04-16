import streamlit as st
import re
from utils import (
    get_file_from_s3,
    map_un_classified_sharks,
    process_classifier_form_and_push_S3,
    check_password,
)

if not check_password():
    st.stop()  # Do not continue if check_password is not True.


st.set_page_config(layout="wide")

st.title("Classifier Page")
st.write(
    """This is the Classifier Form.
    Here you can see unclassified sharks, and also classify them.
    Data is backed up on Amazon S3."""
)

mapping_file = get_file_from_s3(
    bucket_name="mada-whales-python",
    object_key="files/mapping_testset.parquet",
)

shark_sightings = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="sharks/sightings.parquet"
)

unclassified_sharks = map_un_classified_sharks(shark_sightings, mapping_file)

col1, col2 = st.columns(spec=[0.3, 0.7])

with col1:
    # Streamlit form
    with st.form(key="classifier_form", clear_on_submit=True):
        sighting_id = st.selectbox(
            "Select Sighting ID:",
            [""] + unclassified_sharks.sighting_id.tolist(),
        )
        i3s_id = st.text_input("Enter I3S ID (format MD-XXX):")
        no_id_reason = st.radio(
            "Reason for no ID:", ["advice_needed", "unusable_sighting", "done"]
        )

        submit_button = st.form_submit_button(label="Submit")

    # Step 2: Validate Inputs and Process Data
    if submit_button:
        error_message = None

        mapping_file = get_file_from_s3(
            bucket_name="mada-whales-python",
            object_key="files/mapping_testset.parquet",
        )
        not_allowed_advice_needed = mapping_file[
            ~mapping_file["no_id_reason"].isin(["advice_needed"])
        ]

        if sighting_id == "" and i3s_id == "":
            error_message = "Required: sighting ID and I3S ID"
        elif sighting_id in not_allowed_advice_needed["sighting_id"].tolist():
            error_message = "Sighting ID has already been mapped"
        elif (
            no_id_reason in ["advice_needed", "unusable_sighting"]
            and i3s_id != ""
        ):
            error_message = (
                "If I3S ID available, sighting should be marked 'done'."
            )
        elif (
            no_id_reason not in ["advice_needed", "unusable_sighting"]
            and i3s_id == ""
        ):
            error_message = "No I3S ID is given but sighting filed as done."
        elif not re.match(r"MD-\d{3}$", i3s_id):
            error_message = "I3S ID must be of the format MD-123."

        if error_message:
            st.error(error_message)
        else:
            mapping_file = process_classifier_form_and_push_S3(
                sighting_id,
                i3s_id,
                no_id_reason,
                bucket_name="mada-whales-python",
                object_key="files/mapping_testset.parquet",
            )
            st.success("Data submitted successfully.")

            shark_sightings = get_file_from_s3(
                bucket_name="mada-whales-python",
                object_key="sharks/sightings.parquet",
            )

            unclassified_sharks = map_un_classified_sharks(
                shark_sightings, mapping_file
            )

with col2:
    st.dataframe(unclassified_sharks.reset_index(drop=True))
