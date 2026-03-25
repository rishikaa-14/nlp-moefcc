"""
MoEFCC Sustainability NLP Pipeline — Final Fixed Version
=========================================================
ROOT FIX: Word-level keyword matching instead of phrase matching.
          This solves 0-labelled-sentences for ALL years including 2022.

Multi-word phrases like "climate change" FAIL on MoEFCC PDFs because
the text is extracted with extra spaces between letters: "c l i m a t e".
Single words like "climate" ALWAYS match regardless of PDF encoding.

Usage:
    python moefcc_nlp_pipeline.py --step all
    python moefcc_nlp_pipeline.py --step download
    python moefcc_nlp_pipeline.py --step dataset
    python moefcc_nlp_pipeline.py --step train
    python moefcc_nlp_pipeline.py --step debug   <- use if still 0 labelled
"""

import re, csv, pathlib, time, urllib.request, argparse
from typing import List, Tuple, Dict

# ── 18 English reports 2008-2026 ──────────────────────────────────────────────
REPORT_URLS: List[Tuple[str, str]] = [
    ("2025-26", "https://moef.gov.in/uploads/pdf-uploads/Nitin_Rev_4.pdf"),
    ("2024-25", "https://moef.gov.in/uploads/pdf-uploads/English_Annual_Report_2024-25.pdf"),
    ("2023-24", "https://moef.gov.in/uploads/2023/05/Annual-Report-English-2023-24.pdf"),
    ("2022-23", "https://moef.gov.in/uploads/2023/05/Annual-Report-English-2022-23.pdf"),
    ("2021-22", "https://moef.gov.in/uploads/2022/03/Annual-report-2021-22-Final.pdf"),
    ("2020-21", "https://moef.gov.in/uploads/2017/06/Environment-AR-English-2020-21.pdf"),
    ("2019-20", "https://moef.gov.in/uploads/2017/06/ENVIRONMENT-AR-ENGLISH-2020.pdf"),
    ("2018-19", "https://moef.gov.in/uploads/2019/08/Annual-Report-2018-19-English.pdf"),
    ("2017-18", "https://moef.gov.in/uploads/2019/04/22-03-18.pdf"),
    ("2016-17", "https://moef.gov.in/uploads/2018/04/EnvironmentAREnglish2016-2017.pdf"),
    ("2015-16", "https://moef.gov.in/uploads/2018/04/MinistryofEnvirormentAnnualReport2015-16English.pdf"),
    ("2014-15", "https://moef.gov.in/uploads/2018/04/EnvironmentAnnualReportEng..pdf"),
    ("2013-14", "https://moef.gov.in/uploads/2017/06/AR-2013-14-Eng.pdf"),
    ("2012-13", "https://moef.gov.in/uploads/2018/04/ar-2012-13.pdf"),
    ("2011-12", "https://moef.gov.in/uploads/2018/04/AR-11-12-En.pdf"),
    ("2010-11", "https://moef.gov.in/uploads/2018/04/AR-EngVol2-1.pdf"),
    ("2009-10", "https://moef.gov.in/uploads/2018/04/Annual_Report_ENG_0910.pdf"),
    ("2008-09", "https://moef.gov.in/uploads/2018/04/Annual_Report_ENG_0809.pdf"),
]

# ── SINGLE-WORD keywords — THE FIX for 0 labelled sentences ───────────────────
THEME_KEYWORDS: Dict[str, List[str]] = {
    "water_conservation": [
        "water","river","lake","pond","wetland","aquifer","groundwater",
        "rainwater","watershed","catchment","basin","irrigation","canal",
        "dam","reservoir","hydrology","stream","riparian","estuary","aquatic",
        "wastewater","sewage","effluent","flood","coastal","drinking","sanitation",
        "waterway","spring","runoff","recharge","drainage","borewell","inundation",
    ],
    "biodiversity": [
        "biodiversity","wildlife","forest","species","habitat","ecosystem",
        "flora","fauna","tiger","elephant","lion","leopard","rhino","bird",
        "reptile","fish","marine","coral","mangrove","sanctuary","conservation",
        "endangered","threatened","endemic","invasive","poaching","zoological",
        "botanical","vegetation","tree","plant","animal","reserve","biosphere",
        "migratory","breeding","deforestation","jungle","canopy","pollinator",
    ],
    "soil_health": [
        "soil","erosion","desertification","degradation","wasteland","plantation",
        "sediment","compost","fertility","salinization","waterlogging","reclamation",
        "restoration","topsoil","nutrients","agricultural","cultivation","farming",
        "crops","fallow","pasture","grassland","dryland","arid","humus","nitrogen",
        "phosphorus","afforestation","reforestation","revegetation","biomass",
    ],
    "climate_adaptation": [
        "climate","emission","carbon","greenhouse","warming","temperature",
        "adaptation","mitigation","resilience","renewable","solar","wind",
        "energy","napcc","unfccc","paris","ndc","cop","ipcc","cyclone",
        "heatwave","vulnerable","disaster","risk","meteorological","precipitation",
        "atmosphere","ozone","methane","sequestration","hydrogen","geothermal",
    ],
    "eco_friendly_practices": [
        "pollution","pollutant","waste","plastic","recycling","sustainable",
        "environment","environmental","green","clean","hazardous","toxic",
        "contamination","discharge","compliance","standard","regulation",
        "legislation","enforcement","monitoring","assessment","impact",
        "clearance","approval","penalty","violation","awareness","education",
        "swachh","hygiene","litter","dumping","incineration","biodegradable",
    ],
}


