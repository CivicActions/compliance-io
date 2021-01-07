from pathlib import Path

import click

from compliance_io.opencontrol import OpenControl


@click.command()
@click.argument(
    "source",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
@click.argument(
    "dest",
    type=click.Path(dir_okay=True, exists=True, file_okay=False, resolve_path=True),
)
def main(source, dest):
    p = Path(source)
    OpenControl.load(p).save_as(dest)


if __name__ == "__main__":
    main()
