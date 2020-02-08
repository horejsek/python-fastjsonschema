from collections import OrderedDict
import re

from .exceptions import JsonSchemaException, JsonSchemaDefinitionException
from .indent import indent
from .ref_resolver import RefResolver
from .scope_path import ScopePath


def enforce_list(variable):
    if isinstance(variable, list):
        return variable
    return [variable]


# pylint: disable=too-many-instance-attributes,too-many-public-methods
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

    def __init__(self, definition, resolver=None):
        self._code = []
        self._compile_regexps = {}

        # Any extra library should be here to be imported only once.
        # Lines are imports to be printed in the file and objects
        # key-value pair to pass to compile function directly.
        self._extra_imports_lines = []
        self._extra_imports_objects = {}

        self._variables = set()
        self._indent = 0
        self._indent_last_line = None
        self._variable = None
        self._variable_name = None
        self._root_definition = definition
        self._definition = None

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

        return '\n'.join(self._code)

    @property
    def global_state(self):
        """
        Returns global variables for generating function from ``func_code``. Includes
        compiled regular expressions and imports, so it does not have to do it every
        time when validation function is called.
        """
        self._generate_func_code()

        return dict(
            **self._extra_imports_objects,
            REGEX_PATTERNS=self._compile_regexps,
            re=re,
            JsonSchemaException=JsonSchemaException,
            ScopePath=ScopePath,
        )

    @property
    def global_state_code(self):
        """
        Returns global variables for generating function from ``func_code`` as code.
        Includes compiled regular expressions and imports.
        """
        self._generate_func_code()

        lines = [
            'from fastjsonschema import JsonSchemaException, ScopePath',
            '',
            '',
        ]

        if self._compile_regexps:
            regexs = ['"{}": re.compile(r"{}")'.format(key, value.pattern) for key, value in self._compile_regexps.items()]
            lines = ['import re'] + lines + [
                'REGEX_PATTERNS = {',
                '    ' + ',\n    '.join(regexs),
                '}',
                '',
            ]
            
        return '\n'.join(self._extra_imports_lines + lines)


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

    def scope_path(self, scope_name):
        return self.l('with ScopePath(path,' + scope_name + '):')

    def generate_validation_function(self, uri, name):
        """
        Generate validation function for given uri with given name
        """
        self._validation_functions_done.add(uri)
        self.l('')
        with self._resolver.resolving(uri) as definition:
            with self.l('def {}(data, name=None, path=[]):', name):
                self.generate_func_code_block(definition, 'data', 'data', 'name', clear_variables=True)
                self.l('return data')

    def generate_func_code_block(self, definition, variable, variable_name, scope_name=None, clear_variables=False):
        """
        Creates validation rules for current definition.
        """
        backup = self._definition, self._variable, self._variable_name
        self._definition, self._variable, self._variable_name = definition, variable, variable_name
        if clear_variables:
            backup_variables = self._variables
            self._variables = set()

        if scope_name:
            with self.scope_path(scope_name):
                self._generate_func_code_block(definition)
        else:
            self._generate_func_code_block(definition)

        self._definition, self._variable, self._variable_name = backup
        if clear_variables:
            self._variables = backup_variables

    def _generate_func_code_block(self, definition):
        if not isinstance(definition, dict):
            raise JsonSchemaDefinitionException("definition must be an object")
        if '$ref' in definition:
            # needed because ref overrides any sibling keywords
            self.generate_ref()
        else:
            self.run_generate_functions(definition)

    def run_generate_functions(self, definition):
        for key, func in self._json_keywords_to_function.items():
            if key in definition:
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
            self.l('{}({variable}, path=path)', name)


    # pylint: disable=invalid-name
    @indent
    def l(self, line, *args, **kwds):
        """
        Short-cut of line. Used for inserting line. It's formated with parameters
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
        spaces = ' ' * self.INDENT * self._indent

        name = self._variable_name
        if name and '{' in name:
            name = '"+"{}".format(**locals())+"'.format(self._variable_name)

        context = dict(
            self._definition or {},
            variable=self._variable,
            name=name,
            **kwds
        )
        line = line.format(*args, **context)
        line = line.replace('\n', '\\n').replace('\r', '\\r')
        self._code.append(spaces + line)
        return line

    def e(self, string):
        """
        Short-cut of escape. Used for inserting user values into a string message.

        .. code-block:: python

            self.l('raise JsonSchemaException("Variable: {}")', self.e(variable))
        """
        return str(string).replace('"', '\\"')

    def exc(self, msg, *args, rule=None):
        """
        """
        msg = 'raise JsonSchemaException("'+msg+'", value={variable}, name="{name}", definition={definition}, rule={rule}, path=path)'
        self.l(msg, *args, definition=repr(self._definition), rule=repr(rule))

    def create_variable_with_length(self):
        """
        Append code for creating variable with length of that variable
        (for example length of list or dictionary) with name ``{variable}_len``.
        It can be called several times and always it's done only when that variable
        still does not exists.
        """
        variable_name = '{}_len'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_len = len({variable})')

    def create_variable_keys(self):
        """
        Append code for creating variable with keys of that variable (dictionary)
        with a name ``{variable}_keys``. Similar to `create_variable_with_length`.
        """
        variable_name = '{}_keys'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_keys = set({variable}.keys())')

    def create_variable_is_list(self):
        """
        Append code for creating variable with bool if it's instance of list
        with a name ``{variable}_is_list``. Similar to `create_variable_with_length`.
        """
        variable_name = '{}_is_list'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_is_list = isinstance({variable}, list)')

    def create_variable_is_dict(self):
        """
        Append code for creating variable with bool if it's instance of list
        with a name ``{variable}_is_dict``. Similar to `create_variable_with_length`.
        """
        variable_name = '{}_is_dict'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_is_dict = isinstance({variable}, dict)')
