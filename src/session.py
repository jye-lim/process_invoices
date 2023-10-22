import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
upload_path = os.getenv('UPLOAD_PATH')
output_path = os.getenv('OUTPUT_PATH')


def initialize_session_state():
    """
    Initialize session state for file uploader and uploaded files.
    """
    # Initialize session state for file uploader if it doesn't exist
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0

    # Initialize session state for uploaded files if it doesn't exist
    if 'uploaded_files' not in st.session_state:
        st.session_state["uploaded_files"] = []

    # Remove all uploaded and output files, including temporary files
    os.system("rm -rf {}".format(os.path.join(upload_path, "*")))
    os.system("rm -rf {}".format(os.path.join(output_path, "*")))
    os.system("rm -rf {}".format(os.path.join(upload_path, "._*")))
    os.system("rm -rf {}".format(os.path.join(output_path, "._*")))


def clear_uploads():
    """
    Clears all uploaded files.
    """
    st.session_state["uploaded_files"] = []
    st.session_state["file_uploader_key"] += 1
    os.system("rm -rf {}".format(os.path.join(upload_path, "*")))
    os.system("rm -rf {}".format(os.path.join(upload_path, "._*")))
    st.rerun()
