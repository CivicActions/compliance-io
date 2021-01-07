# compliance-io

Python library for reading/writing compliance as code

## Usage

### OpenControl

```
from compliance_io import opencontrol

oc = opencontrol.load("path/to/opencontrol.yaml")
print(oc.name)

# modify oc and save

oc.save()

```

### OSCAL

```
from compliance_io import oscal

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
