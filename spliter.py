import os
import re
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter

# Paths
MASTER_FOLDER = r"C:\Users\mooki\Desktop\LSAT Prep Tool" #Update Path To Local
PDF_DIR = os.path.join(MASTER_FOLDER, "LSATPreptests")
OUTPUT_BASE = os.path.join(MASTER_FOLDER, "SplitSections")
os.makedirs(OUTPUT_BASE, exist_ok=True)

def clean_filename(name):
    """Sanitize file names to avoid issues with special characters."""
    return re.sub(r'[^\w\-_. ]', '_', name)

def extract_section_map(doc):
    """
    Looks through the first few pages for a section guide (e.g. SECTION I: Logical Reasoning),
    and builds a mapping of section number to section name.
    """
    for i in range(min(5, len(doc))):
        text = doc[i].get_text()
        if "SECTION" in text and any(term in text for term in ["Reading", "Logical", "Analytical"]):
            section_map = {}
            for line in text.split('\n'):
                match = re.search(r"(Reading Comprehension|Logical Reasoning|Analytical Reasoning).*SECTION\s+([IVX]+)", line)
                if match:
                    name = match.group(1).strip()
                    number = match.group(2).strip()
                    section_map[number] = name
            return section_map
    return {}

def find_section_starts(doc):
    """
    Scans through the document to find which pages mark the start of each section.
    Returns a dictionary mapping section number to page index.
    """
    starts = {}
    for i, page in enumerate(doc):
        match = re.search(r'SECTION\s+([IVX]+)', page.get_text())
        if match:
            starts[match.group(1)] = i
    return starts

def find_answer_key_range(doc):
    """
    Looks backwards through the document to find the start of the answer key section.
    Returns the start and end page index (exclusive).
    """
    for i in range(len(doc) - 1, 0, -1):
        text = doc[i].get_text().upper()
        if "ANSWER KEY" in text or "ANSWER" in text:
            return i, len(doc)
    return None, None

def split_preptest(pdf_path, pt_number):
    print(f"Processing PT {pt_number}...")
    output_dir = os.path.join(OUTPUT_BASE, f"PT_{pt_number}")
    os.makedirs(output_dir, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
        reader = PdfReader(pdf_path)

        section_map = extract_section_map(doc)
        starts = find_section_starts(doc)
        answer_start, answer_end = find_answer_key_range(doc)

        sorted_starts = sorted(starts.items(), key=lambda x: x[1])
        ranges = [
            (sec, start, sorted_starts[idx+1][1] if idx+1 < len(sorted_starts) else answer_start or len(doc))
            for idx, (sec, start) in enumerate(sorted_starts)
        ]

        lr_counter = 1
        for sec, start, end in ranges:
            label = section_map.get(sec, f"Unknown_{sec}")
            if "Logical Reasoning" in label:
                filename = f"PT_{pt_number}_Logical_Reasoning_{lr_counter}.pdf"
                lr_counter += 1
            else:
                filename = f"PT_{pt_number}_{clean_filename(label)}.pdf"

            writer = PdfWriter()
            for i in range(start, end):
                writer.add_page(reader.pages[i])
            with open(os.path.join(output_dir, filename), "wb") as f:
                writer.write(f)

        if answer_start is not None:
            writer = PdfWriter()
            for i in range(answer_start, answer_end):
                writer.add_page(reader.pages[i])
            with open(os.path.join(output_dir, f"PT_{pt_number}_Answer_Key.pdf"), "wb") as f:
                writer.write(f)
        else:
            print(f"Warning: No answer key found for PT {pt_number}.")

    except Exception as e:
        print(f"Error processing PT {pt_number}: {e}")

def batch_split_all():
    print("Starting batch split...")
    for filename in sorted(os.listdir(PDF_DIR)):
        if not filename.endswith(".pdf") or not filename.startswith("LSAT_PT_"):
            continue
        match = re.search(r'LSAT_PT_(\d+)', filename)
        if match:
            pt_number = int(match.group(1))
            pdf_path = os.path.join(PDF_DIR, filename)
            split_preptest(pdf_path, pt_number)

if __name__ == "__main__":
    batch_split_all()