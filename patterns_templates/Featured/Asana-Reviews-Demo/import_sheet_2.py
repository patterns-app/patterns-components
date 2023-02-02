import requests
from patterns import Connection, Parameter, Table
from patterns_components.helpers.api import handle_rate_limiting


table = Table("spreadsheet", "w")
connection = Parameter(
    "connection",
    type=Connection("google-sheets"),
    description="A Google Sheets connection",
)
spreadsheet = Parameter(
    "spreadsheet_url",
    type=str,
    description="Can be the url or id of the Google spreadsheet, e.g. https://docs.google.com/spreadsheets...",
)
sheet_title = Parameter(
    "sheet_title",
    type=str,
    description="Title of the sheet (tab) within the spreadsheet",
)
header_row_index = Parameter(
    "header_row",
    type=int,
    default=1,
    description="The header row number. Set to 0 if no header (field names will default to col_a, col_b, etc)",
)

ss_id = spreadsheet.split("s/d/")[1].split("/")[0]


def gsheets_request(path: str, params: dict = None) -> dict:
    url = f"https://sheets.googleapis.com/v4/spreadsheets" + path
    auth = {"Authorization": "Bearer " + connection.get("access_token")}
    resp = requests.get(url, params=params, headers=auth)
    resp = handle_rate_limiting(resp)
    resp_json = resp.json()
    if not resp.ok:
        print(resp_json)
        resp.raise_for_status()
    return resp_json


def conform_header(header: list[str]) -> list[str]:
    """Sheet can have blank or duplicate header values, must conform to valid unique field names"""
    conformed = []
    for i, h in enumerate(header):
        if not h:
            h = "col_" + str(i + 1)
        h = str(h)
        if h in conformed:
            j = 1
            h = h + str(j)
            while h in conformed:
                j += 1
                h = h[:-1] + str(j)
        conformed.append(h)
    return conformed


def import_sheet(spreadsheet_id: str, sheet_title: str, header_row_index: int = 1):
    path = f"/{spreadsheet_id}/values:batchGet"
    params = {"ranges": sheet_title, "valueRenderOption": "UNFORMATTED_VALUE"}
    resp_json = gsheets_request(path, params)

    values = resp_json["valueRanges"][0]["values"]

    records = []

    if not values:
        return records

    if header_row_index:
        if len(values) < header_row_index:
            return []
        header = values[header_row_index - 1]
    else:
        # If no header rows, just use generic index
        header = [f"col_{i + 1}" for i in range(len(values[0]))]
        header_row_index = 0

    # Ensure strings
    header = conform_header(header)

    # for each row, create a json {header1: cell1, header2: cell2, ...}
    for row_i in range(header_row_index, len(values)):
        record = {}
        for col_i in range(0, len(header)):
            if col_i >= len(values[row_i]):
                break
            record[header[col_i]] = values[row_i][col_i] or None
        records.append(record)

    return records


table.replace(import_sheet(ss_id, sheet_title, header_row_index))
