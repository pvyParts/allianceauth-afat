# Alliance Auth AFAT - Another Fleet Activity Tracker

[![Version](https://img.shields.io/pypi/v/allianceauth-afat?label=release)](https://pypi.org/project/allianceauth-afat/)
[![License](https://img.shields.io/badge/license-GPLv3-green)](https://pypi.org/project/allianceauth-afat/)
[![Python](https://img.shields.io/pypi/pyversions/allianceauth-afat)](https://pypi.org/project/allianceauth-afat/)
[![Django](https://img.shields.io/pypi/djversions/allianceauth-afat?label=django)](https://pypi.org/project/allianceauth-afat/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/allianceauth-afat)](https://pypi.org/project/allianceauth-afat/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](http://black.readthedocs.io/en/latest/)

An Improved FAT/PAP System for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth). 

AFAT is a privately maintained whitelabel of ImicusFAT. Updates will only be pushed when ImicusFAT get updates to keep on par with it.

### Feature Highlights/Differences
- FATLink Creation and Population from ESI
- Fleet Type Classification (can be added in the Admin Menu)
- Graphical Statistics Views
- Many Core Functionality Improvements and Fixes

AFAT will work alongside the built-in native FAT System, bFAT and ImicusFAT. However data does not share, but you can migrate their data to AFAT, for more information see below.

## Contents

- [Installation](#installation)
- [Updating](#updating)
- [Data Migration](#data-migration)
    - [From Alliance Auth native FAT](#from-alliance-auth-native-fat)
    - [From bFAT](#from-bfat)
    - [From ImicusFAT](#from-imicusfat)
- [Credits](#credits)

## Installation

### Important
This app is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html) for details)

**For users migrating from one of the other FAT systems, please read the specific instructions FIRST.**

### Step 1 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the latest version:

```bash
pip install allianceauth-afat
```

### Step 2 - Update your AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'afat',` to `INSTALLED_APPS`

### Step 3 - Finalize the installation

Run migrations & copy static files

```bash
python manage.py collectstatic
python manage.py migrate
```

Restart your supervisor services for AA.

## Updating

To update your existing installation of ImicusFAT, first enable your virtual environment (venv) of your Alliance Auth installation.

```bash
pip install -U allianceauth-afat

python manage.py collectstatic
python manage.py migrate
```

Finally restart your supervisor services for AA

## Data Migration

Right after the **initial** installation and running migrations, you can import the data from Alliance Auth's native FAT system, from bFAT or from ImicusFAT if you have used one of these until now.

**!!IMPORTANT!!**

Only do this once and ONLY BEFORE you are using AFAT. A later migration is **not** possible.

### From Alliance Auth native FAT

Before installation, temporarily comment out `allianceauth.fleetactivitytracking` in your AA settings (`local.py`) by doing:

- Modify `'allianceauth.fleetactivitytracking',` to `#'allianceauth.fleetactivitytracking',` under `INSTALLED_APPS`

And then continue installation as normal. You may undo this after successful installation.

#### Import from native FAT

To import your old FAT data from Alliance Auth's own FAT, you have to disable foreign key checks temporarily.


```
INSERT INTO afat_afat (id, `system`, `shiptype`, character_id, afatlink_id) 
SELECT id, `system`, `shiptype`, character_id, fatlink_id 
FROM fleetactivitytracking_fat;

INSERT INTO afat_afatlink (id, afattime, fleet, `hash`, creator_id) 
SELECT id, fatdatetime, fleet, `hash`, creator_id 
FROM fleetactivitytracking_fatlink;
```

### From bFAT

Before installation, temporarily comment out `bfat` in your AA settings (`local.py`) by doing:

- Modify `'bfat',` to `#'bfat',` under `INSTALLED_APPS`

And then continue installation as normal. You may undo this after successful installation.

#### Import from bFAT

To import your old FAT data from bFAT, you have to disable foreign key checks temporarily.

```
INSERT INTO afat_clickafatduration (id, duration, fleet_id)
SELECT id, duration, fleet_id
FROM bfat_clickfatduration;

INSERT INTO afat_afatdellog (id, deltype, `string`, remover_id)
SELECT id, deltype, `string`, remover_id
FROM bfat_dellog;

INSERT INTO afat_afat (id, `system`, `shiptype`, character_id, ifatlink_id)
SELECT id, `system`, `shiptype`, character_id, fatlink_id
FROM bfat_fat;

INSERT INTO afat_afatlink (id, ifattime, fleet, `hash`, creator_id)
SELECT id, fattime, fleet, hash, creator_id 
FROM bfat_fatlink;

INSERT INTO afat_manualafat (id, character_id, creator_id, ifatlink_id)
SELECT id, character_id, creator_id, fatlink_id
FROM bfat_manualfat;
```

### From ImicusFAT

Before installation, temporarily comment out `imicusfat` in your AA settings (`local.py`) by doing:

- Modify `'imicusfat',` to `#'imicusfat',` under `INSTALLED_APPS`

And then continue installation as normal. You may undo this after successful installation.

#### Import from ImicusFAT

To import your old FAT data from ImicusFAT, you have to disable foreign key checks temporarily.

```
INSERT INTO afat_afat (id, `system`, `shiptype`, character_id, afatlink_id, deleted_at)
SELECT id, `system`, `shiptype`, character_id, ifatlink_id, deleted_at
FROM imicusfat_ifat;

INSERT INTO afat_afatdellog (id, deltype, `string`, remover_id)
SELECT id, deltype, `string`, remover_id
FROM imicusfat_dellog;

INSERT INTO afat_afatlink (id, afattime, fleet, `hash`, creator_id, creator_id, deleted_at, link_type_id)
SELECT id, afattime, fleet, `hash`, creator_id, creator_id, deleted_at, link_type_id
FROM imicusfat_ifatlink;

INSERT INTO afat_afatlinktype (id, `name`, deleted_at)
SELECT id, `name`, deleted_at
FROM imicusfat_ifatlinktype;

INSERT INTO afat_clickafatduration (id, duration, fleet_id)
SELECT id, duration, fleet_id
FROM imicusfat_clickifatduration;

INSERT INTO afat_manualafat (id, character_id, creator_id, afatlink_id)
SELECT id, character_id, creator_id, ifatlink_id
FROM imicusfat_manualifat;
```

## Credits
• AFAT • Privately maintained by @ppfeufer is a whitelabel of [ImicusFAT](https://gitlab.com/evictus.iou/allianceauth-imicusfat) maintained by @exiom with @Aproia and @ppfeufer • Based on [allianceauth-bfat](https://gitlab.com/colcrunch/allianceauth-bfat) by @colcrunch •
