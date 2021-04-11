import json
from collections import defaultdict
from itertools import groupby

import click

from complianceio.opencontrol import OpenControl


@click.command()
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
@click.argument("component-name")
def main(source, component_name):
    oc = OpenControl.load(source)

    statements = defaultdict(list)

    for component in oc.components:
        if component.name == component_name:
            for control in component.satisfies:
                for statement in control.narrative:
                    statements[control.control_key].append(statement)

    for control in sorted(statements.keys()):
        for key, stmts_by_key in groupby(
            sorted(statements[control], key=lambda s: s.key or ""), lambda s: s.key
        ):
            text = "\n".join([s.text for s in stmts_by_key])
            if key:
                control_label = f"{control}.{key}"
            else:
                control_label = control
            line = json.dumps(dict(control=control_label, text=text))
            print(line)


if __name__ == "__main__":
    main()
