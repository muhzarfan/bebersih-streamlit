# Bebersih – Data Cleaning App

Bebersih is a web app for checking and cleaning data before it is used for analysis.

Upload a CSV or Excel file, review the issues found in the data, choose how to handle them, and download the cleaned file.

This project was created as part of a Data Analyst portfolio.

## Main Features

### 1. Upload and Preview Data

Upload a file in one of these formats:
- CSV
- Excel (`.xlsx` or `.xls`)

After uploading, you can view basic file information and preview the data.

### 2. Check Data Quality

The app checks for common data issues, including:

- **Missing values:** cells that have no value.
- **Duplicate rows:** records that appear more than once.
- **Incorrect data formats:** for example, numbers that are read as text.
- **Inconsistent text:** extra spaces or different ways of writing the same category.
- **Different date formats:** dates written in more than one format.

You can also view simple summaries of number and category columns, along with an overall data quality score.

### 3. Find Unusual Values

Some values may be very different from most of the other values in a column. For example, most orders may be worth a few hundred thousand, while one order is worth several million.

The app highlights these values in charts and in a list. For each column, you can choose to:

- **Keep:** leave the values as they are.
- **Remove:** remove rows that contain the selected values.
- **Limit:** reduce unusually high or low values to a chosen limit.

A value that looks unusual is not always wrong. Review it before deciding what to do.

### 4. Clean the Data

Choose how to handle each issue based on your needs.

| Issue | Available actions |
|---|---|
| Missing values | Remove rows or fill empty cells using the average, middle value, most common value, or a value you enter |
| Duplicate rows | Remove repeated rows using all columns or selected columns |
| Text | Remove extra spaces and make text use a consistent letter style |
| Data format | Change a column to numbers, text, or dates |
| Dates | Use one date format throughout a column |
| Column names | Rename columns |
| Inconsistent values | Correct spelling mistakes or use the same name for matching categories |
| Unusual values | Keep, remove, or limit selected values |

You can preview the planned changes before applying them. If your choices may remove rows, the app shows a warning and asks you to confirm.

### 5. Compare Before and After

After cleaning the data, compare the original file with the cleaned version.

The comparison includes:
- A summary of the data before and after cleaning.
- Charts showing the changes.
- Data previews.
- A list of the changes made.

### 6. View the Cleaning Report

The app creates a report with:
- Issues found in the original data.
- The actions chosen to handle those issues.
- Changes made during cleaning.
- Issues that may still remain.
- Data quality scores before and after cleaning.

### 7. Download the Results

Choose a file name and download the results as:
- CSV
- Excel (`.xlsx`)
- A text report

## How to Use the App

1. **Upload a file** from the Dashboard.
2. **Check the data** to see if there are missing values, repeated rows, or inconsistent entries.
3. **Review unusual values** and decide whether to keep, remove, or limit them.
4. **Choose how to clean the data** on the Data Cleaning page.
5. **Preview and confirm** your choices before applying them.
6. **Review the results** on the Before & After Comparison and Cleaning Report pages.
7. **Download the cleaned file** from the Export Dataset page.

If the result is not what you expected, you can return to Data Cleaning, change your choices, and apply them again.

## App Screenshots

### Dashboard
![Bebersih Dashboard](https://muhzharfan.wordpress.com/wp-content/uploads/2026/11/dashboard.jpg)

### Data Quality Analysis
![Data Quality Analysis](https://muhzharfan.wordpress.com/wp-content/uploads/2026/11/dataqualityanalysis.jpg)

### Outlier Detection
![Outlier Detection](https://muhzharfan.wordpress.com/wp-content/uploads/2026/11/outlier.jpg)

### Data Cleaning
![Data Cleaning]()

### Before & After Comparison
<!-- Add Before & After Comparison screenshot here -->

### Cleaning Report
<!-- Add Cleaning Report screenshot here -->

### Export Dataset
<!-- Add Export Dataset screenshot here -->

## Tools Used

- **Python** – used to build the app.
- **Streamlit** – used to create the web app.
- **Pandas and NumPy** – used to work with the data.
- **OpenPyXL** – used to read and work with Excel files.
- **Plotly** – used to create interactive charts.
- **Pytest** – used to test parts of the app.

## Run the App on Your Computer

### 1. Download the Project

```bash
git clone https://github.com/muhzarfan/bebersih-streamlit.git
```

### 2. Open the Project Folder

```bash
cd bebersih-streamlit
```

### 3. Install the Required Packages

```bash
pip install -r requirements.txt
```

Streamlit version 1.50 or newer is required.

### 4. Start the App

```bash
streamlit run app.py
```

Once the app starts, open the local address shown in your terminal in a web browser.

## Notes and Limitations

- **Unusual values are not always errors.** They may be valid records, so check them before removing or limiting them.
- **The unusual-value check has limits.** It may mark many values in columns where values are unevenly spread, such as prices or durations. It is also not useful for columns that only contain 0 and 1.
- **Value replacement uses exact matches.** It is available for text columns with up to 200 different values.
- **Older Excel files (`.xls`)** need the `xlrd` package, which is included in the project requirements.

## How Changes Are Applied

The original uploaded data is kept unchanged. Each time you apply your cleaning choices, the app starts again from the original data and applies your current choices to a separate copy.

This means that changes are not added on top of previous cleaning results. If you want to change something, update your choices and apply them again.

The app also follows a set order when applying the selected changes so that the steps work consistently.
