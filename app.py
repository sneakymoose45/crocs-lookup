import streamlit as st
import pandas as pd
import time

st.title("Dynamic Lookup Tool")

st.write("Upload Master and Input files to perform dynamic lookup.")

# Upload files
master_file = st.file_uploader("Upload Master File", type=["csv", "xlsx"])
input_file = st.file_uploader("Upload Input File", type=["csv", "xlsx"])


# Sheet selection variables
master_sheet = None
input_sheet = None


# If Excel → show sheet selector
if master_file is not None and master_file.name.endswith(".xlsx"):
    master_sheets = pd.ExcelFile(master_file).sheet_names
    master_sheet = st.selectbox("Select Master Sheet", master_sheets)

if input_file is not None and input_file.name.endswith(".xlsx"):
    input_sheets = pd.ExcelFile(input_file).sheet_names
    input_sheet = st.selectbox("Select Input Sheet", input_sheets)


# Preview file without headers
def read_preview(file, sheet=None):

    if file.name.endswith(".csv"):
        return pd.read_csv(file, header=None)

    else:
        return pd.read_excel(file, sheet_name=sheet, header=None)


# Read file using selected header
def read_file(file, header_row, sheet=None):

    if file.name.endswith(".csv"):
        df = pd.read_csv(file, header=header_row)

    else:
        df = pd.read_excel(file, sheet_name=sheet, header=header_row)

    return df


if master_file and input_file:

    st.subheader("Step 1: Select Header Row")

    master_preview = read_preview(master_file, master_sheet)
    input_preview = read_preview(input_file, input_sheet)

    col1, col2 = st.columns(2)

    with col1:
        st.write("Master File Preview")
        st.dataframe(master_preview.head(10))

        master_header = st.number_input(
            "Header Row Number (Master)",
            min_value=1,
            value=1
        )

    with col2:
        st.write("Input File Preview")
        st.dataframe(input_preview.head(10))

        input_header = st.number_input(
            "Header Row Number (Input)",
            min_value=1,
            value=1
        )

    # Convert to zero index
    master_df = read_file(master_file, master_header - 1, master_sheet)
    input_df = read_file(input_file, input_header - 1, input_sheet)

    st.subheader("Step 2: Data Preview")

    st.write("Master Data")
    st.dataframe(master_df.head())

    st.write("Input Data")
    st.dataframe(input_df.head())

    master_columns = master_df.columns.tolist()
    input_columns = input_df.columns.tolist()

    st.subheader("Step 3: Select Lookup Keys")

    col3, col4 = st.columns(2)

    with col3:
        master_key = st.selectbox("Master Key Column", master_columns)

    with col4:
        input_key = st.selectbox("Input Key Column", input_columns)

    st.subheader("Step 4: Select Columns to Pull")

    available_columns = [c for c in master_columns if c != master_key]

    selected_columns = st.multiselect(
        "Columns from Master to Add",
        available_columns
    )

    if st.button("Run Lookup"):

        progress = st.progress(0)
        status = st.empty()

        status.text("Preparing data...")
        progress.progress(10)

        # Clean key columns to ensure matching
        input_df[input_key] = (
            input_df[input_key]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        master_df[master_key] = (
            master_df[master_key]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        time.sleep(0.3)
        progress.progress(30)

        merge_cols = [master_key] + selected_columns

        status.text("Running lookup...")

        merged = pd.merge(
            input_df,
            master_df[merge_cols],
            left_on=input_key,
            right_on=master_key,
            how="left",
            suffixes=("", "_master")
        )

        progress.progress(60)

        status.text("Updating columns...")

        for col in selected_columns:

            if col in input_df.columns:

                merged[col] = merged[col].combine_first(
                    merged[col + "_master"]
                )

                merged.drop(columns=[col + "_master"], inplace=True)

            else:

                merged.rename(
                    columns={col + "_master": col},
                    inplace=True
                )

        progress.progress(80)

        # Remove duplicate key if different
        if master_key != input_key:
            merged.drop(columns=[master_key], inplace=True)

        status.text("Finalizing output...")
        time.sleep(0.3)

        progress.progress(100)

        status.text("Lookup Completed!")

        st.subheader("Output Preview")

        st.dataframe(merged)

        csv = merged.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Output File",
            csv,
            "lookup_output.csv",
            "text/csv"
        )