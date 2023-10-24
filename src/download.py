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
from src.utils import zip_pdfs

##################
# Configurations #
##################

# Load environment variables
load_dotenv()
output_path = os.getenv('OUTPUT_PATH')

#############
# Functions #
#############

def download_xlsx(option, result):
    """
    Download Excel file containing processed data.

    Args:
        option (str): Selected option
        result (pd.DataFrame): Processed data
    """
    result_path = os.path.join(output_path, f"{option}.xlsx")
    result.to_excel(result_path, index=False)

    with open(result_path, "rb") as file:
        st.download_button(
            label="Download result",
            data=file,
            file_name=f"{option}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    # Display warning message to inform user to refresh page
    st.warning("Please clear the uploaded files or refresh page to process another set of files.")


def download_zip(option):
    """
    Download zipped file containing processed PDFs.

    Args:
        option (str): Selected option
    """
    zip_filename = f"{option}.zip"
    zip_path = os.path.join(output_path, zip_filename)
    zip_pdfs(output_path, zip_path)

    with open(zip_path, "rb") as file:
        bytes_data = file.read()
        st.download_button(
            label="Download result",
            data=bytes_data,
            file_name=zip_filename,
            mime="application/zip"
        )
    # Display warning message to inform user to refresh page
    st.warning("Please clear the uploaded files or refresh page to process another set of files.")
