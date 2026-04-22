import re, datetime
from pprint import pprint
from urllib.parse import urlparse
import yaml
import MEDFORD.mfdglobals as mfdglobals
mfdglobals.init()
__DEBUG__ = mfdglobals.debug

# Primitive type names that can be validated directly.
# Any type name starting with a capital letter is a complex/structured type
# (e.g. Contributor, Institution) and should be ignored at this level.
_PRIMITIVE_TYPES = {"string", "text", "email", "uri", "phone", "number", "integer", "date"}

# Allow "string" as an alias for the "text" validator method.
_TYPE_ALIASES = {"string": "text"}


class Validator:
    """Container for validation methods"""

    # translations from operators to methods
    translations = {"<": "lt", ">": "gt", "<=": "le", ">=": "ge", "==": "eq"}

    # The instance of Validator keeps track of which labels have been seen.
    # This allows cross-label validations including errant duplications.
    # The validator is driven off of a YAML file (medford.yaml).
    def __init__(self, filename="medford.yaml"):
        """Initialize a Validator instance.
        This includes setting up initial structures of tags that have
        been seen.
        """
        self.validators = {}

        self.tags_seen = {}
        self.file_references = {}
        self.validation_errors = []

        # Read MEDFORD YAML validator spec.
        # Format:
        #   TagName:
        #     type: <typename>        # string | text | email | uri | phone | number | integer | date
        #                             # Capitalized types (e.g. Contributor) are skipped.
        #   "*-URI":                  # wildcard: matches any tag whose minor token is URI
        #     type: uri
        with open(filename, "r") as f:
            spec = yaml.safe_load(f)

        if spec is None:
            spec = {}

        for tag, rules in spec.items():
            if not isinstance(rules, dict):
                print("Skipping tag '{}': expected a mapping of rules.".format(tag))
                continue

            # Process each rule key.  The most common key is "type"; the
            # comparison operators (gt, lt, ge, le, eq) may also appear.
            for key, val in rules.items():
                # Translate symbolic operators to canonical names
                canon_key = self.translations.get(key, key)

                if canon_key == "type":
                    type_name = str(val)
                    # Skip complex/structured types (e.g. Contributor)
                    if type_name and type_name[0].isupper():
                        continue
                    method = _TYPE_ALIASES.get(type_name, type_name)
                    entry = [method]
                else:
                    # Comparison validator: e.g. gt: 0  →  ["gt", "0"]
                    method = canon_key
                    entry = [method, str(val)]

                if tag in self.validators:
                    self.validators[tag].append(entry)
                else:
                    self.validators[tag] = [entry]

        if __DEBUG__:
            pprint(self.validators)

    def add_tag_occurrence(self, tag, value, line_number, file_path, minor_tokens=None):
        if minor_tokens is None:
            minor_tokens = {}

        occurrence = {
            "value": value,
            "line_number": line_number,
            "minor_tokens": minor_tokens,
            "file_path": file_path,
        }

        if tag in self.tags_seen:
            self.tags_seen[tag].append(occurrence)
        else:
            self.tags_seen[tag] = [occurrence]

    # for later
    def add_file_reference(self, filename, tag):
        if filename in self.file_references:
            self.file_references[filename].append(tag)
        else:
            self.file_references[filename] = [tag]

    def add_validation_error(self, tag, value, line_number, file_path, error_message):
        error = {
            "tag": tag,
            "value": value,
            "line_number": line_number,
            "file_path": file_path,
            "error": error_message,
        }
        self.validation_errors.append(error)

    def validate(self, tag, value, line_number=None, file_path=None):
        """validate one tag's value"""
        self.add_tag_occurrence(tag, value, line_number, file_path)

        # check if this is a file reference and track it
        if tag.endswith("_File") or tag.endswith("-File"):
            from pathlib import Path

            filename = Path(value).name
            self.add_file_reference(filename, tag)

        if tag in self.validators:
            valids = self.validators[tag]
            for v in valids:
                func = v[0]
                args = v[1:]
                response = self.invoke(tag, func, value, *args)
                if response:
                    self.add_validation_error(
                        tag, value, line_number, file_path, response
                    )

        elif "-" in tag:
            tags = tag.split("-")
            minor = tags[1]

            matchtag = "*-" + minor
            if matchtag in self.validators:
                valids = self.validators[matchtag]
                for v in valids:
                    func = v[0]
                    args = v[1:]
                    response = self.invoke(tag, func, value, *args)
                    if response:
                        self.add_validation_error(
                            tag, value, line_number, file_path, response
                        )
        else:
            if __DEBUG__:
                # print("no validator for {}".format(tag))
                pass

    def print_validation_summary(self):
        if not self.validation_errors:
            print("All validations passed!")
            return True

        for error in self.validation_errors:
            context = (
                f"Line {error['line_number']}"
                if error["line_number"]
                else "Unknown line"
            )
            if error["file_path"]:
                context += f" in {error['file_path']}"

            print(f"Error: {context}")
            print(f"  Tag: @{error['tag']}")
            print(f"  Value: '{error['value']}'")
            print(f"  Issue: {error['error']}")
            print()

        return False

    def invoke(self, tag, validator, value, *args):
        """Validate a specific value for a tag.
        tag: the tag to validate against.
        validator: the text name of a method in the class Validator
        value: the value to validate.
        *args: a freeform list of extra arguments that might be specified in the
        validation specification.
        """
        # Fetch the local method with the name in validator
        valid = getattr(self, validator, None)
        if valid is not None:
            retval = valid(tag, value, *args)
            return retval
        else:
            return "Specified validator '{}' does not exist.".format(validator)

    def email(self, tag, value, *args):
        """An email value is valid.
        Value is the value to be validated as an email address.
        """
        print("validating email {}".format(value))
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        if not re.match(email_pattern, value):
            return f"Invalid email format: '{value}'"

        # additional checks
        if len(value) > 254:
            return f"Email address too long: '{value}'"

        if ".." in value:
            return f"Email contains consecutive dots: '{value}'"

        return None  # no error

    def text(self, tag, value, *args):
        if __DEBUG__:
            print(
                "text invoked with tag='{}' value='{}' args='{}'".format(
                    tag, value, args
                )
            )

        if not value or not value.strip():
            return "Text value cannot be empty or whitespace only"
        return None

    def date(self, tag, value, *args):
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d")

            current_year = datetime.now().year
            if parsed_date.year < 1900 or parsed_date.year > current_year + 10:
                return f"Year {parsed_date.year} is outside reasonable range (1900-{current_year + 10})"

            return None

        except ValueError:
            return f"Invalid date format: '{value}'. Expected formats: YYYY-MM-DD"

    def number(self, tag, value, *args):
        print(
            "number invoked with tag='{}' value='{}' args='{}'".format(tag, value, args)
        )

        try:
            value = int(value)
            if value > 0:
                return None
            else:
                return "Value '{}' is not an integer greater than 0".format(value)
        except ValueError as e:
            return "Value '{}' is not an integer".format(value)

    def integer(self, tag, value, *args):
        if __DEBUG__:
            print(
                "integer invoked with tag='{}' value='{}' args='{}'".format(
                    tag, value, args
                )
            )
        try:
            value = int(value)
            return None
        except ValueError:
            return "Value '{}' is not an integer".format(value)

    def phone(self, tag, value, *args):
        digits = re.sub(r"[\s\(\)\-\.\+]", "", value)
        if not digits.isdigit():
            return f"Invalid phone number (non-numeric characters): '{value}'"
        if not (7 <= len(digits) <= 15):
            return f"Invalid phone number (must be 7–15 digits): '{value}'"
        return None

    def uri(self, tag, value, *args):
        if __DEBUG__:
            print(
                "uri invoked with tag='{}' value='{}' args='{}'".format(
                    tag, value, args
                )
            )
        try:
            urlparse(value)
            return None
        except ValueError as e:
            return "Value '{}' is not a valid URI: {}".format(value, e)

    def lt(self, tag, value, *args):
        if __DEBUG__:
            print(
                "lt invoked with tag='{}' value='{}' args='{}'".format(tag, value, args)
            )
        if len(args) < 1:
            print("No limiting value specified")
        else:
            limit = args[0]
            try:
                value = int(value)
            except ValueError:
                return "Value '{}' is not an integer"
            try:
                limit = int(limit)
            except ValueError:
                return "Limit '{}' is not an integer"
            if value < limit:
                return None
            else:
                return "Value {} is not less than limit {}".format(value, limit)

    def gt(self, tag, value, *args):
        if __DEBUG__:
            print(
                "gt invoked with tag='{}' value='{}' args='{}'".format(tag, value, args)
            )
        if len(args) < 1:
            print("No threshold value specified")
        else:
            limit = args[0]
            try:
                value = int(value)
            except ValueError:
                return "Threshold value '{}' is not an integer".format(value)
            try:
                limit = int(limit)
            except ValueError:
                return "Threshold value '{}' is not an integer".format(limit)
            if value > limit:
                return None
            else:
                return "Value {} is not greater than threshold value {}".format(
                    value, limit
                )

    def le(self, tag, value, *args):
        if __DEBUG__:
            print(
                "le invoked with tag='{}' value='{}' args='{}'".format(tag, value, args)
            )
        if len(args) < 1:
            print("No limiting value specified")
        else:
            limit = args[0]
            try:
                value = int(value)
            except ValueError:
                return "Value '{}' is not an integer".format(value)
            try:
                limit = int(limit)
            except ValueError:
                return "Limit '{}' is not an integer".format(limit)
            if value <= limit:
                return None
            else:
                return "Value {} is not less than or equal to limit {}".format(
                    value, limit
                )


