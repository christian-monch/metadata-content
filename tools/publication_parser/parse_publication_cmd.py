import logging
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from typing import List, Tuple

from tools.person_info import PersonInfo
from tools.publication_parser.parse_publication import MiniLexer, PublicationParser


PARSER = ArgumentParser(
    formatter_class=RawDescriptionHelpFormatter,
    description="""Publication parser

This tool will parse citations in APA format and emit ministudy Yaml objects
containing a publication and a person object for the publication authors. It
will use known author information from a given person object-file (default:
person-list.yaml).

The syntax is:

    PubSpec:     ["Publication:"] Name [ "," Name ]* "(" Year ")" "." Title "." Publication
                 ["," Volume ["(" Issue ")"] ["," Pages]] "." [DOI]
    
    Name:        LastNames "," FirstNames
    Year:        NUMBER
    Title:       CHARACTERS without "."
    Publication: CHARACTERS without "," or "."
    Volume:      NUMBER
    Issue:       NUMBER


If an author's name is found in the person list, the email and other information
from the person list will be used to create the person object-entry for the name.
If the name is not in the person list, the email address will be created 
automatically from the first and last name with the host "example.com".

""")
PARSER.add_argument("publication_specs", type=str, nargs="*")
PARSER.add_argument("--header", type=str, help="write given header before the publication")
PARSER.add_argument("--show-spec", action="store_true", default=False, help="write comment with the publication spec")
PARSER.add_argument(
    "--person-file",
    type=str, default="person-list.yaml",
    help="file name of the person file that should be used")


LOGGER = logging.getLogger("parse_publication_command")


PUBLICATION_TEMPLATE = """publication:
  - title: "{title}"
    author:
{author_list}
    year: {year}
    publication: {journal}
{volume}{issue}{pages}{doi}

person:
{person_list}
"""

PERSON_RECORD_KEYS = ("given_name", "last_name", "orcid-id", "title", "affiliation", "contact_information")

PERSON_INFO = None


def parse_text(text) -> Tuple[List, str, int, str]:
    if text.startswith("Publication: "):
        text = text[13:]
    parser = PublicationParser(MiniLexer(text))
    return parser.read_publication()


def parse_stream(character_stream, _) -> Tuple[List, str, int, str]:
    return parse_text(character_stream.read())


def get_publication_representation(publication, spec, arguments):
    names, year, title, journal, volume, issue, pages, doi = publication

    author_list = ""
    for given_names, last_name in names:
        if not given_names and last_name.startswith("et al"):
            continue
        email, _ = PERSON_INFO.get_person(given_names, last_name)
        author_list += f"      - {email}\n"

    person_list = ""
    for given_names, last_name in names:
        email, person_record = PERSON_INFO.get_person(given_names, last_name)
        person_list += f"  {email}:\n"
        person_list += "\n".join(
            [f"    {key}: {person_record[key]}" for key in PERSON_RECORD_KEYS if key in person_record])
        person_list += "\n\n"

    publication_representation = PUBLICATION_TEMPLATE.format(
        title=title,
        year=year,
        journal=journal,
        volume=f"    volume: {volume}\n" if volume is not None else "",
        issue=f"    issue: {issue}\n" if issue is not None else "",
        pages=f"    pages: {pages}\n" if pages is not None else "",
        doi=f"    doi: {doi}\n" if doi is not None else "",
        author_list=author_list,
        person_list=person_list)

    if arguments.show_spec:
        return f"# created from: {spec}\n" + publication_representation
    return publication_representation


def main():
    global PERSON_INFO

    logging.basicConfig(level=logging.INFO)

    arguments = PARSER.parse_args()

    PERSON_INFO = PersonInfo(arguments.person_file)
    publication_specs = arguments.publication_specs
    if not publication_specs:
        publication_specs = sys.stdin.read().splitlines()
    for publication_spec in publication_specs:
        if not publication_spec:
            continue
        LOGGER.info(f"parsing: {publication_spec}")
        publication = parse_text(publication_spec)
        publication_representation = get_publication_representation(publication, publication_spec, arguments)
        print(publication_representation)
    return 0


if __name__ == "__main__":
    exit(main())