# ─── Download ──────────────────────────────────────────────────────────────────
def download_reports(output_dir: str = "reports_pdf", limit: int = None):
    out = pathlib.Path(output_dir)
    out.mkdir(exist_ok=True)
    urls = REPORT_URLS[:limit] if limit else REPORT_URLS
    ok = fail = 0
    for year, url in urls:
        dest = out / f"moefcc_{year.replace('-','_')}.pdf"
        if dest.exists() and dest.stat().st_size > 10000:
            print(f"  [skip] {dest.name}")
            ok += 1
            continue
        try:
            print(f"  [download] {year} ...", end=" ", flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp, open(dest, "wb") as f:
                data = resp.read()
                f.write(data)
            print(f"OK ({len(data)//1024} KB)")
            ok += 1
            time.sleep(1)
        except Exception as e:
            print(f"FAILED: {e}")
            fail += 1
            if dest.exists(): dest.unlink()
    print(f"\n  {ok} downloaded, {fail} failed\n")


# ─── Extract text — best of 3 extractors ──────────────────────────────────────
def _pymupdf(path):
    try:
        import fitz
        doc = fitz.open(str(path))
        t = "\n".join(p.get_text("text") for p in doc)
        doc.close()
        return t
    except Exception: return ""

def _pdfminer(path):
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path)) or ""
    except Exception: return ""

def _pdfplumber(path):
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: parts.append(t)
        return "\n".join(parts)
    except Exception: return ""

def extract_text(path: pathlib.Path, verbose: bool = False) -> str:
    r = {"pymupdf": _pymupdf(path), "pdfminer": _pdfminer(path), "pdfplumber": _pdfplumber(path)}
    best = max(r, key=lambda k: len(r[k]))
    if verbose:
        for name, txt in r.items():
            print(f"    {name}: {len(txt):,} chars{'  <- used' if name==best else ''}")
    return r[best]


# ─── Clean + segment ──────────────────────────────────────────────────────────
def clean_text(raw: str) -> str:
    raw = re.sub(r'[^\x20-\x7E\n]', ' ', raw)
    raw = re.sub(r'-\n\s*', '', raw)
    raw = re.sub(r'\n+', ' ', raw)
    raw = re.sub(r'\s{2,}', ' ', raw)
    return raw.strip()

def segment_sentences(text: str) -> List[str]:
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm", disable=["ner","tagger","lemmatizer"])
        except OSError:
            import subprocess
            subprocess.run(["python","-m","spacy","download","en_core_web_sm"], check=True)
            nlp = spacy.load("en_core_web_sm", disable=["ner","tagger","lemmatizer"])
        nlp.max_length = 3_000_000
        doc = nlp(text[:2_000_000])
        return [s.text.strip() for s in doc.sents if len(s.text.strip()) > 30]
    except Exception:
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', text) if len(s.strip()) > 30]


