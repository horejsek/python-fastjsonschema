
class JsonSchemaException(ValueError):
    """
    Exception raised by validation function. Contains ``message`` with
    information what is wrong.
    """

    def __init__(self, message):
        self.message = message
