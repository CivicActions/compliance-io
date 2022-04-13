# Define OSCAL Component using Component Definition Model v1.0.0
# https://pages.nist.gov/OSCAL/reference/1.0.0/component-definition/json-outline/
from enum import Enum
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

from pydantic import Field

from .oscal import BackMatter
from .oscal import Link
from .oscal import MarkupLine
from .oscal import MarkupMultiLine
from .oscal import Metadata
from .oscal import NCName
from .oscal import OSCALElement
from .oscal import Property
from .oscal import ResponsibleRole
from .oscal import SetParameter


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
    statement_id: NCName
    uuid: UUID = Field(default_factory=uuid4)
    description: MarkupMultiLine = MarkupMultiLine("")
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    responsible_roles: Optional[List[ResponsibleRole]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {
            "statement_id": "statement-id",
            "responsible_roles": "responsible-roles",
        }
        allow_population_by_field_name = True


class ImplementedRequirement(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    control_id: str
    description: MarkupMultiLine
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    set_parameters: Optional[List[SetParameter]]
    responsible_roles: Optional[List[ResponsibleRole]]
    statements: Optional[List[Statement]]
    remarks: Optional[MarkupMultiLine]

    def add_statement(self, statement: Statement):
        key = statement.statement_id
        if not self.statements:
            self.statements = []
        elif key in self.statements:
            raise KeyError(
                f"Statement {key} already in ImplementedRequirement"
                " for {self.control_id}"
            )
        self.statements.append(statement)
        return self

    def add_parameter(self, set_parameter: SetParameter):
        key = set_parameter.param_id
        if not self.set_parameters:
            self.set_parameters = []
        elif key in self.set_parameters:
            raise KeyError(
                f"SetParameter {key} already in ImplementedRequirement"
                " for {self.control_id}"
            )
        self.set_parameters.append(set_parameter)
        return self

    def add_property(self, property: Property):
        key = property.name
        if not self.props:
            self.props = []
        elif key in self.props:
            raise KeyError(
                f"Property {key} already in ImplementedRequirement"
                " for {self.control_id}"
            )
        self.props.append(property)
        return self

    class Config:
        fields = {
            "control_id": "control-id",
            "responsible_roles": "responsible-roles",
            "set_parameters": "set-parameters",
            "properties": "props"
            
        }
        allow_population_by_field_name = True
        exclude_if_false = ["statements", "responsible-roles", "set-parameters"]


class ControlImplementation(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    source: str
    description: MarkupMultiLine
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    implemented_requirements: List[ImplementedRequirement] = []

    class Config:
        fields = {"implemented_requirements": "implemented-requirements"}
        allow_population_by_field_name = True


class Protocol(OSCALElement):
    pass


class Component(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    type: ComponentTypeEnum = ComponentTypeEnum.software
    title: MarkupLine
    description: MarkupMultiLine
    purpose: Optional[MarkupLine]
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    responsible_roles: Optional[List[ResponsibleRole]]
    protocols: Optional[List[Protocol]]
    control_implementations: List[ControlImplementation] = []
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {
            "component_type": "component-type",
            "control_implementations": "control-implementations",
            "responsible_roles": "responsible-roles",
        }
        allow_population_by_field_name = True
        exclude_if_false = ["control-implementations"]


class IncorporatesComponent(OSCALElement):
    component_uuid: UUID
    description: str

    class Config:
        fields = {"component_uuid": "component-uuid"}


class Capability(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    name: str
    description: MarkupMultiLine
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    control_implementations: Optional[List[ControlImplementation]]
    incorporates_components: Optional[List[IncorporatesComponent]]

    class Config:
        fields = {
            "control_implementations": "control-implementations",
            "incorporates_components": "incorporates-components",
        }


class ImportComponentDefinition(OSCALElement):
    href: str  # really uri-reference


class ComponentDefinition(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    metadata: Metadata
    components: Optional[List[Component]]
    back_matter: Optional[BackMatter]
    capabilities: Optional[List[Capability]]
    import_component_definitions: Optional[List[ImportComponentDefinition]]

    def add_component(self, component: Component):
        key = str(component.uuid)
        # initialize optional component list
        if not self.components:
            self.components = []
        elif key in self.components:
            raise KeyError(f"Component {key} already in ComponentDefinition")
        self.components.append(component)
        return self

    def add_capability(self, capability: Capability):
        key = str(capability.uuid)
        # initialize optional capability list
        if not self.capabilities:
            self.capabilities = []
        elif key in self.capabilities:
            raise KeyError(f"Capability {key} already in ComponentDefinition")
        self.capabilities.append(capability)
        return self

    class Config:
        fields = {
            "back_matter": "back-matter",
            "import_component_definitions": "import-component-definitions",
        }
        allow_population_by_field_name = True
        exclude_if_false = ["components", "capabilities"]


class Model(OSCALElement):
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


class OSCALComponentJson(Model):
    def load(self, f):
        return Model()

    def save_as(self, f):
        pass


def main():
    md = Metadata(title="Component", version="1.2.3")
    cd = ComponentDefinition(metadata=md)
    c = Component(title="My Component", description="Description of my component")
    ci = ControlImplementation(description="800-53 controls", source="800-53")
    ir = ImplementedRequirement(control_id="ac-1", description="AC-1 statements")
    ir.add_statement(
        Statement(
            statement_id="ac-1_smt", description="Refers to AC-1 in its entirety."
        )
    )
    ir.add_statement(
        Statement(statement_id="ac-1_smt.a", description="Refers to part a of AC-1")
    )
    ir.add_statement(
        Statement(
            statement_id="ac-1_smt.a.1",
            description="Refers to item 1 of part a of AC-1",
        )
    )
    ci.implemented_requirements = [ir]
    c.control_implementations = [ci]
    cd.add_component(c)
    root = Model(component_definition=cd)
    print(root.json(indent=2))


if __name__ == "__main__":
    main()
