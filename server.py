from fastapi import FastAPI, Body
import pandas as pd
import requests
import json

app = FastAPI()

@app.post("/vehicles")
async def upload_csv(csv_data: list = Body(...)):
    try:
        token = get_access_token()
        api_data = get_active_vehicles(token)

        all_data = csv_data + api_data
        df_all = pd.DataFrame(all_data)
        if "rnr" in df_all.columns:
            df_all = df_all.drop_duplicates(subset=["rnr"])
        # Filter out any resources that do not have a value set for hu field
        if "hu" in df_all.columns:
            df_all = df_all[df_all["hu"].notnull() & (df_all["hu"] != "")]
        result = df_all.to_dict(orient="records")
        
        # fillna'yı sadece string alanlar için yap, labelIds'ı koru
        for vehicle in result:
            for key, value in vehicle.items():
                if key != "labelIds":
                    try:
                        if value is None or (pd.isna(value) if not isinstance(value, (list, dict)) else False):
                            vehicle[key] = ""
                    except (ValueError, TypeError):
                        # pd.isna() array ile çalışmıyor, geç
                        pass

        for vehicle in result:
            color_codes = []
            label_ids = vehicle.get("labelIds")
            
            # labelIds işleme
            if label_ids is not None and str(label_ids).strip():
                if isinstance(label_ids, str):
                    try:
                        # Eğer virgülle ayrılmış sayılar varsa (örn: "134,133")
                        if "," in label_ids:
                            label_ids = [int(x.strip()) for x in label_ids.split(",")]
                        else:
                            label_ids = [int(label_ids)]
                    except ValueError:
                        label_ids = []
                elif isinstance(label_ids, (int, float)):
                    label_ids = [int(label_ids)]
                elif isinstance(label_ids, list):
                    label_ids = [int(x) for x in label_ids if x is not None]
                else:
                    label_ids = []
            else:
                label_ids = []
                
            # Her label_id için color_code al
            for label_id in label_ids:
                try:
                    color_code = get_label_color(label_id, token)
                    if color_code:
                        color_codes.append(color_code)
                except Exception:
                    pass
                    
            vehicle["colorCode"] = color_codes[0] if color_codes else None

        return {"vehicles": result}
    except Exception as e:
        print(f"Server hatası: {e}")
        import traceback
        traceback.print_exc()
        raise e

def get_access_token():
    url = "https://api.baubuddy.de/index.php/login"
    payload = {
        "username": "365",
        "password": "1"
    }
    headers = {
        "Authorization": "Basic QVBJX0V4cGxvcmVyOjEyMzQ1NmlzQUxhbWVQYXNz",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["oauth"]["access_token"]

def get_active_vehicles(token):
    url = "https://api.baubuddy.de/dev/index.php/v1/vehicles/select/active"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_label_color(label_id, token):
    url = f"https://api.baubuddy.de/dev/index.php/v1/labels/{label_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    # API bir array döndürüyor, ilk elemanı al
    if data and len(data) > 0:
        return data[0].get("colorCode")
    return None