def ge(self, tag, value, *args):
    if __DEBUG__:
        print("ge invoked with tag='{}' value='{}' args='{}'".format(tag, value, args))
    if len(args) < 1:
        print("No threshold value specified")
    else:
        limit = args[0]
        try:
            value = int(value)
        except ValueError:
            return "Threshold value '{}' is not an integer".format(value)
        try:
            limit = int(limit)
        except ValueError:
            return "Threshold value '{}' is not an integer".format(limit)
        if value >= limit:
            return None
        else:
            return "Value {} is not greater than or equal to threshold value {}".format(
                value, limit
            )


def eq(self, tag, value, *args):
    if __DEBUG__:
        print("eq invoked with tag='{}' value='{}' args='{}'".format(tag, value, args))
    if len(args) < 1:
        print("No comparison value specified")
    else:
        expected = args[0]
        try:
            value = int(value)
        except ValueError:
            return "Value '{}' is not an integer".format(value)
        try:
            expected = int(expected)
        except ValueError:
            return "Expected value '{}' is not an integer".format(expected)
        if value == expected:
            return None
        else:
            return "Value {} does not equal expected {}".format(value, expected)


# Usage
# foo = Validator()
# result = foo.invoke('Contributor.email', 'email','tcmits@eff.org')
# print(result)

# result = foo.validate("@Contributor-email", "tcmits@eff.org")
# print("result is '{}'".format(result))
# result = foo.validate("@Paper-URI", "https://foo.on.us/foo.pdf")
# print("result is '{}'".format(result))
# result = foo.validate("@Paper-volume", "foo")
# print("result is '{}'".format(result))
# result = foo.validate("@Paper-volume", "1200")
# print("result is '{}'".format(result))
# result = foo.validate("@some-URI", "https://foo.us/foo.py")
# print("result is '{}'".format(result))
