import streamlit as st
import hmac
import requests
import json
import pandas as pd


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


def import_data_from_api():

    base_url = "https://kf.kobotoolbox.org/api/v2/assets"
    form_id = "aJ5NwkApvziLAUE7i9eHcn"

    url = base_url + f"/{form_id}/data.json"

    username = "madawhale"
    password = "Wh6l3Sh6rk"

    # Call the API and parse JSON
    response = requests.get(url, auth=(username, password))
    data = json.loads(response.text)
    results = data["results"]

    return results


def import_tablet_ids_from_csv():
    return pd.read_csv("../data/tablet_ids.csv")


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

    return all_sightings
