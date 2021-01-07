from typing import Dict
from typing import List
from typing import Optional
from uuid import UUID
from uuid import uuid4

from component import ImplementedRequirement
from component import Statement
from oscal import Annotation
from oscal import BackMatter
from oscal import Link
from oscal import MarkupLine
from oscal import MarkupMultiLine
from oscal import Metadata
from oscal import NCName
from oscal import OSCALElement
from oscal import Property
from oscal import Resource
from pydantic import Field


class ImportProfile(OSCALElement):
    href: str  # really URI
    remarks: Optional[str]


class Impact(OSCALElement):
    base: str
    selected: Optional[str]
    adjustment_justification: Optional[MarkupMultiLine]

    class Config:
        fields = {"adjustment_justification": "adjustment-justification"}
        allow_population_by_field_name = True


class Categorization(OSCALElement):
    system: str  # really URI
    information_type_ids: Optional[List[str]]

    class Config:
        fields = {"information_type_ids": "information-type-ids"}
        allow_population_by_field_name = True


class InformationType(OSCALElement):
    uuid: Optional[UUID]
    title: str
    description: MarkupMultiLine
    categorizations: Optional[List[Categorization]]
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    confidential_impact: Impact
    integrity_impact: Impact
    availability_impact: Impact
    links: Optional[List[Link]]

    class Config:
        fields = {
            "confidential_impact": "confidential-impact",
            "integrity_impact": "integrity-impact",
            "availability_impact": "availability-impact",
        }
        allow_population_by_field_name = True


class SystemInformation(OSCALElement):
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    information_types: List[InformationType] = []
    annotations: Optional[List[Annotation]]

    class Config:
        fields = {"information_types": "information-types"}
        allow_population_by_field_name = True


