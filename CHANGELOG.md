# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [1.3.3] - 2020-11-28

### Fixed
- 'NoneType' object has no attribute 'character_name' (This happens when the creator of a FAT link for what ever reason lost his main char and prevents the FAT link list from being loaded.)

### Changed
- Reducing characters displayed on stats main view to only those with FATs


## [1.3.2] - 2020-11-23

### Changed
- couple of tweaks to templates and JS
- show only characters with FAT links in stats main view


## [1.3.1] - 2020-11-22

### Changed
- tables tweaked …
    - preventing DataTables from getting wider than their parent element
    - even/odd styles
    - text alignments


## [1.3.0] - 2020-11-19

### New Feature
- Import scripts for imports from Alliance Auth's FAT module as well as from bFAT and ImicusFAT. These imports can be done initially right after the first install of AFAT. Fiddling around with SQL to import is no linger needed with this.

### Added
- Filter to the Fat Links List view. You can now filter for Fleet Type and is a FAT link was created via ESI or not in the FAT links list.

### Changed
- FAT links information in FAT links list is now loaded via ajax. This means, especially for installations with a large number of FAT links, this page should be loaded considerably faster.
- Minimum required version of Alliance Auth set to 2.8.0

### Removed
- Support for Django 2


## [1.2.0] - 2020-10-19

### New
- Added a check to `Clickable FATLinks` to verify whether the character is actually online.

### Changed
- Workflow improvements for `ESI FATLinks`
- Show only chars with recent activity in "Recent Activity" view

### Fixed
- Added Average FATs to the monthly corp stats overview.
- Added "Basic Access" permission. This permission prevents unintended audience from accessing the module.

### Updating
**IMPORTANT**:
When updating to this version, you will need to give the state/group that should have access to the AFAT module the `afat|Alliance Auth AFAT|Can access the Alliance Auth AFAT module` permission. Without this permission, the user cannot see the link, open any statistics or register via clickable FATLinks.

To update your existing installation of AFAT, first enable your virtual environment (venv) of your Alliance Auth installation.

```bash
pip install -U allianceauth-afat

python manage.py collectstatic
python manage.py migrate
```

Finally restart your supervisor services for AA


## [1.1.0] - 2020-10-05

### Changes to the URL structure

#### Renamed URL parts
- `stats` to `statistic`
- `ally` to `alliance`
- `corp` to `corporation`
- `char` to `character`

#### Changed URL parts
- `month/year` to `year/month` (this is to enable us to have yearly statistics for certain views)


### Added / Changed behavior
- Added a year switch to main statistics view
- Added a year switch to corporation statistics view
- Added a year switch to alliance statistics view
- Changed the fatlink list to be restricted to a year
- Added year switch to fatlink list
- Added manual FAT log to admin page as read only


### Fixed
- Deleted FATs have not been logged


## [1.0.0] - 2020-09-28

### Added
- Marking fatlinks done via ESI as such in fatlink lists
- Filter to the admin backend
- Enable/Disable fleet types in admin view
- Some more information has been added to the admin view
- Better permission handling in templates

### Checked
- Django 3 compatibility (for AA 2.8.0 - https://gitlab.com/allianceauth/allianceauth/-/issues/1261)

### Changed
- Minimum required Alliance Auth version

### Fixed
- Fleet edit form
- Permissions to edit and delete fatlinks and fats


## [1.0.0a1] - 2020-09-22

### New
- Some more information has been added to the admin view
- Better permission handling in templates
- Django 3 compatibility (for AA 2.8.0 - https://gitlab.com/allianceauth/allianceauth/-/issues/1261)

### Changed
- Minimum required Alliance Auth version

### Fixed
- Permissions to edit and delete fatlinks and fats
- Templates prepared for Django 3 update in Alliance Auth


## [0.3.5] - 2020-09-11

### Added
- Month navigation to stats detail pages to review older stats

### Changed
- baseurl from `afat` to `fleetactivitytracking`
- hard coded links replaced

### Fixed
- an issue with "No Alliance" in stats view
- fleet types are now sorted alphabetically


## [0.3.5] - 2020-08-31

### Changes

- Can Only Create ESI Link if Fleet Boss
- Show Clickable Link Only When Still Valid
- Various Formatting Enhancements

### Removed

- Remaining Flat List Fragments

### Fixes

- ESI FAT Messages
- Various Formatting Enhancements
