from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

from oscal import Annotation
from oscal import BackMatter
from oscal import Link
from oscal import MarkupLine
from oscal import MarkupMultiLine
from oscal import Metadata
from oscal import NCName
from oscal import OSCALElement
from oscal import Property
from pydantic import Field


class ComponentTypeEnum(str, Enum):
    software = "software"
    hardware = "hardware"
    service = "service"
    interconnection = "interconnection"
    policy = "policy"
    process = "process"
    procedure = "procedure"
    plan = "plan"
    guidance = "guidance"
    standard = "standard"
    validation = "validation"


class Statement(OSCALElement):
    statement_id: Optional[NCName]
    uuid: UUID = Field(default_factory=uuid4)
    description: MarkupMultiLine = MarkupMultiLine("")
    properties: Optional[List[Property]]
    remarks: Optional[MarkupMultiLine]
    links: Optional[List[Link]]

    class Config:
        container_assigned = ["statement_id"]


class ImplementedRequirement(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    control_id: str
    description: MarkupMultiLine
    statements: Dict[NCName, Statement] = {}
    remarks: Optional[MarkupMultiLine]
    properties: Optional[List[Property]]

    def add_statement(self, statement: Statement):
        key = statement.statement_id
        if key in self.statements:
            raise KeyError(
                f"Statement {key} already in ImplementedRequirement"
                " for {self.control_id}"
            )
        self.statements[NCName(statement.statement_id)] = statement
        return self

    class Config:
        fields = {"control_id": "control-id"}
        allow_population_by_field_name = True
        exclude_if_false = ["statements"]


class ControlImplementation(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    description: MarkupMultiLine
    source: str
    properties: Optional[List[Property]]
    implemented_requirements: List[ImplementedRequirement] = []
    links: Optional[List[Link]]

    class Config:
        fields = {"implemented_requirements": "implemented-requirements"}
        allow_population_by_field_name = True


class Component(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    name: str
    type: ComponentTypeEnum = ComponentTypeEnum.software
    title: MarkupLine
    description: MarkupMultiLine
    purpose: Optional[MarkupLine]
    props: Optional[List[Property]]
    control_implementations: List[ControlImplementation] = []
    links: Optional[List[Link]]
    annotations: Optional[List[Annotation]]

    class Config:
        fields = {
            "component_type": "component-type",
            "control_implementations": "control-implementations",
        }
        allow_population_by_field_name = True
        container_assigned = ["uuid"]
        exclude_if_false = ["control-implementations"]


class Capability(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    name: str
    description: MarkupMultiLine
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    annotations: Optional[List[Annotation]]


class ComponentDefinition(OSCALElement):
    metadata: Metadata
    components: Dict[str, Component] = {}
    back_matter: Optional[BackMatter]
    capabilities: Dict[str, Capability] = {}

    def add_component(self, component: Component):
        key = str(component.uuid)
        if key in self.components:
            raise KeyError(f"Component {key} already in ComponentDefinition")
        self.components[str(component.uuid)] = component
        return self

    def add_capability(self, capability: Capability):
        key = str(capability.uuid)
        if key in self.capabilities:
            raise KeyError(f"Capability {key} already in ComponentDefinition")
        self.capabilities[str(capability.uuid)] = capability
        return self

    class Config:
        fields = {"back_matter": "back-matter"}
        allow_population_by_field_name = True
        exclude_if_false = ["components", "capabilities"]


class ComponentRoot(OSCALElement):
    component_definition: ComponentDefinition

    class Config:
        fields = {"component_definition": "component-definition"}
        allow_population_by_field_name = True

    def json(self, **kwargs):
        if "by_alias" in kwargs:
            kwargs.pop("by_alias")
        if "exclude_none" in kwargs:
            kwargs.pop("exclude_none")

        return super().json(by_alias=True, exclude_none=True, **kwargs)


class OSCALComponentJson(ComponentRoot):
    def load(self, f):
        return ComponentRoot()

    def save_as(self, f):
        pass


def main():
    pass


if __name__ == "__main__":
    main()
