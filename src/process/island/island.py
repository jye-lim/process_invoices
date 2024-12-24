#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import os
import re

# Libs
import pandas as pd
import streamlit as st

# Custom
from .island_utils import get_scanned_tables

##################
# Configurations #
##################

representative_pattern = re.compile(r'(?P<name>[A-Z\s]+)\s+(?P<contact>\d{8})')

# location_pattern = re.compile(r'(?:PILE:)?\(?([cCfFpP]\d{2,4}[a-zA-Z]?)\)?')
location_pattern = re.compile(r"\((.*?)\)")

subcon_pattern = re.compile(r'^([A-Za-z]+)')

zone_dict = {
    "CSBP": "A",
    "BBR": "B",
}

#############
# Functions #
#############

def process_scans(pdf_file_paths):
    """
    Process scanned files to extract data.

    Args:
        pdf_file_paths (list): List of PDF file paths

    Returns:
        df_all (pandas.core.frame.DataFrame): The DataFrame of all PDFs, combined.
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


def process_excel(excel_file_path):
    """
    Process excel file to extract comments.

    Args:
        excel_file_path (list): Path to excel file

    Returns:
        df_comments (pandas.core.frame.DataFrame): Dataframe with extracted comments
    """
    # Open summary xlxs
    df_xlsx = pd.read_excel(excel_file_path)

    # Get header row
    found_header = False
    for i in range(len(df_xlsx)):
        curr_row = df_xlsx.iloc[i]
        if len(curr_row.dropna()) > 7:
            found_header = True
            break

    # Update header
    if found_header:
        header_row = i + 1
        df_xlsx = pd.read_excel(excel_file_path, header=header_row)
    else:
        raise ValueError("Header row not found in Excel file!")

    # Make a new dataframe to store the extracted data from input Excel
    df_comments = pd.DataFrame({
        "DO No.": df_xlsx["TICKET NUMBER"],
        "Purchaser Representative": df_xlsx["PURCHASER REPRESENTATIVE"],
        "Bored Pile No.: OR Location ***": df_xlsx["PROJECT LOCATION"],
        "Subcons": df_xlsx["PROJECT NAME"],
        "Site Person": df_xlsx["SITE PERSON"],
    })

    # Add site person details to df
    df_comments[["Site Person Name", "Site Person Contact"]] = df_comments["Site Person"].str.extract(representative_pattern)
    df_comments = df_comments.drop("Site Person", axis=1)

    # Updated extracted location
    location_pattern_match = (
        df_comments["Bored Pile No.: OR Location ***"]
        .str.extract(location_pattern)[0]
        .fillna(df_comments["Bored Pile No.: OR Location ***"])
        .str.upper()
        .str.replace(r'([A-Z])(\d+)', r'\1-\2', regex=True)
        .str.strip()
    )
    if df_comments["Bored Pile No.: OR Location ***"] is not None:
        df_comments["Bored Pile No.: OR Location ***"] = location_pattern_match

    # Update the other extracted columns
    df_comments["Subcons"] = df_comments["Subcons"].str.extract(subcon_pattern)
    df_comments["Zone"] = df_comments["Subcons"].map(zone_dict)

    # Remove NaN rows and header
    df_comments = df_comments.dropna(subset=['DO No.'])
    df_comments = df_comments.iloc[1:]
    df_comments.reset_index(drop=True, inplace=True)

    # Update column data types
    df_comments["DO No."] = df_comments["DO No."].astype("object")
    df_comments["Site Person Contact"] = df_comments["Site Person Contact"].astype(int)

    return df_comments


def island_main(pdf_file_paths, excel_file_paths):
    """
    Main function for ISLAND.

    Args:
        pdf_file_paths (list): List of PDF file paths
        excel_file_paths (list): List of excel file paths

    Returns:
        df_all (pandas.core.frame.DataFrame): Dataframe with extracted data
    """
    # Initialize headers and dataframe
    data_headers = [
        "Inv No.",
        "Date",
        "Description",
        "Total Qty",
        "Unit",
        "Unit Rate",
        "Subtotal Amount",
        "Total Amt per Inv",
        "Invoice Num",
        "For Month (YYYY MM)",
        "Zone",
        "Site Person Name",
        "Site Person Contact",
        "Purchaser Representative",
        "Bored Pile No.: OR Location ***",
        "Building",
        "Subcons",
        "DO Date",
        "DO No.",
        "Description2",
        "Conc. Grade",
        "Conc. Slump",
        "Admix. 1",
        "Admix. 2",
        "Admix. 3",
        "Qty",
        "Unit2",
        "Vendor Invoice Unit Rate (S$)",
        "Vendor Invoice Amount",
    ]

    # Process scanned files
    df_all = process_scans(pdf_file_paths)

    # # Process excel file, if any
    if len(excel_file_paths) > 0:
        df_comments = process_excel(excel_file_paths[0])

        # Merge df_all and df_comments based on DO No.
        if "DO No." not in df_all.columns:
            for pdf_file_path in pdf_file_paths:
                filename = os.path.basename(pdf_file_path)
                st.error(f"Failed to extract the following PDF: {filename}")
            return None
        else:
            df_all = pd.merge(df_all, df_comments, how='left', on='DO No.')

    # Add empty column for future use
    df_all["Size"] = None

    # # Reorder columns
    df_all = df_all[data_headers]

    return df_all
