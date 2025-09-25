# MediaHaven Metadata Updater

Python service to add or update and correct metadata in MediaHaven.

This service:

* selects records in a database,
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

1. Fill in and export the environment variables in `.env`:

```bash
(.venv) export $(grep -v '^#' .env | xargs)
```

Check usage:

```bash
(.venv) python main.py -h

usage: main.py [-h] -r REASON [-n LIMIT] [-s SLEEP]

Python service to add or update and correct metadata in MediaHaven.

options:
  -h, --help            show this help message and exit
  -r REASON, --reason REASON
                        The reason to be provided for the updates that will be performed. Usually a reference to a Jira-ticket.
  -n LIMIT, --limit LIMIT
                        Number of items to process (optional)
  -s SLEEP, --sleep SLEEP
                        Number of seconds to wait between each item (optional: defaults to 0)
```

2. Run with:

```bash
(.venv) python main.py --reason "JIRA-XXX"
```

