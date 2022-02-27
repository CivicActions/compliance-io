from catalogio import Catalog
import click


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


if __name__ == "__main__":
    main()