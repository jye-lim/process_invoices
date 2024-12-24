#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import os
import re

# Libs
import cv2
import numpy as np
import pandas as pd
import pytesseract
import streamlit as st
import tabula
from pdf2image import convert_from_path
from PIL import Image

# Custom
from ...config import poppler_path, tesseract_path

##################
# Configurations #
##################

pytesseract.pytesseract.tesseract_cmd = tesseract_path

inv_no_pattern = re.compile(r"(?P<inv_no>\d{8,})")

do_date_pattern = re.compile(r"DOCUMENT\s*DATE\s*(?P<do_date>\d{2}/\d{2}/\d{2,4})")

desc_pattern = re.compile(
    r"(?P<grade>G\d{2})\s*"  # Matches the grade
    r"(?P<slump>\d{3}-\d{3})\s*"  # Matches the slump
    r"(?:\s*(?P<duration>\d{1,2}H))?\s*"  # Optionally matches the duration
    r"(?:\s*(?P<rtd>R?T?D?))?\s*"  # Optionally matches RTD
)

grade_dict = {
    "10": "C12/10",
    "15": "C12/15",
    "20": "C16/20",
    "25": "C20/25",
    "30": "C25/30",
    "35": "C28/35",
    "40": "C32/40",
    "45": "C35/45",
    "50": "C40/50",
    "55": "C45/55",
    "60": "C50/60",
}

#############
# Functions #
#############


def convert_pdf_to_binimg(file_path):
    """
    Converts a PDF into a list of binarised images.

    Args:
        file_path (str): Path to PDF file

    Returns:
        preprocessed_images (list[PIL.Image.Image]): List of binarised PIL images
    """
    # Convert PDF to images for each page
    images = convert_from_path(file_path, poppler_path=poppler_path, dpi=300)

    # Preprocessing each image
    preprocessed_images = []
    for img in images:
        # Convert image to grayscale and binarise it
        img_np = np.array(img)
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Convert back to PIL Image for downstream processing
        preprocessed_img = Image.fromarray(binary)
        preprocessed_images.append(preprocessed_img)

    return preprocessed_images


def get_scanned_data(image):
    """
    Extracts the invoice number, DO date, and subtotal from an image using OCR.

    Args:
        image (PIL.Image.Image): A binarized image containing the text to be processed.

    Returns:
        inv_no (str or None): The extracted invoice number, or None if not found.
        do_date (str or None): The extracted date of the DO, or None if not found.
        subtotal (float or None): The extracted subtotal value, or None if not found.
        building (str or None): The extracted building name, or None if not found.
    """
    # Perform OCR using pytesseract
    text = pytesseract.image_to_string(image)
    lines = text.split("\n")

    # Initialise placeholder values
    inv_no = None
    do_date = None
    subtotal = None
    building = None

    # Loop through each line to find required info
    for line in lines:
        # Get invoice number
        if "INVOICE NO" in line.upper():
            inv_match = re.search(inv_no_pattern, line)
            if inv_match:
                inv_no = inv_match.group("inv_no")

        if "DOCUMENT DATE" in line.upper():
            date_match = re.search(do_date_pattern, line.upper())
            if date_match:
                do_date = date_match.group("do_date")

        # Get sub total of each DO
        if "SUB TOTAL" in line.upper():
            subtotal_str = line.split(" ")[-1]
            subtotal = float(subtotal_str.replace(",", ""))

        if "PROJECT" in line.upper():
            building = line.split("-")[0].split(":")[1].strip()

    return inv_no, do_date, subtotal, building


def fill_missing_entries(info_list, start_indices, end_indices):
    """
    Fills in missing entries based on its DO's start and end indices.
    Performs a forward pass, before a backward pass, to check

    Args:
        info_list (list): List of information where some entries may be None.
        start_indices (list): List of index that indicates the start of the DO.
        end_indices (list): List of index that indicates the end of the DO.

    Returns:
        info_list (list): Updated list with missing entries filled in.
    """
    # Fill in missing entries
    for start, end in zip(start_indices, end_indices):
        # Get the entry within the DO
        entry_in_do = info_list[start : end + 1]

        # Exclude None values and assign most frequent entry in DO
        entry_valid = [entry for entry in entry_in_do if entry is not None]
        if entry_valid:
            majority_entry = max(set(entry_valid), key=entry_valid.count)
            for i in range(start, end + 1):
                info_list[i] = majority_entry

    return info_list


def add_nan_col(df, col_name):
    """
    Adds a new column to the DataFrame with the specified column name and
    initializes all values in the column as NaN. The column's data type is
    set to 'object' to allow for both string and numeric values in the future.

    Args:
        df (pandas.DataFrame): The DataFrame to which the new column will be added.
        col_name (str): The name of the new column to be added.

    Returns:
        df (pandas.DataFrame): The DataFrame with the newly added column, where all
        values are initialized as NaN and the column type is 'object'.
    """
    df[col_name] = pd.NA
    df[col_name] = df[col_name].astype("object")
    return df


