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
from .acs_utils import add_data, get_data, get_totals

##################
# Configurations #
##################

# Pattern to match for invoice details
inv_pattern = re.compile(
    r'\s*(?P<date>\d{2}/\d{2}/\d{4})'                       # Date pattern
    r'\s*(?P<do_no>\w{2} \d{8})'                            # DO NO.
    r'\s*(?P<desc>.*?)'                                     # Description
    r'\s*(?P<qty>(?:\d{1,3},)*(?:\d+)(?:\.\d{1,2})?)\s*CU'  # Quantity
    r'\s*(?P<unit_price>(?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)'  # Unit Price
    r'\s*(?P<inv_amt>(?:\d{1,3},)*(?:\d+)(?:\.\d{2})?)'     # Invoice Amount
)

# Pattern for location and subcon
loc_subcon_pattern = re.compile(
    r'\s*(?P<project>[A-Za-z]+)'                    # Project
    r'\s*@'
    r'\s*(?P<location>[A-Z\s\.]+)-'                 # Location
    r'\s*(?P<subcon>[A-Z]+)'                        # Subcontractor
    r'\s*Contract\s*No\s*:\s*(?P<contact>\d+)\s*'  # Contact number
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
        "Size",
        "Ordered by TAK or Subcon? [Pintary/ BBR/ KKL..etc]",
        "DO Date",
        "DO No.",
        "Description2",
        "Code1",
        "Code2",
        "Code3",
        "Code4",
        "Qty",
        "Vendor Invoice Amount",
    ]

    # Loop through all PDF files
    for f in pdf_file_paths:
        pdf_file = PdfReader(open(f, 'rb'))

        # Initialize variables
        df_data = pd.DataFrame(columns=data_headers)
        inv_no = None
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
                if inv_no is None:
                    if ('INVOICE NO' in lines[i].upper()) and (len(lines[i].split(' ')[-1]) == 6):
                        inv_no = lines[i].split(' ')[-1]

                # Get invoice date
                if date is None:
                    if ('DATE:' in lines[i].upper()) and (lines[i].count('/') == 2):
                        date = lines[i].split(' ')[-1]
                        date = pd.to_datetime(date, format='%d/%m/%Y').strftime('%d %b %Y')

                # Get subcon and location
                match = re.search(loc_subcon_pattern, lines[i])
                if match:
                    subcon = match.group("subcon").strip().upper() if not None else ""
                    location = match.group("location").strip() if not None else ""

                # Get invoice details
                match = inv_pattern.match(lines[i])
                if match:
                    do_date = pd.to_datetime(match.group("date"), format='%d/%m/%Y').strftime('%d %b %Y')
                    do_mth = pd.to_datetime(match.group("date"), format='%d/%m/%Y').strftime('%Y %m')
                    do_no = match.group("do_no").strip().upper().replace(" ", "") if not None else ""
                    do_desc = match.group("desc").strip() if not None else ""
                    do_qty = match.group("qty").strip() if not None else ""
                    do_unitprice = match.group("unit_price").strip() if not None else ""
                    do_invamt = float(match.group("inv_amt").strip().replace(",", ""))
                    contents.append([do_mth, do_date, do_no, do_desc, do_qty, do_unitprice, do_invamt])

                # Get underload charges
                if 'UNDERLOAD CHARGES' in lines[i].upper():
                    previous = contents[-1]
                    underload = [
                        previous[0], 
                        previous[1], 
                        previous[2], 
                        previous[3] + f' - UNDERLOAD CHARGES - {float(previous[4])}m3',
                        '1',
                        lines[i].split(' ')[-1],
                        lines[i].split(' ')[-1],
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

        # Add data to dataframe
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
            df_all = pd.concat([df_all, df_data])

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
        "Purchaser Personnel Contact": df_xlsx["SITE CONTACT NO"],
        "Bored Pile No.: OR Location ***": df_xlsx["STRUCTURAL ELEMENT"],
        "Purchaser Personnel Name": df_xlsx["PURCHASER REPRESENTATIVE"],
    })

    # Remove NaN rows and header
    df_comments = df_comments.dropna(subset=['DO No.'])
    df_comments = df_comments.iloc[1:]
    df_comments.reset_index(drop=True, inplace=True)

    return df_comments


def acs_main(pdf_file_paths, excel_file_paths):
    """
    Main function for ACS.

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
            "Purchaser Personnel Name",
            "Purchaser Personnel Contact",
            "Bored Pile No.: OR Location ***",
            "Size",
            "Ordered by TAK or Subcon? [Pintary/ BBR/ KKL..etc]",
            "DO Date",
            "DO No.",
            "Description2",
            "Code1",
            "Code2",
            "Code3",
            "Code4",
            "Qty",
            "Vendor Invoice Amount",
        ]
    ]

    return df_all
