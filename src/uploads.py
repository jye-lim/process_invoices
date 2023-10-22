import os
import shutil
import zipfile
import streamlit as st

def unzip_file(zipped_file, upload_path):
    """
    Unzip a file into a given path

    Args:
        zipped_file (FileStorage): The file to be unzipped
        upload_path (str): The path where the file will be unzipped
    """
    with zipfile.ZipFile(zipped_file, 'r') as z:
        for member in z.infolist():
            if not member.is_dir():
                with z.open(member) as source, open(os.path.join(upload_path, os.path.basename(member.filename)), 'wb') as target:
                    shutil.copyfileobj(source, target)


def copy_uploads(uploaded_file, upload_path):
    """
    Copy user uploads into a given path

    Args:
        uploaded_file (FileStorage): The file to be copied
        upload_path (str): The path where the file will be copied
    """
    if uploaded_file.name.endswith(".zip"):
        unzip_file(uploaded_file, upload_path)
    else:
        with open(os.path.join(upload_path, uploaded_file.name), 'wb') as f:
            f.write(uploaded_file.getvalue())


def show_uploads():
    """
    Displays the list of uploaded files.
    """
    if st.session_state["uploaded_files"]:
        st.write("#### List of Uploaded Files:")
        for file_name in st.session_state["uploaded_files"]:
            st.markdown(f"- {file_name}")
    else:
        st.write("No files uploaded yet.")
