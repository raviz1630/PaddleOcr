from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobClient
from datetime import datetime, timedelta
from pdf2image import convert_from_path
from PIL import Image
import json
import os
import sys
import uuid
import mimetypes

# Document Intelligence credentials
endpoint = "https://non-po-resource.cognitiveservices.azure.com/"
key = "639b590033394b9d9be9942269d7e69d"

# Azure Blob Storage credentials
storage_account_name = "nonpoaiplay"
storage_account_key = "QCxdq0lJ5j6xn84DwkvJcEalRkLfcYNyAZQZnCx23+0XqxrF1KUr9ASiuKiSk0URtHyXXBTZ0SNi+AStlmlXFg=="
container_name = "arabic"

def get_blob_service_client():
    return BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )

def upload_to_blob(local_file_path, blob_subfolder="uploads"):
    """Upload a file to Azure Blob Storage under the specified folder"""
    blob_service_client = get_blob_service_client()
    file_name = os.path.basename(local_file_path)
    blob_name = f"{blob_subfolder}/{str(uuid.uuid4())}_{file_name}"

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    print(f"Uploading {local_file_path} to blob storage as {blob_name}...")
    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(data)

    print(f"Upload complete: {blob_name}")
    return blob_name

def generate_sas_url(blob_name):
    blob_service_client = get_blob_service_client()
    sas_token = generate_blob_sas(
        account_name=storage_account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=storage_account_key,
        permission="r",
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    return f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

def upload_result_to_blob(result_dict, original_file_name, suffix=None):
    blob_service_client = get_blob_service_client()
    base_name = os.path.splitext(os.path.basename(original_file_name))[0]
    if suffix:
        base_name += f"_{suffix}"
    result_blob_name = f"extracted_json_folder/{base_name}_{uuid.uuid4()}.json"

    blob_client = blob_service_client.get_blob_client(container=container_name, blob=result_blob_name)
    json_data = json.dumps(result_dict, ensure_ascii=False, indent=4).encode('utf-8')
    blob_client.upload_blob(json_data)
    print(f"OCR result uploaded to: {result_blob_name}")

def process_and_upload_images(local_file_path):
    """Convert PDF pages to images or handle a single image, then upload all to segmented_images"""
    mime_type, _ = mimetypes.guess_type(local_file_path)
    print(f"Detected MIME type: {mime_type}")

    segmented_blob_names = []

    if mime_type == "application/pdf":
        print("File is a PDF. Converting pages to images...")
        images = convert_from_path(local_file_path)
        for idx, img in enumerate(images):
            img_path = f"/tmp/{uuid.uuid4()}_page_{idx + 1}.png"
            img.save(img_path, "PNG")
            blob_name = upload_to_blob(img_path, blob_subfolder="segmented_images")
            segmented_blob_names.append(blob_name)
        return segmented_blob_names, "pdf"

    elif mime_type and mime_type.startswith("image"):
        print("File is an image. No conversion needed.")
        blob_name = upload_to_blob(local_file_path, blob_subfolder="segmented_images")
        segmented_blob_names.append(blob_name)
        return segmented_blob_names, "image"

    else:
        raise ValueError("Unsupported file type. Please provide a PDF or image file.")

def run_ocr_on_segmented_images(blob_names, original_file_path):
    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    
    for idx, blob_name in enumerate(blob_names):
        print(f"Running OCR on: {blob_name}")
        try:
            sas_url = generate_sas_url(blob_name)
            poller = client.begin_analyze_document("prebuilt-layout", AnalyzeDocumentRequest(url_source=sas_url))
            result = poller.result()
            result_dict = result.as_dict()

            upload_result_to_blob(result_dict, original_file_path, suffix=f"page_{idx+1}")
        except Exception as e:
            print(f"Failed OCR on {blob_name}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_file>")
        sys.exit(1)

    local_file_path = sys.argv[1]

     
    try:
        uploaded_original_blob = upload_to_blob(local_file_path, blob_subfolder="uploads")
    except Exception as e:
        print(f"Error uploading original file to 'uploads': {e}")
        sys.exit(1)

    try:
        segmented_blob_names, file_type = process_and_upload_images(local_file_path)
    except Exception as e:
        print(f"Error during segmentation/upload: {e}")
        sys.exit(1)

    if file_type == "pdf":
        try:
            run_ocr_on_segmented_images(segmented_blob_names, local_file_path)
        except Exception as e:
            print(f"Error during OCR on segmented images: {e}")
            sys.exit(1)
    else:
        # For image input, do the usual direct OCR
        try:
            blob_name = segmented_blob_names[0]
            sas_url = generate_sas_url(blob_name)

            client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
            poller = client.begin_analyze_document("prebuilt-layout", AnalyzeDocumentRequest(url_source=sas_url))
            result = poller.result()

            result_dict = result.as_dict()
            upload_result_to_blob(result_dict, local_file_path)
        except Exception as e:
            print(f"Error during image OCR: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
