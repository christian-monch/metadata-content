import enum
import string
from collections import namedtuple
from typing import Tuple


@enum.unique
class TokenType(enum.Enum):
    EMPTY = 0
    END = 1
    WORD = 2
    NUMBER = 3
    COMMA = 4
    PERIOD = 5
    COLON = 6
    LPAREN = 7
    RPAREN = 8
    AMPERSAND = 9
    MINUS = 10
    PLUS = 11
    APOSTROPHE = 12

    TITLE = 100

    UNKNOWN = 1000


letters = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜ"
    "abcdefghijklmnopqrstuvwxyzäöüß"
    "_"
)


Position = namedtuple("Position", ("line", "column"))

Token = namedtuple("Token", ("type", "value", "representation", "start_pos", "end_pos"))


class MiniLexer(object):
    def __init__(self, text: str):
        self.current_position = Position(1, 1)
        self.current_token = Token(TokenType.EMPTY, None, "", None, None)
        self.text = text
        self.lines = self.text.splitlines()
        self.current_index = 0
        self.current_char = self.get_next_char()

    def _get_next_char(self):
        if self.current_index == len(self.text):
            self.current_char = "END"
            return self.current_char
        self.current_index += 1
        self.current_char = self.text[self.current_index - 1]
        if self.current_char == "\n":
            self.current_position = Position(self.current_position.line + 1, 1)
        else:
            self.current_position = Position(self.current_position.line, self.current_position.column + 1)
        return self.current_char

    def _get_span(self, start_position, end_position):
        if start_position.line == end_position.line:
            return self.lines[start_position.line - 1][start_position.column - 1:end_position.column - 1]

        line = start_position.line
        result = self.lines[line - 1][start_position.column - 1:] + "\n"
        while line < end_position.line:
            result += self.lines[line - 1] + "\n"
        result += self.lines[line - 1][:end_position.column - 1]
        return result

    def _get_token_text(self, token):
        return token.representation

    def get_next_char(self):
        self._get_next_char()
        while self.current_char == '"':
            self._get_next_char()
        return self.current_char

    def _parse_single(self, token):
        token_char = self.current_char
        start_position = self.current_position
        self.get_next_char()
        self.current_token = Token(token,
                                   token_char,
                                   token_char,
                                   start_position,
                                   self.current_position)

    def skip_white_space(self):
        while self.current_char in string.whitespace:
            self.get_next_char()

    def next_token_terminated_by(self, termination_characters: Tuple[str, ...]):
        """
        A different state in which all characters are consumed
        until on of the termination characters or END is encountered.
        """
        self.skip_white_space()
        if self.current_char == "END":
            self.current_token = Token(TokenType.END,
                                       "END",
                                       "END",
                                       self.current_position[:],
                                       self.current_position[:])
            return self.current_token
        token_chars = ""
        start_position = self.current_position[:]
        end_position = self.current_position[:]
        while self.current_char not in termination_characters + ("END",):
            if self.current_char == '"':
                token_chars += "\\" + self.current_char
            else:
                token_chars += self.current_char
            self._get_next_char()
            end_position = self.current_position[:]
        self.current_token = Token(TokenType.WORD,
                                   token_chars,
                                   token_chars,
                                   start_position,
                                   end_position)
        return self.current_token

    def next_token(self):
        current_token_chars = ""

        self.skip_white_space()
        start_position = self.current_position[:]
        if self.current_char == 'END':
            self.current_token = Token(TokenType.END, None, None, start_position, start_position)

        elif self.current_char in string.digits:
            while self.current_char in string.digits:
                current_token_chars += self.current_char
                self.get_next_char()
            self.current_token = Token(TokenType.NUMBER,
                                       int(current_token_chars),
                                       current_token_chars[:],
                                       start_position[:],
                                       self.current_position[:])

        elif self.current_char in letters:
            while self.current_char in letters:
                current_token_chars += self.current_char
                self.get_next_char()
            self.current_token = Token(TokenType.WORD,
                                       current_token_chars[:],
                                       current_token_chars[:],
                                       start_position[:],
                                       self.current_position[:])

        elif self.current_char == ".":
            self._parse_single(TokenType.PERIOD)
        elif self.current_char == ",":
            self._parse_single(TokenType.COMMA)
        elif self.current_char == ":":
            self._parse_single(TokenType.COLON)
        elif self.current_char == "&":
            self._parse_single(TokenType.AMPERSAND)
        elif self.current_char == "(":
            self._parse_single(TokenType.LPAREN)
        elif self.current_char == ")":
            self._parse_single(TokenType.RPAREN)
        elif self.current_char == "-":
            self._parse_single(TokenType.MINUS)
        elif self.current_char == "+":
            self._parse_single(TokenType.PLUS)
        elif self.current_char == "’":
            self._parse_single(TokenType.APOSTROPHE)
        else:
            self._parse_single(TokenType.UNKNOWN)

        return self.current_token


