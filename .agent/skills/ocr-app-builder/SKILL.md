---
name: ocr-app-builder
description: Guides the agent through planning, scaffolding, and delivering a Python-based Windows desktop app for Automated Order OCR & Excel Consolidation. Use when the user asks to build the OCR data consolidation app or requires an overarching architecture for processing diverse order files into a master Excel sheet.
---

# Automated Order OCR & Consolidation App Builder

## When to Use
- User asks to build an app that processes Excel, documents, or images into a formatted Excel master sheet.
- User requests the automated order OCR processor desktop app.
- User wants to process diverse order files, run OCR, use an item dictionary, and present a human-in-the-loop review interface.

## Workflow Overview
The agent follows a strict Step-by-Step execution process. Because this is a complex Desktop application, do NOT attempt to write everything at once. Complete one phase, verify it works locally, and then move to the next.

### Tool & Technology Inventory
- **Language:** Python 3.10+
- **UI Framework:** `customtkinter` (Modern, clean, and simple UI for non-programmers)
- **Database:** `sqlite3` (Built-in, zero configuration, stores item dictionary and template settings)
- **Data Processing:** `pandas`, `openpyxl` (Strictly mapping by Row 1 headers)
- **PDF & Image Processing:** `pdfplumber`, `opencv-python` (cv2), `Pillow`
- **OCR Engine:** `pytesseract` or `easyocr` (for local processing). Implement a fallback utilizing a free-tier API (like Google Vision Free Tier, or OCR.space API) for poor locally-scanned results.
- **Packaging:** `pyinstaller`

---

## Phase 1 — Project Scaffold & Database Setup
1. Create a logical directory structure.
```
order-ocr-app/
  ├── main.py
  ├── database/
  │   └── db_manager.py
  ├── processing/
  │   ├── excel_parser.py
  │   └── ocr_engine.py
  ├── ui/
  │   ├── app_window.py
  │   └── review_grid.py
  ├── requirements.txt
  └── README.md
```
2. Set up `database/db_manager.py` to initialize SQLite.
   - Table `item_dictionary`: (id, wrong_spelling, correct_spelling)
   - Table `templates`: (id, header_name, mapped_sys_field)
3. Ensure the DB initiates automatically on first run.

## Phase 2 — Excel Parsing Subsystem
1. Implement `processing/excel_parser.py`.
2. Must rigorously load any user-submitted Excel files, read ONLY the **First Row (Header)**, and map the columns strictly based on the header text to the system's 18 default columns (e.g., 訂單號碼, 訂單備註, 送貨方式...等).
3. Ignore column order, ONLY match header names.

## Phase 3 — OCR Subsystem & API Fallback
1. Implement `processing/ocr_engine.py`.
2. Take images/PDFs, apply OpenCV preprocessing (grayscale, binarization).
3. Try standard string extraction using a local OCR library.
4. If confidence is too low or output is obviously garbage, provide an option to switch to a configured Free-Tier HTTP API.
5. Use Regex or predefined layout coordinate bounding boxes to map words to the 18 default fields.

## Phase 4 — Data Aggregation & Dictionary Flagging
1. Take data collected from Phases 2 and 3 and unify it into a basic Python list-of-dicts or Pandas DataFrame.
2. Cross-reference the "Item Number (商品貨號)" against the `item_dictionary` table.
3. **CRITICAL:** Do NOT automatically overwrite. Instead, add a flag `{"value": "ABC-12S", "suggestion": "ABC-125", "requires_review": True}` into the data structure so the UI knows to prompt the user.

## Phase 5 — Human-in-the-Loop Review UI
1. Implement `ui/review_grid.py` using `customtkinter` and possibly `tkinter.ttk.Treeview` for displaying tabular data.
2. All extracted data is presented herein.
3. Cells flagged as `requires_review` must be highlighted (e.g., Yellow).
4. Provide a way for the user to double-click and apply the suggested correction or manually type a correction before approving.

## Phase 6 — Excel Export & ERP Placeholder
1. Once the user clicks "Approve & Export" in the UI, grab the finalized datagrid.
2. Write it to a formatted Excel file using Pandas.
3. Create a dummy function `export_to_erp(dataframe)` placeholder with a simple print statement indicating where future REST API logic goes.

## Phase 7 — Executable Packaging
1. Gather all dependencies into `requirements.txt`.
2. Generate the PyInstaller command: `pyinstaller --noconfirm --onedir --windowed --add-data "<local_tesseract_path>;." main.py`. (Adjust based on final library choices).
3. Document how the user can generate the standalone `.exe`.

---
## Constraints
- **C1**: First-row Excel headers MUST be the absolute source of truth for column identification.
- **C2**: Dictionary corrections MUST require user confirmation in the UI grid.
- **C3**: Prioritize user experience. If it looks daunting, simplify the GUI.
