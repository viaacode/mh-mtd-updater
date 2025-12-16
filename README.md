# MediaHaven Metadata Updater

Python service to add or update and correct metadata in MediaHaven.

This service:

* selects records in a database or reads lines from a CSV
* requests the item's metadata from MediaHaven,
* corrects the metadata,
* adds or updates metadata when these updates are provided.

It is really nothing more then a wrapper around the `meemoo-mh-mtd-lib`.

## Prerequisites

* Python 3.10+
* Access to the meemoo PyPI (VPN required)

## Installation

1. Clone this repository and change into the new dir:

```bash
git clone git@github.com:viaacode/mh-mtd-updater.git
cd mh-mtd-updater
```

2. Init and activate a  virtual env:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Or using `uv`:

```bash
uv venv .venv
source .venv/bin/activate
```

3. Install:

```bash
(.venv) python -m pip install . \
    --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple \
    --trusted-host do-prd-mvn-01.do.viaa.be
```

Or using `uv`:

```bash
(.venv) uv sync --extra-index-url http://do-prd-mvn-01.do.viaa.be:8081/repository/pypi-all/simple
```

## Usage

There are currently two different CLI-interfaces:

1. one that operates with a DB as input (for long running bulk-updates) and
2. one that operates with a CSV as input (for shorter bulk-update runs).

When using the DB as input, status about the transformations and the update are
stored in the database. When using a CSV as input a report is generated
containing the feedback about the update-run.

1. Fill in and export the environment variables in `.env`:

```bash
(.venv) export $(grep -v '^#' .env | xargs)
```

Check usage:

- for a database-driven update-run:

```bash
(.venv) python db.py -h

usage: db.py [-h] -r REASON [-n LIMIT] [-s SLEEP]

Python service to add or update and correct metadata in MediaHaven.

options:
  -h, --help            show this help message and exit
  -r REASON, --reason REASON
                        The reason to be provided for the updates that will be
                        performed. Usually a reference to a Jira-ticket.
  -n LIMIT, --limit LIMIT
                        Number of items to process (optional)
  -s SLEEP, --sleep SLEEP
                        Number of seconds to wait between each item (optional: defaults to 0)
```

- for a CSV-driven update-run:

```bash
(.venv) python csv.py -h

usage: csv.py [-h] -o OR_ID -r REASON [-d CSV_DELIMITER] [--dryrun | --no-dryrun] input_file

Python CLI interface to the `mh-mtd-updater`. Allows for bulk-metadate-updates
in MediaHaven via CSV-input while also validating or correcting (where
possible) MediaHaven-metadata.

positional arguments:
  input_file            Filepath to the CSV-file which contains the metadata-updates.

options:
  -h, --help            show this help message and exit
  -o OR_ID, --or_id OR_ID
                        Provide the OR-id of the partner for which these
                        updates need to be performed. (required)
  -r REASON, --reason REASON
                        Provide a reason for the update. Usually a reference to
                        an Jira-ticket. (required)
  -d CSV_DELIMITER, --csv-delimiter CSV_DELIMITER
                        Provide a custom delimiter to parse the CSV-file. (default: ',')
  --dryrun, --no-dryrun
                        Perform a dry-run. Use the `--no-dryrun` command line
                        argument to disable a dry-run, ie., to actually perform the update against
                        MediaHaven. (default: True)
```


2. Run with:

```bash
(.venv) python db.py --reason "JIRA-XXX"
```

or

```bash
(.venv) python cli.py /path/to/inputfile.csv --or_id "OR-a1b2c3d" --reason "JIRA-XXX"
```
