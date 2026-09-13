import asyncio
from backend.modules.gestion_interoperabilidad.importar_desde_xml.services import import_service
import traceback

xml = """<?xml version="1.0" encoding="windows-1252"?>
<XMI xmi.version="1.1" xmlns:UML="omg.org/UML1.3" timestamp="2026-09-13 09:31:10">
    <XMI.content>
        <UML:Connector xmi.id="EAID_1" name="connector1">
        </UML:Connector>
    </XMI.content>
</XMI>
"""
async def main():
    try:
        print(await import_service.parsear_xmi(xml))
    except Exception as e:
        traceback.print_exc()

asyncio.run(main())
