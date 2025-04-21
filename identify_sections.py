import os, time, pathlib, json
import pdfplumber
from tenacity import retry, wait_exponential, stop_after_attempt
from openai import OpenAI

MODEL     = "gpt-3.5-turbo-16k"
ROOT      = pathlib.Path(__file__).parent
PDF_DIR   = ROOT / "LSATPreptests"
OUT_FILE  = ROOT / "pt_section_map.json"
client    = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@retry(wait=wait_exponential(multiplier=1, max=10), stop=stop_after_attempt(3))
def call_llm(toc_text: str) -> list[str]:
    prompt = [
        {"role":"system","content":
         "You’re given the text of a PrepTest’s table of contents. "
         "Output a JSON array of length 4 indicating in order the 4 sections’ types. "
         "Use exactly these labels: \"LR1\",\"AR\",\"RC\",\"LR2\".  "
         "Example: [\"RC\",\"LR1\",\"LR2\",\"AR\"].  "
         "If it’s a 3‑section test (no AR), output only 3 labels."
        },
        {"role":"user","content":toc_text}
    ]
    resp = client.chat.completions.create(
      model=MODEL,
      temperature=0,
      messages=prompt
    )
    return json.loads(resp.choices[0].message.content)

def extract_toc(path):
    # page 3 is index 2
    with pdfplumber.open(path) as pdf:
        return pdf.pages[2].extract_text() or ""

def main():
    section_map = {}
    for pdf in sorted(PDF_DIR.glob("LSAT_PT_*.pdf")):
        pt = pdf.stem  # e.g. 'LSAT_PT_48'
        try:
            toc = extract_toc(pdf)
            seq = call_llm(toc)
            section_map[pt] = seq
            print(f"✔ {pt}: {seq}")
        except Exception as e:
            print(f"✗ {pt}: {e}")
            time.sleep(1)

    # write out your master map
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(section_map, f, indent=2)

if __name__=="__main__":
    main()
