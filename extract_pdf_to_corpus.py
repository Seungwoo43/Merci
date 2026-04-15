# -*- coding: utf-8 -*-
import os, re, json, hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

BASE = Path("/mnt/data/saju_pdf_tools")
PDF_SCAN_ROOTS = [Path("/mnt/data")]
CORPUS = BASE / "corpus"

HAS = {
    "pdfplumber": False, "pdfminer": False, "fitz": False, "pytesseract": False, "pdf2image": False, "PIL": False
}
try:
    import pdfplumber
    HAS["pdfplumber"] = True
except Exception:
    pass
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    HAS["pdfminer"] = True
except Exception:
    pass
try:
    import fitz
    HAS["fitz"] = True
except Exception:
    pass
try:
    import pytesseract
    HAS["pytesseract"] = True
except Exception:
    pass
try:
    from pdf2image import convert_from_path
    HAS["pdf2image"] = True
except Exception:
    pass
try:
    from PIL import Image
    HAS["PIL"] = True
except Exception:
    pass


from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class RAGRecord:
    id: str
    source_file: str
    page: int
    section: str
    heading_path: List[str]
    quote: str
    keywords: List[str]
    doctrines: List[str]
    tags: List[str]
    use_case: List[str]
    compat_signals: Dict[str, Any]
    final_strength_aliases: List[str]
    note: str

    def to_dict(self):
        return asdict(self)


DOCTRINE_RX = [
    ("적천수", re.compile(r"적천수|滴天髓|진소암|직해|상해|집요")),
    ("자평진전", re.compile(r"자평진전|子平真詮")),
    ("궁통보감", re.compile(r"궁통보감|용신제요")),
    ("삼명통회", re.compile(r"삼명통회|난강망")),
    ("연해자평", re.compile(r"연해자평")),
    ("사주첩경", re.compile(r"사주첩경|첩경")),
    ("신살론", re.compile(r"신살|흉살|백호대살|28")),
]

PATTERN_TAGS = {
    "재다신약": [r"財多身弱", r"재다신약"],
    "군겁쟁재": [r"軍劫爭財", r"군겁쟁재"],
    "관살혼잡": [r"官殺混雜", r"관살혼잡"],
    "재관쌍청": [r"財官雙淸", r"재관쌍청"],
    "식신제살": [r"食神制殺", r"식신제살"],
    "살인상생": [r"殺印相生", r"살인상생"],
    "관인상생": [r"官印相生", r"관인상생"],
    "상관견관": [r"傷官見官", r"상관견관"],
    "패인구조": [r"佩印|配印|敗印", r"패인"],
}

USE_CASE_HINTS = {
    "재물운":["재물","재성","재운","재복","사업","상업","매출","수익"],
    "연애":["연애","연정","이성","연분","도화","홍염","연애운"],
    "결혼":["혼인","배우자","결혼","혼담","혼례","배우자궁","결혼운"],
    "직업":["직업","승진","관직","명예","정관","직장","커리어"],
    "건강":["질병","건강","병","상해","혈","신체"],
    "사건예측":["시비","송사","구설","형충파해","사건","변고","소송"],
}

HEAD_PAT = re.compile(r"^(제?\s*\d+\s*[장편]|[一二三四五六七八九十]+章|CHAPTER|장)\s*[^\n]{0,60}", re.M)

def _hash_id(txt:str)->str:
    return hashlib.md5(txt.encode("utf-8","ignore")).hexdigest()[:12]

def _guess_doctrines(filename:str, page_text:str)->List[str]:
    s = f"{filename}\n{page_text[:1200]}"
    d = []
    for name, rx in DOCTRINE_RX:
        if rx.search(s):
            d.append(name)
    return d or ["(불명)"]

def _slice_quotes(text:str, min_len=200, max_len=800)->List[str]:
    text = re.sub(r"[ \t]+"," ", text)
    chunks = []
    for para in re.split(r"\n{2,}", text):
        para = para.strip()
        if len(para) < min_len: 
            continue
        if len(para) > max_len:
            chunks.append(para[:max_len])
        else:
            chunks.append(para)
        if len(chunks) >= 6:
            break
    return chunks

def _collect_keywords(text:str)->List[str]:
    kws = set()
    key_terms = ["십성","격국","용신","억부","조후","정관","편관","정재","편재","식신","상관",
                 "비견","겁재","인성","정인","편인","삼합","육합","충","형","파","해","원진",
                 "지장간","12운성","장생","제왕","건록","묘","절","합화","합거","암합","회국"]
    for k in key_terms:
        if k in text:
            kws.add(k)
    return list(kws)[:20]

def _detect_tags(text:str)->List[str]:
    tags = []
    for tag, rxs in PATTERN_TAGS.items():
        for rx in rxs:
            if re.search(rx, text):
                tags.append(tag)
                break
    return tags

