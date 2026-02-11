
import json
import codecs

try:
    with open("models.json", "rb") as f:
        # Try utf-16 first as powershell redirect typically uses it
        raw = f.read()
        try:
            content = raw.decode("utf-16-le")
        except:
            content = raw.decode("utf-8", errors="ignore")
            
    # Find JSON start
    start_idx = content.find("{")
    if start_idx != -1:
        json_str = content[start_idx:]
        data = json.loads(json_str)
        print("Available Models:")
        for m in data.get("data", []):
            print(m.get("id"))
    else:
        print("No JSON found")
except Exception as e:
    print(f"Error processing: {e}")
