"""
# helpers.py

Some models and helper-funtions.
"""

#
# Std
from typing import List, NamedTuple
# 3d
from lxml import etree
# Libs
from viaa.configuration import ConfigParser
#
from mediahaven import MediaHaven
from mediahaven.mediahaven import MediaHavenException, AcceptFormat
from mediahaven.oauth2 import ROPCGrant
#
from meemoo_mtd.mediahaven_config import CURRENT_SIDECAR_NAMESPACES
from meemoo_mtd.mediahaven_config import MhFormat
from meemoo_mtd.transformations import (
    Transformation,
    transform,
    default_transformations,
    merge_transformations_lists,
    transformation_from_dict,
)
# Local
from services.xvrl import *


# Some useful things
class Run(NamedTuple):
    reason: str
    id_col: str
    data_cols: list
    or_id: str
    description: str = "Een beschrijving van de run"


class MHRecordMeta(NamedTuple):
    MediaObjectId: str = "N/A"
    FragmentId: str = "N/A"
    ExternalId: str = "N/A"
    Type: str = "N/A"
    PathToKeyframe: str = "N/A"


class UpdateRun(NamedTuple):
    reason: str
    id_col: str
    data_cols: list
    or_id: str
    description: str = "Een beschrijving van de run"

# Some constants
SIDECAR_XPATH = '/Response/Results/mhs:Sidecar'
FID_XPATH = 'mhs:Sidecar/mhs:Internal/mh:FragmentId'

def construct_query_string(q_dict: dict):
    l = [f'+({k}:"{v}")' for k, v in q_dict.items()]
    return " ".join(l)

def list_from_str(string: str, sep: str = ",") -> list:
    """Evaluate a string with a certain seperator to a list."""
    return string.split(sep)

def transformations_from_csv_row(row: dict, data_cols: list) -> List[Transformation]:
    """"""""
    # TODO: `eval` possible list values to get a list?
    # Naive implementation for now: differentiate between licenses and all the rest
    t_list = []
    for k, v in row.items():
        if k == "Dynamic.dc_rights_licenses":
            t_list.append(transformation_from_dict({
                "target": k,
                "fn": "add_values",
                "args": {
                    "value": list_from_str(v)
                }
            }))
        elif k in data_cols:
            t_list.append(Transformation(target=k, transformers=v))
    return t_list
    #return [Transformation(target=k, transformers=v if not k == "Dynamic.dc_rights_licenses" else [v]) for k, v in row.items() if k in data_cols]

# We need to always search within a given CP.
# Especially for Lukasweb since most items exist in multiple tenants.
# (deleted items are not returned by default)
def get_mh_records(mh_client, q_param, q_value, or_id) -> list:
    or_id_key = "Dynamic.CP_id"
    q_dict = {or_id_key: or_id, q_param: q_value}
    q = construct_query_string(q_dict)
    resp = mh_client._get("records", AcceptFormat.XML, q=q)
    doc = etree.fromstring(resp.text.encode("utf-8"))
    return doc.xpath(SIDECAR_XPATH, namespaces=CURRENT_SIDECAR_NAMESPACES)


def get_rec_meta(mh_record) -> MHRecordMeta:
    """"""
    return MHRecordMeta(
        etree.ElementTree(mh_record).xpath("/mhs:Sidecar/mhs:Internal/mh:MediaObjectId/text()", namespaces=CURRENT_SIDECAR_NAMESPACES)[0],      # MediaObjectId
        etree.ElementTree(mh_record).xpath("/mhs:Sidecar/mhs:Internal/mh:FragmentId/text()", namespaces=CURRENT_SIDECAR_NAMESPACES)[0],         # FragmentId
        etree.ElementTree(mh_record).xpath("/mhs:Sidecar/mhs:Administrative/mh:ExternalId/text()", namespaces=CURRENT_SIDECAR_NAMESPACES)[0],   # ExternalId
        etree.ElementTree(mh_record).xpath("/mhs:Sidecar/mhs:Administrative/mh:Type/text()", namespaces=CURRENT_SIDECAR_NAMESPACES)[0],         # Type
        etree.ElementTree(mh_record).xpath("/mhs:Sidecar/mhs:Internal/mh:PathToKeyframe/text()", namespaces=CURRENT_SIDECAR_NAMESPACES)[0],     # PathToKeyframe
    )
