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
from .panu_utils import add_data, get_data, get_totals, process_comment

##################
# Configurations #
##################

# Pattern for location and subcon
loc_subcon_pattern = re.compile(
    r'\s*LOCATION/SITE'               # Matches the literal "LOCATION/SITE"
    r'\s*(?P<location>[A-Z\s]+ \d+)'  # Captures the location (uppercase letters, spaces, and a number)
    r'[\s-]*'                         # Matches optional spaces or hyphens between location and subcon
    r'\s*(?:\([A-Za-z]+-)?'           # Non-capturing group to optionally match "(prefix-", like "(VSMC-"
    r'\s*(?P<subcon>[A-Za-z]+)'       # Captures the subcon
    r'\s*\)?'                         # Optionally matches a closing parenthesis
)

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
        "Inv No.",
        "Date",
        "Description",
        "Total Qty",
        "Unit",
        "Unit Rate",
        "Subtotal Amount",
        "Total Amt per Inv",
        "For Month (YYYY MM)",
        "Zone",
        "For TAK or Subcon? [Pintary/BBR/KKL...etc]",
        "DO Date",
        "DO No.",
        "Description2",
        "Code1",
        "Code2",
        "Code3",
        "Code4",
        "Qty",
        "Subtotal (S$)",
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
        r'(\d{2}/\d{2}/\d{4})\s+'                  # Date in format dd/mm/yyyy
        r'(\d{8})\s+'                              # 8-digit number
        r'(.*?)\s+'                                # Non-greedy match for any text (e.g., GR 40 SL 160-210MM 4HR RTD)
        r'((?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)\s+'   # First number with comma and optional two decimal places (e.g., 9.00)
        r'((?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)\s+'   # Second number with comma and optional two decimal places (e.g., 101.00)
        r'((?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)'      # Third number with comma and optional two decimal places (e.g., 909.00)
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
                match = re.search(loc_subcon_pattern, lines[i])
                if match:
                    location = match.group("location").strip() if not None else ""
                    subcon = match.group("subcon").strip().upper() if not None else ""

                # Get invoice details
                match = pattern.match(lines[i])
                split_match2 = split_pattern2.match(lines[i])

                if match:
                    do_line = list(match.groups())
                    do_mth = pd.to_datetime(do_line[0], format='%d/%m/%Y').strftime('%Y %m')
                    do_date = pd.to_datetime(do_line[0], format='%d/%m/%Y').strftime('%d %b %Y')
                    do_no = int(do_line[1])
                    do_desc = do_line[2]
                    do_qty = do_line[3]
                    do_unitprice = do_line[4]
                    do_invoice_amt = float(do_line[5].replace(",", ""))
                    
                    # Check if underload
                    if '*' in do_desc:
                        # Add entry without underload
                        do_desc = do_desc.replace('*', '')
                        do_desc = do_desc.strip()
                        contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice, do_invoice_amt])

                        # Add entry with underload
                        do_desc = do_desc + f' - UNDERLOAD CHARGES - {float(do_qty)}m3'
                        do_unitprice = underload_charges[float(do_qty)]
                        do_qty = '1'

                    contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice, do_invoice_amt])

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
        (
            for_month,
            do_date,
            do_no,
            description2,
            qty,
            amount,
            code_1,
            code_2,
            code_3,
            code_4,
        ) = get_data(contents)

        # Add data to dataframe, if error, add file name and continue
        df_data = add_data(
            df_data=df_data,
            unique_rows=unique_rows,
            pricings=pricings,
            total_qty=total_qty,
            for_month=for_month,
            do_date=do_date,
            do_no=do_no,
            description2=description2,
            qty=qty,
            amount=amount,
            code_1=code_1,
            code_2=code_2,
            code_3=code_3,
            code_4=code_4,
            inv_no=inv_no,
            date=date,
            sub_total=sub_total,
            subcon=subcon,
        )

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
    # Read the first few rows to inspect and find header row
    sample_rows = pd.read_excel(excel_file_path, nrows=20)  # Read first 20 rows as sample

    # Iterate through the rows to detect the header
    for i, row in sample_rows.iterrows():
        if all(col in row.values for col in ["DO No", "Comments at Order Time", "Name of signee"]):
            header_row = i + 1
            break

    # Open summary xlxs
    df_xlsx = pd.read_excel(excel_file_path, header=header_row)
    
    # Extract data from "Comments at Order Time" column
    extracted_data = df_xlsx["Comments at Order Time"].apply(process_comment)

    # Make a new dataframe to store the extracted data from comments
    df_comments = pd.DataFrame({
        "Purchaser Personnel Name & Contact": extracted_data[0],
        "Bored Pile No.: OR Location ***": extracted_data[1],
        "LP": extracted_data[2],
        "Gate No.": extracted_data[3],
        "Comments at Order Time": df_xlsx["Comments at Order Time"],
        "DO No.": df_xlsx["DO No"],
        "Name of signee": df_xlsx["Name of signee"]
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

    # Process excel file, if any
    if len(excel_file_paths) > 0:
        df_comments = process_excel(excel_file_paths[0])

        # Merge df_all and df_comments based on DO No.
        df_all = pd.merge(df_all, df_comments, how='left', on='DO No.')

    else:
        # Add empty columns
        df_all["Purchaser Personnel Name & Contact"] = None
        df_all["Bored Pile No.: OR Location ***"] = None
        df_all["LP"] = None
        df_all["Gate No."] = None
        df_all['Comments at Order Time'] = None
        df_all['Name of signee'] = None

    # Add empty column for future use
    df_all["Size"] = None

    # Reorder columns
    df_all = df_all[
        [
            "Inv No.",
            "Date",
            "Description",
            "Total Qty",
            "Unit",
            "Unit Rate",
            "Subtotal Amount",
            "Total Amt per Inv",
            "For Month (YYYY MM)",
            "Zone",
            "Comments at Order Time",
            "Purchaser Personnel Name & Contact",
            "LP",
            "Gate No.",
            "Name of signee",
            "Bored Pile No.: OR Location ***",
            "Size",
            "For TAK or Subcon? [Pintary/BBR/KKL...etc]",
            "DO Date",
            "DO No.",
            "Description2",
            "Code1",
            "Code2",
            "Code3",
            "Code4",
            "Qty",
            "Subtotal (S$)",
        ]
    ]

    return df_all
