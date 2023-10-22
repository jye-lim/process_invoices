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
from src.process.utils.panu_utils import add_data, get_data, get_totals

#############
# Functions #
#############

def process_pdf(df_all, pdf_file_paths):
    """
    Process PDF files to extract data.

    Args:
        df_all (pandas.core.frame.DataFrame): Dataframe with extracted data
        pdf_file_paths (list): List of PDF file paths

    Returns:
        df_all (pandas.core.frame.DataFrame): Dataframe with extracted data
    """
    # Initialize headers
    data_headers = [
        'Inv No.', 'Date', 'Description', 'Total Qty', 'Unit', 'Unit Rate', 'Subtotal Amount', 'Total Amt per Inv',
        'For Month (YYYY MM)', 'Zone', 'For TAK or Subcon? [Pintary/BBR/KKL...etc]', 'DO Date', 'DO No.',
        'Description2', 'Code1', 'Code2', 'Code3', 'Code4', 'Qty', 'Subtotal (S$)'
        ]

    # Initialize underload charges dictionary
    underload_charges = {
        1.0: 66.00,
        1.5: 60.00,
        2.0: 54.00,
        2.5: 48.00,
        3.0: 42.00,
        3.5: 36.00,
        4.0: 30.00,
        4.5: 24.00,
        5.0: 18.00,
        5.5: 12.00,
        6.0: 6.00
    }

    # Patterns to match for entries
    pattern = re.compile(
        r'(\d{2}/\d{2}/\d{4})'                  # Date in format dd/mm/yyyy
        r' (\d{8})'                             # 8-digit number
        r' (.*)'                                # Any sequence of characters
        r' ((?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)'  # Number with optional comma separators and optional two decimal points
        r' (\d{1,3}(,\d{3})*|^\d+)(\.\d+)?'     # Number with optional comma separators and optional decimal points
        r' (\d{1,3}(,\d{3})*|^\d+)(\.\d+)?'     # Another number with similar format
    )

    split_pattern1 = re.compile(
        r'(\d{2}/\d{2}/\d{4})'   # Date in format dd/mm/yyyy
        r' (\d{8})'              # 8-digit number
        r' (.*)'                 # Any sequence of characters
    )

    split_pattern2 = re.compile(
        r'(\d+%[A-Z|a-z]+'                 # A number followed by a '%' and then letters
        r'(?:&[A-Z|a-z]+)*)'               # Optionally followed by '&' and more letters (zero or more times)
        r' *\*?'                           # Optional spaces followed by an optional '*'
        r'(\d{1,3}(?:,\d{3})*\.\d{2})'     # Number with optional comma separators followed by a period and two digits
        r' (\d{1,3}(?:,\d{3})*\.\d{2})'    # Same format number as above
        r' (\d{1,3}(?:,\d{3})*\.\d{2})'    # Same format number as above
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
                    if 'INVOICE NO' in lines[i].upper():
                        inv_no = re.search(r'\d{9}', lines[i+1])[0]

                # Get invoice date
                if date is None:
                    if ('DATE' in lines[i].upper()) and (lines[i+1].count('/') == 2):
                        date = re.search(r'\d{2}/\d{2}/\d{4}', lines[i+1])[0]
                        date = pd.to_datetime(date, format='%d/%m/%Y').strftime('%d %b %Y')

                # Get subcon and location
                if subcon is None:
                    if 'LOCATION/SITE' in lines[i].upper():
                        match = re.findall(r'\((.*?)\)', lines[i])[0]
                        #location = match.split(' ')[0]
                        subcon = match.split(' ')[-1]

                # Get invoice details
                match = pattern.match(lines[i])
                split_match2 = split_pattern2.match(lines[i])

                if match:
                    do_line = list(match.groups())
                    do_mth = pd.to_datetime(do_line[0], format='%d/%m/%Y').strftime('%Y %m')
                    do_date = pd.to_datetime(do_line[0], format='%d/%m/%Y').strftime('%d %b %Y')
                    do_no = do_line[1]
                    do_desc = do_line[2]
                    do_qty = do_line[3]
                    do_unitprice = do_line[4]

                    # Check if underload
                    if '*' in do_desc:
                        # Add entry without underload
                        do_desc = do_desc.replace('*', '')
                        do_desc = do_desc.strip()
                        contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice])

                        # Add entry with underload
                        do_desc = do_desc + f' - UNDERLOAD CHARGES - {float(do_qty)}m3'
                        do_unitprice = underload_charges[float(do_qty)]
                        do_qty = '1'

                    contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice])

                elif split_match2:
                    split_match1 = split_pattern1.match(lines[i-1])
                    if split_match1:
                        do_line1 = list(split_match1.groups())
                        do_line2 = list(split_match2.groups())
                        do_mth = pd.to_datetime(do_line1[0], format='%d/%m/%Y').strftime('%Y %m')
                        do_date = pd.to_datetime(do_line1[0], format='%d/%m/%Y').strftime('%d %b %Y')
                        do_no = do_line1[1]
                        do_desc = do_line1[2] + ' ' + do_line2[0].strip()
                        do_qty = do_line2[1]
                        do_unitprice = do_line2[2]
                        do_subtotal = do_line2[3]

                        # Check if underload
                        if ('*' in do_desc) or ('*' in lines[i]):
                            # Add entry without underload
                            do_desc = do_desc.replace('*', '')
                            do_desc = do_desc.strip()
                            contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice])

                            # Add entry with underload
                            do_desc = do_desc + f' - UNDERLOAD CHARGES - {float(do_qty)}m3'
                            do_unitprice = underload_charges[float(do_qty)]
                            do_qty = '1'

                        contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice])

                # Get underload charges
                if 'UNDERLOAD CHARGES' in lines[i].upper():
                    underload_unitprice = lines[i].split(' ')[-1]

                # Get sub-total
                if 'SUB-TOTAL' in lines[i].upper():
                    sub_total = float(lines[i].split('$')[-1].replace(',', ''))

        # Get unique descriptions and total qty
        pricings, total_qty = get_totals(contents)

        # Add rows to dataframe
        unique_rows = len(pricings.keys())-1
        total_rows = len(contents)
        df_data = df_data.reindex(range(total_rows))

        # Get data from contents
        for_month, do_date, do_no, description2, qty = get_data(contents)

        # Add data to dataframe, if error, add file name and continue
        df_data = add_data(df_data, unique_rows, pricings, total_qty, for_month, do_date, do_no, description2, qty, inv_no, date, sub_total, subcon)

        # Add empty row
        df_data.loc[total_rows] = pd.Series(dtype='object')

        # Append data to df_all
        if df_all is None:
            df_all = df_data
        else:
            df_all = pd.concat([df_all, df_data], ignore_index=True)

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

    # Get data from summary xlsx
    xlsx_do_no = df_xlsx.iloc[:, 4]
    xlsx_comments_order = df_xlsx.iloc[:, 16]
    xlsx_comments_ipad = df_xlsx.iloc[:, 17]
    xlsx_signee = df_xlsx.iloc[:, 18]

    # Put extracted data into new df
    df_comments = pd.DataFrame({
        'DO No.': xlsx_do_no,
        'Comments at Order Time': xlsx_comments_order,
        'Comments on iPad': xlsx_comments_ipad,
        'Name of Signee': xlsx_signee
        })

    # Remove NaN rows and header
    df_comments = df_comments.dropna(subset=['DO No.'])
    df_comments = df_comments.iloc[1:]
    df_comments.reset_index(drop=True, inplace=True)

    return df_comments


def panu_main(pdf_file_paths, excel_file_paths):
    """
    Main function for PANU.

    Args:
        pdf_file_paths (list): List of PDF file paths
        excel_file_paths (list): List of excel file paths

    Returns:
        df_all (pandas.core.frame.DataFrame): Dataframe with extracted data
    """
    # Initialize empty dataframe
    df_all = None

    # Process PDF files
    df_all = process_pdf(df_all, pdf_file_paths)

    # Process excel file
    df_comments = process_excel(excel_file_paths[0])

    # Merge df_all and df_comments based on DO No.
    df_all = pd.merge(df_all, df_comments, how='left', on='DO No.')

    # Reorder columns
    df_all = df_all[[
        'Inv No.', 'Date', 'Description', 'Total Qty', 'Unit', 'Unit Rate', 'Subtotal Amount', 'Total Amt per Inv', 'For Month (YYYY MM)',
        'Zone', 'Comments at Order Time', 'Comments on iPad', 'Name of Signee', 'For TAK or Subcon? [Pintary/BBR/KKL...etc]', 'DO Date', 
        'DO No.', 'Description2', 'Code1', 'Code2', 'Code3', 'Code4', 'Qty', 'Subtotal (S$)'
        ]]

    return df_all
