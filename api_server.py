from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from azure.storage.blob import BlobServiceClient
import subprocess
import os
import shutil
from typing import List
import json

app = FastAPI()

# Azure Blob Storage Configuration
storage_account_name = "nonpoaiplay"
storage_account_key = "QCxdq0lJ5j6xn84DwkvJcEalRkLfcYNyAZQZnCx23+0XqxrF1KUr9ASiuKiSk0URtHyXXBTZ0SNi+AStlmlXFg=="
container_name = "arabic"
blob_name = "combined_translated_document.pdf"

# Create connection string
connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key};EndpointSuffix=core.windows.net"

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

def get_blob_url():
    """Generate a URL to access the blob directly"""
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    return blob_client.url

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save the uploaded file with its original name
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {"filename": file.filename}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/")
async def process_file(file_data: dict):
    try:
        filename = file_data["filename"]
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
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
        
        # Get the URL for the final PDF in Azure Storage
        pdf_url = get_blob_url()
        
        return {
            "status": "completed",
            "result_url": pdf_url,
            "result_path": f"arabic/final_results/{blob_name}",
            "details": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/")
async def check_status():
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)