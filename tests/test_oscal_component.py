from compliance_io.oscal import component
from compliance_io.oscal.oscal import Metadata
from compliance_io.oscal.oscal import oscalize_control_id


def test_component():
    md = Metadata(title="Some Components", version="1.2.3")
    cd = component.ComponentDefinition(metadata=md)
    c = component.Component(title="AWS", description="Amazon Web Services")
    c.control_implementations = []
    ci = component.ControlImplementation(
        description="NIST 800-53 Rev 4", source="nist_800_53_rev_4"
    )
    ci.implemented_requirements = []
    control_id = oscalize_control_id("AC-1")
    ir = component.ImplementedRequirement(
        control_id=control_id, description="AC-1 statements"
    )
    statement_id = "ac-1_smt"
    ir.add_statement(
        component.Statement(
            statement_id=statement_id, description="Here is how we implement AC-1"
        )
    )
    ci.implemented_requirements.append(ir)
    c.control_implementations.append(ci)
    cd.add_component(c)
    root = component.Model(component_definition=cd)
    assert root is not None
    print(root.json(indent=2))
