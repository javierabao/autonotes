from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from starlette.background import BackgroundTask
from pathlib import Path
import tempfile
import shutil
import logging

from ocr_formatter.ocr import OCRProcessor
from ocr_formatter.formatter import TextFormatter

app = FastAPI(title="AutoNotes - Smart Lecture Notes")

TEMPLATE_PATH = Path(__file__).parent / "templates" / "index.html"

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(TEMPLATE_PATH.read_text(encoding="utf-8"))

@app.post("/process")
async def process(
    file: UploadFile = File(...),
    output_format: str = Form("docx"),
    preview: str = Form(None),
    markdown_content: str = Form(None)
):
    """Accept an uploaded image or markdown content, run OCR + formatter if needed, and return the resulting file."""
    try:
        formatter = TextFormatter()
        
        # Create a temporary directory that will last for the entire request
        tmp_dir = tempfile.mkdtemp()
        
        try:
            if markdown_content:
                # If markdown content is provided, use it directly
                formatted = markdown_content
            else:
                # Process the image
                in_path = Path(tmp_dir) / file.filename
                content = await file.read()
                in_path.write_bytes(content)

                # Run OCR
                ocr = OCRProcessor()
                extracted_text = ocr.process_image(str(in_path))

                # Run formatter
                formatted = formatter.format_with_llm(extracted_text)

            # If preview is requested, return JSON
            if preview == "true" and (output_format == "md" or output_format == "markdown"):
                return JSONResponse({"text": formatted})

            # Save the output file
            stem = Path(file.filename).stem if file.filename else "notes"
            
            if output_format == "md" or output_format == "markdown":
                out_path = Path(tmp_dir) / f"{stem}.md"
                formatter.save_as_markdown(formatted, str(out_path))
                media_type = "text/markdown"
            else:
                out_path = Path(tmp_dir) / f"{stem}.docx"
                formatter.save_as_docx(formatted, str(out_path))
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

            # Verify the file exists and has content
            if not out_path.exists():
                raise Exception(f"Output file was not created at {out_path}")
            if out_path.stat().st_size == 0:
                raise Exception("Output file was created but is empty")

            # Return file as attachment and schedule temp-dir cleanup after response is sent
            bg = BackgroundTask(shutil.rmtree, tmp_dir, True)
            return FileResponse(
                str(out_path),
                media_type=media_type,
                filename=out_path.name,
                background=bg
            )

        except Exception as e:
            logging.error(f"Error processing request: {str(e)}")
            # Clean up immediately on error path
            try:
                shutil.rmtree(tmp_dir)
            except Exception as clean_e:
                logging.error(f"Error cleaning up temporary directory after failure: {str(clean_e)}")
            raise
                
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process document: {str(e)}"}
        )
