#!/usr/bin/env python

####################
# Required Modules #
####################

# Generic/Built-in
import re

# Libs
import pandas as pd

##################
# Configurations #
##################

# Pattern to match description for code column
description_pattern = re.compile(
    r'(?P<description>.*?)'                # Captures everything in front
    r'(?:.*?\b(?P<duration>\d+\s*[Hh]?[Rr]?)\b)?'  # Optionally captures retardation duration
    r'(?:.*?\b(?P<rtd>RTD)\b)?'            # Optionally captures 'RTD'
)

# Dictionary for different concrete grades
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

# Dictionary of zones for each subcon
zone_dict = {
    "CSBP": "A",
    "BBR": "B",
}

#############
# Functions #
#############

def get_totals(contents):
    """
    Get unique descriptions and total qty

    Args:
        contents (list): List of lists containing invoice details

    Returns:
        pricings (dict): Dictionary of unique descriptions and unit prices
        total_qty (dict): Dictionary of unique descriptions and total quantities
    """
    pricings = dict()
    total_qty = dict()

    for entries in contents:
        if entries[3] not in pricings:
            pricings[entries[3]] = entries[5]
            total_qty[entries[3]] = float(entries[4])
        else:
            total_qty[entries[3]] += float(entries[4])
            
    return pricings, total_qty


def extract_data(line, data_dict):
    """
    Extract data from line using for loop

    Args:
        line (str): Line of text
        data_dict (dict): Dictionary of data

    Returns:
        str: Data extracted from line
    """
    for key in data_dict:
        if key in line:
            return data_dict[key]
    return ''


def extract_description(desc):
    """
    Extract data from description for code columns in resulting Excel.

    Args:
        desc (str): Description2 value

    Returns:
        rtd (str): RTD if retardant was used, else ""
        duration (str): Duration of retardation
    """
    match = re.search(description_pattern, desc)
    if match:
        duration = match.group("duration") if not None else ""
        rtd = match.group("rtd") if not None else ""
    if "R" not in duration:
        duration = duration.upper() + "R"
    
    return rtd, duration


def get_data(contents):
    """
    Get data from contents.

    Args:
        contents (list): List of lists containing invoice details

    Returns:
        for_month (list): List of for_month
        do_date (list): List of do_date
        do_no (list): List of do_no
        description2 (list): List of description2
        qty (list): List of qty
        amount (list): List of invoice amounts
        code_1 (list): List of concrete grades
        code_2 (list): List of slump values
        code_3 (list): List of retardant used
        code_4 (list): List of retardant duration
    """
    for_month = list()
    do_date = list()
    do_no = list()
    description2 = list()
    qty = list()
    amount = list()
    code_1 = list()
    code_2 = list()
    code_3 = list()
    code_4 = list()

    for sublist in contents:
        for_month.append(sublist[0])
        do_date.append(sublist[1])
        do_no.append(sublist[2])
        description2.append(sublist[3])
        qty.append(sublist[4])
        amount.append(sublist[6])

        # Get code contents
        code_contents = extract_description(sublist[3])
        code_3.append(code_contents[0])
        code_4.append(code_contents[1])
        
    return for_month, do_date, do_no, description2, qty, amount, code_1, code_2, code_3, code_4


def add_data(
    df_data,
    unique_rows,
    pricings,
    total_qty,
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
    inv_no,
    date,
    sub_total,
    subcon,
):
    """
    Add data to dataframe.

    Args:
        df_data (pandas.core.frame.DataFrame): Dataframe of table
        unique_rows (int): Number of unique rows
        pricings (dict): Dictionary of unique descriptions and unit prices
        total_qty (dict): Dictionary of unique descriptions and total quantities
        for_month (list): List of for_month
        do_date (list): List of do_date
        do_no (list): List of do_no
        description2 (list): List of description2
        qty (list): List of qty
        amount (list): List of invoice amount
        code_1 (list): List of concrete grades
        code_2 (list): List of slump values
        code_3 (list): List of retardant used
        code_4 (list): List of retardant duration
        inv_no (str): Invoice number
        date (str): Invoice date
        sub_total (float): Subtotal amount
        subcon (str): Subcon name

    Returns:
        df_data (pandas.core.frame.DataFrame): Dataframe of table
    """
    df_data.loc[0, "Inv No."] = inv_no
    df_data.loc[0, "Date"] = date
    df_data.loc[0, "Total Amt per Inv"] = sub_total

    df_data.loc[:unique_rows, "Description"] = list(pricings.keys())
    df_data.loc[:unique_rows, "Total Qty"] = list(total_qty.values())
    df_data.loc[:unique_rows, "Unit Rate"] = list(pricings.values())

    df_data["For Month (YYYY MM)"] = for_month
    df_data["Ordered by TAK or Subcon? [Pintary/ BBR/ KKL..etc]"] = subcon
    df_data["Zone"] = zone_dict[subcon.upper()]
    df_data["DO Date"] = do_date
    df_data["DO No."] = do_no
    df_data["Description2"] = description2
    df_data["Qty"] = qty
    df_data["Vendor Invoice Amount"] = amount
    df_data["Code1"] = None
    df_data["Code2"] = None
    df_data["Code3"] = code_3
    df_data["Code4"] = code_4

    df_data["Total Qty"] = pd.to_numeric(df_data["Total Qty"], errors="coerce")
    df_data["Unit Rate"] = pd.to_numeric(df_data["Unit Rate"], errors="coerce")
    df_data["Total Amt per Inv"] = pd.to_numeric(df_data["Total Amt per Inv"], errors="coerce")
    df_data["Qty"] = pd.to_numeric(df_data["Qty"], errors="coerce")
    df_data["Vendor Invoice Amount"] = pd.to_numeric(df_data["Vendor Invoice Amount"], errors="coerce")

    df_data['Subtotal Amount'] = df_data['Total Qty'] * df_data['Unit Rate']

    # Add units
    for i in range(len(pricings.keys())):
        if 'UNDERLOAD CHARGES' in df_data.loc[i, 'Description']:
            df_data.loc[i, 'Unit'] = 'trip'
        else:
            df_data.loc[i, 'Unit'] = 'm3'

    return df_data
