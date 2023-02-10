from datetime import datetime, timezone
from typing import Any, Tuple

import requests
from patterns import Connection, Parameter, Table
from patterns_components.helpers.api import handle_rate_limiting


table = Table("table")
connection = Parameter(
    "connection",
    type=Connection("google-sheets"),
    description="A Google Sheets connection",
)
spreadsheet = Parameter(
    "spreadsheet_url",
    type=str,
    description="URL of the Google spreadsheet, e.g. https://docs.google.com/spreadsheets.../. Can be omitted if mode='new_doc'",
    default=None,
)
sheet_title = Parameter(
    "sheet_title",
    type=str,
    description="Title of the sheet (tab) within the spreadsheet. Optional, must be set if mode='replace'",
    default=None,
)
mode = Parameter(
    "mode",
    type=str,
    description="One of 'replace', 'new_doc', or 'new_sheet'",
    default="new_doc",
)

ss_id = None
if spreadsheet:
    ss_id = spreadsheet.split("s/d/")[1].split("/")[0]


def gsheets_request(path: str, json_data: dict = None) -> dict:
    url = f"https://sheets.googleapis.com/v4/spreadsheets" + path
    auth = {"Authorization": "Bearer " + connection.get("access_token")}
    resp = requests.post(url, json=json_data, headers=auth)
    resp = handle_rate_limiting(resp)
    if not resp.ok:
        if 'application/json' in resp.headers.get('Content-Type', ''):
            print(resp.json())
        else:
            print(resp.content)
        resp.raise_for_status()
    return resp.json()


def default_title() -> str:
    now = datetime.now(tz=timezone.utc).strftime("%F %T")
    return f"Untitled {now}"


def create_new_doc(title: str, sheet_title: str = None) -> Tuple[str, str]:
    sheet_title = sheet_title or title
    data = {
        "properties": {"title": title},
        "sheets": {"properties": {"title": sheet_title}},
    }
    resp_json = gsheets_request("", json_data=data)
    return resp_json["spreadsheetId"], sheet_title


def create_new_sheet(spreadsheet_id: str, sheet_title: str = None) -> str:
    path = f"/{spreadsheet_id}:batchUpdate"
    
    if sheet_title is None:
        sheet_title = default_title()
    data = {
        "requests": {
            "addSheet": {"properties": {"title": sheet_title, "index": 1}}
        },
    }

    gsheets_request(path, json_data=data)
    return sheet_title


def clear_sheet(spreadsheet_id: str, sheet_title: str):
    path = f"/{spreadsheet_id}/values/{sheet_title}:clear"
    return gsheets_request(path)


def records_to_cells(records: list[dict]) -> list[list]:
    record = records[0]
    headers = list(record.keys())
    rows = []
    for record in records:
        rows.append([record.get(header) for header in headers])
    return [headers] + rows 


def export_data(records: list[dict], mode: str = "replace", spreadsheet_id: str = None, sheet_title: str = None)->str:
    match mode:
        case "replace":
            if not spreadsheet_id or not sheet_title:
                raise Exception("Invalid: must specify both spreadsheet and sheet_title if mode='replace'.")
            clear_sheet(spreadsheet_id, sheet_title)
        case "new_doc":
            spreadsheet_id, sheet_title = create_new_doc(sheet_title or default_title())
            print(f"New spreadsheet '{sheet_title}' created")
        case "new_sheet":
            if not spreadsheet_id:
                raise Exception("Invalid: must specify both spreadsheet if mode='new_sheet'.")
            sheet_title = create_new_sheet(spreadsheet_id, sheet_title)
            print(f"New sheet '{sheet_title}' created")
        case _:
            raise NotImplementedError(mode)

    path = f"/{spreadsheet_id}/values:batchUpdate"
    cells = records_to_cells(records)
    data = {
        "data": [{"range": sheet_title, "values": cells}],
        "valueInputOption": "RAW",
    }
    gsheets_request(path, json_data=data)
    return spreadsheet_id


records = table.read()
ss_id = export_data(records, mode, ss_id, sheet_title)

print(f"{len(records)} records written to https://docs.google.com/spreadsheets/d/{ss_id}")

