import sys
from typing import List

import yaml


ORCID_HTTPS_PREFIX = "https://orcid.org/"


def write_gin_datacite_authors(persons: dict):
    if not persons:
        return

    persons = sorted(persons.values(), key=lambda pr: pr["last_name"])

    print("authors:")
    for person_entry in persons:
        print(f"  - firstname: {person_entry['given_name']}")
        print(f"    lastname: {person_entry['last_name']}")
        if "affiliation" in person_entry:
            print(f"    affiliation: {person_entry['affiliation']}")
        if "orcid-id" in person_entry:
            orcid_id = person_entry["orcid-id"]
            if orcid_id.startswith(ORCID_HTTPS_PREFIX):
                orcid_id = orcid_id.replace(ORCID_HTTPS_PREFIX, "", 1)
            print(f"    id: ORCID:{orcid_id}")
        print("")


def main(arguments: List[str]):

    with open(arguments[1], "rt") as f:
        data_object = yaml.safe_load(f)

    write_gin_datacite_authors(data_object["person"])


if __name__ == "__main__":
    main(sys.argv)