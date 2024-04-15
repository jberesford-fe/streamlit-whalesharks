import streamlit as st
import hmac
import requests
import json
import pandas as pd
import boto3
from io import BytesIO


# Password checking
def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["password_correct"] = True
            del st.session_state[
                "password"
            ]  # Don't store the username or password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


# Raw data import
def import_data_from_api():
    base_url = "https://kf.kobotoolbox.org/api/v2/assets"
    form_id = "aJ5NwkApvziLAUE7i9eHcn"

    url = base_url + f"/{form_id}/data.json"

    st.session_state["username"] = st.secrets["kobo"]["username"]
    st.session_state["password"] = st.secrets["kobo"]["password"]

    response = requests.get(
        url, auth=(st.session_state["username"], st.session_state["password"])
    )
    data = json.loads(response.text)
    results = data["results"]

    return results


def import_tablet_ids_from_csv():
    return pd.read_csv("data/tablet_ids.csv")


def convert_json_to_dataframe(results, tablet_ids):
    """_summary_

    Args:
        results (_type_): _description_
        tablet_ids (_type_): _description_
    """
    df = pd.DataFrame(results)
    df = pd.json_normalize(results)
    df.columns = df.columns.str.replace("Faune/", "", regex=False)
    df = pd.merge(df, tablet_ids, on="client_identifier", how="left")
    df.drop(columns=["trichodesmium_pct"], inplace=True)

    df_exploded = df.explode("sighting_repeat")
    df_sightings = pd.json_normalize(df_exploded["sighting_repeat"])
    df_exploded = df_exploded.drop(columns=["sighting_repeat"]).reset_index(
        drop=True
    )
    all_sightings = pd.concat([df_exploded, df_sightings], axis=1)

    all_sightings.columns = all_sightings.columns.str.replace(
        "sighting_repeat/", "", regex=True
    )

    all_sightings = all_sightings.rename(columns={"shark_uuid": "sighting_id"})
    all_sightings["sighting_id"] = (
        all_sightings["sighting_id"]
        .str.replace("uuid:", "", regex=False)
        .str[:13]
    )
    numbers = [
        "meteo",
        "sst",
        "sea_state",
        "trichodesmium_pct",
    ]
    for col in numbers:
        if col in all_sightings.columns:
            all_sightings[col] = pd.to_numeric(
                all_sightings[col], errors="coerce"
            )

    if "start" in all_sightings.columns:
        all_sightings["start"] = pd.to_datetime(all_sightings["start"])

    dates = ["survey_start", "survey_end", "start", "end"]
    for col in dates:
        if col in all_sightings.columns:
            # Convert to datetime, coercing errors to NaT
            all_sightings[col] = pd.to_datetime(
                all_sightings[col], errors="coerce"
            )

    all_sightings.rename(
        columns={"_id": "trip_id", "shark_uuid": "sighting_id"}, inplace=True
    )

    all_sightings["sighting_id"] = all_sightings[
        "sighting_id"
    ].str.removeprefix("uuid:")

    all_sightings["megaf_id"] = all_sightings["megaf_id"].str.removeprefix(
        "uuid:"
    )

    return all_sightings


def split_sightings_shark_megaf(all_sightings):
    """_summary_

    Args:
        all_sightings (_type_): _description_
    """
    # Split the data into two dataframes
    shark_sightings = all_sightings[
        (all_sightings["megaf_or_shark"].isin(["shark", "chasse"]))
        & all_sightings["sighting_id"].notna()
    ]

    # Filter for megafauna sightings where 'megaf_or_shark' is "megaf"
    megaf_sightings = all_sightings[all_sightings["megaf_or_shark"] == "megaf"]

    return shark_sightings, megaf_sightings


def filter_df_on_dates(df, start_date, end_date):
    """_summary_

    Args:
        df (_type_): _description_
        start_date (_type_): _description_
        end_date (_type_): _description_
    """
    # df_no_nan = df[~df.survey_start.isna()]

    df["survey_start"] = pd.to_datetime(df.survey_start, utc=True)

    df["survey_start"] = df["survey_start"].dt.date

    df_filtered_dates = df[
        (df["survey_start"] >= start_date) & (df["survey_start"] <= end_date)
    ]

    return df_filtered_dates


# Classifier form
def get_file_from_s3(bucket_name, object_key):
    """Get file from S3

    Args:
        bucket_name (str): login to aws console
        object_key (str): associated with IAM user role called streamlit-access

    Returns:
        df: file from S3
    """
    s3_resource = boto3.resource(
        "s3",
        region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"],
        aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
    )
    s3_mapping_file = s3_resource.Object(bucket_name, object_key)

    buffer = BytesIO()
    s3_mapping_file.download_fileobj(buffer)
    buffer.seek(0)
    map = pd.read_parquet(buffer)

    return map
