#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import re

# Libs
import pandas as pd
from PyPDF2 import PdfReader

# Custom
from .acs_utils import add_data, extract_data, get_data, get_totals

#############
# Functions #
#############

def acs_main(pdf_file_paths):
    """
    Main function for ACS.

    Args:
        pdf_file_paths (list): List of PDF file paths

    Returns:
        df_all (pandas.core.frame.DataFrame): Dataframe with extracted data
    """

    # Initialize empty dataframe
    df_all = None

    # Initialize headers
    data_headers = [
        'Ref No.', 'Date', 'Description', 'Total Qty', 'Unit', 'Unit Price', 'Subtotal Amount', 
        'Total Amt per Inv', 'For Month (YYYY MM)', 'Invoice No.', 'Zone', 'Specific Location', 
        'Location', 'Contact No.', 'Ordered By / Remarks', 'For TAK or Subcon? [Pintary/BBR/KKL...etc]', 
        'DO Date', 'DO No.', 'Description3', 'Code1', 'Code2', 'Code3', 'Code4', 'Qty', 'Subtotal (S$)'
        ]

    # Dictionary to store values
    subcons = {
        'SRM': 'SRM',
        'FATT HENG': 'FATT HENG',
        'CHIAN TECK': 'CT',
        'SIONG': 'SIONG'
    }

    sites = {
        'OB/LAB': 'OB',
        'FAB': 'FAB'
    }

    # Pattern to match for entries
    pattern = re.compile(
        r'(\d{2}/\d{2}/\d{4})'                   # Date pattern
        r' (\w{2} \d{8})'                        # Alphanumeric pattern
        r' (.*?)'                                # Lazy matching any character
        r' ((?:\d{1,3},)*(?:\d+)(?:\.\d{1,2})?)' # Number with optional comma and decimal
        r' (CU)'                                 # Literal "CU"
        r' ((?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)'   # Number with optional comma and decimal
        r' ((?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)'   # Number with optional comma and decimal
    )

    # Loop through all PDF files
    for f in pdf_file_paths:
        pdf_file = PdfReader(open(f, 'rb'))

        # Initialize variables
        df_data = pd.DataFrame(columns=data_headers)
        ref_no = None
        date = None
        subcon = None
        contents = list()

        # Iterate through pages
        for p in range(len(pdf_file.pages)):
            page = pdf_file.pages[p]
            text = page.extract_text()
            lines = text.split('\n')

            for i in range(len(lines)):
                # Get reference number
                if ref_no is None:
                    if ('INVOICE NO' in lines[i].upper()) and (len(lines[i].split(' ')[-1]) == 6):
                        ref_no = lines[i].split(' ')[-1]

                # Get invoice date
                if date is None:
                    if ('DATE:' in lines[i].upper()) and (lines[i].count('/') == 2):
                        date = lines[i].split(' ')[-1]
                        date = pd.to_datetime(date, format='%d/%m/%Y').strftime('%d %b %Y')

                # Get subcon and location
                if ('UMC' in lines[i].upper()) and ('@' not in lines[i].upper()) and (subcon is None):
                    subcon = extract_data(lines[i].upper(), subcons)
                    location = extract_data(lines[i].upper(), sites)          

                # Get invoice details
                match = pattern.match(lines[i])
                if match:
                    do_line = list(match.groups())
                    do_date = pd.to_datetime(do_line[0], format='%d/%m/%Y').strftime('%d %b %Y')
                    do_mth = pd.to_datetime(do_line[0], format='%d/%m/%Y').strftime('%Y %m')
                    do_no = do_line[1]
                    do_desc = do_line[2]
                    do_qty = do_line[3]
                    do_unitprice = do_line[5]
                    contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice])

                # Get underload charges
                if 'UNDERLOAD CHARGES' in lines[i].upper():
                    previous = contents[-1]
                    underload = [
                        previous[0], 
                        previous[1], 
                        previous[2], 
                        previous[3] + f' - UNDERLOAD CHARGES - {float(previous[4])}m3', '1', lines[i].split(' ')[-1]
                    ]
                    contents.append(underload)

                # Get sub-total
                if 'SUB-TOTAL' in lines[i].upper():
                    sub_total = float(lines[i].split(' ')[-1].replace(',', ''))

        # Get unique descriptions and total qty
        pricings, total_qty = get_totals(contents)

        # Add rows to dataframe
        unique_rows = len(pricings.keys())-1
        total_rows = len(contents)
        df_data = df_data.reindex(range(total_rows))

        # Get data from contents
        for_month, do_date, do_no, description3, qty = get_data(contents)

        # Add data to dataframe
        df_data = add_data(
            df_data, unique_rows, pricings, total_qty, for_month, do_date, 
            do_no, description3, qty, ref_no, date, sub_total, location, subcon
        )
        df_data.loc[total_rows] = pd.Series(dtype='object')

        if df_all is None:
            df_all = df_data
        else:
            df_all = pd.concat([df_all, df_data])

    return df_all
