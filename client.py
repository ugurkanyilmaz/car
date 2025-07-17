import argparse
import pandas as pd
import requests
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.styles import PatternFill
from datetime import date, datetime, timedelta

def parse_args():
    parser = argparse.ArgumentParser(description="vehicle data processing.")

    parser.add_argument(
        "-k", "--keys",
        nargs="+",
        required=True,
        help= "keys to process, kurzname"
    )
    parser.add_argument(
        "-c", "--colored",
        type=bool,
        default=True,
        help="enable colored output"
    )
    return parser.parse_args()


def read_csv_data():
    df = pd.read_csv("vehicle_data.csv")
    csv_data = df.to_dict(orient="records")
    return csv_data


def fetch_data_from_api(csv_data):
    response = requests.post("http://localhost:8000/vehicles", json=csv_data)
    response.raise_for_status()
    return response.json()


def save_to_excel(data , keys, colored):
    # df = pd.DataFrame(data)
    df = pd.DataFrame(data)
    df = df.sort_values("gruppe")
    columns = ["rnr"] + keys
    df = df[columns]

    #filename
    filename = f"vehicles_{date.today().isoformat()}.xlsx"
    df.to_excel(filename, index=False)

    #coloring
    wb = load_workbook(filename)
    ws = wb.active

    #finding the header row
    col_indices = {col: idx+1 for idx, col in enumerate(df.columns)}

    for row_idx, row in enumerate(df.itertuples(index=False), start=2):
        # Satır renkleri (hu alanı için)
        if colored and "hu" in df.columns:
            hu_value = getattr(row, "hu", None)
            if hu_value:
                try:
                    hu_date = datetime.strptime(str(hu_value), "%Y-%m-%d")
                    diff = (date.today() - hu_date.date()).days
                    if diff <= 90:
                        fill = PatternFill(start_color="007500", end_color="007500", fill_type="solid")
                    elif diff <= 365:
                        fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
                    else:
                        fill = PatternFill(start_color="b30000", end_color="b30000", fill_type="solid")
                    for col in range(1, len(columns)+1):
                        ws.cell(row=row_idx, column=col).fill = fill
                except Exception:
                    pass

        # labelIds ve colorCode için hücre metni rengi
        if "labelIds" in keys and "colorCode" in df.columns:
            label_ids = getattr(row, "labelIds", None)
            color_code = getattr(row, "colorCode", None)
            if label_ids and color_code:
                cell = ws.cell(row=row_idx, column=col_indices["labelIds"])
                cell.font = Font(color=color_code)

    wb.save(filename)
    print(f"Excel dosyası oluşturuldu: {filename}")