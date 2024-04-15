import streamlit as st
from utils import get_file_from_s3

st.title("Classifier Page")
st.write(
    """This is the Classifier Form.
    Here you can see unclassified sharks, and also classify them.
    Data is backed up on Amazon S3."""
)

mapping_file = get_file_from_s3(
    bucket_name="mada-whales-python", object_key="files/mapping.parquet"
)

st.dataframe(mapping_file)
