import re


SPLIT_RE = re.compile(r'[\.\[\]]+')


class JsonSchemaException(ValueError):
    """
    Exception raised by validation function. Available properties:

     * ``message`` with information what is wrong,
     * ``value`` of invalid data,
     * ``name`` as a string with a path in the input,
     * ``path`` as an array with a path in the input,
     * and ``definition`` which was broken.
    """

    def __init__(self, message, value=None, name=None, definition=None):
        super().__init__(message)
        self.message = message
        self.value = value
        self.name = name
        self.definition = definition

    @property
    def path(self):
        return [item for item in SPLIT_RE.split(self.name) if item != '']


class JsonSchemaDefinitionException(JsonSchemaException):
    """
    Exception raised by generator of validation function.
    """
