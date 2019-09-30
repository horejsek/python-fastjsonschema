from collections import defaultdict, deque, OrderedDict
from contextlib import contextmanager
import re

from .exceptions import JsonSchemaException
from .indent import indent
from .ref_resolver import RefResolver

MARKER = object()


def enforce_list(variable):
    if isinstance(variable, list):
        return variable
    return [variable]


def single_type_optimization(checked_type):
    def outer(func):
        def inner(self, *args, **kwargs):
            if self.has_type(checked_type):
                self.l('# type of {variable} is {} (enforced by exception)', checked_type)
                return func(self, *args, **kwargs)
            variable_suffix = '_is_{}'.format(checked_type)
            variable_generator = getattr(self, 'create_variable{}'.format(variable_suffix))
            duplicate = variable_generator()
            with self.l('if {{variable}}{}:'.format(variable_suffix), deduplicate=duplicate):
                return func(self, *args, **kwargs)
        return inner
    return outer


# pylint: disable=too-many-instance-attributes,too-many-public-methods,too-many-arguments
class CodeGenerator:
    """
    This class is not supposed to be used directly. Anything
    inside of this class can be changed without noticing.

    This class generates code of validation function from JSON
    schema object as string. Example:

    .. code-block:: python

        CodeGenerator(json_schema_definition).func_code
    """

    INDENT = 4  # spaces

    def __init__(self, definition, resolver=None, formats=None, verbose=False, root_name='data'):
        self._code = []
        self._compile_regexps = {}
        self._custom_formats = formats or {}
        self._verbose = verbose
        self._root_name = root_name
        self._variables = set()
        self._indent = 0
        self._variable = None
        self._variable_name = None
        self._root_definition = definition
        self._definition = None
        self._probing = 0
        self._context = deque()

        # map schema URIs to validation function names for functions
        # that are not yet generated, but need to be generated
        self._needed_validation_functions = {}
        # validation function names that are already done
        self._validation_functions_done = set()

        if resolver is None:
            resolver = RefResolver.from_schema(definition)
        self._resolver = resolver
        # add main function to `self._needed_validation_functions`
        self._needed_validation_functions[self._resolver.get_uri()] = self._resolver.get_scope_name()

        self._json_keywords_to_function = OrderedDict()

    @property
    def func_code(self):
        """
        Returns generated code of whole validation function as string.
        """
        self._generate_func_code()
        source = [(token, line) for token, line in self._code if token is not MARKER]
        indented_code = ['{}{}'.format(' ' * self.INDENT * (depth or 0), line or '') for depth, line in source]
        return '\n'.join(indented_code)

    @property
    def global_state(self):
        """
        Returns global variables for generating function from ``func_code``. Includes
        compiled regular expressions and imports, so it does not have to do it every
        time when validation function is called.
        """
        self._generate_func_code()

        return dict(
            REGEX_PATTERNS=self._compile_regexps,
            re=re,
            JsonSchemaException=JsonSchemaException,
            custom_formats=self._custom_formats,
        )

    @property
    def global_state_code(self):
        """
        Returns global variables for generating function from ``func_code`` as code.
        Includes compiled regular expressions and imports.
        """
        self._generate_func_code()

        if not self._compile_regexps:
            return '\n'.join(
                [
                    'from fastjsonschema import JsonSchemaException',
                    '',
                    '',
                ]
            )
        regexs = ['"{}": re.compile(r"{}")'.format(key, value.pattern) for key, value in self._compile_regexps.items()]
        return '\n'.join(
            [
                'import re',
                'from fastjsonschema import JsonSchemaException',
                '',
                '',
                'REGEX_PATTERNS = {',
                '    ' + ',\n    '.join(regexs),
                '}',
                '',
            ]
        )

    def _generate_func_code(self):
        if not self._code:
            self.generate_func_code()

    def generate_func_code(self):
        """
        Creates base code of validation function and calls helper
        for creating code by definition.
        """
        self.l('NoneType = type(None)')
        # Generate parts that are referenced and not yet generated
        while self._needed_validation_functions:
            # During generation of validation function, could be needed to generate
            # new one that is added again to `_needed_validation_functions`.
            # Therefore usage of while instead of for loop.
            uri, name = self._needed_validation_functions.popitem()
            self.generate_validation_function(uri, name)

    def generate_validation_function(self, uri, name):
        """
        Generate validation function for given uri with given name
        """
        self._validation_functions_done.add(uri)
        self.l('')
        with self._resolver.resolving(uri) as definition:
            self.code_break()
            with self.l('def {{}}(data, scope="{}"):'.format(self._root_name), name):
                var_name = '{scope}' if self._verbose else 'data'
                self.generate_func_code_block(definition, 'data', var_name, clear_variables=True)
                self.l('return data')

    def generate_func_code_block(self, definition, variable, variable_name, clear_variables=False):
        """
        Creates validation rules for current definition.
        """
        backup = self._definition, self._variable, self._variable_name
        self._definition, self._variable, self._variable_name = definition, variable, variable_name
        if clear_variables:
            backup_variables = self._variables
            self._variables = set()

        self._generate_func_code_block(definition)

        self._definition, self._variable, self._variable_name = backup
        if clear_variables:
            self._variables = backup_variables

    def _generate_func_code_block(self, definition):
        if '$ref' in definition:
            # needed because ref overrides any sibling keywords
            self.generate_ref()
        else:
            self.run_generate_functions(definition)

    def run_generate_functions(self, definition):
        for key, func in self._json_keywords_to_function.items():
            if key in definition:
                with self.in_context(key):
                    self.l('# {}'.format(self.e(key)))
                    func()

    def generate_ref(self):
        """
        Ref can be link to remote or local definition.

        .. code-block:: python

            {'$ref': 'http://json-schema.org/draft-04/schema#'}
            {
                'properties': {
                    'foo': {'type': 'integer'},
                    'bar': {'$ref': '#/properties/foo'}
                }
            }
        """
        with self._resolver.in_scope(self._definition['$ref']):
            name = self._resolver.get_scope_name()
            uri = self._resolver.get_uri()
            if uri not in self._validation_functions_done:
                self._needed_validation_functions[uri] = name
            # call validation function
            if self._verbose:
                self.l('{}({variable}, "{name}")', name)
            else:
                self.l('{}({variable})', name)

    def _emit(self, indentation, source_line, deduplicate=False):
        """
        Store or ignore the generated line and indentation information.

        If deduplicate is set, try to find an identical line of code at the same indent level and
        if such exists do not store it - DRY!

        Information is stored as tuple(indentation, source_line).
        There are two abused values for indentation:
        - None  which means end of scope of a functional block
        - marker which marks a special case, e.g. types to instruct the compiler about last checked type of a variable

        :param indentation: level of indentation (it's level and not space-count)
        :param source_line: python-line source
        :param deduplicate: check for repetitive code
        :return:
        """
        if deduplicate:
            for ind, code in reversed(self._code):
                if ind is None:
                    break
                if ind == indentation:
                    commented = '# {}'.format(source_line)
                    if code in (source_line, commented):
                        self._code.append((indentation, commented))
                        return
                    break
        self._code.append((indentation, source_line))

    def code_break(self):
        self._emit(None, None)

    def mark_type(self, variable, types):
        for ind, code in reversed(self._code):
            if ind is None:
                break
            if ind is MARKER:
                code['types'][variable] = types
                return
        self._emit(MARKER, defaultdict(types={variable: types}))

    def get_mark(self, mark):
        for ind, code in reversed(self._code):
            if ind is None:
                return None
            if ind is MARKER:
                return code[mark]
        return None

    def has_type(self, atype):
        types = self.get_mark('types')
        return types and self._variable in types and atype in types[self._variable]

    @contextmanager
    def in_context(self, path):
        """
        Tracks the context path of the schema definition.
        :param path: Element to add to the path upon invocation
        :return:
        """
        self._context.append(path)
        try:
            yield
        finally:
            self._context.pop()

    def context_path(self):
        path = self._context.copy()
        return '{} in schema{}'.format(repr(path.pop()), ''.join('[{}]'.format(repr(item)) for item in path))

    @contextmanager
    def probing(self):
        """
        Context manager to keep track of probing blocks to support quick exception generation.

        When using exceptions in constructs like `oneOf` parts of input are probed if they satisfy some definition.
        One can spot this be `self.l('except JsonSchemaException: pass')` catching exceptions with `pass` statement.
        In those cases the message held by exception is meaningless so expanding them is useless. That block of code
        should be executed in the context of:

        ... code-block:: python
            with self.probing():
                for definition_item in self._definition['oneOf']:
                    ..
        """
        self._probing += 1
        try:
            yield
        finally:
            self._probing -= 1

    @property
    def is_probing(self):
        return bool(self._probing)

    # pylint: disable=invalid-name
    @indent
    def l(self, line, *args, deduplicate=False, expand_locals=True, **kwds):  # noqa
        """
        Short-cut of line. Used for inserting line. It's formatted with parameters
        ``variable``, ``variable_name`` (as ``name`` for short-cut), all keys from
        current JSON schema ``definition`` and also passed arguments in ``args``
        and named ``kwds``.

        .. code-block:: python

            self.l('if {variable} not in {enum}: raise JsonSchemaException("Wrong!")')

        When you want to indent block, use it as context manager. For example:

        .. code-block:: python

            with self.l('if {variable} not in {enum}:'):
                self.l('raise JsonSchemaException("Wrong!")')
        """
        name = self._variable_name
        if expand_locals and '{name}' in line and name and '{' in name:
            name = '"+"{}".format(**locals())+"'.format(self._variable_name)

        context = dict(
            self._definition or {},
            variable=self._variable,
            name=name,
            **kwds,
        )
        code = line.format(*args, **context)
        code = code.replace('\n', '\\n').replace('\r', '\\r')
        self._emit(self._indent, code, deduplicate)

    @staticmethod
    def e(string):
        """
        Short-cut of escape. Used for inserting user values into a string message.

        .. code-block:: python
            self.l('raise JsonSchemaException("Variable: {}")', self.e(variable))
        """
        return str(string).replace('"', '\\"')

    def throw(self, message: str, *args, **kwargs):
        """
        Generate code for `raise JsonSchemaException(...)`

        This function has two purposes:
        - to keep the code less verbose
        - distinguish between final validation failures and probing validation failures

        :param message: string to be included in the exception
        """
        expand = not self.is_probing
        if self._verbose:
            message += '\\n  caused by {path} {rule}'
            kwargs.update(path=self.context_path(), rule=self._definition)
        self.l('raise JsonSchemaException("{}")'.format(message if expand else ''),
               expand_locals=expand, *args, **kwargs)

    def declare_var(self, suffix: str, initializer: str = None) -> bool:
        """
        Add a new variable into the current scope and initialize it if appropriate.

        :param suffix: full variable name is formed by adding suffic to the variable in scope
        :param initializer: value to initialize the variable with
        :return: True if the variable was already declared
        """
        variable_name = '{}_{}'.format(self._variable, suffix)
        result = variable_name in self._variables
        if not result:
            self._variables.add(variable_name)
            if initializer is not None:
                self.l('{} = {}'.format(variable_name, initializer))
        return result

    def create_variable_missing(self):
        return self.declare_var('missing', '{{prop for prop in {required} if prop not in {variable}}}')

    def create_variable_with_length(self):
        """
        Append code for creating variable with length of that variable
        (for example length of list or dictionary) with name ``{variable}_len``.
        It can be called several times and always it's done only when that variable
        still does not exists.
        """
        return self.declare_var('len', 'len({variable})')

    def create_variable_keys(self):
        """
        Append code for creating variable with keys of that variable (dictionary)
        with a name ``{variable}_keys``. Similar to `create_variable_with_length`.
        """
        return self.declare_var('keys', 'set({variable}.keys())')

    def create_variable_is_list(self):
        """
        Append code for creating variable with bool if it's instance of list
        with a name ``{variable}_is_list``. Similar to `create_variable_with_length`.
        """
        return self.declare_var('is_list', 'isinstance({variable}, list)')

    def create_variable_is_dict(self):
        """
        Append code for creating variable with bool if it's instance of list
        with a name ``{variable}_is_dict``. Similar to `create_variable_with_length`.
        """
        return self.declare_var('is_dict', 'isinstance({variable}, dict)')
