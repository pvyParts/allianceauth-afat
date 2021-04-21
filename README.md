# Alliance Auth AFAT - Another Fleet Activity Tracker

[![Version](https://img.shields.io/pypi/v/allianceauth-afat?label=release)](https://pypi.org/project/allianceauth-afat/)
[![License](https://img.shields.io/badge/license-GPLv3-green)](https://pypi.org/project/allianceauth-afat/)
[![Python](https://img.shields.io/pypi/pyversions/allianceauth-afat)](https://pypi.org/project/allianceauth-afat/)
[![Django](https://img.shields.io/pypi/djversions/allianceauth-afat?label=django)](https://pypi.org/project/allianceauth-afat/)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)
[![PyPI Downloads](https://img.shields.io/pypi/dm/allianceauth-afat)](https://pypi.org/project/allianceauth-afat/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](http://black.readthedocs.io/en/latest/)
[![Discord](https://img.shields.io/discord/790364535294132234?label=discord)](https://discord.gg/zmh52wnfvM)

An Improved FAT/PAP System for
[Alliance Auth](https://gitlab.com/allianceauth/allianceauth).


## Contents

- [Features and highlights](#features-and-highlights)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Updating](#updating)
- [Data Migration](#data-migration)
  - [From Alliance Auth native FAT](#import-from-native-fat)
  - [From bFAT](#import-from-bfat)
  - [From ImicusFAT](#import-from-imicusfat)
- [Settings](#settings)
- [Permissions](#permissions)
- [Changelog](#changelog)
- [Credits](#credits)
- [Contributing](#contributing)


## Features and highlights

- Automatic tracking of participation on FAT links created via ESI
- Multiple ESI fleets (with your alts)
- Manually end ESI tracking per fleet
- Fleet type classification (can be added in the admin backend)
- Ship type overview per FAT link
- Graphical statistics views
- Custom module name
- Re-open FAT link if the FAT link has expired and is withing the defined grace time
  (only for clickable FAT links)
- Manually add pilots to FAT links, in case they missed to click the link
- Log for the following actions (Logs are kept for a certain time, 60 days per default):
  - Create FAT link
  - Change FAT link
  - Remove FAT link
  - Re-open FAT link
  - Manually add pilot to FAT link
  - Remove pilot from FAT link

AFAT will work alongside the built-in native FAT System, bFAT and ImicusFAT.
However, data does not share, but you can migrate their data to AFAT, for more
information see below.

## Screenshots

### Dashboard
![AFAT Dashboard](https://raw.githubusercontent.com/ppfeufer/allianceauth-afat/master/afat/docs/images/afat-dashboard.png)

### FAT link list
![AFAT FAT Link LIst](https://raw.githubusercontent.com/ppfeufer/allianceauth-afat/master/afat/docs/images/fatlink-list.png)

### FAT link details
![AFAT FAT Link Details](https://raw.githubusercontent.com/ppfeufer/allianceauth-afat/master/afat/docs/images/ship-type-overview.png)

### Add FAT link view for FCs
![AFAT Add FAT Link](https://raw.githubusercontent.com/ppfeufer/allianceauth-afat/master/afat/docs/images/add-fatlink.png)


## Installation

### Important
This app is a plugin for Alliance Auth. If you don't have Alliance Auth running already,
please install it first before proceeding. (see the official
[AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html)
for details)

**For users migrating from one of the other FAT systems, please read the specific
instructions FIRST.**

### Step 1 - Install the app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation.
Then install the latest version:

```bash
pip install allianceauth-afat
```

### Step 2 - Update your AA settings

Configure your AA settings in your `local.py` as follows:

- Add `'afat',` to `INSTALLED_APPS`
- Add the scheduled tasks

```python
# AFAT - https://github.com/ppfeufer/allianceauth-afat
CELERYBEAT_SCHEDULE["afat_update_esi_fatlinks"] = {
    "task": "afat.tasks.update_esi_fatlinks",
    "schedule": crontab(minute="*/1"),
}

CELERYBEAT_SCHEDULE["afat_logrotate"] = {
    "task": "afat.tasks.logrotate",
    "schedule": crontab(minute="0", hour="1"),
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

It is possible that some versions need some more changes. Always read the
[release notes](https://github.com/ppfeufer/allianceauth-afat/releases) to find out
more.


## Data Migration

Right after the **initial** installation and running migrations,
you can import the data from Alliance Auth's native FAT system,
from bFAT or from ImicusFAT if you have used one of these until now.

### Import from native FAT

To import from the native FAT module, simply run the following command:

```shell
python myauth/manage.py afat_import_from_allianceauth_fat
```

### Import from bFAT

To import from the bFAT module, simply run the following command:

```shell
python myauth/manage.py afat_import_from_bfat
```

### Import from ImicusFAT

First, you need to remove all "deleted" FAT links and FATs.

This step needs to be done, because we cannot import entries marked as "deleted" due
to the way Django is handling this, and some other entries might rely on them, so we
need to meke sure the "deleted" data doesn't cause any trouble. You don't need to
worry, you are not losing any data that is/was actively used besides what is already
marked as "deleted" and ImicusFAT is no longer working with it anyways and never did.

To do so, login to your mysql database and run the following commands:

```mysql
# de-activate foreign key checks
SET FOREIGN_KEY_CHECKS=0;

# remove all "deleted" FATs
delete from imicusfat_ifat where deleted_at is not null;

# remove all "deleted" fat link types
delete from imicusfat_ifatlinktype where deleted_at is not null;

# get all fatlink IDs of "deleted" fatlinks as comma separated list and make sure
# to have that in your notepad saved, you need this list for the next comamnds
select group_concat(id) from imicusfat_ifatlink where deleted_at is not null;

# now remove everything that is related to those IDs
# make sure to replace "id_list" with the comma separated
# list of IDs from the earlier command
delete from imicusfat_clickifatduration where fleet_id in (id_list);
delete from imicusfat_ifat where ifatlink_id in (id_list);
delete from imicusfat_ifatlink where id in(id_list);

# re-activate foreign key checks
SET FOREIGN_KEY_CHECKS=1;
```

Once done, start the actual import script like this:

```shell
python myauth/manage.py afat_import_from_imicusfat
```


## Settings

To customize the module, the following settings are available.

| Name                             | Description                                                     | Default Value           |
|:---------------------------------|:----------------------------------------------------------------|:------------------------|
| AFAT_APP_NAME                    | Custom application name, in case you'd like a different name  | Fleet Activity Tracking |
| AFAT_DEFAULT_FATLINK_EXPIRY_TIME | Default expiry time for clickable FAT links in Minutes | 60                      |
| AFAT_DEFAULT_FATLINK_REOPEN_GRACE_TIME | Time in minutes a FAT link can be re-opened after it has expired | 60                      |
| AFAT_DEFAULT_FATLINK_REOPEN_DURATION | Time in minutes a FAT link is re-opened | 60                      |
| AFAT_DEFAULT_LOG_DURATION | Time in days before log entries are being removed from the DB | 60                      |


## Permissions

| Name | Description | Notes |
|:-----|:------------|:-----|
| basic_access | Can access the AFAT module | Your line member probably want this permission, so they can see the module and click the FAT links they are given. They also can see their own statistics with this permission. |
| manage_afat | Can manage the AFAT module | Your Military lead probably should get this permission |
| add_fatlink | Can create FAT Links | Your regular FC or who ever should be able to add FAT links should have this permission |
| stats_corporation_own | Can see own corporation statistics |  |
| stats_corporation_other | Can see statistics of other corporations |  |
| logs_view | Can view the modules logs |  |


## Changelog

To keep track of all changes, please read the
[Changelog](https://github.com/ppfeufer/allianceauth-afat/blob/master/CHANGELOG.md).


## Contributing

You want to contribute to this project? That's cool!

Please make sure to read the [contribution guidelines](https://github.com/ppfeufer/allianceauth-afat/blob/master/CONTRIBUTING.md)
(I promise, it's not much, just some basics)


## Credits

AFAT is maintained by @ppfeufer is based on
[ImicusFAT](https://gitlab.com/evictus.iou/allianceauth-imicusfat) maintained
by @exiom with @Aproia and @ppfeufer (no longer) which is based on
[allianceauth-bfat](https://gitlab.com/colcrunch/allianceauth-bfat) by @colcrunch
