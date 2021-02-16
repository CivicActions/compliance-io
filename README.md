# compliance-io

Python library for reading/writing compliance as code

**Note**: this library should be considered *alpha*.  All APIs are
subject to change.

## Installation

```
pip install https://github.com/woodt/compliance-io.git#egg=complianceio
```

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

* `examples/oc_to_oscal_components.py`

  Take an OpenControl repository and extract the components
  as a JSON OSCAL component definition.

* `examples/defenestrate.py`

  Take an OpenControl repository that might be in "Fen" format and
  write it out using a more standard OpenControl layout.

* `examples/to_csv.py`

  Write out a CSV file of all controls and statements loaded from an
  OpenControl repository.

* `examples/to_jsonl.py`

  Write out a JSON-L file of all controls and statements loaded from
  an OpenControl repository.

## Development

This library uses [poetry](https://python-poetry.org/) to maintain
dependencies.  If you don't have Poetry installed, follow the
[installation instructions](https://python-poetry.org/docs/).

To install this package for development,

```sh
poetry install
```

To run tests,

```sh
poetry run python -m pytest
```

## License

GNU General Public License v3.0 or later. Some portions of this work
were produced under a Government contract and are licensed under the
terms of Creative Commons Zero v1.0 Universal.

SPDX-License-Identifier: `GPL-3.0-or-later`
