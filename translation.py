import json
import requests
import uuid


translator_key   = "5kBwvZgIbQBIT3Xh1imnyr4CKNugy0UPSOzg8GxZnWHi2Dm5wZRSJQQJ99BEACYeBjFXJ3w3AAAbACOGY8Rc"
translator_region= "eastus"   
endpoint         = "https://api.cognitive.microsofttranslator.com"
path             = "/translate?api-version=3.0&from=ar&to=en"


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


with open("analysis_result.json", encoding="utf-8") as f:
    data = json.load(f)


for para in data.get("paragraphs", []):
    orig = para.get("content", "")
    para["translatedContent"] = translate_text(orig)


for table in data.get("tables", []):
    for cell in table.get("cells", []):
        orig = cell.get("content", "")
        cell["translatedContent"] = translate_text(orig)


with open("translated_results.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Wrote translated_results.json")
