
#    ___
#    \./     DANGER: This module implements some code generation
# .--.O.--.          techniques involving string concatenation.
#  \/   \/           If you look at it, you might die.
#

from collections import OrderedDict
import re

import requests

from .exceptions import JsonSchemaException
from .indent import indent
from .ref_resolver import RefResolver


def enforce_list(variable):
    if isinstance(variable, list):
        return variable
    return [variable]


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

    JSON_TYPE_TO_PYTHON_TYPE = {
        'null': 'NoneType',
        'boolean': 'bool',
        'number': 'int, float',
        'integer': 'int',
        'string': 'str',
        'array': 'list',
        'object': 'dict',
    }

    def __init__(self, definition, resolver=None):
        self._code = []
        self._compile_regexps = {}

        self._variables = set()
        self._indent = 0
        self._variable = None
        self._variable_name = None
        self._root_definition = definition
        self._definition = None

        # map schema URIs to validation function names for functions
        # that are not yet generated, but need to be generated
        self._needed_validation_functions = {}
        # validation function names that are already done
        self._validation_functions_done = set()

        if resolver == None:
            resolver = RefResolver.from_schema(definition)
        self._resolver = resolver
        # add main function to `self._needed_validation_functions`
        self._needed_validation_functions[self._resolver.get_uri()] = self._resolver.get_scope_name()

        self._json_keywords_to_function = OrderedDict((
            ('type', self.generate_type),
            ('enum', self.generate_enum),
            ('allOf', self.generate_all_of),
            ('anyOf', self.generate_any_of),
            ('oneOf', self.generate_one_of),
            ('not', self.generate_not),
            ('minLength', self.generate_min_length),
            ('maxLength', self.generate_max_length),
            ('pattern', self.generate_pattern),
            ('format', self.generate_format),
            ('minimum', self.generate_minimum),
            ('maximum', self.generate_maximum),
            ('multipleOf', self.generate_multiple_of),
            ('minItems', self.generate_min_items),
            ('maxItems', self.generate_max_items),
            ('uniqueItems', self.generate_unique_items),
            ('items', self.generate_items),
            ('minProperties', self.generate_min_properties),
            ('maxProperties', self.generate_max_properties),
            ('required', self.generate_required),
            ('properties', self.generate_properties),
            ('patternProperties', self.generate_pattern_properties),
            ('additionalProperties', self.generate_additional_properties),
            ('dependencies', self.generate_dependencies),
        ))

        self.generate_func_code(definition)

    @property
    def func_code(self):
        """
        Returns generated code of whole validation function as string.
        """
        return '\n'.join(self._code)

    @property
    def global_state(self):
        """
        Returns global variables for generating function from ``func_code``. Includes
        compiled regular expressions and imports, so it does not have to do it every
        time when validation function is called.
        """
        return dict(
            self._compile_regexps,
            re=re,
            JsonSchemaException=JsonSchemaException,
        )

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
        self._code.append(spaces + line.format(*args, **context))

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
        with name ``{variable}_len``. It can be called several times and always
        it's done only when that variable still does not exists.
        """
        variable_name = '{}_keys'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_keys = set({variable}.keys())')

    def generate_func_code(self, definition):
        """
        Creates base code of validation function and calls helper
        for creating code by definition.
        """
        self.l('NoneType = type(None)')
        # Generate parts that are referenced and not yet generated
        while len(self._needed_validation_functions) > 0:
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
            with self.l('def {}(data):', name):
                self.generate_func_code_block(definition, 'data', 'data', clear_variables=True)
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

        if '$ref' in definition:
            # needed because ref overrides any sibling keywords
            self.generate_ref()
        else:
            self.run_generate_functions(definition)

        self._definition, self._variable, self._variable_name = backup
        if clear_variables:
            self._variables = backup_variables

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
            self.l('{}({variable})', name)

    def generate_type(self):
        """
        Validation of type. Can be one type or list of types.

        .. code-block:: python

            {'type': 'string'}
            {'type': ['string', 'number']}
        """
        types = enforce_list(self._definition['type'])
        python_types = ', '.join(self.JSON_TYPE_TO_PYTHON_TYPE.get(t) for t in types)

        extra = ''
        if ('number' in types or 'integer' in types) and 'boolean' not in types:
            extra = ' or isinstance({variable}, bool)'.format(variable=self._variable)

        with self.l('if not isinstance({variable}, ({})){}:', python_types, extra):
            self.l('raise JsonSchemaException("{name} must be {}")', ' or '.join(types))


    def generate_enum(self):
        """
        Means that only value specified in the enum is valid.

        .. code-block:: python

            {
                'enum': ['a', 'b'],
            }
        """
        with self.l('if {variable} not in {enum}:'):
            self.l('raise JsonSchemaException("{name} must be one of {enum}")')

    def generate_all_of(self):
        """
        Means that value have to be valid by all of those definitions. It's like put it in
        one big definition.

        .. code-block:: python

            {
                'allOf': [
                    {'type': 'number'},
                    {'minimum': 5},
                ],
            }

        Valid values for this definition are 5, 6, 7, ... but not 4 or 'abc' for example.
        """
        for definition_item in self._definition['allOf']:
            self.generate_func_code_block(definition_item, self._variable, self._variable_name, clear_variables=True)

    def generate_any_of(self):
        """
        Means that value have to be valid by any of those definitions. It can also be valid
        by all of them.

        .. code-block:: python

            {
                'anyOf': [
                    {'type': 'number', 'minimum': 10},
                    {'type': 'number', 'maximum': 5},
                ],
            }

        Valid values for this definition are 3, 4, 5, 10, 11, ... but not 8 for example.
        """
        self.l('{variable}_any_of_count = 0')
        for definition_item in self._definition['anyOf']:
            with self.l('if not {variable}_any_of_count:'):
                with self.l('try:'):
                    self.generate_func_code_block(definition_item, self._variable, self._variable_name, clear_variables=True)
                    self.l('{variable}_any_of_count += 1')
                self.l('except JsonSchemaException: pass')

        with self.l('if not {variable}_any_of_count:'):
            self.l('raise JsonSchemaException("{name} must be valid by one of anyOf definition")')

    def generate_one_of(self):
        """
        Means that value have to be valid by only one of those definitions. It can't be valid
        by two or more of them.

        .. code-block:: python

            {
                'oneOf': [
                    {'type': 'number', 'multipleOf': 3},
                    {'type': 'number', 'multipleOf': 5},
                ],
            }

        Valid values for this definitions are 3, 5, 6, ... but not 15 for example.
        """
        self.l('{variable}_one_of_count = 0')
        for definition_item in self._definition['oneOf']:
            with self.l('try:'):
                self.generate_func_code_block(definition_item, self._variable, self._variable_name, clear_variables=True)
                self.l('{variable}_one_of_count += 1')
            self.l('except JsonSchemaException: pass')

        with self.l('if {variable}_one_of_count != 1:'):
            self.l('raise JsonSchemaException("{name} must be valid exactly by one of oneOf definition")')

    def generate_not(self):
        """
        Means that value have not to be valid by this definition.

        .. code-block:: python

            {'not': {'type': 'null'}}

        Valid values for this definitions are 'hello', 42, {} ... but not None.
        """
        if not self._definition['not']:
            with self.l('if {}:', self._variable):
                self.l('raise JsonSchemaException("{name} must not be valid by not definition")')
        else:
            with self.l('try:'):
                self.generate_func_code_block(self._definition['not'], self._variable, self._variable_name)
            self.l('except JsonSchemaException: pass')
            self.l('else: raise JsonSchemaException("{name} must not be valid by not definition")')

    def generate_min_length(self):
        with self.l('if isinstance({variable}, str):'):
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minLength}:'):
                self.l('raise JsonSchemaException("{name} must be longer than or equal to {minLength} characters")')

    def generate_max_length(self):
        with self.l('if isinstance({variable}, str):'):
            self.create_variable_with_length()
            with self.l('if {variable}_len > {maxLength}:'):
                self.l('raise JsonSchemaException("{name} must be shorter than or equal to {maxLength} characters")')

    def generate_pattern(self):
        with self.l('if isinstance({variable}, str):'):
            self._compile_regexps['{}_re'.format(self._definition['pattern'])] = re.compile(self._definition['pattern'])
            with self.l('if not globals()["{}_re"].search({variable}):', self._definition['pattern']):
                self.l('raise JsonSchemaException("{name} must match pattern {pattern}")')

    def generate_format(self):
        with self.l('if isinstance({variable}, str):'):
            self._generate_format('date-time', 'date_time_re_pattern', r'^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+(?:[+-][0-2]\d:[0-5]\d|Z)?$')
            self._generate_format('uri', 'uri_re_pattern', r'^\w+:(\/?\/?)[^\s]+$')
            self._generate_format('email', 'email_re_pattern', r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
            self._generate_format('ipv4', 'ipv4_re_pattern', r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
            self._generate_format('ipv6', 'ipv6_re_pattern', r'^(?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)$')
            self._generate_format('hostname', 'hostname_re_pattern', r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{1,62}[A-Za-z0-9])$')
            # format regex is used only in meta schemas
            if self._definition['format'] == 'regex':
                with self.l('try:'):
                    self.l('re.compile({variable})')
                with self.l('except Exception:'):
                    self.l('raise JsonSchemaException("{name} must be a valid regex")')

    def _generate_format(self, format_name, regexp_name, regexp):
            if self._definition['format'] == format_name:
                self._compile_regexps[regexp_name] = re.compile(regexp)
                with self.l('if not {}.match({variable}):', regexp_name):
                    self.l('raise JsonSchemaException("{name} must be {}")', format_name)

    def generate_minimum(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            if self._definition.get('exclusiveMinimum', False):
                with self.l('if {variable} <= {minimum}:'):
                    self.l('raise JsonSchemaException("{name} must be bigger than {minimum}")')
            else:
                with self.l('if {variable} < {minimum}:'):
                    self.l('raise JsonSchemaException("{name} must be bigger than or equal to {minimum}")')

    def generate_maximum(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            if self._definition.get('exclusiveMaximum', False):
                with self.l('if {variable} >= {maximum}:'):
                    self.l('raise JsonSchemaException("{name} must be smaller than {maximum}")')
            else:
                with self.l('if {variable} > {maximum}:'):
                    self.l('raise JsonSchemaException("{name} must be smaller than or equal to {maximum}")')

    def generate_multiple_of(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            self.l('quotient = {variable} / {multipleOf}')
            with self.l('if int(quotient) != quotient:'):
                self.l('raise JsonSchemaException("{name} must be multiple of {multipleOf}")')

    def generate_min_items(self):
        with self.l('if isinstance({variable}, list):'):
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minItems}:'):
                self.l('raise JsonSchemaException("{name} must contain at least {minItems} items")')

    def generate_max_items(self):
        with self.l('if isinstance({variable}, list):'):
            self.create_variable_with_length()
            with self.l('if {variable}_len > {maxItems}:'):
                self.l('raise JsonSchemaException("{name} must contain less than or equal to {maxItems} items")')

    def generate_unique_items(self):
        """
        With Python 3.4 module ``timeit`` recommended this solutions:

        .. code-block:: python

            >>> timeit.timeit("len(x) > len(set(x))", "x=range(100)+range(100)", number=100000)
            0.5839540958404541
            >>> timeit.timeit("len({}.fromkeys(x)) == len(x)", "x=range(100)+range(100)", number=100000)
            0.7094449996948242
            >>> timeit.timeit("seen = set(); any(i in seen or seen.add(i) for i in x)", "x=range(100)+range(100)", number=100000)
            2.0819358825683594
            >>> timeit.timeit("np.unique(x).size == len(x)", "x=range(100)+range(100); import numpy as np", number=100000)
            2.1439831256866455
        """
        self.create_variable_with_length()
        with self.l('if {variable}_len > len(set(str(x) for x in {variable})):'):
            self.l('raise JsonSchemaException("{name} must contain unique items")')

    def generate_items(self):
        with self.l('if isinstance({variable}, list):'):
            self.create_variable_with_length()
            if isinstance(self._definition['items'], list):
                for x, item_definition in enumerate(self._definition['items']):
                    with self.l('if {variable}_len > {}:', x):
                        self.l('{variable}_{0} = {variable}[{0}]', x)
                        self.generate_func_code_block(
                            item_definition,
                            '{}_{}'.format(self._variable, x),
                            '{}[{}]'.format(self._variable_name, x),
                        )
                    if 'default' in item_definition:
                        self.l('else: {variable}.append({})', repr(item_definition['default']))

                if 'additionalItems' in self._definition:
                    if self._definition['additionalItems'] is False:
                        self.l('if {variable}_len > {}: raise JsonSchemaException("{name} must contain only specified items")', len(self._definition['items']))
                    else:
                        with self.l('for {variable}_x, {variable}_item in enumerate({variable}[{0}:], {0}):', len(self._definition['items'])):
                            self.generate_func_code_block(
                                self._definition['additionalItems'],
                                '{}_item'.format(self._variable),
                                '{}[{{{}_x}}]'.format(self._variable_name, self._variable),
                            )
            else:
                if self._definition['items']:
                    with self.l('for {variable}_x, {variable}_item in enumerate({variable}):'):
                        self.generate_func_code_block(
                            self._definition['items'],
                            '{}_item'.format(self._variable),
                            '{}[{{{}_x}}]'.format(self._variable_name, self._variable),
                        )

    def generate_min_properties(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minProperties}:'):
                self.l('raise JsonSchemaException("{name} must contain at least {minProperties} properties")')

    def generate_max_properties(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_with_length()
            with self.l('if {variable}_len > {maxProperties}:'):
                self.l('raise JsonSchemaException("{name} must contain less than or equal to {maxProperties} properties")')

    def generate_required(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_with_length()
            with self.l('if not all(prop in {variable} for prop in {required}):'):
                self.l('raise JsonSchemaException("{name} must contain {required} properties")')

    def generate_properties(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_keys()
            for key, prop_definition in self._definition['properties'].items():
                key_name = re.sub(r'($[^a-zA-Z]|[^a-zA-Z0-9])', '', key)
                with self.l('if "{}" in {variable}_keys:', key):
                    self.l('{variable}_keys.remove("{}")', key)
                    self.l('{variable}_{0} = {variable}["{1}"]', key_name, key)
                    self.generate_func_code_block(
                        prop_definition,
                        '{}_{}'.format(self._variable, key_name),
                        '{}.{}'.format(self._variable_name, key),
                    )
                if 'default' in prop_definition:
                    self.l('else: {variable}["{}"] = {}', key, repr(prop_definition['default']))

    def generate_pattern_properties(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_keys()
            for pattern, definition in self._definition['patternProperties'].items():
                self._compile_regexps['{}_re'.format(pattern)] = re.compile(pattern)
            with self.l('for key, val in {variable}.items():'):
                for pattern, definition in self._definition['patternProperties'].items():
                    with self.l('if globals()["{}_re"].search(key):', pattern):
                        with self.l('if key in {variable}_keys:'):
                            self.l('{variable}_keys.remove(key)')
                        self.generate_func_code_block(
                            definition,
                            'val',
                            '{}.{{key}}'.format(self._variable_name),
                        )

    def generate_additional_properties(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_keys()
            add_prop_definition = self._definition["additionalProperties"]
            if add_prop_definition:
                properties_keys = self._definition.get("properties", {}).keys()
                with self.l('for {variable}_key in {variable}_keys:'):
                    with self.l('if {variable}_key not in "{}":', properties_keys):
                        self.l('{variable}_value = {variable}.get({variable}_key)')
                        self.generate_func_code_block(
                            add_prop_definition,
                            '{}_value'.format(self._variable),
                            '{}.{{{}_key}}'.format(self._variable_name, self._variable),
                        )
            else:
                with self.l('if {variable}_keys:'):
                    self.l('raise JsonSchemaException("{name} must contain only specified properties")')

    def generate_dependencies(self):
        with self.l('if isinstance({variable}, dict):'):
            self.create_variable_keys()
            for key, values in self._definition["dependencies"].items():
                with self.l('if "{}" in {variable}_keys:', key):
                    if isinstance(values, list):
                        for value in values:
                            with self.l('if "{}" not in {variable}_keys:', value):
                                self.l('raise JsonSchemaException("{name} missing dependency {} for {}")', value, key)
                    else:
                        self.generate_func_code_block(values, self._variable, self._variable_name, clear_variables=True)
