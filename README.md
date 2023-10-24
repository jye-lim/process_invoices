# Invoice Info Extraction

This repository contains a Streamlit application that allows users to upload invoices and extract relevant information from them.

You can either access it through the [Streamlit Sharing](https://process-invoices.streamlit.app) platform or run it locally.
<br></br>

## Features

- **File Uploading**: Users can upload invoices in the form of ZIP, PDF, or XLSX files.
<br></br>

- **Multiple Processing Options**: The application currently supports processing options for ACS, BRC, PANU, and SINMIX invoices.
<br></br>

- **Results Download**: After processing, users can download the extracted information in Excel format. For the SINMIX option, processed PDFs can be downloaded in a zipped format.
<br></br>

## Running the Application Locally

Ensure you have the required libraries installed by running:

```bash
pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run app.py
```

<br></br>

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
