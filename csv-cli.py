"""
# csv-cli.py

CLI interface to the `mh-mtd-updater` with CSV as input.
"""

# Std
import argparse
import json
from typing import Optional, Any
import logging
import sys
from datetime import datetime as dt
from pprint import pformat
# 3d
from lxml import etree
# Libs
from viaa.configuration import ConfigParser
#
from mediahaven import MediaHaven
from mediahaven.mediahaven import MediaHavenException, AcceptFormat
from mediahaven.oauth2 import ROPCGrant
from meemoo_mtd.mediahaven_config import MhFormat
from meemoo_mtd.transformations import (
    transform,
    default_transformations,
    add_default_licenses,
    merge_transformations_lists,
)
# Local
from helpers import (
    MHRecordMeta,
    get_rec_meta,
    transformations_from_csv_row,
    get_mh_records,
    UpdateRun,
)
from services import csv
from services import xvrl

# TODO: also present in main.py: NEEDS TO BE ORGANIZED!
def error_from(error: Any) -> str:
    """Turn any kind of error we might encounter into a short but intelligible
    string.
    Eg. MH-404 response ⇒ `MH_REC_NOTFOUND`"""
    # The 'MH'-cases
    if isinstance(error, MediaHavenException):
        if error.status_code == 400:
            return "MH_BAD_REQUEST"
        elif error.status_code in (401, 403):
            return "MH_UNAUTHORIZED"
        elif error.status_code == 404:
            return "MH_REC_NOTFOUND"
        elif error.status_code == 429:
            return "MH_TOO_MANY_REQUESTS"
        elif error.status_code == 500:
            return "MH_SERVER_ERROR"
        else:
            return "MH_UNKOWN_ERROR"
    elif isinstance(error, ValueError):
        return "MH_REC_UNCORRECTABLE"
    # The Generic unknown case
    else:
        return "UNKOWN_ERROR"


def error_msg_from(error: Any) -> str:
    """Retrieve the `message`-attr from an error, or something else if it's
    not present."""
    if hasattr(error, "msg"):
        return error.msg
    elif hasattr(error, "message"):
        return error.message
    elif hasattr(error, "error_msg"):
        return error.error_message
    else:
        return str(error)

# Init the config: TODO,don't always init!'
configParser = ConfigParser()
config = configParser.app_cfg
mh_config = config["mediahaven"]
grant = ROPCGrant(
    mh_config["host"],
    mh_config["client_id"],
    mh_config["client_secret"],
)
grant.request_token(mh_config["username"], mh_config["password"])
mh_client = MediaHaven(mh_config["host"], grant)

# Configure logging (OR NOT?)
# ~ log = logging.getLogger(__name__)
# ~ logging.basicConfig(
    # ~ format="%(asctime)s %(name)s %(filename)s %(funcName)s %(lineno)d %(levelname)s %(message)s",
    # ~ level=logging.DEBUG,
    # ~ stream=sys.stdout,
# ~ )

# Toggle boolean propgation value to True/False to enable or disable logging
# from the library respectively.
# ~ logging.getLogger("mh-mtd-updater").propagate = False


