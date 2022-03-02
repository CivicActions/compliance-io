import click
from complianceio.oscal.catalogio import Catalog


@click.command()
@click.argument(
    "src",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
    required=True,
)
def main(src):
    """
    Perform operations on OSCAL Catalog.
    """
    catalog = Catalog(src)
    control = catalog.get_control_by_id("ac-2")
    print(catalog.get_control_parameters(control))
    print(type(catalog.get_control_parameters(control)))


if __name__ == "__main__":
    main()
