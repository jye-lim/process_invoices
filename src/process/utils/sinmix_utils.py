#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import os
import re

# Libs
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageEnhance

# Custom
from ...config import poppler_path

#############
# Functions #
#############

def extract_text_from_page(pdf_path, page_number, contrast):
    """
    Extract text from a specific page of the PDF using OCR.

    Args:
        pdf_path (str): Path to the PDF file
        page_number (int): Page number to extract text from
        contrast (int): Contrast value for image enhancement

    Returns:
        text (str): Extracted text
    """
    images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number, poppler_path=poppler_path)
    if images:
        img = images[0].convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img_enhanced = enhancer.enhance(contrast)
        return pytesseract.image_to_string(img_enhanced)
    return None


def find_do_number(text):
    """
    Find the DO number from the extracted text.

    Args:
        text (str): Extracted text

    Returns:
        do (str): DO number
    """
    do_pattern = r'\b\d{8}\b'
    lines = text.split('\n')
    for line in lines:
        if 'DONO' in line.upper():
            matches = re.findall(do_pattern, line)
            do = matches[0] if matches else None
            if do and len(do) == 8:
                return do
    return None


def save_page_as_pdf(original_pdf_path, page_number, do_number, output_directory):
    """
    Save the specified page of the original PDF to the output directory with a new name.

    Args:
        original_pdf_path (str): Path to the original PDF file
        page_number (int): Page number to save
        do_number (str): DO number
        output_directory (str): Path to the output directory
    """
    images = convert_from_path(original_pdf_path, first_page=page_number, last_page=page_number, poppler_path=poppler_path)
    if images:
        save_path = os.path.join(output_directory, f"{do_number}.pdf")
        count = 1
        while os.path.exists(save_path):
            save_path = os.path.join(output_directory, f"{do_number} ({count}).pdf")
            count += 1
        images[0].save(save_path, "PDF")
        