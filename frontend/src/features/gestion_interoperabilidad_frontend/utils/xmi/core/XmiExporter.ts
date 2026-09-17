import type { DiagramState } from '@/features/gestion_modelado/shared/types/types';
import { ElementFactory } from './ElementFactory';
import { RelationFactory } from './RelationFactory';
import { escapeXml, getDuid } from './utils';

export class XmiExporter {
    export(state: DiagramState, projectName: string = "LocalProject"): string {
        const id = "local";
        let xml = `<?xml version="1.0" encoding="windows-1252"?>\n`;
        xml += `<XMI xmi.version="1.1" xmlns:UML="omg.org/UML1.3">\n`;
        xml += `<XMI.header>
            <XMI.documentation>
                <XMI.exporter>Enterprise Architect</XMI.exporter>
                <XMI.exporterVersion>2.5</XMI.exporterVersion>
            </XMI.documentation>
        </XMI.header>\n`;
        
        xml += `<XMI.content>
            <UML:Model name="EA Model" xmi.id="MX_EAID_${id}">
                <UML:Namespace.ownedElement>
                    <UML:Package name="${escapeXml(projectName)}" xmi.id="EAPK_${id}" isRoot="false" isLeaf="false" isAbstract="false" visibility="public">
                        <UML:Namespace.ownedElement>\n`;

        state.nodes.forEach((node) => {
            const mapper = ElementFactory.getMapper(node.type);
            xml += mapper.toXml(node) + "\n";
        });

        state.relations.forEach((rel) => {
            const mapper = RelationFactory.getMapper(rel.type);
            xml += mapper.toXml(rel) + "\n";
        });

        xml += `                    </UML:Namespace.ownedElement>
                    </UML:Package>
                </UML:Namespace.ownedElement>
            </UML:Model>\n`;

        xml += `        <UML:Diagram name="${escapeXml(projectName)}" xmi.id="EAID_DIAG_${id}" diagramType="ClassDiagram" owner="EAPK_${id}" toolName="Enterprise Architect 2.5">
                <UML:ModelElement.taggedValue>
                    <UML:TaggedValue tag="version" value="1.0" />
                    <UML:TaggedValue tag="author" value="AutoExporter" />
                    <UML:TaggedValue tag="package" value="EAPK_${id}" />
                    <UML:TaggedValue tag="type" value="Logical" />
                    <UML:TaggedValue tag="EAStyle" value="ShowPrivate=1;ShowProtected=1;ShowPublic=1;HideRelationships=0;Locked=0;Border=1;HighlightForeign=1;PackageContents=1;SequenceNotes=0;ScalePrintImage=0;PPgs.cx=0;PPgs.cy=0;DocSize.cx=827;DocSize.cy=1169;ShowDetails=0;Orientation=P;Zoom=100;ShowTags=0;OpParams=1;VisibleAttributeDetail=0;ShowOpRetType=1;ShowIcons=1;CollabNums=0;HideProps=0;ShowReqs=0;ShowCons=0;PaperSize=9;HideParents=0;UseAlias=0;HideAtts=0;HideOps=0;HideStereo=0;HideElemStereo=0;ShowTests=0;ShowMaint=0;ConnectorNotation=UML 2.1;ExplicitNavigability=0;ShowShape=1;AllDockable=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;ShowNotes=0;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;" />
                    <UML:TaggedValue tag="styleex" value="SaveTag=8EF2F3CE;ExcludeRTF=0;DocAll=0;HideQuals=0;AttPkg=1;ShowTests=0;ShowMaint=0;SuppressFOC=1;MatrixActive=0;SwimlanesActive=1;KanbanActive=0;MatrixLineWidth=1;MatrixLineClr=0;MatrixLocked=0;TConnectorNotation=UML 2.1;TExplicitNavigability=0;AdvancedElementProps=1;AdvancedFeatureProps=1;AdvancedConnectorProps=1;m_bElementClassifier=1;SPT=1;MDGDgm=;STBLDgm=;ShowNotes=0;VisibleAttributeDetail=0;ShowOpRetType=1;SuppressBrackets=0;SuppConnectorLabels=0;PrintPageHeadFoot=0;ShowAsList=0;SuppressedCompartments=;Theme=:119;" />
                </UML:ModelElement.taggedValue>
                <UML:Diagram.element>\n`;

        state.nodes.forEach((cls, i) => {
            const x = Math.floor(cls.x || 100);
            const y = Math.floor(cls.y || 100);
            const w = Math.floor(cls.width || 220);
            
            let h = 45 + (cls.atributos?.length || 0) * 28 + (cls.metodos?.length || 0) * 28 + 40;
            if (cls.type === 'note') h = 90;
            else if (cls.type === 'enum') h = 45 + (cls.valores?.length || 0) * 28 + 20;

            xml += `                <UML:DiagramElement geometry="Left=${x};Top=${y};Right=${x+w};Bottom=${y+h};" subject="EAID_${cls.id}" seqno="${i+1}" style="DUID=${getDuid(cls.id)};" />\n`;
        });

        xml += `            </UML:Diagram.element>
            </UML:Diagram>
        </XMI.content>\n`;
        
        xml += `    <XMI.difference />
        <XMI.extensions xmi.extender="Enterprise Architect 2.5">
            <EAModel.paramSub />
        </XMI.extensions>
    </XMI>`;

        return xml;
    }
}
