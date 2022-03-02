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
    print(catalog.catalog_title)


if __name__ == "__main__":
    main()
