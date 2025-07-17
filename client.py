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