import json
import requests
import uuid
from azure.storage.blob import BlobServiceClient
import os
from io import BytesIO

# Translator API credentials
translator_key = "5kBwvZgIbQBIT3Xh1imnyr4CKNugy0UPSOzg8GxZnWHi2Dm5wZRSJQQJ99BEACYeBjFXJ3w3AAAbACOGY8Rc"
translator_region = "eastus"
endpoint = "https://api.cognitive.microsofttranslator.com"
path = "/translate?api-version=3.0&from=ar&to=en"

# Azure Blob Storage credentials
storage_account_name = "nonpoaiplay"
storage_account_key = "QCxdq0lJ5j6xn84DwkvJcEalRkLfcYNyAZQZnCx23+0XqxrF1KUr9ASiuKiSk0URtHyXXBTZ0SNi+AStlmlXFg=="
container_name = "arabic"
input_folder = "extracted_json_folder"
output_folder = "translated_json_folder"

def get_blob_service_client():
    return BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )

def translate_text(text: str) -> str:
    if not text:
        return ""
    headers = {
        "Ocp-Apim-Subscription-Key": translator_key,
        "Ocp-Apim-Subscription-Region": translator_region,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4())
    }
    body = [{ "text": text }]
    resp = requests.post(endpoint + path, headers=headers, json=body)
    resp.raise_for_status()
    translations = resp.json()
    return translations[0]["translations"][0]["text"]

def translate_json_data(data: dict) -> dict:
    for para in data.get("paragraphs", []):
        orig = para.get("content", "")
        para["translatedContent"] = translate_text(orig)

    for table in data.get("tables", []):
        for cell in table.get("cells", []):
            orig = cell.get("content", "")
            cell["translatedContent"] = translate_text(orig)

    return data

def main():
    blob_service = get_blob_service_client()
    container = blob_service.get_container_client(container_name)

    print("🔍 Listing blobs in extracted_json_folder...")
    blobs = container.list_blobs(name_starts_with=input_folder + "/")

    for blob in blobs:
        blob_name = blob.name
        if not blob_name.endswith(".json"):
            continue

        print(f"⬇️ Downloading: {blob_name}")
        blob_client = container.get_blob_client(blob_name)
        blob_data = blob_client.download_blob().readall()
        json_data = json.loads(blob_data)

        print("🌍 Translating content...")
        translated_data = translate_json_data(json_data)

        # Prepare upload
        output_blob_name = f"{output_folder}/{os.path.basename(blob_name)}"
        output_blob_client = container.get_blob_client(output_blob_name)

        print(f"⬆️ Uploading translated JSON to: {output_blob_name}")
        translated_json_bytes = json.dumps(translated_data, ensure_ascii=False, indent=2).encode("utf-8")
        output_blob_client.upload_blob(translated_json_bytes, overwrite=True)

    print("✅ All translations completed and uploaded.")

if __name__ == "__main__":
    main()
