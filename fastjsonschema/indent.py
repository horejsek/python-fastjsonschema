

def indent(func):
    """
    Decorator for allowing to use method as normal method or with
    context manager for auto-indenting code blocks.
    """
    def wrapper(self, *args, **kwds):
        func(self, *args, **kwds)
        return Indent(self)
    return wrapper


class Indent:
    def __init__(self, instance):
        self.instance = instance

    def __enter__(self):
        self.instance._indent += 1

    def __exit__(self, type, value, traceback):
        self.instance._indent -= 1
