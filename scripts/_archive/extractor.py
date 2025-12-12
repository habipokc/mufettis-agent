import pdfplumber
import json
import os
from pathlib import Path


def extract_pdf(pdf_path: str) -> dict:
    """
    PDF dosyasından metin ve tabloları çıkarır.
    
    Args:
        pdf_path: PDF dosyasının yolu
        
    Returns:
        Dosya adı, sayfalar, metin ve tablolar içeren dict
    """
    data = {"filename": os.path.basename(pdf_path), "pages": []}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Extract text
            text = page.extract_text() or ""
            
            # Extract tables
            tables = page.extract_tables()
            
            page_data = {
                "page_number": i + 1,
                "text": text,
                "tables": tables
            }
            data["pages"].append(page_data)
    return data


def main():
    """Ana fonksiyon - tüm PDF'leri işler."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(raw_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs in {raw_dir.absolute()}")

    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        try:
            extracted = extract_pdf(pdf_file)
            output_file = processed_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extracted, f, ensure_ascii=False, indent=2)
            print(f"Saved to {output_file.name}")
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")


if __name__ == "__main__":
    main()
