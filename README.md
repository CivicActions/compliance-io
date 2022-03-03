# compliance-io

Python library for reading/writing compliance as code:

* Read / write OpenControl repositories
* Serialize OSCAL SSP and component definitions to JSON

Future work will add the abilities to:

* Serialize OSCAL SSP and component definitions to YAML
* Read OSCAL SSP and component definitions in JSON and YAML formats

**Note**: this library is incomplete and should be considered *alpha*.
All APIs are subject to change.

## Installation

Via pip:

```
pip install git+https://github.com/CivicActions/compliance-io.git@main#egg=complianceio
```

Via poetry:

```
poetry add git git+https://github.com/CivicActions/compliance-io.git#main
```

## Usage

### OpenControl

```python
from complianceio import opencontrol

oc = opencontrol.load("path/to/opencontrol.yaml")
print(oc.name)

# modify oc and save

oc.save()

```

### OSCAL

API exists for constructing OSCAL documents and serializing them
to JSON.  See `examples/oc_to_oscal_components.py`.

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

* `examples/catalog.py`

  Load an OSCAL catalog and get values from it.

## Development

Note that the branch of "truth" in this repo is called *main*.

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

To run examples,

```sh
poetry run python examples/to_csv.py ...
```

Alternatively, since `poetry install` will use an existing virtualenv
if activated, you are free to create your own virtualenv manually, run
`poetry install`, and then behave as usual in a Python virtualenv.

## Release process

Use `poetry version` to bump the version number.  E.g.,

```sh
poetry version patch
```

Use `poetry run attribution tag VERSION` to tag the release and
generate the CHANGELOG.md file.

Push to GitHub and merge to `main`.

## License

GNU General Public License v3.0 or later.

SPDX-License-Identifier: `GPL-3.0-or-later`
