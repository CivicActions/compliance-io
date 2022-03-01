import pytest

from complianceio.oscal.catalogio import Catalog


catalog = Catalog('tests/NIST_SP-800-53_rev5_test.json')


def test_load_catalog():
    """Test loading a Catalog"""
    assert isinstance(catalog, Catalog)
 

def test_get_group_ids():
    """Test getting the Groups for a Catalog"""
    groups = catalog.get_group_ids()
    assert "ac" in groups

def test_get_group_title_by_id():
    """Test getting the Group title by ID"""
    title = catalog.get_group_title_by_id("ac")
    assert title == "Access Control"

def test_get_group_id_by_control_id():
    """Test getting a Group ID from a Control ID"""
    group_id = catalog.get_group_id_by_control_id("ac-1")
    assert group_id == "ac"

def test_get_controls():
    """Test getting all controls"""
    controls = catalog.get_controls()
    assert len(controls) == 2
    assert controls[0].get("title") == "Policy and Procedures"

def test_get_control_by_id():
    """Get a control by the Control ID"""
    control = catalog.get_control_by_id("ac-2")
    assert control.get("title") == "Account Management"
    assert isinstance(control.get("params"), list)


