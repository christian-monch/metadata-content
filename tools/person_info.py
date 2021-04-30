
from typing import Iterable, List, Tuple
import yaml


class PersonInfo(object):
    def __init__(self, file_name):
        with open(file_name, "rt") as f:
            self.person = yaml.safe_load(f.read())["person"]
        self.file_name = file_name
        self.last_name_index = {
            details["last_name"]: list(
                filter(lambda p: p[1]["last_name"] == details["last_name"], self.person.items())
            )
            for _, details in self.person.items()}

    def clean(self, names: List[str]) -> Iterable:
        for name in names:
            if name.endswith("."):
                yield name[:-1]
            else:
                yield name

    def _unknown_person(self, given_names: List[str], last_name: str) -> Tuple[str, dict]:
        return f"{'.'.join(map(str.lower, self.clean(given_names)))}.{last_name.lower()}@example.com", {
            "given_name": " ".join(given_names),
            "last_name": last_name
        }

    def get_person(self, given_names: List[str], last_name: str) -> Tuple[str, dict]:
        last_matches_entries = self.last_name_index.get(last_name, [])
        for email, person in last_matches_entries:
            person_names = person["given_name"].split()
            if person_names == given_names:
                return email, person
            for person_name, given_name in zip(person_names, self.clean(given_names)):
                if person_name.startswith(given_name):
                    return email, person
        return self._unknown_person(given_names, last_name)
