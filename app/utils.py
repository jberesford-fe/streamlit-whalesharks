import streamlit as st
import hmac
import requests
import json
import pandas as pd
import numpy as np
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


# Amazon s3 interactions
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
    s3_object = s3_resource.Object(bucket_name, object_key)

    buffer = BytesIO()
    s3_object.download_fileobj(buffer)
    buffer.seek(0)
    map = pd.read_parquet(buffer)

    return map


def push_df_to_s3(bucket_name, object_key, dataframe):
    """Push dataframe to S3

    Args:
        bucket_name (str): mada-whales-python
        object_key (str): folder / file_name.parquet
        dataframe (df): any dataframe, it will get converted to parquet

    Returns:
        _type_: _description_
    """
    s3_resource = boto3.resource(
        "s3",
        region_name=st.secrets["aws"]["AWS_DEFAULT_REGION"],
        aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
    )

    parquet_buffer = BytesIO()
    dataframe.to_parquet(parquet_buffer, index=False)

    s3_object = s3_resource.Object(bucket_name, object_key)
    s3_object.put(Body=parquet_buffer.getvalue())

    print(
        f"""{dataframe} pushed to S3 bucket
            {bucket_name} with key
            {object_key}"""
    )


def map_un_classified_sharks(shark_sightings, mapping_file):
    """
    Args:
        shark_sightings (df): dataframe pulled from s3
        mapping_file (_type_): dataframe pulled from s3

    Returns:
        df: all sharks for which we have not yet assigned an I³S ID
    """
    uc = pd.merge(shark_sightings, mapping_file, on="sighting_id", how="outer")

    uc = uc[uc["left_id"] == "yes"]
    uc["t"] = uc.groupby("sighting_id")["sighting_id"].transform("size")
    uc = uc[uc["t"] == 1]
    uc = uc[uc["i3s_id"].isna() | (uc["i3s_id"] == "")]
    uc = uc[~uc["no_id_reason"].isin(["unusable_sighting"])]
    uc["date"] = pd.to_datetime(uc["survey_start"])
    uc["date"] = uc["date"].dt.date

    uc = uc[
        [
            "sighting_id",
            "date",
            "tablet_name",
            "observer",
            "operator",
            "trip_id",
            "sighting_number",
            "sex",
            "size",
            "scars",
            "shark_name_known",
            "no_id_reason",
            "surrounding_objects",
        ]
    ]
    uc = uc.rename(columns={"surrounding_objects": "notes"})

    return uc


def process_classifier_form_and_push_S3(
    sighting_id, i3s_id, no_id_reason, bucket_name, object_key
):
    new_row = pd.DataFrame(
        {
            "sighting_id": [sighting_id],
            "i3s_id": [i3s_id],
            "no_id_reason": [no_id_reason],
        }
    )
    existing_mapping = get_file_from_s3(
        bucket_name,
        object_key,
    )
    combined_map = pd.concat([existing_mapping, new_row], ignore_index=True)

    push_df_to_s3(
        bucket_name,
        object_key,
        dataframe=combined_map,
    )
    st.session_state["i3s_id"] = ""

    return combined_map


# Classified sightings page


def mapUpdateClassified(shark_sightings, mapping):
    result = pd.merge(shark_sightings, mapping, on="sighting_id", how="outer")
    result = result[result["i3s_id"].str.match(r"^MD-\d{3}") is True]
    result["survey_start"] = pd.to_datetime(result["survey_start"])
    result["survey_start"] = result["survey_start"].dt.date

    result = result[
        [
            "sighting_id",
            "i3s_id",
            "survey_start",
            "tablet_name",
            "observer",
            "operator",
            "trip_id",
            "sighting_number",
            "sex",
            "size",
            "scars",
            "biopsy",
            "biopsy_number",
            "tag",
            "tag_no",
        ]
    ]

    return result


# Unique shark sightings page
def mapUpdateKnownSharks(shark_sightings, mapping):
    mapping_filtered = mapping[
        ~mapping["no_id_reason"].isin(["advice_needed", "unusable_sighting"])
    ]

    merged_data = pd.merge(
        shark_sightings, mapping_filtered, on="sighting_id", how="outer"
    )
    merged_data = merged_data[
        merged_data["i3s_id"].str.match(r"^MD-\d{3}") is True
    ]
    merged_data["survey_start"] = pd.to_datetime(merged_data["survey_start"])
    merged_data["survey_start"] = merged_data["survey_start"].dt.date

    merged_data["size"] = pd.to_numeric(
        merged_data["size"], errors="coerce"
    ).round(2)

    merged_data["survey_start"] = pd.to_datetime(merged_data["survey_start"])

    grouped = (
        merged_data.groupby("i3s_id")
        .agg(
            {
                "size": lambda x: round(np.nanmean(x), 2),
                "sex": lambda x: (
                    pd.Series.mode(x.dropna())[0]
                    if not pd.Series.mode(x.dropna()).empty
                    else "Undetermined"
                ),
                "scars": lambda x: "yes" if "yes" in x.values else "no",
                "left_id": lambda x: "yes" if "yes" in x.values else "no",
                "right_id": lambda x: "yes" if "yes" in x.values else "no",
                "tag": lambda x: np.sum(x == "yes"),
                "drone": lambda x: np.sum(x == "yes"),
                "prey": lambda x: np.sum(x == "yes"),
                "survey_start": ["min", "count"],
            }
        )
        .reset_index()
    )
    grouped.columns = [
        " ".join(col).strip() if isinstance(col, tuple) else col
        for col in grouped.columns
    ]

    column_renames = {
        "i3s_id": "I3S ID",
        "size <lambda>": "Size (mean)",
        "survey_start min": "First sighting",
        "survey_start count": "Total sightings",
        "sex <lambda>": "Sex (mode)",
        "scars <lambda>": "Identified scars",
        "left_id <lambda>": "Left ID",
        "right_id <lambda>": "Right ID",
        "tag <lambda>": "Tag count",
        "drone <lambda>": "Drone measurements",
        "prey <lambda>": "Prey samples",
    }
    grouped = grouped.rename(columns=column_renames)
    grouped["First sighting"] = grouped["First sighting"].dt.date

    return grouped


# Summary statistics
def get_summary_stats(df):
    # Add a constant column 'Year' with value 'All Years'
    df["Year"] = "All Years"

    summary_stats = df.groupby("Year").agg(
        **{
            "Total sightings": ("Total sightings", np.sum),
            "Unique sightings": ("I3S ID", "count"),
            "Sightings per shark": ("Total sightings", np.mean),
            "Average size": ("Size (mean)", lambda x: x.mean()),
            "male_count": (
                "Sex (mode)",
                lambda x: (x == "male").sum(skipna=True),
            ),
            "female_count": (
                "Sex (mode)",
                lambda x: (x == "female").sum(skipna=True),
            ),
        }
    )

    summary_stats["Male % of total"] = 100 * (
        summary_stats.male_count
        / (summary_stats.female_count + summary_stats.male_count)
    )

    summary_stats.drop(columns=["male_count", "female_count"], inplace=True)

    return summary_stats