class Diagram(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    description: Optional[MarkupMultiLine]
    caption: Optional[MarkupLine]
    remarks: Optional[MarkupMultiLine]

    class Config:
        container_assigned = ["uuid"]


class AuthorizationBoundary(OSCALElement):
    description: MarkupMultiLine
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    diagrams: Dict[str, Diagram] = {}
    remarks: Optional[MarkupMultiLine]

    class Config:
        exclude_if_false = ["diagrams"]


class SecurityImpactLevel(OSCALElement):
    security_objective_confidentiality: str
    security_objective_integrity: str
    security_objective_availability: str

    class Config:
        fields = {
            "security_objective_confidentiality": "security-objective-confidentiality",
            "security_objective_integrity": "security-objective-integrity",
            "security_objective_availability": "security-objective-availability",
        }
        allow_population_by_field_name = True


class SystemStatus(OSCALElement):
    state: str
    remarks: Optional[MarkupMultiLine]


class SystemCharacteristics(OSCALElement):
    system_name: str
    system_name_short: Optional[str]
    description: MarkupMultiLine
    security_sensitivity_level: str
    security_impact_level: SecurityImpactLevel
    system_information: SystemInformation
    authorization_boundary: AuthorizationBoundary
    status: SystemStatus
    props: Optional[List[Property]]
    links: Optional[List[Link]]
    annotations: Optional[List[Annotation]]

    # missing lots

    class Config:
        fields = {
            "authorization_boundary": "authorization-boundary",
            "system_name": "system-name",
            "system_name_short": "system-name-short",
            "security_sensitivity_level": "security-sensitivity-level",
            "security_impact_level": "security-impact-level",
            "system_information": "system-information",
        }
        allow_population_by_field_name = True


class User(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    title: Optional[MarkupLine]
    short_name: Optional[str]
    description: Optional[MarkupMultiLine]
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    role_ids: Optional[List[NCName]]
    authorized_privileges: Optional[List[str]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {
            "authorized_privileges": "authorized-privileges",
            "role_ids": "role-ids",
        }
        container_assigned = ["uuid"]
        allow_population_by_field_name = True


class Protocol(OSCALElement):
    pass


class Role(OSCALElement):
    pass


class SystemComponent(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    type: Optional[str]
    title: MarkupLine
    description: MarkupMultiLine
    status: SystemStatus
    purpose: Optional[MarkupLine]
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    responsible_roles: Dict[str, Role] = {}
    protocols: Optional[List[Protocol]]
    remarks: Optional[MarkupMultiLine]

    class Config:
        fields = {"responsible_roles": "responsible-roles"}
        container_assigned = ["uuid"]
        allow_population_by_field_name = True
        exclude_if_false = ["responsible-roles"]


class InventoryItem(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    description: MarkupMultiLine
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]

    remarks: Optional[MarkupMultiLine]


class SystemImplementation(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    leveraged_authorizations: Optional[List[str]]
    users: Dict[str, User] = {}
    components: Dict[str, SystemComponent] = {}
    inventory_items: Optional[List[InventoryItem]]
    remarks: Optional[MarkupMultiLine]

    def add_component(self, component: SystemComponent):
        key = str(component.uuid)
        if key in self.components:
            raise KeyError(f"Component {key} already in SystemImplementation")
        self.components[key] = component
        return self

    class Config:
        fields = {
            "leveraged_authorizations": "leveraged-authorizations",
            "inventory_items": "inventory-items",
        }
        allow_population_by_field_name = True


class Inherited(OSCALElement):
    pass


class Satisfied(OSCALElement):
    pass


class ByComponent(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    component_uuid: UUID
    description: MarkupMultiLine
    props: Optional[List[Property]]
    annotations: Optional[List[Annotation]]
    links: Optional[List[Link]]
    inherited: Optional[List[Inherited]]
    satisfied: Optional[List[Satisfied]]

    class Config:
        fields = {"component_uuid": "component-uuid"}
        container_assigned = ["component_uuid"]
        allow_population_by_field_name = True


class SetParameter(OSCALElement):
    param_id: NCName
    values: List[str]

    class Config:
        fields = {"param_id": "param-id"}
        allow_population_by_field_name = True


class SystemImplementedRequirement(ImplementedRequirement):
    by_components: Dict[str, ByComponent] = {}
    parameter_settings: Optional[List[SetParameter]]

    class Config:
        fields = {
            "by_components": "by-components",
            "parameter_settings": "parameter-settings",
        }
        allow_population_by_field_name = True
        exclude_if_false = ["by-components"]


class ControlImplementation(OSCALElement):
    description: MarkupMultiLine
    implemented_requirements: List[SystemImplementedRequirement]

    class Config:
        fields = {"implemented_requirements": "implemented-requirements"}
        allow_population_by_field_name = True


class SystemSecurityPlan(OSCALElement):
    uuid: UUID = Field(default_factory=uuid4)
    metadata: Metadata
    import_profile: ImportProfile
    system_characteristics: SystemCharacteristics
    system_implementation: SystemImplementation
    control_implementation: ControlImplementation
    back_matter: Optional[BackMatter]

    class Config:
        fields = {
            "import_profile": "import-profile",
            "system_characteristics": "system-characteristics",
            "system_implementation": "system-implementation",
            "control_implementation": "control-implementation",
            "back_matter": "back-matter",
        }
        allow_population_by_field_name = True


class SystemSecurityPlanRoot(OSCALElement):
    system_security_plan: SystemSecurityPlan

    class Config:
        fields = {"system_security_plan": "system-security-plan"}
        allow_population_by_field_name = True

    def json(self, **kwargs):
        if "by_alias" in kwargs:
            kwargs.pop("by_alias")
        if "exclude_none" in kwargs:
            kwargs.pop("exclude_none")

        return super().json(by_alias=True, exclude_none=True, **kwargs)


class OSCALSystemSecurityPlanJson(SystemSecurityPlanRoot):
    def load(self, f):
        return SystemSecurityPlanRoot()

    def save_as(self, f):
        pass


def main():
    md = Metadata(title="System Security Plan", version="1.2.3")
    ip = ImportProfile(href="https://nist.gov/800-53-rev4")
    ssec = SecurityImpactLevel(
        security_objective_confidentiality="high",
        security_objective_availability="low",
        security_objective_integrity="low",
    )
    itype = InformationType(
        title="Information Type",
        description="Information Type",
        confidential_impact=Impact(base="low"),
        integrity_impact=Impact(base="moderate"),
        availability_impact=Impact(base="low"),
    )
    sinfo = SystemInformation(information_types=[itype])
    ab = AuthorizationBoundary(description="Authorization Boundary")
    sc = SystemCharacteristics(
        system_name="ODP",
        description="ODP Description",
        system_information=sinfo,
        security_sensitivity_level="moderate",
        security_impact_level=ssec,
        authorization_boundary=ab,
        status=SystemStatus(state="operational"),
    )
    si = SystemImplementation()
    si.add_component(
        SystemComponent(
            title="This System",
            type="this-system",
            description="This System",
            status=SystemStatus(state="operational"),
        )
    )
    ir = SystemImplementedRequirement(control_id="AC-1", description="Access Control")
    ir.parameter_settings = [
        SetParameter(param_id="AC-1_prm_1", values=["every 30 days"])
    ]
    ir.add_statement(Statement(statement_id="AC-1_smt"))

    ci = ControlImplementation(
        description="Our requirements", implemented_requirements=[ir]
    )
    bm = BackMatter(resources=[Resource(title="Test Resource")])

    ssp = SystemSecurityPlan(
        metadata=md,
        import_profile=ip,
        system_characteristics=sc,
        system_implementation=si,
        control_implementation=ci,
        back_matter=bm,
    )
    root = SystemSecurityPlanRoot(system_security_plan=ssp)

    print(root.json(indent=2))


if __name__ == "__main__":
    main()
