from complianceio.oscal.catalogio import Catalog

catalog = Catalog("tests/NIST_SP-800-53_rev5_test.json")


# Catalog
def test_load_catalog():
    """Test loading a Catalog"""
    assert isinstance(catalog, Catalog)


def test_catalog_title():
    """Get the Catalog title"""
    assert catalog.catalog_title == "NIST SP 800-53 Rev 5 Controls Test Catalog"


# Groups
def test_get_groups():
    """Get Catalog Groups as list"""
    groups = catalog.get_groups()
    assert isinstance(groups, list)
    assert len(groups) == 20


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


# Controls
def test_get_controls():
    """Test getting all controls"""
    controls = catalog.get_controls()
    assert len(controls) == 53
    assert controls[0].get("title") == "Policy and Procedures"


def test_get_control_by_id():
    """Get a control by the Control ID"""
    control = catalog.get_control_by_id("ac-2")
    assert control.get("title") == "Account Management"
    assert isinstance(control.get("params"), list)


def test_get_control_statement():
    """Get the control statement with placeholders"""
    control = catalog.get_control_by_id("ac-2")
    prose = catalog.get_control_statement(control)
    assert prose.startswith("a. Define and document the")


def test_get_controls_all():
    controls = catalog.get_controls_all()
    assert isinstance(controls, list)
    assert isinstance(controls[0], dict)


def test_get_controls_all_ids():
    controls = catalog.get_controls_all_ids()
    assert isinstance(controls, list)
    assert len(controls) == 186


def test_get_control_property_by_name():
    control = catalog.get_control_by_id("ac-2")
    prop = catalog.get_control_property_by_name(control, "label")
    assert prop == "AC-2"


def test_get_control_part_by_name():
    control = catalog.get_control_by_id("ac-2")
    part = catalog.get_control_part_by_name(control, "statement")
    assert isinstance(part, dict)


# Params
def test_get_control_parameter_label_by_id():
    control = catalog.get_control_by_id("ac-2")
    label = catalog.get_control_parameter_label_by_id(control, "ac-02_odp.01")
    assert label == "prerequisites and criteria"


def test_get_control_parameters():
    control = catalog.get_control_by_id("ac-2")
    params = catalog.get_control_parameters(control)
    assert isinstance(params, dict)
    assert "ac-02_odp.01" in params


def test_get_resource_by_uuid():
    resource = catalog.get_resource_by_uuid("91f992fb-f668-4c91-a50f-0f05b95ccee3")
    assert "uuid" in resource
    assert resource.get("title") == "32 CFR 2002"
