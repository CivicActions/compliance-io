from enum import Enum
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import click
import yaml
from pydantic import BaseModel
from pydantic import PrivateAttr
from yaml import CSafeLoader as SafeLoader

OPENCONTROL_SCHEMA_VERSION = "1.0.0"
COMPONENT_SCHEMA_VERSION = "3.1.0"


class OpenControlElement(BaseModel):
    pass


class Reference(OpenControlElement):
    name: str
    path: str  # TODO (url?)
    type: str  # TODO (enum)


class Statement(OpenControlElement):
    text: str
    key: Optional[str]


class Parameter(OpenControlElement):
    key: str
    text: str


class ImplementationStatusEnum(str, Enum):
    partial = "partial"
    complete = "complete"
    planned = "planned"
    none = "none"


class Control(OpenControlElement):
    control_key: str
    standard_key: str
    covered_by: Optional[List[str]]  # TODO (what?)
    narrative: Optional[List[Statement]]
    references: Optional[List[Reference]]
    implementation_statuses: Optional[Set[ImplementationStatusEnum]]
    control_origins: Optional[List[str]]  # TODO (enum)
    parameters: Optional[List[Parameter]]
    _file: str = PrivateAttr()


class Metadata(OpenControlElement):
    description: Optional[str]
    maintainers: Optional[List[str]]


class Component(OpenControlElement):
    schema_version: str = COMPONENT_SCHEMA_VERSION
    name: str
    key: Optional[str]
    system: Optional[str]
    documentation_complete: Optional[bool]
    responsible_role: Optional[str]
    references: Optional[List[Reference]]
    satisfies: Optional[List[Control]]
    _file: str = PrivateAttr()


class StandardControl(OpenControlElement):
    family: str
    name: str
    description: str


class Standard(OpenControlElement):
    name: str
    license: Optional[str]
    source: Optional[str]
    controls: Dict[str, StandardControl]


class Certification(OpenControlElement):
    name: str
    standards: Dict[str, Dict[str, dict]]

    def standard_keys(self):
        return set(self.standards.keys())

    def controls(self, standard):
        return set(self.standards[standard].keys())


class System(OpenControlElement):
    pass


class Dependency(OpenControlElement):
    url: str
    revision: str


class OpenControl(OpenControlElement):
    schema_version: str = OPENCONTROL_SCHEMA_VERSION
    name: str
    metadata: Metadata
    components: List[Component] = []
    standards: Dict[str, Standard] = {}
    systems: List[System] = []
    certifications: List[Certification] = []


class FenComponent(BaseModel):
    schema_version: str
    name: str
    satisfies: Optional[List[str]]


class FenFamily(BaseModel):
    schema_version: Optional[str]
    family: str
    satisfies: List[Control]


class OpenControlYaml(BaseModel):
    schema_version: str
    name: str
    metadata: Metadata
    components: Optional[List[str]]
    certifications: List[str] = []
    standards: List[str] = []
    systems: Optional[List[str]]
    dependencies: Optional[Dict[str, List[Dependency]]]

    def _component_path(self, component, relative_to):
        path = relative_to / component
        if path.is_dir():
            path = path / "component.yaml"
        return path

    def resolve(self, relative_to):
        resolved_components = self.resolve_components(relative_to)
        resolved_certifications = self.resolve_certifications(relative_to)
        resolved_standards = self.resolve_standards(relative_to)
        obj = OpenControl(
            schema_version=self.schema_version,
            name=self.name,
            metadata=self.metadata,
            components=resolved_components,
            certifications=resolved_certifications,
            standards=resolved_standards,
        )
        return obj

    def resolve_components(self, relative_to):
        resolved_components = []
        for component in self.components:
            component_path = self._component_path(component, relative_to)
            if component_path.is_file():
                component = self.resolve_component(component_path)
                resolved_components.append(component)
            else:
                msg = f"Can't open component file '{component_path}'"
                raise Exception(msg)
        return resolved_components

    def _is_fen(self, obj):
        satisfies = obj.get("satisfies", [])
        if isinstance(satisfies, list) and len(satisfies) > 0:
            return isinstance(satisfies[0], str)
        return False

    def resolve_fen_component(self, obj, component_path):
        fc = FenComponent.parse_obj(obj)
        resolved_satisfiers = []
        for satisfier in fc.satisfies:
            satisfier_path = component_path.parent / satisfier
            if satisfier_path.is_file():
                with satisfier_path.open() as f:
                    obj = yaml.load(f, Loader=SafeLoader)
                    family = FenFamily.parse_obj(obj)
                    for satisfaction in family.satisfies:
                        satisfaction._file = satisfier_path
                        resolved_satisfiers.append(satisfaction)

        c = Component(
            schema_version=fc.schema_version,
            name=fc.name,
            satisfies=resolved_satisfiers,
        )
        c._file = str(component_path)
        return c

    def resolve_component(self, component_path):
        with component_path.open() as f:
            obj = yaml.load(f, Loader=SafeLoader)
            if self._is_fen(obj):
                return self.resolve_fen_component(obj, component_path)
            else:
                comp = Component.parse_obj(obj)
            comp._file = str(component_path)
            return comp

    def resolve_certifications(self, relative_to):
        certifications = []
        for certification in self.certifications:
            certification_path = relative_to / certification
            if certification_path.is_file():
                with certification_path.open() as f:
                    obj = yaml.load(f, Loader=SafeLoader)
                    cert = Certification.parse_obj(obj)
                    print(f"Loaded certification {certification_path}")
                    certifications.append(cert)
            else:
                msg = f"Can't open certification file '{certification_path}'"
                raise Exception(msg)
        return certifications

    def resolve_standards(self, relative_to):
        standards = {}
        for standard in self.standards:
            standard_path = relative_to / standard
            if standard_path.is_file():
                with standard_path.open() as f:
                    obj = yaml.load(f, Loader=SafeLoader)
                    print(f"Loaded standard {standard_path}")

                    name = obj.pop("name")
                    if "source" in obj:
                        source = obj.pop("source")
                    if "license" in obj:
                        license = obj.pop("license")

                    controls = {
                        control: StandardControl.parse_obj(desc)
                        for control, desc in obj.items()
                        if "family" in desc
                    }

                    standard = Standard(
                        name=name, controls=controls, source=source, license=license
                    )
                    standards[name] = standard
            else:
                raise Exception(f"Can't open standard file '{standard_path}'")
        return standards

    def resolve_dependencies(self, relative_to):
        pass


def load(f):
    p = Path(f)
    with p.open() as f:
        root = yaml.load(f, Loader=SafeLoader)
    oc = OpenControlYaml.parse_obj(root)
    return oc.resolve(p.parent)


@click.command()
@click.argument("path", type=click.Path())
def main(path):
    oc = load(path)
    print(oc.metadata.description)
    print(len(oc.certifications), "certifications")
    for c in oc.certifications:
        print(" *", c.name)
        for s in c.standard_keys():
            print("    ", s, len(c.controls(s)), "controls")

    print(len(oc.standards), "standards")
    for s in oc.standards.values():
        print(" *", s.name, len(s.controls.keys()), "controls")
    print(len(oc.components), "components")
    for c in oc.components:
        print(" *", c.name, "from", c._file)
        print("   ", len(c.satisfies), "controls")


#        for c in c.satisfies:
#            print("    ", c.control_key, c._file)
if __name__ == "__main__":
    main()
