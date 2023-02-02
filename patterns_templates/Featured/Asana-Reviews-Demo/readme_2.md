# Google Spreadsheet Importer

Sync a Google spreadsheet with a table in Patterns. When triggered, this component will replace 
data in it's connected table with the current data in your Google Sheet. Pass an optional 
`header_row` parameter to use as column names, set to first row by default.

Required parameters:

- `connection` - A Connection of type 'Google Sheets', which is configurable from the home screen. 
- `spreadsheet` - A spreadsheet URL or id: https://docs.google.com/spreadsheets/d/`spreadsheetId`/edit
- `sheet_title` - Title of the sheet (tab) within the spreadsheet

Optional parameters:

- `header_row` - default is row 1. If not row 1, indicate the header row number

Note: "Spreadsheet" refers to the overall file/document itself. "Sheet" refers to a particular 
tab/worksheet within a spreadsheet.
