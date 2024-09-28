#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import re

# Libs
import pandas as pd
import pytesseract
import tabula
from pdf2image import convert_from_path

# Custom
from ...config import poppler_path, tesseract_path

##################
# Configurations #
##################

pytesseract.pytesseract.tesseract_cmd = tesseract_path

#############
# Functions #
#############

def add_column(table, name, val, fill=False):
    """
    Insert column with specified name and value at first row only.

    Args:
        table (pandas.core.frame.DataFrame): Dataframe of table to insert column into
        name (str): Name of column
        val (str): Value of column
        fill (bool): Whether to fill column with value or leave it blank. Defaults to False

    Returns:
        table (pandas.core.frame.DataFrame): Dataframe with new column
    """
    if fill:
        table.insert(0, name, val)
    else:
        table.insert(0, name, '')
        table.at[0, name] = val
    return table


def get_scanned_data(file_path, page_no):
    """
    Get data from scanned portion of PDF.

    Args:
        file_path (str): Path to PDF file
        page_no (int): Page number of PDF file

    Returns:
        date_req (str): Date required
        location (str): Location of site
    """
    images = convert_from_path(file_path, poppler_path=poppler_path)

    # Convert image to grayscale
    img = images[page_no].convert('L')

    # Perform OCR using pytesseract
    text = pytesseract.image_to_string(img)
    lines = text.split('\n')

    # Get date required and location
    date_req = None
    location = None
    for line in lines:
        # Get date required
        if "DATE REQUIRED" in line.upper():
            loc = line.find('/')
            date_req = line[loc-2:loc+8]

        # Get project location
        if "PART OF JOB" in line.upper():
            pattern = r"PART OF JOB\s*:?\s*(.*)"
            match = re.search(pattern, line)
            if match:
                location = match.group(1).strip()
            else:
                raise ValueError("Location not found!")
            
        # Exit loop once both data are found
        if (date_req is not None) and (location is not None):
            break
        
    return date_req, location


def get_table(file_path):
    """
    Get table from PDF.

    Args:
        file_path (str): Path to PDF file

    Returns:
        table (pandas.core.frame.DataFrame): Dataframe of table
    """
    # Initialize variables
    page_no = 1
    found_total = False
    table = pd.DataFrame()
    table_list = tabula.read_pdf(file_path, pages=page_no)

    # Loop through pages to find page with total SGD
    while not found_total:
        if len(table_list) == 2:
            table = pd.concat([table, table_list[0]], ignore_index=True)
            found_total = True
        elif len(table_list[0].columns) != 9:
            found_total = True
        else:
            table = pd.concat([table, table_list[0]], ignore_index=True)
            page_no += 1
            table_list = tabula.read_pdf(file_path, pages=page_no)

    # Drop unwanted columns
    drop = ['IT', 'UNIT', 'UNIT PRICE', 'PER', 'DISC.']
    table.drop(drop, axis=1, inplace=True)

    # Get data from scanned portion of PDF
    date_req, location = get_scanned_data(file_path, page_no)
    table = add_column(table, 'DATE REQ.', date_req, fill=True)
    table = add_column(table, 'LOCATION', location, fill=True)

    # Replace values
    table.replace(to_replace=r'\r', value=' ', regex=True, inplace=True)
    table.replace(to_replace=',', value='', regex=True, inplace=True)

    # Rename columns
    subtotal_header = '$ AMOUNT'
    if subtotal_header not in table.columns:
        subtotal_header = 'AMOUNT IN SGD'
    table.rename(columns={subtotal_header: 'PDF SUBTOTAL'}, inplace=True)
    table['PDF SUBTOTAL'] = table['PDF SUBTOTAL'].astype('float64')

    # Get total amount from sum of subtotals
    total = sum(table['PDF SUBTOTAL'])
    table = add_column(table, 'TOTAL AMT', total, fill=False)

    # Fill in blank values in DO/NO and convert to integer
    table['DO/NO'] = table['DO/NO'].ffill()
    table['DO/NO'] = table['DO/NO'].astype(int)

    # Convert QTY to 6 d.p.
    table['QTY'] = table['QTY'].astype('float64')
    table.loc[table['QTY'] != '', 'QTY'] = pd.to_numeric(table.loc[table['QTY'] != '', 'QTY'], errors='coerce').round(6)

    return table


def complete_table(table, lines):
    """
    Complete table with all other required variables.

    Args:
        table (pandas.core.frame.DataFrame): Dataframe of table
        lines (list): List of lines from PDF

    Returns:
        table (pandas.core.frame.DataFrame): Dataframe of table with all other required variables
    """
    for i in range(len(lines)):
        # Get Invoice no.
        if 'INVOICE NO' in lines[i].upper():
            inv_no = int(lines[i].split(':')[-1].strip())
            table = add_column(table, 'INVOICE NO. 1', inv_no, fill=False)
            table = add_column(table, 'INVOICE NO. 2', inv_no, fill=True)

        # Get Invoice date
        if ('DATE' in lines[i].upper()) and ('DUE' not in lines[i].upper()):
            inv_date = lines[i].split(':')[-1].strip()
            table = add_column(table, 'INVOICE DATE', inv_date, fill=False)

        # Get Order ref. no.
        if 'CUSTOMER ORDER REF' in lines[i].upper():
            order_ref = lines[i].split(':')[1].strip().split(' ')[0].strip()
            table = add_column(table, 'ORDER REF.', order_ref, fill=True)

            if "CSBP" in order_ref.upper():                
                subcon = "CSBP"
                zone = "A"

            elif "BBR" in order_ref.upper():
                subcon = "BBR"
                zone = "B"

            else:
                raise ValueError("Invalid order ref!")
                
            table = add_column(table, 'ZONE', zone, fill=True)
            table = add_column(table, 'SUBCON', subcon, fill=True)

    # Get MMMM YY
    mmmm_yy = pd.to_datetime(inv_date).strftime('%Y %m')
    table = add_column(table, 'FOR MONTH (YYYY MM)', mmmm_yy, fill=True)

    # Insert blank columns
    table.insert(0, 'CODE 1', '')
    table.insert(0, 'CODE 2', '')

    return table
