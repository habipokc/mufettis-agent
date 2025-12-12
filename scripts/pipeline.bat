@echo off
echo ==========================================
echo Mufettis Agent ETL Pipeline (v2)
echo ==========================================
echo.

echo [STEP 1/2] Chunking PDFs with Docling...
echo (This may take a while for large PDFs)
echo.
poetry run python scripts/docling_chunker.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Chunking failed.
    exit /b %ERRORLEVEL%
)

echo.
echo [STEP 2/2] Embedding and Indexing to ChromaDB...
echo.
poetry run python scripts/embed_and_index.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Embedding failed.
    exit /b %ERRORLEVEL%
)

echo.
echo ==========================================
echo Pipeline completed successfully!
echo ==========================================
echo.
echo IMPORTANT: Please restart the backend server:
echo   poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
echo.
