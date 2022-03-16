from itertools import groupby
from pathlib import Path

import click
import json
import requests

from complianceio import opencontrol

"""
Read an OpenControl repo and perform gap analysis against a Catalog.
TODO: apply a Profile to the catalog to tailor out e.g. High controls.
Return:
    Count and List of Controls Fully Inherited
    Count and list of Controls with Shared Responsibility
    Count and list of Controls have no implementation statement
"""


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


def get_catalog_keys(standard_key, profile_ids):
    keys = {}
    source_uri = get_source_uri(standard_key)
    url = requests.get(source_uri)
    catalog = json.loads(url.text)

    groups = catalog["catalog"]["groups"]
    for group in groups:
        for control in group["controls"]:
            control_id = control["id"]
            if control_id not in profile_ids:
                # if "cms" in control_id:
                # print(control_id)
                continue
            # ARS 3.1 uses "properties" but 5.0 uses "props"
            if "properties" in control:
                keys[control["properties"][0]["value"]] = []
            elif "props" in control:
                keys[control["props"][0]["value"]] = []
            else:
                print("Can't find props (properties) of {:s}".format(control))
    return keys


def read_opencontrol_components(source, profile_ids):
    """
    Read an OpenControl repo and perform gap analysis against a Catalog.
    """

    catalog_keys = {}

    p = Path(source)
    oc = opencontrol.load(p)
    for comp in oc.components:
        print("{:s} - {:s}".format(comp.key, comp.name))

        sorted_controls = sorted(comp.satisfies, key=lambda c: c.standard_key)
        grouped_controls = groupby(sorted_controls, lambda c: c.standard_key)

        for standard_key, controls in grouped_controls:
            if standard_key not in catalog_keys:
                catalog_keys[standard_key] = get_catalog_keys(standard_key, profile_ids)
            print(standard_key)

            for control in controls:
                key = control.control_key
                status = "Implemented"
                if (
                        control.parameters and
                        control.parameters[0].key == "security_control_type"
                ):
                    if key in catalog_keys[standard_key]:
                        control_type = control.parameters[0].text
                    else:
                        catalog_keys[standard_key][key] = []
                        control_type = control.parameters[0].text + " Not in Profile"
                else:
                    control_type = "Shared"
                catalog_keys[standard_key][key].append(
                            {"system": comp.key,
                             "security_control_type": control_type}
                )
    return catalog_keys


def read_profile_ids(profile_source):
    url = requests.get(profile_source)
    profile = json.loads(url.text)
    title = profile["profile"]["metadata"]["title"]
    profile_ids = profile["profile"]["imports"][0]["include-controls"][0]["with-ids"]
    print("{:d} controls in {:s}".format(len(profile_ids), title))
    return profile_ids


def print_report(gap_analysis):
    rv = {}
    empty = []
    for standard, controls in gap_analysis.items():
        print("{:d} controls in {:s}".format(len(controls), standard))
        for control, types in controls.items():
            if not types:
                empty.append(control)
            else:
                for type in types:
                    system = type["system"]
                    secure = type["security_control_type"]
                    if system not in rv:
                        rv[system] = {
                            "inherit": [],
                            "hybrid": [],
                            "not_in": [],
                            "not_hy": []
                        }
                    if "Inherit" in secure:
                        if "Not" in secure:
                            rv[system]["not_in"].append(control)
                        else:
                            rv[system]["inherit"].append(control)
                    else:
                        if "Not" in secure:
                            rv[system]["not_hy"].append(control)
                        else:
                            rv[system]["hybrid"].append(control)
        print("{:<10} {:<10} {:<8} {:<8} {:<8} {:<8}".format(
            'System', 'Inherited', 'Hybrid', 'In-Not', 'Hy-Not', 'Total'))
        tot_in = 0
        tot_hy = 0
        tot_ni = 0
        tot_nh = 0
        totals = 0
        for system, values in rv.items():
            inherit = len(rv[system]["inherit"])
            tot_in += inherit
            hybrid = len(rv[system]["hybrid"])
            tot_hy += hybrid
            not_in = len(rv[system]["not_in"])
            tot_ni += not_in
            not_hy = len(rv[system]["not_hy"])
            tot_nh += not_hy
            total = inherit + hybrid + not_in + not_hy
            totals += total
            print("{:<10} {:<10} {:<8} {:<8} {:<8} {:<8}".format(
                system, inherit, hybrid, not_in, not_hy, total))
        print("{:<10} {:<10} {:<8} {:<8} {:<8} {:<8}".format(
            "Totals", tot_in, tot_hy, tot_ni, tot_nh, totals))
        print("{:<10} {:<10}".format("Empty:", len(empty)))


"""
Return:
    Count and list of Controls Fully Inherited
    Count and list of Controls with Shared Responsibility
    Count and list of Controls not in catalog
    Count and list of Controls have no implementation statement
"""


@click.command()
@click.option(
    "-e",
    "--empty",
    is_flag=True,
    help="Count and list of controls with no implementation statement",
)
@click.option(
    "-h",
    "--hybrid",
    is_flag=True,
    help="Count and list of Hybrid or Shared controls",
)
@click.option(
    "-i",
    "--inherited",
    is_flag=True,
    help="Count and list of Fully Inherited controls",
)
@click.option(
    "-j",
    "--json_out",
    is_flag=True,
    help="Output raw json of catalog control contributions",
)
@click.option(
    "-p",
    "--profile_url",
    help="URL to OSCAL Profile in JSON format for tailoring Catalog",
)
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
def main(source, profile_url, empty, hybrid, inherited, json_out):
    if not profile_url:
        profile = (
            'https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov'
            '/SP800-53/rev4/json/NIST_SP-800-53_rev4_MODERATE-baseline_profile.json'
        )
    profile_ids = read_profile_ids(profile)
    gap_analysis = read_opencontrol_components(source, profile_ids)
    if json_out:
        print(json.dumps(gap_analysis, indent=4))
    else:
        print_report(gap_analysis)
    


if __name__ == "__main__":
    main()
