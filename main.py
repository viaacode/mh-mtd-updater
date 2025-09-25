import time
import datetime
import argparse
from typing import Any
from io import BytesIO
from services.db import DatabaseService, RecordStatus
import logging

from viaa.configuration import ConfigParser
# ~ from viaa.observability import logging

from mediahaven import MediaHaven
from mediahaven.mediahaven import MediaHavenException, AcceptFormat
from mediahaven.oauth2 import ROPCGrant

from meemoo_mtd.mediahaven_config import MhFormat
from meemoo_mtd.transformations import (
    transform,
    default_transformations,
)


# Init the config
configParser = ConfigParser()
config = configParser.app_cfg

# Configure logging
log = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s %(name)s %(filename)s %(funcName)s %(lineno)d %(levelname)s %(message)s",
    level=logging.INFO,
    # ~ stream=sys.stdout,
)
# Alternatively, struct logging: from viaa.observability import logging
# ~ log = logging.get_logger(__name__, config=configParser)

mh_config = config["mediahaven"]
grant = ROPCGrant(
    mh_config["host"],
    mh_config["client_id"],
    mh_config["client_secret"],
)
grant.request_token(mh_config["username"], mh_config["password"])
mh_client = MediaHaven(mh_config["host"], grant)


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


def process_item(item, database, reason: str):
    log.info(f'Processing "{item.fragment_id}"...')
    # Get item from MediaHaven and turn it into a bytes-object
    try:
        mh_record_xml = mh_client.records.get(
            item.fragment_id, accept_format=AcceptFormat.XML
        )
    except MediaHavenException as e:
        log.warning("Status_code=%s, msg=%s", e.status_code, error_msg_from(e))
        item.error = error_from(e)
        item.error_msg = error_msg_from(e)
        item.status = RecordStatus.ERROR
    else:
        item.original_metadata = mh_record_xml.raw_response
        mh_rec_as_bytes = BytesIO(mh_record_xml.raw_response.encode("utf-8"))
        # Perform transformations
        try:
            mh_update_object = transform(
                input_file_path=mh_rec_as_bytes,
                static_values={"Reason": reason},
                transformations=default_transformations,
                out_format=MhFormat.MH_UPDATEOBJECT,
            )
        except ValueError as e:
            log.warning(
                'Could not properly transform/clean "%s": %s', item.fragment_id, e
            )
            item.error = error_from(e)
            item.error_msg = error_msg_from(e)
            item.status = RecordStatus.ERROR
        else:
            # We might get `None` back, meaning no cleaning/transformation was
            # needed or perfomed.
            if mh_update_object:
                item.update_object = mh_update_object
                print(mh_update_object)
                # Update item in MediaHaven
                try:
                    # ~ mh_resp = mh_client.records.update(item.fragment_id, xml=mh_update_object)
                    raise MediaHavenException(
                        status_code=666, message="The number of the beast!"
                    )
                except MediaHavenException as e:
                    log.warning(
                        "Status_code=%s, msg=%s", e.status_code, error_msg_from(e)
                    )
                    item.error = error_from(e)
                    item.error_msg = error_msg_from(e)
                    item.status = RecordStatus.ERROR
                else:
                    log.info(f"Succesfully updated {item.fragment_id}.")
                    item.status = RecordStatus.DONE
            else:
                # None returned
                item.status = RecordStatus.DONE
    # Save state and result to the database
    _ = database.update_with_result(item)


def calculate_time_to_process(nr_of_items, limit, sleep_secs) -> str:
    """"""
    nr_of_items = nr_of_items if not limit else limit
    total_secs = nr_of_items * sleep_secs if sleep_secs else nr_of_items
    return str(datetime.timedelta(seconds=total_secs))


def main():
    svc_desc = """Python service to add or update and correct metadata in MediaHaven."""
    parser = argparse.ArgumentParser(description=svc_desc)
    parser.add_argument(
        "-r",
        "--reason",
        type=str,
        required=True,
        help="The reason to be provided for the updates that will be performed. Usually a reference to a Jira-ticket.",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=None,
        help="Number of items to process (optional)",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        default=0,
        help="Number of seconds to wait between each item (optional: defaults to 0)",
    )

    args = parser.parse_args()
    db_conf = config["database"]
    print(f"""Will connect to '{db_conf["table"]}' on '{db_conf["host"]}'.""")

    database = DatabaseService(config, db_conf["table"])

    nr_of_items = database.count_items_to_process()
    time_to_process = calculate_time_to_process(nr_of_items, args.limit, args.sleep)
    print(f"Items to process: {nr_of_items} (status=TODO, with limit={args.limit})")
    print(f"Will take approx.: {time_to_process} (with sleeptime={args.sleep})")

    processed_count = 0
    while True:
        item = database.get_item_to_process()

        if not item:
            print(f"""No more items with status TODO in '{db_conf["table"]}'.""")
            break

        process_item(item, database, args.reason)
        processed_count += 1

        if args.limit and processed_count >= args.limit:
            print("Stopping because limit has been reached...")
            break

        time.sleep(args.sleep)

    print(f"Processed {processed_count} item(s).")


if __name__ == "__main__":
    main()