def extract_description(desc):
    """
    Extract data from description for code columns in resulting Excel.

    Args:
        desc (str): Description2 value

    Returns:
        grade (str): Grade of concrete, or None if not found
        slump (str): Slump value, or None if not found
        rtd (str): RTD if retardant was used, else None
        duration (str): Duration of retardation, or None if not found
    """
    # If description is not a string, return None for all values
    if not isinstance(desc, str):
        return None, None, None, None

    # Attempt to match the description with the regex pattern
    match = re.search(desc_pattern, desc)

    # Extract values or default to None if no match or group is missing
    if match:
        gde = match.group("grade") if match.group("grade") else None
        slump = match.group("slump") if match.group("slump") else None
        duration = match.group("duration") if match.group("duration") else None
        rtd = match.group("rtd") if match.group("rtd") else None
    else:
        gde = slump = duration = rtd = None  # Default to None if no match

    # Convert grade data if available, otherwise default to None
    grade = grade_dict.get(gde[-2:]) if gde else None

    return grade, slump, rtd, duration


def get_scanned_info(file_path):
    """
    Extracts key information (invoice number, delivery order date, and subtotal)
    from a PDF file by converting it into binarized images and processing the data.

    Args:
        file_path (str): The path to the PDF file to be processed.

    Returns:
        start_indices (list): List of index that indicates the start of the DO.
        end_indices (list): List of index that indicates the end of the DO.
        inv_no_list (list): List of invoice number from the scanned document.
        do_date_list (list): List of document date from the scanned document.
        building_list (list): List of building name from the scanned document.
    """
    # Converts PDF into a list of binarised images
    preprocessed_images = convert_pdf_to_binimg(file_path=file_path)

    # Extracts invoice number and subtotal from the images
    inv_no_list = []
    do_date_list = []
    subtotal_list = []
    building_list = []
    for image in preprocessed_images:
        inv_no, do_date, subtotal, building = get_scanned_data(image)
        inv_no_list.append(inv_no)
        do_date_list.append(do_date)
        subtotal_list.append(subtotal)
        building_list.append(building)

    # Get the start and end positions of each DO
    subtotal_positions = [i for i, x in enumerate(subtotal_list) if x is not None]
    start_indices = [0] + [x + 1 for x in subtotal_positions[:-1]]
    end_indices = subtotal_positions

    # Fill any missing entries
    inv_no_list = fill_missing_entries(inv_no_list, start_indices, end_indices)
    do_date_list = fill_missing_entries(do_date_list, start_indices, end_indices)
    building_list = fill_missing_entries(building_list, start_indices, end_indices)

    return start_indices, end_indices, inv_no_list, do_date_list, building_list


