import os, json, csv, argparse
from datacite import schema43

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="get_metadata queries the caltechDATA (Invenio 3) API\
    and returns DataCite-compatable metadata"
    )
    parser.add_argument(
        "filen",
        metavar="file",
        type=str,
        nargs="+",
        help="File name for each record of interest",
    )

    args = parser.parse_args()

    for n in args.filen:

        infile = open(n, "r")
        metadata = json.load(infile)

        # assert schema43.validate(metadata)
        # Debugging if this fails
        v = schema43.validator.validate(metadata)
        errors = sorted(v.iter_errors(instance), key=lambda e: e.path)
        for error in errors:
            print(error.message)