class PublicationParser(object):
    EMPTY = 0
    WORD = 1
    NUMBER = 2
    COMMA = 3
    PERIOD = 4
    END = 5

    def __init__(self, lexer):
        self.lexer = lexer
        self.token = None
        self.token = self.lexer.next_token_terminated_by((",",))

    def next_token(self):
        self.token = self.lexer.next_token()

    def next_token_terminated_by(self, stop_chars: Tuple[str, ...]):
        self.token = self.lexer.next_token_terminated_by(stop_chars)

    def consume(self, token_type):
        assert self.token.type == token_type, f"expected type: {token_type} != found type: {self.token.type}: {self.lexer._get_token_text(self.token)}"
        self.next_token()

    def assert_match(self, token_type):
        assert self.token.type == token_type, f"expected type: {token_type} != found type: {self.token.type}: {self.lexer._get_token_text(self.token)}"

    def match(self, token_type):
        return self.token.type == token_type

    def read_name(self):
        last_name = self.token.value
        if last_name == "et al":
            self.consume(TokenType.PERIOD)
            return [], "et al."
        self.consume(TokenType.WORD)
        assert self.token.type == TokenType.COMMA
        self.next_token_terminated_by((",", "("))
        first_names = self.token.value
        self.next_token()
        return first_names.split(), last_name

    def read_volume_issue(self):
        self.assert_match(TokenType.NUMBER)
        volume = self.token.value
        self.next_token()
        if self.match(TokenType.LPAREN):
            self.next_token()
            assert self.match(TokenType.NUMBER)
            issue = self.token.value
            self.next_token()
            self.consume(TokenType.RPAREN)
        else:
            issue = None
        return volume, issue

    def read_publication(self):
        names = []
        first_names, last_name = self.read_name()
        names.append((first_names, last_name))
        while self.match(TokenType.COMMA) or self.match(TokenType.AMPERSAND):
            self.next_token_terminated_by((",",))
            first_names, last_name = self.read_name()
            names.append((first_names, last_name))

        self.consume(TokenType.LPAREN)
        self.assert_match(TokenType.NUMBER)
        year = self.token.value
        self.consume(TokenType.NUMBER)
        self.consume(TokenType.RPAREN)
        self.match(TokenType.PERIOD)

        self.next_token_terminated_by((".",))
        title = self.token.value
        self.next_token()
        self.assert_match(TokenType.PERIOD)
        self.next_token_terminated_by((",", "."))
        publication = self.token.value
        self.next_token()
        if self.match(TokenType.COMMA):
            self.consume(TokenType.COMMA)
            volume, issue = self.read_volume_issue()
            if self.match(TokenType.COMMA):
                self.next_token_terminated_by((".",))
                pages = self.token.value
                self.next_token()
            else:
                pages = None
        else:
            volume, issue = None, None
            pages = None

        self.assert_match(TokenType.PERIOD)
        self.next_token_terminated_by(())
        if not self.match(TokenType.END):
            doi = self.token.value
        else:
            doi = None

        return names, year, title, publication, volume, issue, pages, doi


if __name__ == "__main__":
    #x = "Camilleri, Julia A., Müller, VI, Fox, P, et al. (2018). Definition and characterization of an extended multiple-demand network. Neuroimage, 2018(165), 138‐147. doi:10.1016/j.neuroimage.2017.10.020"
    #x = "Pläschke, R. N., Cieslik, E. C., Müller, V. I., Hoffstaedter, F., Plachti, A., Varikuti, D. P., Goosses, M., Latz, A., Caspers, S., Jockwitz, C., Moebus, S., Gruber, O., Eickhoff, C. R., Reetz, K., Heller, J., Südmeyer, M., Mathys, C., Caspers, J., Grefkes, C., Eickhoff, S. B. (2017). On the integrity of functional brain networks in schizophrenia, Parkinson’s disease, and advanced age: Evidence from connectivity-based single-subject classification. Human Brain Mapping, 38(12), 5845–5858. https://doi.org/10.1002/hbm.23763"
    x = "Biswal, Bharat B., Bobadilla-Suarez, Sebastian, Bortolini, Tiago (2018). Definition and characterization of an extended multiple-demand network. Neuroimage, 2018(165), 138‐147. doi:10.1016/j.neuroimage.2017.10.020"
    x = "Biswal, Bharat B., Bobadilla-Suarez, Sebastian, Bortolini, Tiago (2018). Definition and characterization of an extended multiple-demand network. Neuroimage, 2018(165), 138‐147."
    ml = MiniLexer(x)
    pp = PublicationParser(ml)

    names, year, title, publication, volume, issue, pages, doi = pp.read_publication()

    author_list = ""
    for first_names, last_name in names:
        author_list += f"      - {last_name}@fz-juelich.de\n"

    person_list = ""
    for first_names, last_name in names:
        person_list += f"  {last_name}@fz-juelich.de:\n"
        person_list += f"    given_name: {' '.join(first_names)}\n"
        person_list += f"    last_name: {last_name}\n\n"


    print(f"""
publication:
  - title: "{title}"
    author:
{author_list}
    year: {year}
    publication: {publication}""")
    if volume is not None:
        print(f"    volume: {volume}")
    if issue is not None:
        print(f"    issue: {issue}")
    if doi is not None:
        print(f"    doi: {doi}")

    print(f"""
person:
{person_list}
""")
