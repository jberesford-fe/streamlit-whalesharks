import streamlit as st
import re
from utils import (
    get_file_from_s3,
    map_un_classified_sharks,
    process_classifier_form_and_push_S3,
    process_classifier_form_and_delete_from_S3,
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

# Initialize the session state for deletion confirmation
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = False
if "sighting_id_to_delete" not in st.session_state:
    st.session_state.sighting_id_to_delete = None
if "i3s_id_to_delete" not in st.session_state:
    st.session_state.i3s_id_to_delete = None

# Create two main columns: one for the forms and the other for the table
col1, col2 = st.columns([0.3, 0.7])

with col1:
    # Streamlit form for adding/updating classifications
    with st.form(key="classifier_form", clear_on_submit=True):
        st.subheader("Add/Update Sighting")
        sighting_id = st.selectbox(
            "Select Sighting ID to classify:",
            [""] + unclassified_sharks.sighting_id.tolist(),
        )
        i3s_id = st.text_input("Enter I3S ID (format MD-XXX):")
        no_id_reason = st.radio(
            "Reason for no ID:", ["advice_needed", "unusable_sighting", "done"]
        )

        # Submit button for adding/updating classifications
        submit_button = st.form_submit_button(label="Submit Classification")

    # Handle the submit action for classification
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
        elif no_id_reason not in [
            "advice_needed",
            "unusable_sighting",
        ] and not re.match(r"MD-\d{3}$", i3s_id):
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

    # Streamlit form for deleting a sighting_id
    st.subheader("Delete Sighting")
    sighting_id_to_delete = st.selectbox(
        "Select Sighting ID to delete:",
        [""] + mapping_file.sighting_id.tolist(),
    )

    # Look up the corresponding I3S ID for the selected sighting_id
    i3s_id_to_delete = mapping_file.loc[
        mapping_file["sighting_id"] == sighting_id_to_delete, "i3s_id"
    ].values
    i3s_id_to_delete = (
        i3s_id_to_delete[0] if len(i3s_id_to_delete) > 0 else None
    )

    # Create a delete button that opens a confirmation modal
    delete_button = st.button("Delete Sighting")

    if delete_button:
        if sighting_id_to_delete == "":
            st.error("Please select a sighting ID to delete.")
        elif i3s_id_to_delete is None:
            st.error(
                f"No I3S ID found for sighting ID {sighting_id_to_delete}."
            )
        else:
            # Store the deletion information in session state and trigger confirmation
            st.session_state.confirm_delete = True
            st.session_state.sighting_id_to_delete = sighting_id_to_delete
            st.session_state.i3s_id_to_delete = i3s_id_to_delete

    # Check if deletion is pending confirmation
    if st.session_state.confirm_delete:
        # Display a confirmation message before deleting, showing the I3S ID
        st.warning(
            f"Are you sure you want to delete the sighting with I3S ID {st.session_state.i3s_id_to_delete}?"
        )

        # Add a 'Confirm' button for deletion confirmation
        if st.button("Confirm Deletion"):
            mapping_file = process_classifier_form_and_delete_from_S3(
                st.session_state.sighting_id_to_delete,
                bucket_name="mada-whales-python",
                object_key="files/mapping_testset.parquet",
            )
            st.success(
                f"Sighting with I3S ID {st.session_state.i3s_id_to_delete} deleted successfully."
            )

            shark_sightings = get_file_from_s3(
                bucket_name="mada-whales-python",
                object_key="sharks/sightings.parquet",
            )

            unclassified_sharks = map_un_classified_sharks(
                shark_sightings, mapping_file
            )

            # Reset the session state after deletion
            st.session_state.confirm_delete = False
            st.session_state.sighting_id_to_delete = None
            st.session_state.i3s_id_to_delete = None

# Display the unclassified sharks table in the right column
with col2:
    st.subheader("Unclassified Sharks")
    st.dataframe(unclassified_sharks.reset_index(drop=True))
