# dealpdf

This repository contains a simple script for converting PDF files into structured data.

## Requirements

The script optionally relies on the following Python packages:

- `PyMuPDF` (package name `PyMuPDF` or `fitz`)
- `pdfplumber`
- `pdfminer.six` (fallback text extraction)
- `camelot` (for table extraction)

For extracting images, the external `pdfimages` command from `poppler-utils` is used if available.

## Usage

Run the pipeline with one or more PDF files:

```bash
python pipeline.py file1.pdf file2.pdf --outdir output
```

Each PDF gets its own folder inside `output/`. By default the script extracts
text, layout, images and tables. Use `--no-text`, `--no-images`, `--no-layout`
or `--no-tables` to skip a step.
