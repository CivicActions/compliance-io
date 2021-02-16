# compliance-io

Python library for reading/writing compliance as code

**Note**: this library should be considered *alpha*.  APIs are subject
to change.

## Usage

### OpenControl

```
from complianceio import opencontrol

oc = opencontrol.load("path/to/opencontrol.yaml")
print(oc.name)

# modify oc and save

oc.save()

```

### OSCAL

```
from complianceio import oscal

components = oscal.component.load("path/to/components.json")
print(components.metadata.title)

ssp = oscal.ssp.load("path/to/ssp.json")
print(ssp.metadata.title)
```

## Examples

* `examples/defenestrate.py`

  Take an OpenControl repository that might be in "Fen" format and
  write it out using a more standard OpenControl layout.

* `examples/to_csv.py`

  Write out a CSV file of all controls and statements loaded from an
  OpenControl repository.

## License

GNU General Public License v3.0 or later. Some portions of this work
were produced under a Government contract and are licensed under the
terms of Creative Commons Zero v1.0 Universal.

SPDX-License-Identifier: `GPL-3.0-or-later`
