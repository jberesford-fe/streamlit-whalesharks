import streamlit as st
from utils import check_password


def main():

    if not check_password():
        st.stop()  # Do not continue if check_password is not True.

    st.title("Whalesharks Dashboard")

    st.write("This is a test dashboard for whalesharks")


if __name__ == "__main__":
    main()