def proces_csv(args):
    # Init vars from args
    csv_filepath = args.input_file
    or_id = args.or_id
    reason = args.reason
    csv_parsed = csv.CsvParser(csv_filepath, delimiter=args.csv_delimiter)
    #
    run_meta = UpdateRun(reason, csv_parsed.id_col, csv_parsed.data_cols, or_id)
    # Perform some basic checks first
    try:
        csv_parsed.validate()
    except csv.CsvInvalidError as e:
        print(f"CsvInvalidError: {e}")
        exit(1)
    # Start a XVRL Report Doc
    xvrl_report_doc = xvrl.create_XVRLReportsDoc(run_meta)
    csv_lines = csv_parsed.iterator()
    start_time = dt.now().astimezone()
    xvrl_report_doc.metadata.supplemental.add(
        xvrl.Node("StartTime", data=start_time.replace(microsecond=0).isoformat(), ns="http://www.meemoo.be/ns")
    )
    for row in csv_lines:
        # First, skip the first line if it has no ID-value
        # Assume the first non-header row contains the "human fieldnames".
        if not row[run_meta.id_col]:
            print(f"Skipping first line: ID-value for {run_meta.id_col} is empty.")
            continue
        # Get the object from MediaHaven
        q_param, q_value = run_meta.id_col, row[run_meta.id_col]
        print(f'Handling: {q_param}:{q_value} in {run_meta.or_id}')
        mh_records = get_mh_records(mh_client, q_param, q_value, run_meta.or_id)
        if not mh_records:
            # Add it to the report and skip the row
            err_string = f'WARN: Not found: {q_param}:{q_value} in {run_meta.or_id}'
            print(err_string)
            rec_meta = MHRecordMeta()
            report_node = xvrl.create_ReportNode(rec_meta)
            report_node.metadata.supplemental.add(
                xvrl.Node("IdentifierValue", data=q_value, ns="http://www.meemoo.be/ns")
            )
            report_node.digest.attribs = {"valid": "false"}
            report_node.metadata.supplemental.add(
                xvrl.Node("CsvRow", data=pformat(row), ns="http://www.meemoo.be/ns")
            )
            xvrl_report_doc.add(report_node)
            detection = xvrl.Node("detection",
                attribs={"severity": "error"}
            )
            msg = xvrl.Node("message",
                attribs={"xmllang": "en"}, data=err_string
            )
            detection.add(msg)
            report_node.add(detection)
            mh_update_object = "N/A"
            valid = "false"
            continue
        # Make list of Transformations while filtering out the identifier-column
        # and any possible None-columns at the end.
        # The transformations on this CSV-row need to be applied to all MH-records
        # that might get returned for this idenifier and value.
        dyn_ts = transformations_from_csv_row(row, run_meta.data_cols)
        all_ts = merge_transformations_lists([add_default_licenses] + dyn_ts + default_transformations)
        row_transfos = xvrl.Node("DynamicTransformations", data=str(dyn_ts), ns="http://www.meemoo.be/ns")
        for rec in mh_records:
            # Get some metadata for this record
            rec_meta = get_rec_meta(rec)
            valid = "true" # Assume success
            # We create one report-node for every MH-record we might find for
            # the given identifier
            report_node = xvrl.create_ReportNode(rec_meta)
            # Add the same row-based update transformations to every report
            # for every record returned by MediaHaven.
            report_node.metadata.supplemental.add(row_transfos)
            report_node.metadata.supplemental.add(
                xvrl.Node("CsvRow", data=pformat(row), ns="http://www.meemoo.be/ns")
            )
            report_node.metadata.supplemental.add(
                xvrl.Node("MhOriginalRecord", data=xvrl.reduceSidecar(rec), ns="http://www.meemoo.be/ns", cdata=True)
            )
            report_node.metadata.supplemental.add(
                xvrl.Node("IdentifierValue", data=q_value, ns="http://www.meemoo.be/ns")
            )
            try:
                # The transform-fn accepts either a string (file of file-like object)
                # or an XML-document (this an lxml.etree._ElementTree)
                mh_update_object = transform(
                    input_file_path=etree.ElementTree(rec),
                    static_values={"Reason": run_meta.reason},
                    transformations=all_ts,
                    out_format=MhFormat.MH_UPDATEOBJECT,
                )
            except ValueError as e:
                err_string = f'Could not properly transform/clean record: {e}'
                print(err_string)
                detection = xvrl.Node("detection",
                    attribs={"severity": "error"}
                )
                msg = xvrl.Node("message",
                    attribs={"xmllang": "en"}, data=err_string
                )
                detection.add(msg)
                report_node.add(detection)
                mh_update_object = "N/A"
                valid = "false"
            else:
                print(f"OK: {row[run_meta.id_col]}")
                # ~ print(mh_update_object)
                if not args.dryrun:
                    # Update item in MediaHaven
                    print(f"Performing update for item: {q_param}:{q_value} => FragmentId:{rec_meta.FragmentId}")
                    try:
                        mh_resp = mh_client.records.update(rec_meta.FragmentId, xml=mh_update_object)
                        # ~ raise MediaHavenException(status_code=500, message="Something wrong...")
                    except MediaHavenException as e:
                        err_string = error_msg_from(e)
                        error = error_from(e)
                        full_err_string = f"Status_code={e.status_code}, status_msg={error}, msg={err_string}"
                        print(full_err_string)
                        detection = xvrl.Node("detection",
                            attribs={"severity": "error"}
                        )
                        msg = xvrl.Node("message",
                            attribs={"xmllang": "en"}, data=full_err_string
                        )
                        detection.add(msg)
                        report_node.add(detection)
                        valid = "false"
                    else:
                        print(f"Succesfully updated {rec_meta.FragmentId}.")
                        detection = xvrl.Node("detection",
                            attribs={"severity": "info"}
                        )
                        msg = xvrl.Node("message",
                            attribs={"xmllang": "en"}, data=f"Succesfully updated item: {q_value}"
                        )
                        detection.add(msg)
                        report_node.add(detection)
                else:
                    print(f"Dryrun: not actualy performing update for item: {q_param}:{q_value}")
            # Add the validation/traonsformation report node
            report_node.digest.attribs = {"valid": valid}
            report_node.metadata.supplemental.add(
                xvrl.Node("MhUpdateRecord", data=mh_update_object, ns="http://www.meemoo.be/ns", cdata=True)
            )
            xvrl_report_doc.add(report_node)
    # Add end-time
    end_time = dt.now().astimezone()
    xvrl_report_doc.metadata.supplemental.add(
        xvrl.Node("EndTime", data=end_time.replace(microsecond=0).isoformat(), ns="http://www.meemoo.be/ns")
    )
    # Finally, write the XVRL Report to file
    xvrl_report_filename = "./reports/xvrl_report.xml"
    tree = xvrl_report_doc.to_Etree_doc().write(xvrl_report_filename, encoding='UTF-8', pretty_print=True, xml_declaration=True)
    print(f"XVRL Report written to: {xvrl_report_filename}")
    html_abspath = xvrl.writeXVRL2html(xvrl_report_filename, "./reports/report.html")
    print(f"Html Report written to: {html_abspath}")


