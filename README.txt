MoEFCC NLP Pipeline — HOW TO RUN
==================================
Windows + VS Code + Python 3.11

WHAT'S FIXED IN THIS VERSION
------------------------------
- 0 labelled sentences: FIXED — now uses word-level matching
- 2022-23 drop to zero: FIXED — 3 PDF extractors, picks best one
- Added --step debug to diagnose any remaining issues
- Added historical event annotations to charts (COVID, Paris, etc.)

FILES IN THIS FOLDER
---------------------
moefcc_nlp_pipeline.py  <- main pipeline
themes_over_years.py    <- generates charts with historical events
moefcc_demo.html        <- open in browser (no Python needed)
requirements.txt        <- libraries

STEP 1 — Install libraries (ONCE, already done if you ran before)
-------------------------------------------------------------------
Open VS Code terminal (Ctrl + `)

pip install PyMuPDF pdfminer.six pdfplumber spacy scikit-learn pandas numpy matplotlib

python -m spacy download en_core_web_sm

STEP 2 — Fresh start: delete old files
----------------------------------------
del moefcc_sustainability_dataset.csv
del baseline_model.pkl
rmdir /s /q reports_pdf

STEP 3 — Download 18 English reports (2008-2026)
-------------------------------------------------
python moefcc_nlp_pipeline.py --step download

Watch for OK or FAILED per year. FAILED is fine, pipeline skips it.

STEP 4 — Build labelled dataset
---------------------------------
python moefcc_nlp_pipeline.py --step dataset

YOU MUST SEE numbers > 0 like this:
[2022-23] 850 sentences -> 612 labelled, 238 skipped   <- GOOD
[2022-23] 850 sentences -> 0 labelled, 850 skipped     <- BAD

IF you still see 0 labelled for any year:
python moefcc_nlp_pipeline.py --step debug
(paste what it shows here and I can fix it)

STEP 5 — Train classifier
--------------------------
python moefcc_nlp_pipeline.py --step train

STEP 6 — Generate all charts
------------------------------
python themes_over_years.py --mode all

Charts saved to charts/ folder:
  01_line.png          <- theme sentences over time
  02_stacked.png       <- stacked bar chart
  03_pct_share.png     <- % share per year
  04_events.png        <- with COVID, Paris, Jal Jeevan annotations
  05_heatmap.png       <- heatmap
  06_dashboard.png     <- all 4 charts + event descriptions

STEP 7 — Open the demo
-----------------------
Right-click moefcc_demo.html -> Open with Live Server
OR double-click to open in browser
