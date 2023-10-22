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


def print_result(option, total_files, error_files=None):
    """
    Print result of processing.

    Args:
        option (str): Selected option
        total_files (int): Total number of files
        error_count (int): Optional. Number of error files
    """
    if option == "ACS":
        st.write(f"{total_files}/{total_files} files processed successfully!")

    elif option == "BRC":
        # Display error files if any
        if error_files:
            st.write("\nThe following files encountered errors during processing:")
            for file in error_files:
                st.write(file)

        st.write(f"{total_files - len(error_files)}/{total_files} files processed successfully!")

    elif option == "PANU":
        st.write(f"{total_files}/{total_files} files processed successfully!")

    elif option == "SINMIX":
        pass
    