def get_scanned_tables(file_path):
    """
    Extracts and processes tabular data from scanned PDFs.

    Args:
        file_path (str): The path to the PDF file to be processed.

    Returns:
        df_pdf (pandas.DataFrame): The DataFrame of all scanned files in the PDF, combined.
    """
    # Initialise list to store tabular df
    dfs_do = []

    # Get scanned info
    start_indices, end_indices, inv_no_list, do_date_list, building_list = get_scanned_info(file_path)

    for start, end in zip(start_indices, end_indices):
        # Get all dataframes for the same DO and combine them
        do_pages = list(range(start + 1, end + 2))  # Page index starts from 1
        df_list = tabula.read_pdf(file_path, pages=do_pages)
        df_list = [df.dropna(axis=1, how="all") for df in df_list if not df.empty]

        # If no valid data extracted, continue to next DO
        if (
            pd.isna(do_date_list[start])    # Check if DO date is missing
            or pd.isna(inv_no_list[start])  # Check if invoice number is missing
            or len(df_list) == 0            # Check if no data extracted
        ):
            filename = os.path.basename(file_path)
            st.write(f"No entry found in {filename} from page {start + 1} to {end + 1}.")
            continue

        # Get column names
        reference_columns = []
        for df in df_list:
            if not df.columns[0].startswith("Unnamed"):  # Look for valid column names
                reference_columns = df.columns.tolist()
                break

        # If no valid headers extracted, continue to next DO
        if len(reference_columns) == 0:
            filename = os.path.basename(file_path)
            st.write(f"No headers found in {filename} from page {start + 1} to {end + 1}.")
            continue

        # Normalise column names
        for i, df in enumerate(df_list):
            if not df.columns.equals(pd.Index(reference_columns)):
                df.columns = reference_columns

        # Stack dataframes together
        df_do = pd.concat(df_list, ignore_index=True)

        # Set date in MMMM YY format
        df_do.iloc[:, 0] = pd.to_datetime(df_do.iloc[:, 0], dayfirst=True).dt.strftime("%Y %m")

        # Set column headers
        df_do.columns = [
            "For Month (YYYY MM)",
            "DO No.",
            "Description2",
            "Qty+Unit",
            "Unit Rate",
            "Vendor Invoice Amount",
        ]

        # Use regex to split the quantity and its unit
        df_do[["Qty", "Unit"]] = df_do["Qty+Unit"].str.extract(r"(\d*\.?\d+)\s*(.*)")

        # Update column data
        df_do = df_do.dropna(subset=["DO No."])
        df_do["DO No."] = df_do["DO No."].astype("object")
        df_do["Unit Rate"] = df_do["Unit Rate"].astype(float)
        df_do["Qty"] = df_do["Qty"].str.replace(",", "").astype(float)
        df_do["Unit"] = df_do["Unit"].str.strip().str.lower()
        df_do["Unit2"] = df_do["Unit"]
        df_do["Vendor Invoice Unit Rate (S$)"] = df_do["Unit Rate"]

        # Calculate vendor invoice amount
        df_do["Vendor Invoice Amount"] = df_do["Unit Rate"] * df_do["Qty"]

        # Add NaN columns. Use object type to contain NaNs.
        new_cols = [
            "Inv No.",
            "Date",
            "Building",
            "Description",
            "Total Qty",
            "Subtotal Amount",
            "Total Amt per Inv",
            "Admix. 3",
        ]
        for col in new_cols:
            df_do = add_nan_col(df_do, col)

        # Update NaN columns
        formatted_date = pd.to_datetime(do_date_list[start], dayfirst=True).strftime("%d-%b-%y")
        df_do.loc[0, "Inv No."] = int(inv_no_list[start])
        df_do.loc[0, "Date"] = formatted_date

        # Add new columns of repeated data
        df_do["Invoice Num"] = inv_no_list[start]
        df_do["Invoice Num"] = df_do["Invoice Num"].astype(int)
        df_do["DO Date"] = formatted_date
        df_do["Building"] = building_list[start]

        # Get summary data and update remaining NaN columns
        total_amt = 0
        unique_desc = df_do["Description2"].unique()
        for i, desc in enumerate(unique_desc):
            filtered_df = df_do[df_do["Description2"] == desc]

            # Skip if empty
            if len(filtered_df) == 0:
                continue

            # Get summary
            total_qty = filtered_df["Qty"].sum()
            unit = filtered_df["Unit"].values[0]
            unit_rate = filtered_df["Unit Rate"].mean()
            subtotal_amt = total_qty * unit_rate

            # Update columns
            df_do.loc[i, "Description"] = desc
            df_do.loc[i, "Total Qty"] = total_qty
            df_do.loc[i, "Unit"] = unit
            df_do.loc[i, "Unit Rate"] = unit_rate
            df_do.loc[i, "Subtotal Amount"] = subtotal_amt

            # Track total amount
            total_amt += subtotal_amt

        # Update total amount
        df_do.loc[0, "Total Amt per Inv"] = total_amt

        # Empty out non-unique unit and unit rate rows, as per requirements
        df_do["Unit"] = df_do["Unit"].astype("object")
        df_do["Unit Rate"] = df_do["Unit Rate"].astype("object")
        df_do.loc[len(unique_desc) :, "Unit"] = pd.NA
        df_do.loc[len(unique_desc) :, "Unit Rate"] = pd.NA

        # Get data for "Code" columns
        df_codes = df_do["Description2"].apply(extract_description)
        df_codes = pd.DataFrame(df_codes.tolist(), columns=["Conc. Grade", "Conc. Slump", "Admix. 1", "Admix. 2"])
        df_do[["Conc. Grade", "Conc. Slump", "Admix. 1", "Admix. 2"]] = df_codes

        # Loop through each index in the DataFrame and update
        for i in df_do.index:
            # For concrete slump, strip and append "MM" if not NaN
            if pd.notna(df_do.at[i, "Conc. Slump"]):
                df_do.at[i, "Conc. Slump"] = df_do.at[i, "Conc. Slump"].strip() + "MM"

            # For Admixture 2, strip and append "R" only if the value is not NaN or empty
            if pd.notna(df_do.at[i, "Admix. 2"]) and df_do.at[i, "Admix. 2"].strip() != "":
                df_do.at[i, "Admix. 2"] = df_do.at[i, "Admix. 2"].strip() + "R"

        # Drop unused columns
        df_do = df_do.drop("Qty+Unit", axis=1)

        # Standardise empty values
        df_do = df_do.replace(["", None, np.nan], pd.NA)

        # Add an empty row at the end, as per requirements
        empty_row = pd.DataFrame([[pd.NA] * len(df_do.columns)], columns=df_do.columns)
        df_do = pd.concat([df_do, empty_row], ignore_index=True)

        # Add DO df to the list
        dfs_do.append(df_do)

    # Combine all tables if not empty
    if dfs_do:
        return pd.concat(dfs_do, ignore_index=True)
    else:
        return pd.DataFrame()
