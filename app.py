import os
import warnings
import streamlit as st
from dotenv import load_dotenv
from src.process import acs_main, brc_main, panu_main
from src.session import clear_uploads, initialize_session_state
from src.uploads import copy_uploads, show_uploads
from src.utils import dropdown_options, get_file_paths

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables
load_dotenv()
upload_path = os.getenv('UPLOAD_PATH')
output_path = os.getenv('OUTPUT_PATH')

# Clear and initialize session the first time the app starts up
if "uploaded_files" not in st.session_state:
    initialize_session_state()

# Set up Streamlit page
st.set_page_config(
    page_title="Invoice Info Extraction",
    page_icon="💸",
    layout="centered"
)

st.title("Extract Information from Invoices")

uploaded_file = st.file_uploader(
    "Upload your invoices for information extraction!",
    type=["zip", "pdf", "xlsx"],
    key=st.session_state["file_uploader_key"],
)

if uploaded_file:
    # Copy the uploaded file into the upload_path
    copy_uploads(uploaded_file, upload_path)
    
    # Append to the list of uploaded files in session state
    if uploaded_file.name not in st.session_state["uploaded_files"]:
        st.session_state["uploaded_files"].append(uploaded_file.name)

    # Display the list of uploaded files
    show_uploads()

    # Clear uploaded files
    if st.button("Clear uploaded files"):
        clear_uploads()

    # Get file paths of uploads
    pdf_file_paths, excel_file_paths = get_file_paths()

    # Get option to process data from dropdown menu
    option = dropdown_options()
    
    if st.button("Process"):
        result = None

        if option == "ACS":
            result = acs_main(pdf_file_paths)
            st.write(f"{len(pdf_file_paths)}/{len(pdf_file_paths)} files processed successfully!")

        elif option == "BRC":
            result, error_files = brc_main(pdf_file_paths)

            # Display error files if any
            if error_files:
                st.write("\nThe following files encountered errors during processing:")
                for file in error_files:
                    st.write(file)

            # Display the number of files processed
            st.write(f"\n{len(pdf_file_paths) - len(error_files)}/{len(pdf_file_paths)} files processed successfully!")

        elif option == "PANU":
            result = panu_main(pdf_file_paths, excel_file_paths)
            total_files = len(pdf_file_paths) + len(excel_file_paths)
            st.write(f"{total_files}/{total_files} files processed successfully!")

        elif option == "SINMIX":
            pass

        if result is not None:
            result_path = os.path.join(output_path, f"{option}.xlsx")
            result.to_excel(result_path, index=False)

            with open(result_path, "rb") as file:
                st.download_button(
                    label="Download result",
                    data=file,
                    file_name=f"{option}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.warning("Please clear the uploaded files or refresh page to process another set of files.")
