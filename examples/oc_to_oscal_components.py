from itertools import groupby
from pathlib import Path

import click

from complianceio import opencontrol
from complianceio.oscal import component
from complianceio.oscal.oscal import Metadata
from complianceio.oscal.oscal import oscalize_control_id


@click.command()
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
def main(source):
    """
    Read an OpenControl repo and emit an OSCAL component definition in JSON.
    """

    # FIXME: temporarily hardwired NIST 800-53 and dictionary keys
    source_uri_dict = {
        'NIST_SP80053r4': (
            'https://raw.githubusercontent.com/usnistgov/oscal-content/'
            'master/nist.gov/SP800-53/rev4/json/NIST_SP-800-53_rev4_catalog.json'
        ),
        'NIST_SP80053r5': (
            'https://raw.githubusercontent.com/usnistgov/oscal-content/'
            'master/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json'
        ),
        'CMS_ARS_3_1': (
            'https://raw.githubusercontent.com/CMSgov/ars-machine-readable'
            '/main/3.1/oscal/CMS_ARS_3_1_catalog.json'
        ),
        'CMS_ARS_5_0': (
            'https://raw.githubusercontent.com/CMSgov/ars-machine-readable'
            'main/5.0/oscal/CMS_ARS_5_0_catalog.json'
        )
    }

    p = Path(source)
    oc = opencontrol.load(p)

    md = Metadata(title=oc.name, version="unknown")
    cd = component.ComponentDefinition(metadata=md)
    cd.components = []
    for o_comp in oc.components:
        c = component.Component(title=o_comp.name, description=o_comp.name)
        c.control_implementations = []

        sorted_controls = sorted(o_comp.satisfies, key=lambda c: c.standard_key)
        grouped_controls = groupby(sorted_controls, lambda c: c.standard_key)
        for standard_key, o_controls in grouped_controls:
            if standard_key in source_uri_dict:
                source_uri = source_uri_dict[standard_key]
            else:
                source_uri = source_uri_dict['NIST_SP80053r4']
            ci = component.ControlImplementation(
                description=standard_key, source=source_uri
            )
            ci.implemented_requirements = []

            for o_control in o_controls:
                control_id = oscalize_control_id(o_control.control_key)
                ir = component.ImplementedRequirement(
                    control_id=control_id,
                    # Default description used when narratives are all sub-parts
                    description=(
                        'Requirements are implemented as described '
                        'in the included statements.'
                    )
                )
                if o_control.parameters:
                    for o_parameter in o_control.parameters:
                        ir.add_property(
                            component.Property(
                                name=o_parameter.key,
                                value=o_parameter.text
                            )
                        )
                for o_statement in o_control.narrative:
                    # Do not consider "shared" a key; may be others...
                    if o_statement.key and o_statement.key != "shared":
                        statement_id = f"{control_id}_smt.{o_statement.key}"
                        ir.add_statement(
                            component.Statement(
                                statement_id=statement_id,
                                description=o_statement.text.strip(),
                            )
                        )
                    else:
                        ir.description = o_statement.text.strip()
                ci.implemented_requirements.append(ir)
            c.control_implementations.append(ci)
        cd.add_component(c)
    root = component.Model(component_definition=cd)
    print(root.json(indent=2))


if __name__ == "__main__":
    main()
