@echo off
echo ==========================================
echo Mufettis Agent ETL Pipeline
echo ==========================================

echo [step 1/3] Extracting Text & Tables from PDFs...
poetry run python scripts/extractor.py
if %ERRORLEVEL% NEQ 0 (
    echo Extraction failed.
    exit /b %ERRORLEVEL%
)

echo [step 2/3] Chunking extracted data...
poetry run python scripts/chunker.py
if %ERRORLEVEL% NEQ 0 (
    echo Chunking failed.
    exit /b %ERRORLEVEL%
)

echo [step 3/3] Embedding (Requires GEMINI_API_KEY)...
if "%GEMINI_API_KEY%"=="" (
    echo WARNING: GEMINI_API_KEY is not set. Skipping embedding step to avoid errors.
    echo Please set GEMINI_API_KEY in your environment and run 'poetry run python scripts/embed_and_index.py' manually.
) else (
    poetry run python scripts/embed_and_index.py
)

echo Pipeline finished.
