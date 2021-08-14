from complianceio.oscal.oscal import BackMatter
from complianceio.oscal.oscal import Metadata
from complianceio.oscal.oscal import Party
from complianceio.oscal.oscal import Resource
from complianceio.oscal.oscal import Role
from complianceio.oscal.ssp import ByComponent
from complianceio.oscal.ssp import Component
from complianceio.oscal.ssp import ControlImplementation
from complianceio.oscal.ssp import Impact
from complianceio.oscal.ssp import ImplementedRequirement
from complianceio.oscal.ssp import ImportProfile
from complianceio.oscal.ssp import InformationType
from complianceio.oscal.ssp import Model
from complianceio.oscal.ssp import NetworkDiagram
from complianceio.oscal.ssp import SecurityImpactLevel
from complianceio.oscal.ssp import SetParameter
from complianceio.oscal.ssp import Statement
from complianceio.oscal.ssp import SystemCharacteristics
from complianceio.oscal.ssp import SystemId
from complianceio.oscal.ssp import SystemImplementation
from complianceio.oscal.ssp import SystemInformation
from complianceio.oscal.ssp import SystemSecurityPlan
from complianceio.oscal.ssp import SystemStatus
from complianceio.oscal.ssp import User


def test_ssp():
    md = Metadata(title="System Security Plan", version="1.2.3")
    ciso = Role(id="security-operations", title="CISO")
    fen = Party(type="person", name="Fen", email_addresses=["fen@civicactions.com"])
    tom = Party(type="person", name="Tom", email_addresses=["tom@civicactions.com"])
    md.parties = [fen, tom]
    md.roles = [ciso]
    md.responsible_parties

    ip = ImportProfile(href="https://nist.gov/800-53-rev4")
    ssec = SecurityImpactLevel(
        security_objective_confidentiality="high",
        security_objective_availability="low",
        security_objective_integrity="low",
    )
    itype = InformationType(
        title="Information Type",
        description="Information Type",
        confidentiality_impact=Impact(base="low"),
        integrity_impact=Impact(base="moderate"),
        availability_impact=Impact(base="low"),
    )
    sinfo = SystemInformation(information_types=[itype])
    sids = SystemId(id="test")
    ab = NetworkDiagram(description="Authorization Boundary")
    sc = SystemCharacteristics(
        system_ids=[sids],
        system_name="ODP",
        description="ODP Description",
        system_information=sinfo,
        security_sensitivity_level="moderate",
        security_impact_level=ssec,
        authorization_boundary=ab,
        status=SystemStatus(state="operational"),
    )
    si = SystemImplementation()
    this_system = Component(
        title="This System",
        type="this-system",
        description="This System",
        status=SystemStatus(state="operational"),
    )
    drupal = Component(
        title="Drupal",
        type="software",
        description="Drupal",
        status=SystemStatus(state="operational"),
    )
    user = User(short_name="User Short Name")
    si.add_component(this_system).add_component(drupal)
    si.users = [user]
    ir = ImplementedRequirement(control_id="AC-1", description="Access Control")
    ir.add_by_component(
        ByComponent(component_uuid=drupal.uuid, description="AC-1 provided by Drupal")
    )
    ir.add_parameter(SetParameter(param_id="AC-1_prm_1", values=["every 30 days"]))
    ir.add_statement(
        Statement(statement_id="AC-1_smt").add_by_component(
            ByComponent(
                component_uuid=drupal.uuid, description="AC-1 provided by Drupal"
            )
        )
    )
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
    root = Model(system_security_plan=ssp)
    assert root is not None
