from itertools import groupby
from pathlib import Path

import click
import json
import requests

from complianceio import opencontrol


def get_source_uri(standard_key):
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
    if standard_key in source_uri_dict:
        source_uri = source_uri_dict[standard_key]
    else:
        source_uri = source_uri_dict['NIST_SP80053r4']
    return source_uri


def get_catalog_keys(standard_key):
    keys = {}
    source_uri = get_source_uri(standard_key)
    url = requests.get(source_uri)
    catalog = json.loads(url.text)

    groups = catalog["catalog"]["groups"]
    for group in groups:
        for control in group["controls"]:
            # ARS 3.1 uses "properties" but 5.0 uses "props"
            if "properties" in control:
                keys[control["properties"][0]["value"]] = []
            elif "props" in control:
                keys[control["props"][0]["value"]] = []
            else:
                print("Can't find props (properties) of {:s}".format(control))
    return keys


@click.command()
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
def main(source):
    """
    Read an OpenControl repo and perform gap analysis against a catalog Profile.
    Return:
        Count and List of Controls Fully Inherited
        Count and list of Controls with Shared Responsibility
        Count and list of Controls have no implementation statement
    """

    '''
    p = Path(source)
    with open(p, 'r') as stream:
        try:
            parsed = yaml.safe_load(stream)
            print(json.dumps(parsed, indent=4))
        except yaml.YAMLError as exc:
            print(exc)
    quit()
    '''

    catalog_keys = {}

    p = Path(source)
    oc = opencontrol.load(p)
    for comp in oc.components:
        print("{:s} - {:s}".format(comp.key, comp.name))
        sorted_controls = sorted(comp.satisfies, key=lambda c: c.standard_key)
        grouped_controls = groupby(sorted_controls, lambda c: c.standard_key)

        for standard_key, controls in grouped_controls:
            if standard_key not in catalog_keys:
                # catalog_keys[standard_key] = get_catalog_keys(standard_key)
                catalog_keys = get_catalog_keys(standard_key)
            print(standard_key)
            for control in controls:
                key = control.control_key
                if (
                        control.parameters and
                        control.parameters[0].key == "security_control_type"
                ):
                    # print("{:9s} - {:s}".format(control.control_key,
                    #                            control.parameters[0].text))
                    if key in catalog_keys:
                        control_type = control.parameters[0].text
                    else:
                        catalog_keys[key] = []
                        control_type = "Not in catalog"
                else:
                    # print(control.control_key)
                    control_type = "Shared"
                catalog_keys[key].append(
                            {"system": comp.key,
                             "security_control_type": control_type}
                )
        print(json.dumps(catalog_keys, indent=4))


if __name__ == "__main__":
    main()
