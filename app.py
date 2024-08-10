#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import os

# Libs
import streamlit as st
from dotenv import load_dotenv

# Custom
from src.download import download_xlsx, download_zip
from src.process import acs_main, brc_main, panu_main, sinmix_main
from src.session import initialize_session_state, next_session_state
from src.uploads import copy_uploads, show_uploads
from src.utils import dropdown_options, get_file_paths, print_result

##################
# Configurations #
##################

# Load environment variables
load_dotenv()
upload_path = os.getenv('UPLOAD_PATH')
output_path = os.getenv('OUTPUT_PATH')

##########
# Script #
##########

# Clear and initialize session the first time the app starts up
if "uploaded_files" not in st.session_state:
    initialize_session_state()

# Set up Streamlit page
st.set_page_config(
    page_title="Invoice Info Extraction",
    page_icon="💸",
    layout="centered"
)

st.title("Extract Information from Invoices")

uploaded_file = st.file_uploader(
    "Upload your invoices for information extraction!",
    type=["zip", "pdf", "xlsx"],
    key=st.session_state["file_uploader_key"],
)

if uploaded_file:
    # Copy the uploaded file into the upload_path
    copy_uploads(uploaded_file, upload_path)
    
    # Append to the list of uploaded files in session state
    if uploaded_file.name not in st.session_state["uploaded_files"]:
        st.session_state["uploaded_files"].append(uploaded_file.name)

    # Display the list of uploaded files
    show_uploads()

    # Clear all files
    if st.button("Clear uploaded files"):
        next_session_state()

    # Get file paths of uploads
    pdf_file_paths, excel_file_paths = get_file_paths()

    # Get option to process data from dropdown menu
    option = dropdown_options()
    
    # Process data
    if st.button("Process"):
        result = None
        result_zipped = False

        if option == "ACS":
            result = acs_main(pdf_file_paths, excel_file_paths)
            print_result(option, len(pdf_file_paths))

        elif option == "BRC":
            result, error_files = brc_main(pdf_file_paths)
            print_result(option, len(pdf_file_paths), error_files=error_files)

        elif option == "PANU":
            result = panu_main(pdf_file_paths, excel_file_paths)
            print_result(option, len(pdf_file_paths))

        elif option == "SINMIX":
            error_dict = sinmix_main(pdf_file_paths)
            print_result(option, len(pdf_file_paths), error_dict=error_dict)
            result_zipped = True

        # Download result in Excel format
        if result is not None:
            download_xlsx(option, result)

        # Download zipped file containing processed PDFs
        if result_zipped:
            download_zip(option)
