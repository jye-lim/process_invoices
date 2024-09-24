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

# Patterns to match for comments in Excel
start_pattern = re.compile(
    r'(?P<name>[A-Za-z\s]+)\s+'  # Captures the name, consisting of letters and spaces
    r'(?P<number>\d{8})\s*'      # Captures an 8-digit number
    r'.*'                        # Matches anything else at the end
)

pile_pattern = re.compile(
    r'.*?'                               # Matches any content before pile
    r'(?P<pile>[CcFfPp]?\s*-?\s*\d{3})'  # Captures the pile (C/P optional, followed by 3 digits)
    r'.*'                                # Matches any content after pile
)

lp_pattern = re.compile(
    r'.*?'                              # Matches any content before LP (non-greedy)
    r'(?P<lp>[lL][pP]\s*-?\s*\d+)\s*'   # Captures LP (case-insensitive) and an optional number
    r'.*'                               # Matches anything else at the end
)

gate_pattern = re.compile(
    r'.*?'                                       # Matches any content before pile
    r'(?P<gate>[Gg][Aa][Tt][Ee]\s*-?\s*\d+)\s*'  # Captures Gate (case-insensitive) and an optional number
    r'.*'                                        # Matches anything else at the end
)

# Pattern to match description for code column
description_pattern = re.compile(
    r'(GR\s*\d+)'                                      # Matches concrete grade
    r'(?:.*?\b(\d{2,4}\s*-\s*\d{2,4}\s*[Mm][Mm])\b)?'  # Optionally matches the size range in MM (e.g., 160-210MM)
    r'(?:.*?\b(\d+\s*HR)\b)?'                          # Optionally matches time duration (e.g., 4HR)
    r'(?:.*?\b(RTD)\b)?'                               # Optionally matches "RTD"
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
    Get unique descriptions and total qty.

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
    Extract data from line using for loop.

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
        grade (str): Grade of concrete
        size (str): Slump value
        rtd (str): RTD if retardant was used, else ""
        duration (str): Duration of retardation
    """
    match = re.search(description_pattern, desc)
    if match:
        gde = match.group(1) if match.group(1) else ""
        size = match.group(2) if match.group(2) else ""
        duration = match.group(3) if match.group(3) else ""
        rtd = match.group(4) if match.group(4) else ""
    
    # Convert grade data
    grade = grade_dict[gde[-2:]]

    return grade, size, rtd, duration


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
        code_1.append(code_contents[0])
        code_2.append(code_contents[1])
        code_3.append(code_contents[2])
        code_4.append(code_contents[3])
        
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
    df_data["For TAK or Subcon? [Pintary/BBR/KKL...etc]"] = subcon
    df_data["Zone"] = zone_dict[subcon.upper()]
    df_data["DO Date"] = do_date
    df_data["DO No."] = do_no
    df_data["Description2"] = description2
    df_data["Qty"] = qty
    df_data["Subtotal (S$)"] = amount
    df_data["Code1"] = code_1
    df_data["Code2"] = code_2
    df_data["Code3"] = code_3
    df_data["Code4"] = code_4

    df_data["Total Qty"] = pd.to_numeric(df_data["Total Qty"], errors="coerce")
    df_data["Unit Rate"] = pd.to_numeric(df_data["Unit Rate"], errors="coerce")
    df_data["Total Amt per Inv"] = pd.to_numeric(df_data["Total Amt per Inv"], errors="coerce")
    df_data["Qty"] = pd.to_numeric(df_data["Qty"], errors="coerce")
    df_data["Subtotal (S$)"] = pd.to_numeric(df_data["Subtotal (S$)"], errors="coerce")

    df_data["Subtotal Amount"] = df_data["Total Qty"] * df_data["Unit Rate"]

    # Add units
    for i in range(len(pricings.keys())):
        if "UNDERLOAD CHARGES" in df_data.loc[i, "Description"]:
            df_data.loc[i, "Unit"] = "TRIP"
        else:
            df_data.loc[i, "Unit"] = "m3"

    return df_data


def standardise_field(data, connector):
    """
    Function to standardise a given field.

    Args:
        data (str): Raw extracted data to be standardised.
        connector (str): Connector to be used to join the alphabet and numeric component.

    Returns:
        str: Standardised data
    """
    # Find the match
    pattern = r'([A-Za-z]+)\s*-?\s*([0-9]+)'
    match = re.search(pattern, data)

    # If a match is found, standardise it. Else, return original data.
    if match:
        data = f"{match.group(1)}{connector}{match.group(2)}"
    return data


def process_field(field, standardize=False, connector="", title_case=False):
    """
    Function to process optional fields.

    Args:
        field (str): Given field to process.
        standardise (bool): Whether to run standardise_field method on field.
        connector (str): Connector to be used to join the alphabet and numeric component.
        title_case (bool): Whether to run title casing on input field.

    Returns
        str: Processed field. If field is None, returns an empty string.
    """
    if field is not None:
        field = field.strip()
        # Edge case for pile data which only consists of pile number
        if field.isnumeric() and len(field) == 3:
            field = "C" + str(field)

        if standardize:
            field = standardise_field(field, connector)
        if title_case:
            field = field.title()
        return field.upper() if not title_case else field
    return ""


def process_comment(comment):
    """
    Function to process each field derived from the Excel comment.

    Args:
        comment (str): Comment from Excel, typically containing information like 
                       name, number, pile, LP, and gate.

    Returns:
        pd.Series: A Pandas Series containing the extracted fields in the following order:
            - name (str): The name extracted from the comment (title-cased).
            - number (str): The 8-digit number extracted from the comment.
            - pile (str): The pile identifier extracted (e.g., 'C101' or '101'), standardized if applicable.
            - lp (str): The LP (license plate) number extracted from the comment.
            - gate (str): The gate information extracted (title-cased).
            
        If no match is found for a specific field, an empty string is returned for that field.
    """
    # Initialize fields with default values
    name, number, pile, lp, gate = "", "", "", "", ""

    # Run regex searches on the comment
    start_match = re.search(start_pattern, comment)
    pile_match = re.search(pile_pattern, comment)
    lp_match = re.search(lp_pattern, comment)
    gate_match = re.search(gate_pattern, comment)

    # Extract matches
    if start_match:
        name = start_match.group('name').strip().title()
        number = start_match.group('number').strip()
        name_number = f"{name} {number}"
    if pile_match:
        pile = process_field(pile_match.group('pile'), standardize=True, connector="-")
    if lp_match:
        lp = process_field(lp_match.group('lp'), standardize=True, connector=" ")
    if gate_match:
        gate = process_field(gate_match.group('gate'), title_case=True)
    
    # Return a Pandas Series containing the extracted fields
    return pd.Series([name_number, pile, lp, gate])
