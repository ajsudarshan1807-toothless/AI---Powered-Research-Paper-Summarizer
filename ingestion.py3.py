import pandas as pd
import json
import threading
import time

# -------------------------------
# Configuration
# -------------------------------
XLSX_PATH = r"C:\Users\sudarshan\OneDrive\Desktop\aiml_for_infosys\Data- excel\Citation_Links.xlsx"
OUTPUT_JSON = "output_citation.json"
HEARTBEAT_INTERVAL = 2  # seconds

# -------------------------------
# Heartbeat Thread
# -------------------------------
def heartbeat(stop_event):
    """Prints a message periodically to indicate the process is running."""
    while not stop_event.is_set():
        print("⏳ Excel to JSON conversion in progress...")
        time.sleep(HEARTBEAT_INTERVAL)

# -------------------------------
# Excel to JSON Conversion
# -------------------------------
def convert_xlsx_to_json(xlsx_path: str, output_path: str) -> None:
    """
    Converts an XLSX file to JSON format.
    Each row becomes a JSON object with column names as keys.
    """
    stop_event = threading.Event()
    hb_thread = threading.Thread(target=heartbeat, args=(stop_event,))
    hb_thread.start()

    try:
        print("Loading Excel file...")
        # Read all sheets into a dict of DataFrames
        xls = pd.ExcelFile(xlsx_path)
        all_sheets_data = {}

        for sheet_name in xls.sheet_names:
            print(f"Processing sheet: {sheet_name} ...")
            df = pd.read_excel(xls, sheet_name=sheet_name)
            # Convert DataFrame to list of dicts
            sheet_data = df.fillna("").to_dict(orient="records")
            all_sheets_data[sheet_name] = sheet_data

        print("Saving JSON output...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_sheets_data, f, indent=2, ensure_ascii=False)

    finally:
        stop_event.set()
        hb_thread.join()

    print(f"✅ Excel conversion completed successfully!\nJSON saved to: {output_path}")


# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    convert_xlsx_to_json(XLSX_PATH, OUTPUT_JSON)
