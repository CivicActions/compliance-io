from itertools import groupby
from pathlib import Path

import click
import json
import yaml
import requests

from complianceio import opencontrol
from complianceio.oscal.oscal import oscalize_control_id
from complianceio.oscal.catalogio import Catalog

"""
Read opencontrol.yaml and perform gap analysis against a Catalog Baseline.
Return:
    Count and List of Controls Fully Inherited
    Count and list of Controls with Shared Responsibility
    Count and list of Controls have no implementation statement
TODO:
    Numbers are off. To fix: Inherited should trump Hybrid,
    but create new "Multiple" list for control contributions
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

    catalog = Catalog(url.text, True)

    for id in profile_ids:
        control = catalog.get_control_by_id(id)
        if control:
            prop = catalog.get_control_property_by_name(control, "label")
            keys[prop] = []
    return keys


def parse_opencontrol_components(source, profile_ids):
    """
    Read an OpenControl repo and perform gap analysis against a Catalog.
    """

    catalog_keys = {}

    p = Path(source)
    oc = opencontrol.load(p)

    for comp in oc.components:
        sorted_controls = sorted(comp.satisfies, key=lambda c: c.standard_key)
        grouped_controls = groupby(sorted_controls, lambda c: c.standard_key)

        for standard, controls in grouped_controls:
            if standard not in catalog_keys:
                catalog_keys[standard] = get_catalog_keys(standard, profile_ids)

            for control in controls:
                key = control.control_key
                if (
                        control.parameters and
                        control.parameters[0].key == "security_control_type"
                ):
                    if key in catalog_keys[standard]:
                        control_type = control.parameters[0].text
                    else:
                        catalog_keys[standard][key] = []
                        control_type = control.parameters[0].text + " Not in Profile"
                else:
                    if key in catalog_keys[standard]:
                        control_type = "Shared"
                    else:
                        catalog_keys[standard][key] = []
                        control_type = "Shared Not in Profile"

                if comp.key:
                    system = comp.key
                else:
                    system = comp.name
                catalog_keys[standard][key].append(
                            {"system": system,
                             "security_control_type": control_type}
                )
    return catalog_keys


def read_nist_json_profile_ids(profile_url, quiet):
    url = requests.get(profile_url)
    profile = json.loads(url.text)
    title = profile["profile"]["metadata"]["title"]
    profile_ids = profile["profile"]["imports"][0]["include-controls"][0]["with-ids"]
    if not quiet:
        print(f'{len(profile_ids)} controls in {title}')
    return profile_ids


def read_ars_yaml_profile_ids(ars, impact_level, quiet):
    ars_yml = (
        'https://raw.githubusercontent.com/CMSgov/ars-machine-readable/main/'
        '{:s}/generic/{:s}.yml'
    )
    profile_url = ars_yml.format(ars, ars)
    url = requests.get(profile_url)
    profile = yaml.safe_load(url.text)

    # profile_ids = []
    profile_ids = {}
    for control, data in profile.items():
        if data["Baseline"] and impact_level in data["Baseline"]:
            # profile_ids.append(oscalize_control_id(control))
            ctrl = profile.get(control)
            family_name = (
                f'{ctrl.get("Control Family")} : {ctrl.get("Control Name")}'
            )
            profile_ids[oscalize_control_id(control)] = family_name
    if not quiet:
        print(f'{len(profile_ids)} controls in ARS {ars} {impact_level}')
    return profile_ids


def prepare_report(gap_analysis, quiet):
    rv = {}
    empty = []
    for standard, controls in gap_analysis.items():
        if not quiet:
            print(f'{len(controls)} controls in {standard} '
                  '(including controls Not in Profile/Baseline)')
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
        rv["Empty"] = empty

    # Remove hybrid controls that are Inherited
    systems = list(rv.keys())
    systems.remove("Empty")
    all_inherited = []
    for system in systems:
        all_inherited.extend(rv[system]["inherit"])
        rv[system]["Both"] = []
    for system in systems:
        if rv[system]["inherit"]:
            continue
        dupes = []
        for control in rv[system]["hybrid"]:
            if control in all_inherited:
                rv[system]["Both"].append(control)
                dupes.append(control)
        if dupes:
            for dupe in dupes:
                rv[system]["hybrid"].remove(dupe)
    return rv


def print_report(rv):
    print(f'{"System":<15} {"Inherited":<10} {"Hybrid":<8} '
          f'{"In-Not":<8} {"Hy-Not":<8} {"Total":<8}| {"(In+Hy)":<8}')
    tot_in = 0
    tot_hy = 0
    tot_bo = 0
    tot_ni = 0
    tot_nh = 0
    totals = 0
    empty = rv.pop("Empty")
    for system, values in rv.items():
        inherit = len(rv[system]["inherit"])
        tot_in += inherit
        hybrid = len(rv[system]["hybrid"])
        tot_hy += hybrid
        both = len(rv[system]["Both"])
        tot_bo += both
        not_in = len(rv[system]["not_in"])
        tot_ni += not_in
        not_hy = len(rv[system]["not_hy"])
        tot_nh += not_hy
        total = inherit + hybrid + not_in + not_hy
        totals += total
        print(f'{system:<15} {inherit:<10} {hybrid:<8} '
              f'{not_in:<8} {not_hy:<8} {total:<8}| {both:<8}')
    print(f'{"Totals":<15} {tot_in:<10} {tot_hy:<8} '
          f'{tot_ni:<8} {tot_nh:<8} {totals:<8}| {tot_bo:<8}')
    print(f'{"Empty:":<15} {len(empty):<10}')


def print_list(rv, shared, inherited, both, not_in_profile, profile_ids, pretty):
    if both:
        column = "Both"
    elif inherited:
        if not_in_profile:
            column = "not_in"
        else:
            column = "inherit"
    else:
        if not_in_profile:
            column = "not_hy"
        else:
            column = "hybrid"
    for system, values in rv.items():
        if system == "Empty":
            continue
        if pretty:
            pretty_print_list(rv[system][column], profile_ids, system)
        else:
            print({system: rv[system][column]})


def pretty_print_list(list, profile_ids, system):
    print(f'==== {system} ====')
    for control in list:
        id = oscalize_control_id(control)
        if id in profile_ids:
            desc = profile_ids[id]
        else:
            desc = "Not in baseline"
        print(f'{control:<9} {desc}')


def pretty_print_controls(rv, profile_ids, system=False):
    if system:
        pretty_print_list(rv[system], profile_ids, system)
    else:
        for sys, controls in profile_ids.items():
            if sys == "Empty":
                continue
            pretty_print_list(rv[sys], profile_ids, sys)


@click.command()
@click.option(
    "-a",
    "--ars",
    default="3.1",
    show_default=True,
    help="ARS machine readable version",
)
@click.option(
    "-l",
    "--level",
    default="Moderate",
    show_default=True,
    help="Impact level: Low, Moderate, High",
)
@click.option(
    "-s",
    "--shared",
    is_flag=True,
    help="List of Shared or Hybrid controls",
)
@click.option(
    "-i",
    "--inherited",
    is_flag=True,
    help="List of Fully Inherited controls",
)
@click.option(
    "-b",
    "--both",
    is_flag=True,
    help="List of Hybrid controls that are also Inherited",
)
@click.option(
    "-n",
    "--not_in_profile",
    is_flag=True,
    help="List controls that are not in profile (with -s or -i)",
)
@click.option(
    "-e",
    "--empty",
    is_flag=True,
    help="List of controls with no implementation statement",
)
@click.option(
    "-p",
    "--pretty",
    is_flag=True,
    help="Pretty print the output (with -s, -i or -e)",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Output machine-readable lines (with -s, -i or -e)",
)
@click.option(
    "-j",
    "--json_out",
    is_flag=True,
    help="Output raw json of catalog control contributions",
)
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
def main(source, ars, level, empty, shared, inherited, both,
         not_in_profile, json_out, pretty, quiet):
    """
    Read opencontrol.yaml and perform gap analysis against a Catalog Baseline.
    """

    if ars:
        profile_ids = read_ars_yaml_profile_ids(ars, level, quiet)
    else:
        profile = (
            'https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov'
            '/SP800-53/rev4/json/NIST_SP-800-53_rev4_MODERATE-baseline_profile.json'
        )
        profile_ids = read_nist_json_profile_ids(profile, quiet)
    gap_analysis = parse_opencontrol_components(source, profile_ids)
    if json_out:
        print(json.dumps(gap_analysis, indent=4))
    else:
        rv = prepare_report(gap_analysis, quiet)
        if empty:
            if pretty:
                pretty_print_controls(rv, profile_ids, "Empty")
            else:
                print({"Empty": rv["Empty"]})
        elif shared or inherited or both:
            print_list(rv, shared, inherited, both, not_in_profile, profile_ids, pretty)
        else:
            print_report(rv)


if __name__ == "__main__":
    main()
