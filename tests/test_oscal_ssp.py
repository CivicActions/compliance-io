from compliance_io.oscal.oscal import BackMatter
from compliance_io.oscal.oscal import Metadata
from compliance_io.oscal.oscal import Party
from compliance_io.oscal.oscal import Resource
from compliance_io.oscal.oscal import Role
from compliance_io.oscal.ssp import AuthorizationBoundary
from compliance_io.oscal.ssp import ByComponent
from compliance_io.oscal.ssp import Component
from compliance_io.oscal.ssp import ControlImplementation
from compliance_io.oscal.ssp import Impact
from compliance_io.oscal.ssp import ImplementedRequirement
from compliance_io.oscal.ssp import ImportProfile
from compliance_io.oscal.ssp import InformationType
from compliance_io.oscal.ssp import Model
from compliance_io.oscal.ssp import SecurityImpactLevel
from compliance_io.oscal.ssp import SetParameter
from compliance_io.oscal.ssp import Statement
from compliance_io.oscal.ssp import SystemCharacteristics
from compliance_io.oscal.ssp import SystemImplementation
from compliance_io.oscal.ssp import SystemInformation
from compliance_io.oscal.ssp import SystemSecurityPlan
from compliance_io.oscal.ssp import SystemStatus


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
    si.add_component(this_system).add_component(drupal)
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
