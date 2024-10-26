#!/usr/bin/env python

####################
# Required Modules #
####################

# Libs
import pandas as pd
import streamlit as st

# Custom
from .gw_utils import get_scanned_tables

#############
# Functions #
#############


def gw_main(pdf_file_paths):
    """
    Main function for GW.

    Args:
        pdf_file_paths (list): List of PDF file paths

    Returns:
        df_all (pandas.core.frame.DataFrame): Dataframe with extracted data
    """
    # Create a Streamlit progress bar
    progress = st.progress(0)
    status_text = st.empty()

    # Iterate through files
    df_pdfs = []
    for index, f in enumerate(pdf_file_paths):
        # Get table from PDF
        df_pdf = get_scanned_tables(f)
        df_pdfs.append(df_pdf)

        # Update the Streamlit progress bar
        percent_complete = (index + 1) / len(pdf_file_paths)
        progress.progress(percent_complete)
        status_text.text(f"Processed: {index + 1}/{len(pdf_file_paths)} files ({int(percent_complete*100)}% complete)")

    # Combine all tables
    df_all = pd.concat(df_pdfs, ignore_index=True)

    return df_all