def main():
    svc_desc = """Python CLI interface to the `mh-mtd-updater`.
    Allows for bulk-metadate-updates in MediaHaven via CSV-input while also
    validating or correcting (where possible) MediaHaven-metadata."""
    parser = argparse.ArgumentParser(description=svc_desc)
    parser.add_argument(
        "input_file",
        type=str,
        help="Filepath to the CSV-file which contains the metadata-updates.",
    )
    parser.add_argument(
        "-o",
        "--or_id",
        type=str,
        required=True,
        help="""Provide the OR-id of the partner for which these updates need to be performed. (required)""",
    )
    parser.add_argument(
        "-r",
        "--reason",
        type=str,
        required=True,
        help="""Provide a reason for the update. Usually a reference to an Jira-ticket. (required)""",
    )
    parser.add_argument(
        "-d",
        "--csv-delimiter",
        type=str,
        required=False,
        default=",",
        help="""Provide a custom delimiter to parse the CSV-file. (default: ',')""",
    )
    parser.add_argument(
        "--dryrun",
        type=bool,
        action=argparse.BooleanOptionalAction,
        default=True,
        help="""Perform a dry-run. Use the `--no-dryrun` command line argument to disable a dry-run, ie., to actually perform the update against MediaHaven.""",
    )
    # ~ parser.add_argument(
        # ~ "-c",
        # ~ "--case",
        # ~ type=str,
        # ~ choices=["lukasweb"],
        # ~ help="""Defines which generic custom transformations are to be performed.
        # ~ Consult the documentation for the currently implemented transformations.
        # ~ In any other, custom, transformation, the default transformations are
        # ~ also always performed.""",
    # ~ )

    args = parser.parse_args()

    try:
        proces_csv(args)
    except ValueError as e:
        print(f'Some error: {e}')


if __name__ == "__main__":
    main()

# vim modeline
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 smartindent
