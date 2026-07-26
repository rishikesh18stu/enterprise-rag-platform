import os
import shutil
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from auth.security import get_current_user
from ingestion.loaders import load_local_files
from ingestion.pipeline import store_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "data"  # reuse the same folder ingestion.run_ingest already reads from

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"}


@router.post("/upload")
def upload_document(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """
    Saves an uploaded file to disk, then immediately ingests it
    (chunk + embed + store in Qdrant) so it's queryable right away.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, file.filename)

    # Stream the upload to disk rather than loading it fully into memory --
    # matters for larger files (e.g. big PDFs/PPTX decks).
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    logger.info("Saved upload: %s (by user %s)", save_path, user["sub"])

    # Ingest just this one new file, not the whole data/ directory again --
    # avoids re-embedding every previously uploaded document on each upload.
    documents = load_local_files(UPLOAD_DIR)
    new_docs = [d for d in documents if d.metadata.get("file_name") == file.filename]
    store_documents(new_docs)

    return {"filename": file.filename, "status": "uploaded and indexed"}
