import json
import time
import threading
from docx import Document

# -------------------------------
# Configuration
# -------------------------------

#for i in range(3,16):
 #   DOCX_PATH = r"C:\Users\sudarshan\OneDrive\Desktop\aiml_for_infosys\Data - abstract\research paper_{}.docx".format(i)
  #  OUTPUT_JSON = "output_docx_words{}.json".format(i)
   # HEARTBEAT_INTERVAL = 2  # seconds
   # """

# -------------------------------
# Heartbeat Thread
# -------------------------------
def heartbeat(stop_event):
    b=1
    """Prints a message periodically to indicate the process is running."""
    while not stop_event.is_set():
        print("⏳ DOCX conversion in progress...",b)
        time.sleep(HEARTBEAT_INTERVAL)
        b+=1

# -------------------------------
# DOCX to Word-level JSON Conversion
# -------------------------------
def convert_docx_to_word_json(docx_path: str, output_path: str) -> None:
    """
    Converts a DOCX document to word-level JSON.
    """
    stop_event = threading.Event()
    hb_thread = threading.Thread(target=heartbeat, args=(stop_event,))
    hb_thread.start()

    try:
        print("Loading DOCX document...")
        doc = Document(docx_path)

        print("Extracting words from the document...")
        words_data = []
        for para_index, paragraph in enumerate(doc.paragraphs, start=1):
            for run_index, run in enumerate(paragraph.runs, start=1):
                # Split run text into words
                for word_index, word in enumerate(run.text.split(), start=1):
                    words_data.append({
                        "text": word,
                        "paragraph": para_index,
                        "run": run_index,
                        "word_index": word_index,
                        "bold": run.bold,
                        "italic": run.italic,
                        "underline": run.underline,
                        "font_name": run.font.name,
                        "font_size": run.font.size.pt if run.font.size else None
                    })

        print("Saving word-level JSON output...")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(words_data, f, indent=2, ensure_ascii=False)

    finally:
        stop_event.set()
        hb_thread.join()

    print(f"✅ DOCX conversion completed!\nJSON saved to: {output_path}")


# -------------------------------
# Run
# -------------------------------
for i in range(3,16):
    DOCX_PATH = r"C:\Users\sudarshan\OneDrive\Desktop\aiml_for_infosys\Data - abstract\research paper_{}.docx".format(i)
    OUTPUT_JSON = "output_docx_words{}.json".format(i)
    HEARTBEAT_INTERVAL = 2  # seconds
    if __name__ == "__main__":
        convert_docx_to_word_json(DOCX_PATH, OUTPUT_JSON)
