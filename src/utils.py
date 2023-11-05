#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import glob
import os
import zipfile

# Libs
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

##################
# Configurations #
##################

# Load environment variables
load_dotenv()
upload_path = os.getenv('UPLOAD_PATH')
option_list = os.getenv('OPTIONS').split(',')

#############
# Functions #
#############

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


def print_result(option, total_files, error_files=None, error_dict=None):
    """
    Print result of processing.

    Args:
        option (str): Selected option
        total_files (int): Total number of files
        error_files (list): Optional. List of error files
        error_dict (dict): Optional. Dictionary of error files and their failed pages
    """
    if option == "ACS":
        st.success(f"{total_files}/{total_files} files processed successfully!")

    elif option == "BRC":
        st.success(f"{total_files - len(error_files)}/{total_files} files processed successfully!")

        # Display error files if any
        if error_files:
            st.write("\nThe following files encountered errors during processing:")
            for file in error_files:
                st.write(file)
        st.warning("If necessary, record the error files before clearing the uploaded files or refreshing page")

    elif option == "PANU":
        st.success(f"{total_files}/{total_files} files processed successfully!")

    elif option == "SINMIX":
        st.success(f"{total_files - len(error_dict)}/{total_files} files processed successfully!")

        # Display error files if any
        if error_dict:
            # Convert the error_dict to a DataFrame
            df_errors = pd.DataFrame(list(error_dict.items()), columns=["PDF", "Page"])
            st.write("\nThe following pages encountered errors during processing:")
            st.table(df_errors)
            st.warning("If necessary, record the error files before clearing the uploaded files or refreshing page")


def zip_pdfs(output_pdf_dir, output_filename):
    """
    Zip all PDF files in the specified directory.

    Args:
        output_pdf_dir (str): Directory containing output PDF files
        output_filename (str): Output filename
    """
    with zipfile.ZipFile(output_filename, 'w') as zipf:
        for foldername, _, filenames in os.walk(output_pdf_dir):
            for filename in filenames:
                if filename.endswith('.pdf'):
                    file_path = os.path.join(foldername, filename)
                    zipf.write(file_path, filename)