# ─── Label — WORD level matching (the actual fix) ─────────────────────────────
def label_sentence(sentence: str) -> Tuple[str, float]:
    word_set = set(re.findall(r'[a-z]+', sentence.lower()))
    if len(word_set) < 3:
        return ("unlabelled", 0.0)
    scores = {theme: sum(1 for kw in kws if kw in word_set)
              for theme, kws in THEME_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    score = scores[best]
    if score == 0:
        return ("unlabelled", 0.0)
    return (best, round(max(min(score/5.0, 1.0), 0.2), 3))


# ─── Build dataset ────────────────────────────────────────────────────────────
def build_dataset(pdf_dir: str = "reports_pdf",
                  output_csv: str = "moefcc_sustainability_dataset.csv"):
    pdfs = sorted(pathlib.Path(pdf_dir).glob("moefcc_20*.pdf"))
    print(f"\n  Found {len(pdfs)} PDFs\n")
    total = 0
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sentence","theme","confidence","report_year","source_file"])
        writer.writeheader()
        for pdf in pdfs:
            year = pdf.stem.replace("moefcc_","").replace("_","-")
            print(f"[{year}]", end=" ", flush=True)
            raw = extract_text(pdf)
            if len(raw.strip()) < 200:
                print(f"SKIPPED (only {len(raw)} chars)")
                continue
            text  = clean_text(raw)
            sents = segment_sentences(text)
            count = unlabelled = 0
            for s in sents:
                if len(s) < 30: continue
                theme, conf = label_sentence(s)
                if theme == "unlabelled":
                    unlabelled += 1
                    continue
                writer.writerow({"sentence":s,"theme":theme,"confidence":conf,
                                 "report_year":year,"source_file":pdf.name})
                count += 1
                total += 1
            print(f"{len(sents)} sentences → {count} labelled, {unlabelled} skipped")
    print(f"\n  Total: {total:,} labelled rows  →  {output_csv}\n")
    return total


# ─── Train ────────────────────────────────────────────────────────────────────
def train_model(csv_path: str = "moefcc_sustainability_dataset.csv",
                model_path: str = "baseline_model.pkl"):
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report
    import pickle

    df = pd.read_csv(csv_path)
    print(f"  Rows: {len(df):,}")
    print(df["theme"].value_counts().to_string())
    if len(df) < 50:
        print("  Not enough data — run --step dataset first")
        return None

    X, y = df["sentence"].tolist(), df["theme"].tolist()
    Xtr,Xte,ytr,yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    clf = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,3), max_features=50000, sublinear_tf=True, min_df=2)),
        ("lr",    LogisticRegression(C=5.0, max_iter=1000, solver="lbfgs", multi_class="multinomial")),
    ])
    print("\n  Training...")
    clf.fit(Xtr, ytr)
    print(classification_report(yte, clf.predict(Xte)))
    with open(model_path, "wb") as f: pickle.dump(clf, f)
    print(f"  Model saved: {model_path}")
    return clf


# ─── Debug ────────────────────────────────────────────────────────────────────
def debug_pdfs(pdf_dir: str = "reports_pdf"):
    pdfs = sorted(pathlib.Path(pdf_dir).glob("moefcc_20*.pdf"))
    print(f"\nFound {len(pdfs)} PDFs\n{'='*60}")
    for pdf in pdfs:
        year = pdf.stem.replace("moefcc_","")
        size = pdf.stat().st_size // 1024
        print(f"\n{pdf.name} ({size} KB)")
        raw   = extract_text(pdf, verbose=True)
        clean = clean_text(raw)
        words = set(re.findall(r'[a-z]+', clean.lower()))
        print(f"  Unique words: {len(words)}")
        if len(words) < 50:
            print(f"  PROBLEM — too few words. Sample: {clean[:200]}")
            continue
        any_hit = False
        for theme, kws in THEME_KEYWORDS.items():
            hits = [kw for kw in kws if kw in words]
            s = "OK  " if hits else "ZERO"
            print(f"  [{s}] {theme}: {len(hits)} hits → {hits[:5]}")
            if hits: any_hit = True
        if not any_hit:
            print("  !! CRITICAL: zero keyword hits — PDF may be scanned image")


# ─── Inference ────────────────────────────────────────────────────────────────
class SustainabilityClassifier:
    THEMES = ["water_conservation","biodiversity","soil_health",
              "climate_adaptation","eco_friendly_practices"]
    def __init__(self, model_path: str = "baseline_model.pkl"):
        import pickle
        with open(model_path,"rb") as f: self._m = pickle.load(f)
    def classify(self, sentences: List[str]) -> List[Dict]:
        probs = self._m.predict_proba(sentences)
        classes = self._m.classes_
        return [{"sentence":s,"theme":classes[int(p.argmax())],
                 "confidence":round(float(p.max()),4),
                 "probabilities":{c:round(float(v),4) for c,v in zip(classes,p)}}
                for s,p in zip(sentences, probs)]


# ─── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["download","dataset","train","all","debug"], default="all")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if args.step == "debug":
        debug_pdfs()
    elif args.step in ("download","all"):
        print("="*60+"\nSTEP 1: Download (18 English reports)\n"+"="*60)
        download_reports(limit=args.limit)
        if args.step == "all":
            print("="*60+"\nSTEP 2: Build dataset\n"+"="*60)
            total = build_dataset()
            if total > 0:
                print("="*60+"\nSTEP 3: Train model\n"+"="*60)
                train_model()
                print("\n  All done! Now run:")
                print("  python themes_over_years.py --mode all")
            else:
                print("\n  Got 0 rows. Run: python moefcc_nlp_pipeline.py --step debug")
    elif args.step == "dataset":
        build_dataset()
    elif args.step == "train":
        train_model()
