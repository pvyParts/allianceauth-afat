# Alliance Auth AFAT - Another Fleet Activity Tracker

[![Version](https://img.shields.io/pypi/v/allianceauth-afat?label=release)](https://pypi.org/project/allianceauth-afat/)
[![License](https://img.shields.io/badge/license-GPLv3-green)](https://pypi.org/project/allianceauth-afat/)
[![Python](https://img.shields.io/pypi/pyversions/allianceauth-afat)](https://pypi.org/project/allianceauth-afat/)
[![Django](https://img.shields.io/pypi/djversions/allianceauth-afat?label=django)](https://pypi.org/project/allianceauth-afat/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/allianceauth-afat)](https://pypi.org/project/allianceauth-afat/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](http://black.readthedocs.io/en/latest/)

An Improved FAT/PAP System for
[Alliance Auth](https://gitlab.com/allianceauth/allianceauth).

AFAT is a privately maintained whitelabel of ImicusFAT. The only reason AFAT exists
is because I don't like having an alliance internal meme as a name for a module in
my Auth system. Nothing else ...


## Features and highlights
- FATLink Creation and Population from ESI
- Fleet Type Classification (can be added in the Admin Menu)
- Graphical Statistics Views
- Many Core Functionality Improvements and Fixes

AFAT will work alongside the built-in native FAT System, bFAT and ImicusFAT.
However, data does not share, but you can migrate their data to AFAT, for more
information see below.


## Contents

- [Installation](#installation)
- [Updating](#updating)
- [Data Migration](#data-migration)
    - [From Alliance Auth native FAT](#import-from-native-fat)
    - [From bFAT](#import-from-bfat)
    - [From ImicusFAT](#import-from-imicusfat)
- [Changelog](CHANGELOG.md)
- [Credits](#credits)


## Installation

### Important
This app is a plugin for Alliance Auth. If you don't have Alliance Auth running already,
please install it first before proceeding.
(see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html) for details)

**For users migrating from one of the other FAT systems,
please read the specific instructions FIRST.**

### Step 1 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation.
Then install the latest version:

```bash
pip install allianceauth-afat
```

### Step 2 - Update your AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'afat',` to `INSTALLED_APPS`
- Add the scheduled task so ESI links will be updated automagically

```python
# AFAT - https://github.com/ppfeufer/allianceauth-afat
CELERYBEAT_SCHEDULE["afat_update_esi_fatlinks"] = {
    "task": "afat.tasks.update_esi_fatlinks",
    "schedule": crontab(minute="*/1"),
}
```

### Step 3 - Finalize the installation

Run migrations & copy static files

```bash
python manage.py collectstatic
python manage.py migrate
```

Restart your supervisor services for AA.


## Updating

To update your existing installation of ImicusFAT, first enable your
virtual environment (venv) of your Alliance Auth installation.

```bash
pip install -U allianceauth-afat

python manage.py collectstatic
python manage.py migrate
```

Finally restart your supervisor services for AA


## Data Migration

Right after the **initial** installation and running migrations,
you can import the data from Alliance Auth's native FAT system,
from bFAT or from ImicusFAT if you have used one of these until now.

**!!IMPORTANT!!**

Only do this once and ONLY BEFORE you are using AFAT.
A later migration is **not** possible.


### Import from native FAT

```bash
python myauth/manage.py afat_import_from_allianceauth_fat
```

### Import from bFAT

```bash
python myauth/manage.py afat_import_from_bfat
```

### Import from ImicusFAT

```bash
python myauth/manage.py afat_import_from_imicusfat
```


## Credits
• AFAT • Privately maintained by @ppfeufer is a whitelabel of
[ImicusFAT](https://gitlab.com/evictus.iou/allianceauth-imicusfat) maintained
by @exiom with @Aproia and @ppfeufer • Based on
[allianceauth-bfat](https://gitlab.com/colcrunch/allianceauth-bfat) by @colcrunch •
