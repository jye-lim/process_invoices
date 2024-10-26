#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import re

# Libs
import cv2
import numpy as np
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

# Custom
from ...config import poppler_path, tesseract_path

##################
# Configurations #
##################

pytesseract.pytesseract.tesseract_cmd = tesseract_path

inv_no_pattern = re.compile(r'(?P<inv_no>\d{8,10})')
do_date_pattern = re.compile(r'\s*DATE\s*(?P<do_date>\d{2}[./]\d{2}[./]\d{2,4})')
subtotal_pattern = re.compile(r'.*?\s*(?P<subtotal>\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
date_pattern = re.compile(r'(?P<date>\d{2}[./]\d{2}[./]\d{4})')

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
    images = convert_from_path(file_path, poppler_path=poppler_path, dpi=500)

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
    """
    # Perform OCR using pytesseract
    text = pytesseract.image_to_string(image)
    lines = text.split('\n')

    # Initialise placeholder values
    inv_no = None
    do_date = None
    subtotal = None

    # Loop through each line to find required info
    for line in lines:
        # Get invoice number
        if "REFERENCE NO" in line.upper():
            inv_match = re.search(inv_no_pattern, line)
            if inv_match:
                inv_no = inv_match.group("inv_no")
                
        if "DATE" in line.upper():
            date_match = re.search(do_date_pattern, line.upper())
            if date_match:
                do_date = date_match.group("do_date")

        # Get sub total of each DO
        if "BEFORE TAX" in line.upper():
            subtotal_match = re.search(subtotal_pattern, line)
            if subtotal_match:
                subtotal_str = subtotal_match.group("subtotal")
                subtotal = float(subtotal_str.replace(",", ""))

    return inv_no, do_date, subtotal


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
        entry_in_do = info_list[start:end + 1]

        # Exclude None values and assign most frequent entry in DO
        entry_valid = [entry for entry in entry_in_do if entry is not None]
        if entry_valid:
            majority_entry = max(set(entry_valid), key=entry_valid.count)
            for i in range(start, end + 1):
                info_list[i] = majority_entry

    return info_list


def get_scanned_info(preprocessed_images):
    """
    Extracts key information (invoice number, delivery order date, and subtotal) 
    from a PDF file by converting it into binarized images and processing the data.

    Args:
        preprocessed_images (list): List of binarised images

    Returns:
        start_indices (list): List of index that indicates the start of the DO.
        end_indices (list): List of index that indicates the end of the DO.
        inv_no_list (list): List of invoice number from the scanned document.
        do_date_list (list): List of document date from the scanned document.
        subtotal_list (list): List of subtotal from the scanned document.
    """
    # Extracts invoice number and subtotal from the images
    inv_no_list = []
    do_date_list = []
    subtotal_list = []
    for image in preprocessed_images:
        inv_no, do_date, subtotal = get_scanned_data(image)
        inv_no_list.append(inv_no)
        do_date_list.append(do_date)
        subtotal_list.append(subtotal)

    # Get the start and end positions of each DO
    subtotal_positions = [i for i, x in enumerate(subtotal_list) if x is not None]
    start_indices = [0] + [x + 1 for x in subtotal_positions[:-1]]
    end_indices = subtotal_positions

    # Fill any missing entries
    inv_no_list = fill_missing_entries(inv_no_list, start_indices, end_indices)
    do_date_list = fill_missing_entries(do_date_list, start_indices, end_indices)

    return start_indices, end_indices, inv_no_list, do_date_list, subtotal_list


def get_scanned_tables(file_path):
    """
    Extracts and processes tabular data from scanned PDFs.

    Args:
        file_path (str): The path to the PDF file to be processed.
    
    Returns:
        df_pdf (pandas.DataFrame): The DataFrame of all scanned files in the PDF, combined.
    """
    # Initialise headers and dataframe
    data_headers = [
        "Inv No.",
        "Date",
        "Description",
        "TOTAL QTY",
        "Unit",
        "Unit Rate",
        "Subtotal Amt",
        "TOTAL AMT per INV",
        "Inv Number",
        "For Month (YYYY MM)",
        "Zone/ Bldg",
        "Pile No./Location",
        "For TAK or Subcon?\n[Pintary/ BBR/ KKL..etc]",
        "DO Date",
        "DO No.",
        "Description2",
        "Code1",
        "Code2",
        "Code3",
        "Code4",
        "Qty",
        "Vendor Invoice Rate",
        "Vendor Invoice Subtotal",
    ]

    df_pdf = pd.DataFrame(columns=data_headers)
    df_pdf["Inv No."] = df_pdf["Inv No."].astype(object)
    df_pdf["Date"] = df_pdf["Date"].astype(object)

    # Converts PDF into a list of binarised images
    preprocessed_images = convert_pdf_to_binimg(file_path=file_path)

    # Get scanned info
    start_indices, end_indices, inv_no_list, do_date_list, subtotal_list = get_scanned_info(preprocessed_images)

    for start, end in zip(start_indices, end_indices):
        # Get all dataframes for the same DO and combine them
        do_pages = [i for i in range(start, end + 1)]

        # Initialise list to store tabular df
        data_list = []

        for page in do_pages:
            # Perform OCR using pytesseract
            image = preprocessed_images[page]
            text = pytesseract.image_to_string(image)
            lines = text.split('\n')
            table_reached = False

            # Loop through each line to find table info
            for line in lines:
                # Check if table header is found
                if ("QTY" in line.upper()) and ("UNIT" in line.upper()):
                    table_reached = True
                    continue

                if table_reached:
                    date_match = re.search(date_pattern, line)
                    if date_match:
                        date = date_match.group("date").strip()
                        contents = line.split()
                        if len(contents) > 1:
                            do_no = contents[1]
                        else:
                            do_no = None
                        date = date.replace(".", "/")
                        date_month = pd.to_datetime(date, dayfirst=True).strftime("%Y %m")
                        date_day = pd.to_datetime(date, dayfirst=True).strftime("%-d/%-m/%Y")
                        data_list.append(
                            {
                                "For Month (YYYY MM)": date_month,
                                "DO Date": date_day,
                                "DO No.": do_no,
                            }
                        )

        # Create a DataFrame from data_list
        temp_df = pd.DataFrame(data_list)
        
        # Add overall document data to the first row
        temp_df["Inv No."] = pd.Series(dtype=object)
        temp_df["Date"] = pd.Series(dtype=object)
        temp_df.loc[0, "Inv No."] = inv_no_list[end]
        temp_df.loc[0, "Date"] = do_date_list[end]
        temp_df.loc[0, "TOTAL AMT per INV"] = subtotal_list[end]

        # Concatenate the data to the main df_pdf
        df_pdf = pd.concat([df_pdf, temp_df], ignore_index=True)

    # Add an empty row at the end, as per requirements
    empty_row = pd.DataFrame([[pd.NA] * len(df_pdf.columns)], columns=df_pdf.columns)
    df_pdf = pd.concat([df_pdf, empty_row], ignore_index=True)

    return df_pdf
