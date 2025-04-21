# parse_sections.py
''' This actually works quite well. It runs the PDF through the 4.1 nano
model and spits out a decent json file. However, I'm realizing now that 
the answer keys just say "Section I" not "Logicial Reasoning" so the AI
cannot properly retrive the answer keys. I need to fix this somehow. '''


import os, json, re, time, pathlib, sys, textwrap
from itertools import islice
import pdfplumber
from tenacity import retry, wait_exponential, stop_after_attempt
from openai import OpenAI, BadRequestError

# ── CONFIG ──────────────────────────────────────────────────────────────
MODEL_FULL = "gpt-4o"        # 128k, solid JSON mode
MODEL_MINI = "gpt-4.1-nano"   # cheap, may or may not have JSON mode yet
USE_MODEL  = MODEL_MINI      # switch here

ROOT      = pathlib.Path(__file__).resolve().parent
PDF_DIR   = ROOT / "SplitSections"
OUT_DIR   = ROOT / "parsed_json_llm"
OUT_DIR.mkdir(exist_ok=True)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ── HELPERS ─────────────────────────────────────────────────────────────
def pdf_text(pdf_path: pathlib.Path) -> list[str]:
    """Return a list of page‑texts from the PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return [pg.extract_text() or "" for pg in pdf.pages]

ANS_RE = re.compile(r"(\d{1,2})[.\s]+([A-E])", re.I)

def answers_of(key_pdf: pathlib.Path) -> dict[int, str]:
    text = "\n".join(pdf_text(key_pdf))
    return {int(n): ltr.upper() for n, ltr in ANS_RE.findall(text)}

SYS_PROMPT = textwrap.dedent("""\
    You are an expert LSAT parser.
    Output ONLY valid JSON, no markdown.
    Schema:
    {
      "section_type": "LR" | "RC",
      "passage": str | null,
      "questions": [
        {
          "number": int,
          "stem": str,
          "choices": { "A": str, "B": str, "C": str, "D": str, "E": str }
        }
      ]
    }
""")

def chunk_pages(pages: list[str], limit_chars=14000):
    """Yield page‑chunks < limit_chars so we stay inside context."""
    buff = []
    size = 0
    for pg in pages:
        if size + len(pg) > limit_chars and buff:
            yield "\n".join(buff)
            buff, size = [], 0
        buff.append(pg)
        size += len(pg)
    if buff:
        yield "\n".join(buff)

# ── LLM CALL ────────────────────────────────────────────────────────────
@retry(wait=wait_exponential(multiplier=2), stop=stop_after_attempt(4))
def call_llm(chunk: str) -> dict:
    messages = [
        {"role": "system", "content": SYS_PROMPT},
        {"role": "user",   "content": chunk}
    ]
    try:
        resp = client.chat.completions.create(
            model          = USE_MODEL,
            temperature    = 0,
            messages       = messages,
            response_format= {"name": "json_object"}
        )
        content = resp.choices[0].message.content
    except BadRequestError as e:
        # mini model in some orgs rejects response_format
        if "response_format" in str(e):
            resp = client.chat.completions.create(
                model       = USE_MODEL,
                temperature = 0,
                messages    = messages
            )
            content = resp.choices[0].message.content
            content = content.strip("` \n")           # remove fences if any
        else:
            raise
    return json.loads(content)

# ── PIPELINE ────────────────────────────────────────────────────────────
def process(pdf_path: pathlib.Path):
    pt = int(pdf_path.name.split("_")[1])            # PT_XX_...
    key_pdf = PDF_DIR / f"PT_{pt:02d}_Answer_Key.pdf"
    if not key_pdf.exists():
        print(f"! answer key missing for {pdf_path.name}")
        return
    answers = answers_of(key_pdf)

    # concatenate LLM results from page‑chunks
    merged = {"section_type": None, "passage": None, "questions": []}
    for chunk in chunk_pages(pdf_text(pdf_path)):
        piece = call_llm(chunk)
        if merged["section_type"] is None:
            merged["section_type"] = piece["section_type"]
            merged["passage"]      = piece["passage"]
        merged["questions"].extend(piece["questions"])

    # add answer letters
    for q in merged["questions"]:
        q["answer"] = answers.get(q["number"])

    out_path = OUT_DIR / (pdf_path.stem + ".json")
    out_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False))
    print("✓", pdf_path.name, "→", out_path.name)

def main():
    if not PDF_DIR.exists():
        sys.exit(f"ERR: {PDF_DIR} missing")

    pdfs = sorted(PDF_DIR.glob("PT_*_Logical_Reasoning_*.pdf")) \
         + sorted(PDF_DIR.glob("PT_*_Reading_Comprehension.pdf"))

    for pdf in pdfs:
        try:
            process(pdf)
        except Exception as exc:
            print("! failed", pdf.name, exc)
            time.sleep(2)

if __name__ == "__main__":
    main()
