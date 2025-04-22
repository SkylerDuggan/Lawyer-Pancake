# parse_sections.py
''' This actually works quite well. It runs the PDF through the 4.1 nano
model and spits out a decent json file.'''

import os, json, re, time, pathlib, sys, textwrap
from itertools import islice
import pdfplumber
from tenacity import retry, wait_exponential, stop_after_attempt
from openai import OpenAI, BadRequestError

#config
MODEL_FULL = "gpt-4o"
MODEL_MINI = "gpt-4o-mini"
USE_MODEL  = MODEL_MINI

ROOT       = pathlib.Path(__file__).resolve().parent
PDF_DIR    = ROOT / "SplitSections"
MAP_FILE   = ROOT / "pt_section_map.json"
OUT_DIR    = ROOT / "parsed_json_llm"
OUT_DIR.mkdir(exist_ok=True)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Load PT Section Map
with open(MAP_FILE) as f:
    pt_section_map = json.load(f)
# example: { "LSAT_PT_01": ["RC","AR","LR1","LR2"], ... }

# helpers
def pdf_pages(path):
    with pdfplumber.open(path) as pdf:
        return [p.extract_text() or "" for p in pdf.pages]

# regex for answer keys like "1 A" or "12. B"
ANS_RE = re.compile(r"(\d{1,2})[.\s]+([A-E])", re.I)

def answers_of(key_pdf):
    """Split the Answer_Key PDF into four blocks (Sec I–IV),
       then extract {qnum:letter} for each."""
    pages = pdf_pages(key_pdf)
    text = "\n".join(pages)
    # split on "Section I", "Section II", etc.
    parts = re.split(r"Section\s+([IVX]+)", text)
    # parts 0 = before first, then [roman, content, roman, content, ...]
    roman_to_idx = {"I":0, "II":1, "III":2, "IV":3}
    answers_by_sec = [ {} for _ in range(4) ]
    for i in range(1, len(parts), 2):
        roman = parts[i]
        body  = parts[i+1]
        idx   = roman_to_idx.get(roman.upper())
        if idx is None: continue
        for n,ltr in ANS_RE.findall(body):
            answers_by_sec[idx][int(n)] = ltr.upper()
    return answers_by_sec

SYS_PROMPT = textwrap.dedent("""\
    You are an expert LSAT parser.
    OUTPUT ONLY VALID JSON (no markdown, no fences).
    Schema:
    {
      "section_type": "LR"|"RC",
      "passage": str|null,
      "questions": [
        {
          "number": int,
          "stem": str,
          "choices": { "A": str, "B": str, "C": str, "D": str, "E": str }
        }
      ]
    }
""")

def chunk_pages(pages, max_chars=14000):
    """Yield page‐chunks <= max_chars."""
    buff, sz = [], 0
    for pg in pages:
        if sz + len(pg) > max_chars and buff:
            yield "\n".join(buff)
            buff, sz = [], 0
        buff.append(pg); sz += len(pg)
    if buff:
        yield "\n".join(buff)

@retry(wait=wait_exponential(multiplier=2), stop=stop_after_attempt(4))
def call_llm(chunk):
    msgs = [
        {"role":"system","content":SYS_PROMPT},
        {"role":"user","content":chunk}
    ]
    try:
        res = client.chat.completions.create(
            model=USE_MODEL,
            temperature=0,
            messages=msgs,
            response_format={"name":"json_object"}
        )
        txt = res.choices[0].message.content
    except BadRequestError as e:
        if "response_format" in str(e):
            # fallback to plain‑text & strip fences
            res = client.chat.completions.create(
                model=USE_MODEL,
                temperature=0,
                messages=msgs
            )
            txt = res.choices[0].message.content.strip("`\n ")
        else:
            raise
    return json.loads(txt)

def detect_section_type(fname):
    if "Reading_Comprehension" in fname:
        return "RC"
    if "Logical_Reasoning_1" in fname:
        return "LR1"
    if "Logical_Reasoning_2" in fname:
        return "LR2"
    # if you ever add AR:
    # if "Analytical_Reasoning" in fname: return "AR"
    return None

def process(pdf_path: pathlib.Path):
    # ─ Identify Preptest number from filename (index=2 → "01", "02", etc)
    pt_num = pdf_path.stem.split("_")[2]            
    prefix = f"LSAT_PT_{pt_num}"
    if prefix not in pt_section_map:
        print(f"! no map entry for {prefix}, skipping")
        return
    ordering = pt_section_map[prefix]   # e.g. ["RC","AR","LR1","LR2"]

    # ─ Load the corresponding Answer Key PDF
    key_pdf = PDF_DIR / f"{prefix}_Answer_Key.pdf"
    if not key_pdf.exists():
        print(f"! missing answer key for {pdf_path.name}")
        return

    # ─ Extract the four answer‐blocks ({1:A,2:B,…}) for Sections I–IV
    answer_blocks = answers_of(key_pdf)

    # ─ Parse the split PDF via the LLM (same as before)
    pages = pdf_pages(pdf_path)
    merged = {"section_type":None, "passage":None, "questions":[]}
    for chunk in chunk_pages(pages):
        part = call_llm(chunk)
        if merged["section_type"] is None:
            merged["section_type"] = part["section_type"]
            merged["passage"]     = part["passage"]
        merged["questions"].extend(part["questions"])

    # ─ Figure out which “Section I–IV” this is by matching
    #   its parsed section_type (e.g. "RC", "LR1", or "LR2")
    sec_type = merged["section_type"]
    try:
        sec_idx = ordering.index(sec_type)
    except ValueError:
        print(f"! unexpected section_type {sec_type} in {pdf_path.name}")
        return

    # ─ Merge in the answer letters
    answers_for_this_section = answer_blocks[sec_idx]
    for q in merged["questions"]:
        q["answer"] = answers_for_this_section.get(q["number"])

    # ─ Write out JSON
    outp = OUT_DIR / (pdf_path.stem + ".json")
    outp.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print("✓", pdf_path.name, "→", outp.name)

def main():
    if not PDF_DIR.exists():
        sys.exit(f"ERR: {PDF_DIR} not found")

    # only LR1, LR2, RC splits
    pdfs = sorted(PDF_DIR.glob("LSAT_PT_*_Logical_Reasoning_1.pdf")) + \
           sorted(PDF_DIR.glob("LSAT_PT_*_Logical_Reasoning_2.pdf")) + \
           sorted(PDF_DIR.glob("LSAT_PT_*_Reading_Comprehension.pdf"))

    for pdf in pdfs:
        try:
            process(pdf)
        except Exception as e:
            print("! failed", pdf.name, e)
            time.sleep(2)

if __name__ == "__main__":
    main()