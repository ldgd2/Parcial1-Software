import asyncio
import sys
sys.path.append('c:\\Users\\ldgd2\\Documents\\universidad\\software 1\\sem 2-2026\\examen1\\Examen')

from backend.modules.gestion_interoperabilidad.exportar_a_xml.services.export_service import generar_xmi
import xml.etree.ElementTree as ET

class DummyUser:
    nombre = 'Test'

class DummyProyecto:
    id = 1
    lienzo_json = '{"nodes": [{"id":"n1","nombre":"Class1","x":100,"y":100,"width":150}], "relations": []}'

class DummyResult:
    def scalar_one_or_none(self):
        return DummyProyecto()

class DummyDB:
    async def execute(self, q):
        return DummyResult()

async def main():
    res = await generar_xmi(1, DummyUser(), DummyDB())
    print(res)

asyncio.run(main())
