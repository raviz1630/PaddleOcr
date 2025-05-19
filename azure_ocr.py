from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.storage.blob import BlobServiceClient, generate_blob_sas
from datetime import datetime, timedelta
import json

# Document Intelligence credentials
endpoint = "https://non-po-resource.cognitiveservices.azure.com/"
key = "639b590033394b9d9be9942269d7e69d"

# Azure Blob Storage credentials
storage_account_name = "nonpoaiplay"
storage_account_key = "QCxdq0lJ5j6xn84DwkvJcEalRkLfcYNyAZQZnCx23+0XqxrF1KUr9ASiuKiSk0URtHyXXBTZ0SNi+AStlmlXFg=="
container_name = "arabic"
blob_name = "test_image4.jpeg"

def generate_sas_url():
    blob_service_client = BlobServiceClient(
        account_url=f"https://{storage_account_name}.blob.core.windows.net",
        credential=storage_account_key
    )
    sas_token = generate_blob_sas(
        account_name=storage_account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=storage_account_key,
        permission="r",
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    return f"https://{storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

#SAS URL
formUrl = generate_sas_url()

# Document Analysis
client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
poller = client.begin_analyze_document("prebuilt-layout", AnalyzeDocumentRequest(url_source=formUrl))
result = poller.result()

result_dict = result.as_dict()

output_path = "analysis_result.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result_dict, f, ensure_ascii=False, indent=4)

print(f"Analysis complete — results written to {output_path}")
