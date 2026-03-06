import json
import sys
import time
import threading
from docling.document_converter import DocumentConverter

# -------------------------------
# Configuration
# -------------------------------
PDF_PATH = r"C:\Users\sudarshan\OneDrive\Desktop\aiml_for_infosys\Data-Research papers\research paper_15.pdf"
OUTPUT_JSON = "output15.json"
HEARTBEAT_INTERVAL = 2  # seconds

# -------------------------------
# Heartbeat Thread
# -------------------------------
def heartbeat(stop_event):
    """
    Prints a message periodically to indicate the process is running.
    """
    
    while not stop_event.is_set():
        print("⏳ PDF conversion in progress...")
        time.sleep(HEARTBEAT_INTERVAL)

# -------------------------------
# PDF to JSON Conversion
# -------------------------------
def convert_pdf_to_json(pdf_path: str, output_path: str) -> None:
    """
    Converts a PDF document to structured JSON using Docling with live heartbeat messages.
    """
    stop_event = threading.Event()
    hb_thread = threading.Thread(target=heartbeat, args=(stop_event,))
    hb_thread.start()

    try:
        print("Initializing DocumentConverter...")
        converter = DocumentConverter()

        print("Converting PDF to structured document...")
        result = converter.convert(pdf_path)

        print("Exporting document to JSON...")
        document_dict = result.document.export_to_dict()

        print("Saving JSON output...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(document_dict, f, indent=2, ensure_ascii=False)

    finally:
        # Stop heartbeat thread
        stop_event.set()
        hb_thread.join()

    print(f"✅ Conversion completed successfully!\nJSON saved to: {output_path}")


# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    convert_pdf_to_json(PDF_PATH, OUTPUT_JSON)
