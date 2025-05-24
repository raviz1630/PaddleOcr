from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import uuid
import shutil
from typing import List
import json

app = FastAPI()

# Allow CORS for your React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"id": file_id, "filename": file.filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/")
async def process_file(file_data: dict):
    try:
        file_id = file_data["id"]
        filename = file_data["filename"]
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        
        # Run the pipeline steps
        steps = [
            ("OCR Processing", ["python", "azure_ocr.py", file_path]),
            ("Translation", ["python", "translation.py"]),
            ("Visual Overlay", ["python", "translated_content_over_canvas.py"])
        ]
        
        results = {}
        for step_name, command in steps:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception(f"{step_name} failed: {result.stderr}")
            results[step_name] = result.stdout
        
        # Get the final PDF path
        final_pdf = "arabic/final_results/combined_translated_document.pdf"
        if not os.path.exists(final_pdf):
            raise Exception("Final PDF not found")
        
        return {
            "status": "completed",
            "result_path": final_pdf,
            "details": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/")
async def check_status():
    # Implement your status checking logic here
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)