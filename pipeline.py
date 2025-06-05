import os
import subprocess
from typing import List, Dict

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except Exception:
    pdfminer_extract_text = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import camelot
except ImportError:
    camelot = None


def extract_images(pdf_path: str, output_dir: str) -> List[str]:
    """Extract images using the pdfimages command."""
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["pdfimages", pdf_path, os.path.join(output_dir, "image")]
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("pdfimages command not found. Please install poppler-utils.")
    except subprocess.CalledProcessError as e:
        print(f"pdfimages failed: {e}")
    return sorted(os.listdir(output_dir)) if os.path.exists(output_dir) else []


def extract_text(pdf_path: str) -> List[str]:
    """Extract text using pdfplumber or pdfminer."""
    pages_text: List[str] = []
    if pdfplumber is not None:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pages_text.append(page.extract_text() or "")
    elif pdfminer_extract_text is not None:
        # pdfminer returns the entire text as a single string
        pages_text.append(pdfminer_extract_text(pdf_path))
    else:
        print("No text extraction library installed. Skipping text extraction.")
    return pages_text


def extract_tables(pdf_path: str, output_dir: str) -> List[str]:
    """Extract tables using Camelot or pdfplumber."""
    os.makedirs(output_dir, exist_ok=True)
    table_files: List[str] = []
    if camelot is not None:
        tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
        for i, table in enumerate(tables):
            csv_path = os.path.join(output_dir, f"table_{i}.csv")
            table.to_csv(csv_path)
            table_files.append(csv_path)
    elif pdfplumber is not None:
        import csv

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                for tb_num, table in enumerate(page.extract_tables() or []):
                    csv_path = os.path.join(output_dir, f"table_{page_num}_{tb_num}.csv")
                    with open(csv_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerows(table)
                    table_files.append(csv_path)
    else:
        print("No table extraction library installed. Skipping table extraction.")
    return table_files


def detect_layout(pdf_path: str) -> List[Dict]:
    """Use PyMuPDF to detect basic page layout."""
    if fitz is None:
        print("PyMuPDF not installed. Skipping layout detection.")
        return []
    doc = fitz.open(pdf_path)
    layout_info = []
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        layout_info.append({
            "number": page.number,
            "blocks": blocks,
        })
    return layout_info


def process_pdf(
    pdf_path: str,
    image_output: str = "images",
    table_output: str = "tables",
    *,
    do_text: bool = True,
    do_images: bool = True,
    do_layout: bool = True,
    do_tables: bool = True,
) -> Dict:
    """Run the processing pipeline on a PDF with optional steps."""
    result: Dict[str, object] = {}
    if do_text:
        result["text"] = extract_text(pdf_path)
    if do_layout:
        result["layout"] = detect_layout(pdf_path)
    if do_images:
        result["images"] = extract_images(pdf_path, image_output)
    if do_tables:
        result["tables"] = extract_tables(pdf_path, table_output)
    return result


if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser(description="Process PDF files into structured data")
    parser.add_argument("pdfs", nargs="+", help="PDF files to process")
    parser.add_argument("--outdir", default="output", help="Directory to store extracted data")
    parser.add_argument("--no-text", action="store_true", help="Skip text extraction")
    parser.add_argument("--no-images", action="store_true", help="Skip image extraction")
    parser.add_argument("--no-layout", action="store_true", help="Skip layout detection")
    parser.add_argument("--no-tables", action="store_true", help="Skip table extraction")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    for pdf in args.pdfs:
        name = os.path.splitext(os.path.basename(pdf))[0]
        outdir = os.path.join(args.outdir, name)
        os.makedirs(outdir, exist_ok=True)
        image_dir = os.path.join(outdir, "images")
        table_dir = os.path.join(outdir, "tables")
        result = process_pdf(
            pdf,
            image_dir,
            table_dir,
            do_text=not args.no_text,
            do_images=not args.no_images,
            do_layout=not args.no_layout,
            do_tables=not args.no_tables,
        )
        with open(os.path.join(outdir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("Processed", pdf, "->", outdir)

