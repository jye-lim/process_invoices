import pandas as pd
import streamlit as st
from PyPDF2 import PdfReader
from src.process.utils.brc_utils import get_table, complete_table

def brc_main(pdf_file_paths):
    """
    Main function for BRC.
    """
    # Initialize dataframe
    headers = ["INVOICE NO. 1", "INVOICE DATE", "TOTAL AMT", "INVOICE NO. 2", "FOR MONTH (YYYY MM)", "ZONE", "LOCATION", "SUBCON", "DATE REQ.", "ORDER REF.", "DO/NO", "DESCRIPTION", "CODE 1", "CODE 2", "QTY", "PDF SUBTOTAL"]
    dfs = pd.DataFrame(columns=headers)

    # List to hold error files
    error_files = []

    # Create a Streamlit progress bar
    progress = st.progress(0)
    status_text = st.empty()

    # Iterate through files
    for index, f in enumerate(pdf_file_paths):
        try:
            # Get table from PDF
            table = get_table(f)

            # Get other variables of interest and add it to table
            pdf_file = PdfReader(open(f, 'rb'))
            page = pdf_file.pages[0]
            text = page.extract_text()
            lines = text.split('\n')
            table = complete_table(table, lines)

            # Sort table columns
            table = table[headers]

            # Append to dataframe
            dfs = pd.concat([dfs, table], ignore_index=True)

        except:
            error_filename = f.split('/')[-1]
            error_files.append(error_filename)

        # Update the Streamlit progress bar
        percent_complete = (index + 1) / len(pdf_file_paths)
        progress.progress(percent_complete)
        status_text.text(f"Processed: {index + 1}/{len(pdf_file_paths)} files ({int(percent_complete*100)}% complete)")

    return dfs, error_files
