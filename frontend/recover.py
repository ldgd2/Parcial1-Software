import json

def search_transcript():
    transcript_path = r"c:\Users\ldgd2\.gemini\antigravity-ide\brain\a71ae693-fa06-4a5d-b83e-682c514a35f9\.system_generated\logs\transcript_full.jsonl"
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "proyectoService" in line or "PermisosModal" in line or "NotifContext" in line:
                try:
                    data = json.loads(line)
                    # if this is a file view or write, we can extract the content
                    if data.get("type") == "TOOL_RESPONSE" and "output" in data.get("content", ""):
                        content = data["content"]
                        if "proyectoService.ts" in content or "PermisosModal.tsx" in content or "NotifContext.tsx" in content:
                            print("---------------------------------------------------")
                            print("FOUND IN TOOL_RESPONSE:")
                            print(content[:2000]) # Print first 2000 chars
                except Exception:
                    pass

if __name__ == "__main__":
    search_transcript()
