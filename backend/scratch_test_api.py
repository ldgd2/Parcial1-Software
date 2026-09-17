import asyncio
import httpx
import json

async def test():
    # Login as ldgd2 to get token
    # Wait, we can just send the request without auth and if we get 401, we know pydantic is fine.
    # Actually, Depends(get_current_user) runs BEFORE pydantic validation?
    # No, FastAPI evaluates dependencies and body parameters concurrently.
    # Let's just do a request.
    
    payload = {
        "nombre_repo": "prueba-123",
        "diagram_json": {"nodes": [], "relations": []}
    }
    
    async with httpx.AsyncClient() as client:
        # Petición falsa sin token
        res = await client.post("http://localhost:8000/exportar-github/exportar", json=payload)
        print("Status:", res.status_code)
        print("Body:", res.text)

if __name__ == "__main__":
    asyncio.run(test())