def _detect_use_cases(text:str)->List[str]:
    hits = []
    for key, words in USE_CASE_HINTS.items():
        for w in words:
            if w in text:
                hits.append(key); break
    return hits or ["일반"]

def _detect_headings(text:str)->Tuple[str,List[str]]:
    heads = HEAD_PAT.findall(text) or []
    if heads:
        return heads[0][:80], heads[:3]
    first = "\n".join([l.strip() for l in text.splitlines()[:2]])
    return first[:80], [first[:80]]

def extract_with_pdfplumber(path:Path)->List[Tuple[int,str]]:
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            pages.append((i, t))
    return pages

def extract_with_pdfminer(path:Path)->List[Tuple[int,str]]:
    try:
        full = pdfminer_extract_text(str(path)) or ""
        splits = full.split("\f")
        return list(enumerate(splits))
    except Exception:
        return []

def extract_with_fitz(path:Path)->List[Tuple[int,str]]:
    pages = []
    doc = fitz.open(str(path))
    for i, pg in enumerate(doc):
        try:
            t = pg.get_text() or ""
        except Exception:
            t = ""
        pages.append((i, t))
    return pages

def extract_with_ocr(path:Path)->List[Tuple[int,str]]:
    pages = []
    if not (HAS["pytesseract"] and HAS["pdf2image"] and HAS["PIL"]):
        return pages
    try:
        imgs = convert_from_path(str(path), dpi=300)
        for i, im in enumerate(imgs):
            try:
                t = pytesseract.image_to_string(im, lang="kor+eng")
            except Exception:
                t = ""
            pages.append((i, t))
    except Exception:
        pass
    return pages

def extract_pages(path:Path)->List[Tuple[int,str]]:
    for name, fn in [("pdfplumber", extract_with_pdfplumber),
                     ("pdfminer", extract_with_pdfminer),
                     ("fitz", extract_with_fitz),
                     ("ocr", extract_with_ocr)]:
        if name != "ocr" and not HAS.get(name, False):
            continue
        pages = fn(path)
        total_chars = sum(len(t or "") for _,t in pages)
        if total_chars >= 500:
            return pages
    ocr = extract_with_ocr(path)
    return ocr

def find_pdfs()->List[Path]:
    pdfs = []
    for root in PDF_SCAN_ROOTS:
        for p in root.rglob("*.pdf"):
            if str(BASE) in str(p.parent):
                continue
            pdfs.append(p)
    uniq = []
    seen = set()
    for p in pdfs:
        key = p.resolve().as_posix()
        if key not in seen:
            uniq.append(p); seen.add(key)
    return sorted(uniq)

def build_record(source:Path, page:int, quote:str, section:str, heading_path:list, raw:str)->Dict[str,Any]:
    doctrines = _guess_doctrines(source.name, raw)
    keywords = _collect_keywords(raw)
    tags = _detect_tags(raw)
    uses = _detect_use_cases(raw)
    compat = {
        "has_hapchung": any(x in raw for x in ["삼합","육합","충","형","파","해","원진"]),
        "has_12un": any(x in raw for x in ["12운성","장생","제왕","건록","묘","절"]),
        "has_jijanggan": "지장간" in raw
    }
    final_alias = [t for t in tags]
    rid = _hash_id(f"{source.name}:{page}:{quote[:40]}")
    rec = RAGRecord(
        id=rid, source_file=source.name, page=page,
        section=section, heading_path=heading_path,
        quote=quote, keywords=keywords, doctrines=doctrines,
        tags=tags, use_case=uses, compat_signals=compat,
        final_strength_aliases=final_alias, note=""
    )
    return rec.to_dict()

def main():
    CORPUS.mkdir(parents=True, exist_ok=True)
    pdfs = find_pdfs()
    if not pdfs:
        print(f"[WARN] /mnt/data 에서 PDF를 찾지 못했습니다.")
        return
    print(f"[INFO] 대상 PDF: {len(pdfs)}개")
    total_records = 0
    for pdf in pdfs:
        print(f" - 처리: {pdf.name}")
        pages = extract_pages(pdf)
        out_path = CORPUS / (pdf.stem + ".jsonl")
        with open(out_path, "w", encoding="utf-8") as fw:
            for (pi, txt) in pages:
                if not txt or len(txt.strip()) < 80:
                    continue
                section, heading_path = _detect_headings(txt)
                for q in _slice_quotes(txt):
                    rec = build_record(pdf, pi, q, section, heading_path, txt)
                    fw.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    total_records += 1
        print(f"   → {out_path.name} 생성")
    print(f"[OK] 추출 완료. 총 레코드: {total_records}개")

if __name__ == "__main__":
    main()
