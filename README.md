# Bebersih – Data Cleaning App

Bebersih is a streamlit website app for checking and cleaning data before it is used for analysis.

Upload a CSV or Excel file, review the issues found in the data, choose how to handle them, and download the cleaned file.

This project was created for my data analyst portfolio.

## Main Features

### 1. Upload and Preview Data

Upload a file in one of these formats:
- CSV
- Excel (`.xlsx` or `.xls`)

After uploading, you can view basic file information and preview the data. If an Excel file has more than one sheet, you can choose which sheet to use.

### 2. Check Data Quality

The app checks for common data issues, including:

- **Missing values:** cells that have no value.
- **Duplicate rows:** records that appear more than once.
- **Incorrect data formats:** for example, numbers, dates, or times that are read as text.
- **Inconsistent text:** extra spaces or different ways of writing the same category.
- **Different date formats:** dates written in more than one format.

You can also view simple summaries of number and category columns, along with an overall data quality score.

### 3. Find Unusual Values

Some values may be very different from most of the other values in a column. For example, most orders may be worth a few hundred thousand, while one order is worth several million.

The app highlights these values in charts and in a list. For each column, you can choose to:

- **Keep:** leave the values as they are.
- **Remove:** remove rows that contain the selected values.
- **Limit:** reduce unusually high or low values to the nearest edge of the usual range, which the app calculates for you.

Your choices here are saved as a plan. Nothing is changed until you apply the cleaning on the Data Cleaning page. A preview shows how many rows and unusual values would remain.

A value that looks unusual is not always wrong. Review it before deciding what to do.

### 4. Clean the Data

Choose how to handle each issue based on your needs.

| Issue | Available actions |
|---|---|
| Missing values | Remove rows or fill empty cells using the average, middle value, most common value, or a value you enter. This is chosen separately for each column, and the average and middle value only work for number columns |
| Duplicate rows | Remove repeated rows using all columns or selected columns, and choose whether to keep the first or the last one |
| Text | Remove extra spaces and make text use a consistent letter style. The letter style can be different for each column, for example capitalised words for city names and capital letters for abbreviations |
| Data format | Change a column to whole numbers, decimal numbers, text, true/false, category, date, date and time, time, or general |
| Dates and times | Done in the same step as data format. Choose whether dates are read day first (05/02/2024 as 5 February) and how dates and times are written, such as 31/01/2024 or 14:30 |
| Column names | Rename columns |
| Inconsistent values | Correct spelling mistakes or use the same name for matching categories |
| Unusual values | Keep, remove, or limit selected values |
| Unneeded columns | Remove columns you do not need, for example columns that are mostly empty. The app can suggest columns with many empty cells |

You can preview the planned changes before applying them. If your choices may remove rows or columns, the app shows a warning and asks you to confirm.

Your choices are remembered when you move to another page and come back.

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

The same file name is used for all three files. The report file adds `_report` to the end of the name.

## How to Use the App

1. **Upload a file** from the Dashboard.
2. **Check the data** to see if there are missing values, repeated rows, or inconsistent entries.
3. **Review unusual values** and decide whether to keep, remove, or limit them.
4. **Choose how to clean the data** on the Data Cleaning page.
5. **Preview and confirm** your choices before applying them.
6. **Review the results** on the Before & After Comparison and Cleaning Report pages.
7. **Download the cleaned file** from the Export Dataset page.

If the result is not what you expected, you can return to Data Cleaning, change your choices, and apply them again. Your earlier choices are still there, so you only need to change what you want to adjust.

## App Screenshots

### Dashboard
![Bebersih Dashboard](https://muhzharfan.wordpress.com/wp-content/uploads/2026/11/dashboard.jpg)

### Data Quality Analysis
![Data Quality Analysis](https://muhzharfan.wordpress.com/wp-content/uploads/2026/11/dataqualityanalysis.jpg)

### Outlier Detection
![Outlier Detection](https://muhzharfan.wordpress.com/wp-content/uploads/2026/11/outlier.jpg)

### Data Cleaning
<!-- Add Data Cleaning screenshot here -->

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

### 5. Run the Tests (Optional)

```bash
python -m pytest
```

## Notes and Limitations

- **Unusual values are not always errors.** They may be valid records, so check them before removing or limiting them.
- **The unusual-value check has limits.** It may mark many values in columns where values are unevenly spread, such as prices or durations. It is also not useful for columns that only contain 0 and 1.
- **Value replacement uses exact matches.** It is available for text columns with up to 200 different values. Corrections use the values as they appear in the original file, so they are applied before text cleaning.
- **Dates and times written as text.** If you choose a text format for dates or times, that column becomes text and can no longer be used for date calculations. Keep the date or time type if you still need to calculate with it.
- **Times without dates.** If a column only contains times, the app does not allow changing it to date and time, because today's date would be added by mistake. Use the time type instead.
- **Removed columns.** Choices made for a removed column are ignored, and repeated rows are checked using the columns that remain.
- **Older Excel files (`.xls`)** need the `xlrd` package, which is included in the project requirements.

## How Changes Are Applied

The original uploaded data is kept unchanged. Each time you apply your cleaning choices, the app starts again from the original data and applies your current choices to a separate copy.

This means that changes are not added on top of previous cleaning results. If you want to change something, update your choices and apply them again.

The app also follows a set order when applying the selected changes so that the steps work consistently:

1. Remove the columns you chose to drop.
2. Replace values (spelling and naming corrections).
3. Clean the text.
4. Change data formats, including dates and times.
5. Remove duplicate rows.
6. Handle missing values.
7. Keep, remove, or limit unusual values.
8. Rename columns.

This order matters. Renaming is done last so that every other choice can still use the original column names. Duplicates are removed before empty cells are filled, so that filling cells cannot create false duplicates.