#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import os

# Libs
import pytesseract
import streamlit as st
from dotenv import load_dotenv
from pdf2image import convert_from_path

# Custom
from src.process.utils.sinmix_utils import (extract_text_from_page,
                                            find_do_number, save_page_as_pdf)

from ..config import poppler_path, tesseract_path

##################
# Configurations #
##################

# Load environment variables
load_dotenv()
output_path = os.getenv('OUTPUT_PATH')

pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Contrast for image enhancement
initial_contrast = 1
max_contrast = 6

#############
# Functions #
#############

def sinmix_main(pdf_file_paths):
    """
    Main function for SINMIX.

    Args:
        pdf_file_paths (list): List of PDF file paths

    Returns:
        error_dict (dict): Dictionary of error files and its failed pages
    """
    # List to hold error files
    error_dict = {}

    # Create a Streamlit progress bar
    progress = st.progress(0)
    status_text = st.empty()

    # Iterate through files
    for index, f in enumerate(pdf_file_paths):
        num_pages = len(convert_from_path(f, poppler_path=poppler_path))

        # Iterate through pages of file
        for page_number in range(1, num_pages + 1):
            do_found = False

            # Iterate through different contrast levels
            for contrast in range(initial_contrast, max_contrast + 1):
                text = extract_text_from_page(f, page_number, contrast)
                if text:
                    do_number = find_do_number(text)
                    if do_number:
                        save_page_as_pdf(f, page_number, do_number, output_path)
                        do_found = True
                        break

            # If DO number is not found, add to error dictionary
            if not do_found:
                filename = f.split('/')[-1]
                if filename not in error_dict:
                    error_dict[filename] = []
                error_dict[filename].append(page_number)

        # Update the Streamlit progress bar
        percent_complete = (index + 1) / len(pdf_file_paths)
        progress.progress(percent_complete)
        status_text.text(f"Processed: {index + 1}/{len(pdf_file_paths)} files ({int(percent_complete*100)}% complete)")

    return error_dict
