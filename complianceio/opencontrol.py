"""
This module provides classes to read, write, and create
OpenControl repositories.
"""
from enum import Enum
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import rtyaml
from blinker import signal
from pydantic import BaseModel
from pydantic import PrivateAttr
from slugify import slugify

OPENCONTROL_SCHEMA_VERSION = "1.0.0"
COMPONENT_SCHEMA_VERSION = "3.1.0"

FILE_SIGNAL = signal("opencontrol_file_operation")


class OpenControlElement(BaseModel):
    def new_relative_path(self):
        assert False

    def storage_path(self, root_dir=None):
        if hasattr(self, "_file"):
            p = Path(self._file)
        else:
            p = self.new_relative_path()
        if root_dir:
            return root_dir / p
        else:
            return p


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


class CoveredBy(OpenControlElement):
    verification_key: str
    system_key: Optional[str]
    component_key: Optional[str]


class Control(OpenControlElement):
    control_key: str
    standard_key: str
    covered_by: Optional[List[CoveredBy]]
    narrative: Optional[List[Statement]]
    references: Optional[List[Reference]]
    implementation_statuses: Optional[Set[ImplementationStatusEnum]]
    control_origins: Optional[List[str]]  # TODO (enum)
    parameters: Optional[List[Parameter]]
    _file: str = PrivateAttr()


class Metadata(OpenControlElement):
    description: Optional[str]
    maintainers: Optional[List[str]]


class Verification(OpenControlElement):
    key: str
    name: str
    type: str
    path: Optional[str]
    description: Optional[str]
    test_passed: Optional[bool]
    last_run: Optional[str]


class Component(OpenControlElement):
    schema_version: str = COMPONENT_SCHEMA_VERSION
    name: str
    key: Optional[str]
    system: Optional[str]
    documentation_complete: Optional[bool]
    responsible_role: Optional[str]
    references: Optional[List[Reference]]
    verifications: Optional[List[Verification]]
    satisfies: Optional[List[Control]]

    _file: str = PrivateAttr()

    def new_relative_path(self):
        return Path("components") / Path(self.name) / Path("component.yaml")


class StandardControl(OpenControlElement):
    family: str
    name: str
    description: str


class Standard(OpenControlElement):
    name: str
    license: Optional[str]
    source: Optional[str]
    controls: Dict[str, StandardControl]
    _file: str = PrivateAttr()

    def new_relative_path(self):
        return Path("standards") / Path(slugify(self.name)).with_suffix(".yaml")


class Certification(OpenControlElement):
    name: str
    standards: Dict[str, Dict[str, dict]]
    _file: str = PrivateAttr()

    def standard_keys(self):
        return set(self.standards.keys())

    def controls(self, standard):
        return set(self.standards[standard].keys())

    def new_relative_path(self):
        return Path("certifications") / Path(slugify(self.name)).with_suffix(".yaml")


class System(OpenControlElement):
    pass


class Dependency(OpenControlElement):
    url: str
    revision: str
    contextdir: Optional[str]


