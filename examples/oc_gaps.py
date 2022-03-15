from itertools import groupby
from pathlib import Path

import click

from complianceio import opencontrol


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

    p = Path(source)
    oc = opencontrol.load(p)
    for o_comp in oc.components:
        print("{:s} - {:s}".format(o_comp.key, o_comp.name))
        sorted_controls = sorted(o_comp.satisfies, key=lambda c: c.standard_key)
        grouped_controls = groupby(sorted_controls, lambda c: c.standard_key)
        for standard_key, o_controls in grouped_controls:
            print(standard_key)
            for o_control in o_controls:
                if (
                        o_control.parameters and
                        o_control.parameters[0].key == "security_control_type"
                ):
                    print("{:9s} - {:s}".format(o_control.control_key,
                                                o_control.parameters[0].text))
                else:
                    print(o_control.control_key)


if __name__ == "__main__":
    main()
