import pydantic
import pytest
import rtyaml

from complianceio import opencontrol


def test_control_covered_by():
    "Test deserialization of control containing a covered by"

    data = """
    control_key: AC-01
    standard_key: NIST-800-53-rev4
    covered_by:
      - verification_key: Configuration
        component_key: Drupal
      - verification_key: Inspec
    """

    obj = rtyaml.load(data)
    control = opencontrol.Control.parse_obj(obj)
    assert len(control.covered_by) == 2
    assert control.covered_by[0].verification_key == "Configuration"
    assert control.covered_by[0].component_key == "Drupal"
    assert control.covered_by[1].verification_key == "Inspec"


def test_invliad_control_covered_by():
    "Test deserialization of control containing an invalid covered by"

    # missing required verification key

    data = """
    control_key: AC-01
    standard_key: NIST-800-53-rev4
    covered_by:
      - verification_key: Configuration
        component_key: Drupal
      - component_key: AWS
    """

    obj = rtyaml.load(data)
    with pytest.raises(pydantic.ValidationError):
        opencontrol.Control.parse_obj(obj)