class OpenControl(OpenControlElement):
    """
    Container for OpenControl repository.
    """

    schema_version: str = OPENCONTROL_SCHEMA_VERSION
    name: str
    metadata: Optional[Metadata]
    components: List[Component] = []
    standards: Dict[str, Standard] = {}
    systems: List[System] = []
    certifications: List[Certification] = []

    _root_dir: str = PrivateAttr()

    def new_relative_path(self):
        return Path("opencontrol.yaml")

    @classmethod
    def debug_file(cls, sender, **kwargs):
        print(
            "Loaded file" if kwargs["operation"] == "read" else "Wrote file",
            kwargs["path"],
        )

    @classmethod
    def load(cls, path: str, debug=True):
        """
        Load an OpenControl repository from a path to the
        `opencontrol.yaml` file.
        """

        p = Path(path)
        if debug:
            FILE_SIGNAL.connect(OpenControl.debug_file)

        with p.open() as f:
            root = rtyaml.load(f)
            FILE_SIGNAL.send(cls, operation="read", path=p)
            oc = OpenControlYaml.parse_obj(root).resolve(p.parent)
            oc._root_dir = p.parent
            return oc

    def save(self):
        "Write back an OpenControl repo to where it was loaded"
        root_dir = self._root_dir
        root = self.dict(exclude={"standards", "components", "systems"})
        root["certifications"] = [
            str(cert.storage_path(root_dir)) for cert in self.certifications
        ]
        root["standards"] = [
            str(std.storage_path(root_dir)) for std in self.standards.values()
        ]
        root["components"] = [str(c.storage_path(root_dir)) for c in self.components]
        print(rtyaml.dump(root))

    def save_as(self, base_dir):
        "Save an OpenControl repo in a new location"
        root = self.dict(exclude={"standards", "components", "systems"})
        root["certifications"] = []
        for cert in self.certifications:
            cert_storage = cert.storage_path(base_dir)
            cert_storage.parent.mkdir(parents=True, exist_ok=True)
            with cert_storage.open("w") as cert_file:
                cert_file.write(rtyaml.dump(cert.dict()))
                FILE_SIGNAL.send(self, operation="write", path=str(cert_storage))
                root["certifications"].append(str(cert.storage_path()))

        root["standards"] = []
        for std in self.standards.values():
            std_storage = std.storage_path(base_dir)
            std_storage.parent.mkdir(parents=True, exist_ok=True)
            with std_storage.open("w") as std_file:
                std_file.write(rtyaml.dump(std.dict()))
                FILE_SIGNAL.send(self, operation="write", path=str(std_storage))
                root["standards"].append(str(std.storage_path()))

        root["components"] = [str(c.storage_path()) for c in self.components]

        root_storage = self.storage_path(base_dir)
        with root_storage.open("w") as root_file:
            root_file.write(rtyaml.dump(root))
            FILE_SIGNAL.send(self, operation="write", path=root_storage)

        for c in self.components:
            component_path = c.storage_path(base_dir)
            component_path.parent.mkdir(parents=True, exist_ok=True)

            with component_path.open("w") as component_file:
                component_file.write(rtyaml.dump(c.dict()))
            FILE_SIGNAL.send(self, operation="write", path=component_path)


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
    metadata: Optional[Metadata]
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
                component._file = component_path.relative_to(relative_to)
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
                    obj = rtyaml.load(f)
                    family = FenFamily.parse_obj(obj)
                    for satisfaction in family.satisfies:
                        satisfaction._file = satisfier_path
                        resolved_satisfiers.append(satisfaction)

        c = Component(
            schema_version=fc.schema_version,
            name=fc.name,
            satisfies=resolved_satisfiers,
        )
        return c

    def resolve_component(self, component_path):
        with component_path.open() as f:
            obj = rtyaml.load(f)
            if self._is_fen(obj):
                return self.resolve_fen_component(obj, component_path)
            else:
                comp = Component.parse_obj(obj)
            return comp

    def resolve_certifications(self, relative_to):
        certifications = []
        for certification in self.certifications:
            certification_path = relative_to / certification
            if certification_path.is_file():
                with certification_path.open() as f:
                    obj = rtyaml.load(f)
                    FILE_SIGNAL.send(self, operation="read", path=certification_path)
                    cert = Certification.parse_obj(obj)
                    cert._file = certification
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
                    obj = rtyaml.load(f)
                    FILE_SIGNAL.send(self, operation="read", path=standard_path)
                    name = obj.pop("name")

                    # TODO: source and license are not in the spec?

                    source = obj.pop("source", "")
                    license = obj.pop("license", "")

                    controls = {
                        control: StandardControl.parse_obj(desc)
                        for control, desc in obj.items()
                        if "family" in desc
                    }

                    std = Standard(
                        name=name, controls=controls, source=source, license=license
                    )
                    std._file = standard
                    standards[name] = std
            else:
                raise Exception(f"Can't open standard file '{standard_path}'")
        return standards

    def resolve_dependencies(self, relative_to):
        pass


def load(f, debug=False):
    return OpenControl.load(f, debug)
