# Google Spreadsheet Exporter

Export a table in Patterns to a Google Spreadsheet. When triggered, this component will write the data to your Google Sheet.

Inputs:

- `table` - The table store in Patterns that is to be exported. The column names of this table is set as the first row of the exported spreadsheet.

Parameters:

- `connection` - A Google Sheets Connection
- `mode` - One of `replace`, `new_doc`, or `new_sheet`.
  - If mode is `replace`, the sheet with `sheet_name` will be replaced with newly exported data.
  - If mode is `new_doc`, data is exported to a new spreadsheet, the url of which will be printed to logs
  - If mode is `new_sheet`, data is exported to a new sheet within the specified spreadsheet.
- `sheet_title` - Name of a page or tab within a spreadsheet.
- `spreadsheet_url` - The URL of the Google sheet e.g. https://docs.google.com/spreadsheets/d/`spreadsheetId`/edit. Required unless `mode=new_doc`

Note: "Spreadsheet" refers to the overall file/document itself. "Sheet" refers to a particular tab/worksheet within a spreadsheet.
