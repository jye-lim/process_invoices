import os
import glob
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
upload_path = os.getenv('UPLOAD_PATH')
option_list = os.getenv('OPTIONS').split(',')


def get_file_paths():
    """
    Get file paths of uploads.

    Returns:
        pdf_file_paths (list): List of PDF file paths
        excel_file_paths (list): List of Excel file paths
    """
    file_paths = glob.glob(os.path.join(upload_path, "*"))
    pdf_file_paths = [file for file in file_paths if file.endswith('.pdf')]
    excel_file_paths = [file for file in file_paths if file.endswith('.xlsx')]
    return pdf_file_paths, excel_file_paths


def dropdown_options():
    """
    Dropdown menu for processing options.

    Returns:
        option (str): Selected option
    """
    option = st.selectbox("Choose an option to process the data:", option_list)
    return option
