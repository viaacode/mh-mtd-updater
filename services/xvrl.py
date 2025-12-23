"""
# xvrl.py

(Not a) library (yet) for generating XVRL-reports.
TODO: Abstract into a library.
"""

# Std
from os.path import abspath
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, NamedTuple
from datetime import datetime as dt, timezone as tz
from pprint import pformat
#
from lxml import etree
from saxonche import PySaxonProcessor
#


# Namesapces map, used, for instance, to clean up namespaces
NS_MAP = {
    "xsl": "http://www.w3.org/1999/XSL/Transform",
    "xs": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "mh": "https://zeticon.mediahaven.com/metadata/25.1/mh/",
    "mhs": "https://zeticon.mediahaven.com/metadata/25.1/mhs/",
    "xvrl": "http://www.xproc.org/ns/xvrl",
    "mets": "http://www.loc.gov/METS/",
    "premis": "info:lc/xmlns/premis-v2",
    "xlink": "http://www.w3.org/1999/xlink",
    "mm": "http://www.meemoo.be/ns",
}

class SerializationFormat(str, Enum):
    XML = "XML"
    JSON = "JSON"

class Node:
    """Generic XVRL Node
    If no namespace is provided, the default XVRL namespace is assumed.
    """
    def __init__(self,
            name: str,
            ns: str | None = "http://www.xproc.org/ns/xvrl",
            data: str | None = None,
            attribs: dict = {},
            cdata: bool = False):
        self.name = name
        self.ns = ns
        self.data = data
        self.cdata = cdata
        self.attribs = attribs
        self.children = []
    #
    def __str__(self):
        return f"XVRL node: {self.name}"
    #
    def add(self, *nodes):
        """Add a child node
        TODO: Obviously, nodes with the same name will not be seperatly
        accessible via the dot-accessor."""
        for node in nodes:
            self.children.append(node)
            setattr(self, node.name, node)
    #
    def to_Etree(self):
        me = create_Etree_element(
            name=self.name, ns=self.ns, data=self.data, attribs=self.attribs, cdata=self.cdata
        )
        for child in self.children:
            me.append(child.to_Etree())
        return me
    #
    def to_Etree_doc(self):
        tree = etree.ElementTree(self.to_Etree())
        cleanup_namespaces(tree)
        return tree

@dataclass
class DetectionAttribs:
    severity: str = ""
    code: str = ""

@dataclass
class DetectionMessage:
    lang: str = ""
    value: str = ""

class Detection(NamedTuple):
    attribs: DetectionAttribs
    msg: DetectionMessage

class Metadata: pass
class Digest: pass


class XVRLReport(NamedTuple):
    reason: str
    id_col: str
    data_cols: list
    or_id: str

    
def create_Etree_element(name: str, ns: str | None = None, data: str | None = None, attribs: dict = {}, cdata: bool = False):
    """"""
    q_name = f"{{{ns}}}{name}" if ns else name
    el = etree.Element(q_name, **attribs)
    el.text = data if not cdata else etree.CDATA(data)
    return el

def create_XVRLReportsDoc(run_meta) -> Node:
    doc = Node("reports")
    s = Node("supplemental")
    c = Node("creator", data="mh-mtd-updater")
    s.add(Node("OrganisationExternalId", data=run_meta.or_id, ns=NS_MAP["mh"]))
    # TODO: cp name!
    s.add(Node("OrganisationName", data="!TBD: OrganisationName", ns=NS_MAP["mh"]))
    s.add(Node("UpdateRun", data="!TBD: Description", ns=NS_MAP["mm"], attribs={"reference": run_meta.reason}))
    s.add(Node("RecordIdentifierKey", data=run_meta.id_col, ns=NS_MAP["mm"]))
    s.add(Node("UpdateFields", data=pformat(run_meta.data_cols), ns=NS_MAP["mm"]))
    m = Node("metadata")
    m.add(s)
    m.add(c)
    doc.add(m)
    return doc

def create_ReportNode(mh_rec_meta):
    """"""
    report_node = Node("report")
    d = Node("digest")
    s = Node("supplemental")
    m = Node("metadata")
    n1 = Node("ExternalId", data=mh_rec_meta.ExternalId, ns=NS_MAP["mh"])
    n2 = Node("MediaObjectId", data=mh_rec_meta.MediaObjectId, ns=NS_MAP["mh"])
    n3 = Node("FragmentId", data=mh_rec_meta.FragmentId, ns=NS_MAP["mh"])
    n4 = Node("Type", data=mh_rec_meta.Type, ns=NS_MAP["mh"])
    n5 = Node("PathToKeyframe", data=mh_rec_meta.PathToKeyframe, ns=NS_MAP["mh"])
    m.add(s)
    s.add(n1, n2, n3, n4, n5)
    report_node.add(m)
    report_node.add(d)
    return report_node

def cleanup_namespaces(tree):
    """"""
    etree.cleanup_namespaces(tree, top_nsmap=NS_MAP)

def writeXVRL2html(path_to_xvrl: str, path_to_output_html: str, path_to_xslt: str = "./xslt/xvrl2html.xslt", params: dict = {}) -> str:
    """Transform XVRL-file (on disk) to html via XSLT and write the main report
    file out to disk.
    One html-file per report-detail will be written to disk as well.
    Returns the absolute filepath of the output HTML-file."""
    with PySaxonProcessor(license=False) as proc:
        xsltproc = proc.new_xslt30_processor()
        # Input XML is relative to lib's root
        document = proc.parse_xml(xml_file_name=path_to_xvrl)
        executable = xsltproc.compile_stylesheet(stylesheet_file=path_to_xslt)
        # XSLT params given?
        for k, v in params.items():
            executable.set_parameter(k, proc.make_string_value(v))
        # ~ output = executable.transform_to_string(xdm_node=document)
        executable.transform_to_file(output_file=path_to_output_html, xdm_node=document)
        return abspath(path_to_output_html)

def reduceSidecar(sidecar_as_etree: etree.Element, path_to_xslt: str = "./xslt/reduceSidecar.xslt", params: dict = {}) -> str:
    """Reduce a Sidecar-XML to only the Descriptve and Dynamic-nodes.
    TODO: should NOT be in xvrl..."""
    with PySaxonProcessor(license=False) as proc:
        xsltproc = proc.new_xslt30_processor()
        # Input XML is relative to lib's root
        xml_text = etree.tostring(sidecar_as_etree, encoding='UTF-8', pretty_print=True).decode()
        document = proc.parse_xml(xml_text=xml_text)
        executable = xsltproc.compile_stylesheet(stylesheet_file=path_to_xslt)
        # XSLT params given?
        for k, v in params.items():
            executable.set_parameter(k, proc.make_string_value(v))
        return executable.transform_to_string(xdm_node=document)

