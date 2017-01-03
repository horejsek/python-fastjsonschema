
#    ___
#    \./     DANGER: This module implements some code generation
# .--.O.--.          techniques involving string concatenation.
#  \/   \/           If you look at it, you might die.
#

from collections import OrderedDict
import re

from .exceptions import JsonSchemaException
from .indent import indent


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

    def __init__(self, definition):
        self._code = []
        self._compile_regexps = {}

        self._variables = set()
        self._indent = 0
        self._variable = None
        self._variable_name = None
        self._definition = None

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
        In code append code for creating variable with length of that variable
        (for example length of list or dictionary) with name ``{variable}_len``.
        It can be called several times and always it's done only when that variable
        still does not exists.
        """
        variable_name = '{}_len'.format(self._variable)
        if variable_name in self._variables:
            return
        self._variables.add(variable_name)
        self.l('{variable}_len = len({variable})')


    def generate_func_code(self, definition):
        """
        Creates base code of validation function and calls helper
        for creating code by definition.
        """
        with self.l('def func(data):'):
            self.l('NoneType = type(None)')
            self.generate_func_code_block(definition, 'data', 'data')
            self.l('return data')

    def generate_func_code_block(self, definition, variable, variable_name):
        """
        Creates validation rules for current definition.
        """
        backup = self._definition, self._variable, self._variable_name
        self._definition, self._variable, self._variable_name = definition, variable, variable_name

        for key, func in self._json_keywords_to_function.items():
            if key in definition:
                func()

        self._definition, self._variable, self._variable_name = backup

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
            self.generate_func_code_block(definition_item, self._variable, self._variable_name)

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
                    self.generate_func_code_block(definition_item, self._variable, self._variable_name)
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
                self.generate_func_code_block(definition_item, self._variable, self._variable_name)
                self.l('{variable}_one_of_count += 1')
            self.l('except JsonSchemaException: pass')

        with self.l('if {variable}_one_of_count != 1:'):
            self.l('raise JsonSchemaException("{name} must be valid exactly by one of oneOf definition")')

    def generate_not(self):
        """
        Means that value have not to be valid by this definition.

        .. code-block:: python

            {'not': {'type': 'null'}}

        Valid values for this definitions are 'hello', 42, ... but not None.
        """
        with self.l('try:'):
            self.generate_func_code_block(self._definition['not'], self._variable, self._variable_name)
        self.l('except JsonSchemaException: pass')
        self.l('else: raise JsonSchemaException("{name} must not be valid by not definition")')

    def generate_min_length(self):
        self.create_variable_with_length()
        with self.l('if {variable}_len < {minLength}:'):
            self.l('raise JsonSchemaException("{name} must be longer than or equal to {minLength} characters")')

    def generate_max_length(self):
        self.create_variable_with_length()
        with self.l('if {variable}_len > {maxLength}:'):
            self.l('raise JsonSchemaException("{name} must be shorter than or equal to {maxLength} characters")')

    def generate_pattern(self):
        self._compile_regexps['{}_re'.format(self._variable)] = re.compile(self._definition['pattern'])
        with self.l('if not {variable}_re.match({variable}):'):
            self.l('raise JsonSchemaException("{name} must match pattern {pattern}")')

    def generate_minimum(self):
        if self._definition.get('exclusiveMinimum', False):
            with self.l('if {variable} <= {minimum}:'):
                self.l('raise JsonSchemaException("{name} must be bigger than {minimum}")')
        else:
            with self.l('if {variable} < {minimum}:'):
                self.l('raise JsonSchemaException("{name} must be bigger than or equal to {minimum}")')

    def generate_maximum(self):
        if self._definition.get('exclusiveMaximum', False):
            with self.l('if {variable} >= {maximum}:'):
                self.l('raise JsonSchemaException("{name} must be smaller than {maximum}")')
        else:
            with self.l('if {variable} > {maximum}:'):
                self.l('raise JsonSchemaException("{name} must be smaller than or equal to {maximum}")')

    def generate_multiple_of(self):
        with self.l('if {variable} % {multipleOf} != 0:'):
            self.l('raise JsonSchemaException("{name} must be multiple of {multipleOf}")')

    def generate_min_items(self):
        self.create_variable_with_length()
        with self.l('if {variable}_len < {minItems}:'):
            self.l('raise JsonSchemaException("{name} must contain at least {minItems} items")')

    def generate_max_items(self):
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
        with self.l('if {variable}_len > len(set({variable})):'):
            self.l('raise JsonSchemaException("{name} must contain unique items")')

    def generate_items(self):
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
                    self.l('if {variable}_len > {}: raise JsonSchemaException("{name} must contain only spcified items")', len(self._definition['items']))
                else:
                    with self.l('for {variable}_x, {variable}_item in enumerate({variable}[{0}:], {0}):', len(self._definition['items'])):
                        self.generate_func_code_block(
                            self._definition['additionalItems'],
                            '{}_item'.format(self._variable),
                            '{}[{{{}_x}}]'.format(self._variable_name, self._variable),
                        )
        else:
            with self.l('for {variable}_x, {variable}_item in enumerate({variable}):'):
                self.generate_func_code_block(
                    self._definition['items'],
                    '{}_item'.format(self._variable),
                    '{}[{{{}_x}}]'.format(self._variable_name, self._variable),
                )

    def generate_min_properties(self):
        self.create_variable_with_length()
        with self.l('if {variable}_len < {minProperties}:'):
            self.l('raise JsonSchemaException("{name} must contain at least {minProperties} properties")')

    def generate_max_properties(self):
        self.create_variable_with_length()
        with self.l('if {variable}_len > {maxProperties}:'):
            self.l('raise JsonSchemaException("{name} must contain less than or equal to {maxProperties} properties")')

    def generate_required(self):
        self.create_variable_with_length()
        with self.l('if not all(prop in {variable} for prop in {required}):'):
            self.l('raise JsonSchemaException("{name} must contain {required} properties")')

    def generate_properties(self):
        self.l('{variable}_keys = set({variable}.keys())')
        for key, prop_definition in self._definition['properties'].items():
            with self.l('if "{}" in {variable}_keys:', key):
                self.l('{variable}_keys.remove("{}")', key)
                self.l('{variable}_{0} = {variable}["{0}"]', key)
                self.generate_func_code_block(
                    prop_definition,
                    '{}_{}'.format(self._variable, key),
                    '{}.{}'.format(self._variable_name, key),
                )
            if 'default' in prop_definition:
                self.l('else: {variable}["{}"] = {}', key, repr(prop_definition['default']))

        if 'additionalProperties' in self._definition:
            if self._definition['additionalProperties'] is False:
                self.l('if {variable}_keys: raise JsonSchemaException("{name} must contain only spcified properties")')
            else:
                with self.l('for {variable}_key in {variable}_keys:'):
                    self.l('{variable}_value = {variable}.get({variable}_key)')
                    self.generate_func_code_block(
                        self._definition['additionalProperties'],
                        '{}_value'.format(self._variable),
                        '{}.{{{}_key}}'.format(self._variable_name, self._variable),
                    )
