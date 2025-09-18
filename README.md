# MediaHaven Metadata Updater

Python service to add or update and correct metadata in MediaHaven.

This service:

* selects records in a database,
* requests the item's metadata from MediaHaven,
* corrects the metadata,
* adds or updates metadata when these updates are provided.

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

And so on and so forth...

![TODO](https://img.shields.io/badge/TODO-009690)


