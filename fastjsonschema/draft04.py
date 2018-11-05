import re

from .exceptions import JsonSchemaDefinitionException
from .generator import CodeGenerator, enforce_list


JSON_TYPE_TO_PYTHON_TYPE = {
    'null': 'NoneType',
    'boolean': 'bool',
    'number': 'int, float',
    'integer': 'int',
    'string': 'str',
    'array': 'list',
    'object': 'dict',
}

DOLLAR_FINDER = re.compile(r"(?<!\\)\$")  # Finds any un-escaped $ (including inside []-sets)


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class CodeGeneratorDraft04(CodeGenerator):
    # pylint: disable=line-too-long
    # I was thinking about using ipaddress module instead of regexps for example, but it's big
    # difference in performance. With a module I got this difference: over 100 ms with a module
    # vs. 9 ms with a regex! Other modules are also unefective or not available in standard
    # library. Some regexps are not 100% precise but good enough, fast and without dependencies.
    FORMAT_REGEXS = {
        'date-time': r'^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?(?:[+-][0-2]\d:[0-5]\d|Z)?\Z',
        'email': r'^[^@]+@[^@]+\.[^@]+\Z',
        'hostname': r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{0,61}[A-Za-z0-9])\Z',
        'ipv4': r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\Z',
        'ipv6': r'^(?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)\Z',
        'uri': r'^\w+:(\/?\/?)[^\s]+\Z',
    }

    def __init__(self, definition, resolver=None):
        super().__init__(definition, resolver)
        self._json_keywords_to_function.update((
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

    def generate_type(self):
        """
        Validation of type. Can be one type or list of types.

        .. code-block:: python

            {'type': 'string'}
            {'type': ['string', 'number']}
        """
        types = enforce_list(self._definition['type'])
        try:
            python_types = ', '.join(JSON_TYPE_TO_PYTHON_TYPE[t] for t in types)
        except KeyError as exc:
            raise JsonSchemaDefinitionException('Unknown type: {}'.format(exc))

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
        if not isinstance(self._definition['enum'], (list, tuple)):
            raise JsonSchemaDefinitionException('enum must be an array')
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
            # When we know it's passing (at least once), we do not need to do another expensive try-except.
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

        Valid values for this definition are 3, 5, 6, ... but not 15 for example.
        """
        self.l('{variable}_one_of_count = 0')
        for definition_item in self._definition['oneOf']:
            # When we know it's failing (one of means exactly once), we do not need to do another expensive try-except.
            with self.l('if {variable}_one_of_count < 2:'):
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

        Valid values for this definition are 'hello', 42, {} ... but not None.

        Since draft 06 definition can be boolean. False means nothing, True
        means everything is invalid.
        """
        not_definition = self._definition['not']
        if not_definition is True:
            self.l('raise JsonSchemaException("{name} must not be there")')
        elif not_definition is False:
            return
        elif not not_definition:
            with self.l('if {}:', self._variable):
                self.l('raise JsonSchemaException("{name} must not be valid by not definition")')
        else:
            with self.l('try:'):
                self.generate_func_code_block(not_definition, self._variable, self._variable_name)
            self.l('except JsonSchemaException: pass')
            self.l('else: raise JsonSchemaException("{name} must not be valid by not definition")')

    def generate_min_length(self):
        with self.l('if isinstance({variable}, str):'):
            self.create_variable_with_length()
            if not isinstance(self._definition['minLength'], int):
                raise JsonSchemaDefinitionException('minLength must be a number')
            with self.l('if {variable}_len < {minLength}:'):
                self.l('raise JsonSchemaException("{name} must be longer than or equal to {minLength} characters")')

    def generate_max_length(self):
        with self.l('if isinstance({variable}, str):'):
            self.create_variable_with_length()
            if not isinstance(self._definition['maxLength'], int):
                raise JsonSchemaDefinitionException('maxLength must be a number')
            with self.l('if {variable}_len > {maxLength}:'):
                self.l('raise JsonSchemaException("{name} must be shorter than or equal to {maxLength} characters")')

    def generate_pattern(self):
        with self.l('if isinstance({variable}, str):'):
            pattern = self._definition['pattern']
            safe_pattern = pattern.replace('"', '\\"')
            end_of_string_fixed_pattern = DOLLAR_FINDER.sub(r'\\Z', pattern)
            self._compile_regexps[pattern] = re.compile(end_of_string_fixed_pattern)
            with self.l('if not REGEX_PATTERNS["{}"].search({variable}):', safe_pattern):
                self.l('raise JsonSchemaException("{name} must match pattern {}")', safe_pattern)

    def generate_format(self):
        """
        Means that value have to be in specified format. For example date, email or other.

        .. code-block:: python

            {'format': 'email'}

        Valid value for this definition is user@example.com but not @username
        """
        with self.l('if isinstance({variable}, str):'):
            format_ = self._definition['format']
            if format_ in self.FORMAT_REGEXS:
                format_regex = self.FORMAT_REGEXS[format_]
                self._generate_format(format_, format_ + '_re_pattern', format_regex)
            # format regex is used only in meta schemas
            elif format_ == 'regex':
                with self.l('try:'):
                    self.l('re.compile({variable})')
                with self.l('except Exception:'):
                    self.l('raise JsonSchemaException("{name} must be a valid regex")')
            else:
                self.l('pass')

    def _generate_format(self, format_name, regexp_name, regexp):
        if self._definition['format'] == format_name:
            if not regexp_name in self._compile_regexps:
                self._compile_regexps[regexp_name] = re.compile(regexp)
            with self.l('if not REGEX_PATTERNS["{}"].match({variable}):', regexp_name):
                self.l('raise JsonSchemaException("{name} must be {}")', format_name)

    def generate_minimum(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            if not isinstance(self._definition['minimum'], (int, float)):
                raise JsonSchemaDefinitionException('minimum must be a number')
            if self._definition.get('exclusiveMinimum', False):
                with self.l('if {variable} <= {minimum}:'):
                    self.l('raise JsonSchemaException("{name} must be bigger than {minimum}")')
            else:
                with self.l('if {variable} < {minimum}:'):
                    self.l('raise JsonSchemaException("{name} must be bigger than or equal to {minimum}")')

    def generate_maximum(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            if not isinstance(self._definition['maximum'], (int, float)):
                raise JsonSchemaDefinitionException('maximum must be a number')
            if self._definition.get('exclusiveMaximum', False):
                with self.l('if {variable} >= {maximum}:'):
                    self.l('raise JsonSchemaException("{name} must be smaller than {maximum}")')
            else:
                with self.l('if {variable} > {maximum}:'):
                    self.l('raise JsonSchemaException("{name} must be smaller than or equal to {maximum}")')

    def generate_multiple_of(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            if not isinstance(self._definition['multipleOf'], (int, float)):
                raise JsonSchemaDefinitionException('multipleOf must be a number')
            self.l('quotient = {variable} / {multipleOf}')
            with self.l('if int(quotient) != quotient:'):
                self.l('raise JsonSchemaException("{name} must be multiple of {multipleOf}")')

    def generate_min_items(self):
        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            if not isinstance(self._definition['minItems'], int):
                raise JsonSchemaDefinitionException('minItems must be a number')
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minItems}:'):
                self.l('raise JsonSchemaException("{name} must contain at least {minItems} items")')

    def generate_max_items(self):
        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            if not isinstance(self._definition['maxItems'], int):
                raise JsonSchemaDefinitionException('maxItems must be a number')
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
        with self.l('if {variable}_len > len(set(str({variable}_x) for {variable}_x in {variable})):'):
            self.l('raise JsonSchemaException("{name} must contain unique items")')

    def generate_items(self):
        """
        Means array is valid only when all items are valid by this definition.

        .. code-block:: python

            {
                'items': [
                    {'type': 'integer'},
                    {'type': 'string'},
                ],
            }

        Valid arrays are those with integers or strings, nothing else.

        Since draft 06 definition can be also boolean. True means nothing, False
        means everything is invalid.
        """
        items_definition = self._definition['items']
        if items_definition is True:
            return

        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            self.create_variable_with_length()
            if items_definition is False:
                with self.l('if {variable}:'):
                    self.l('raise JsonSchemaException("{name} must not be there")')
            elif isinstance(items_definition, list):
                for idx, item_definition in enumerate(items_definition):
                    with self.l('if {variable}_len > {}:', idx):
                        self.l('{variable}_{0} = {variable}[{0}]', idx)
                        self.generate_func_code_block(
                            item_definition,
                            '{}_{}'.format(self._variable, idx),
                            '{}[{}]'.format(self._variable_name, idx),
                        )
                    if isinstance(item_definition, dict) and 'default' in item_definition:
                        self.l('else: {variable}.append({})', repr(item_definition['default']))

                if 'additionalItems' in self._definition:
                    if self._definition['additionalItems'] is False:
                        self.l('if {variable}_len > {}: raise JsonSchemaException("{name} must contain only specified items")', len(items_definition))
                    else:
                        with self.l('for {variable}_x, {variable}_item in enumerate({variable}[{0}:], {0}):', len(items_definition)):
                            self.generate_func_code_block(
                                self._definition['additionalItems'],
                                '{}_item'.format(self._variable),
                                '{}[{{{}_x}}]'.format(self._variable_name, self._variable),
                            )
            else:
                if items_definition:
                    with self.l('for {variable}_x, {variable}_item in enumerate({variable}):'):
                        self.generate_func_code_block(
                            items_definition,
                            '{}_item'.format(self._variable),
                            '{}[{{{}_x}}]'.format(self._variable_name, self._variable),
                        )

    def generate_min_properties(self):
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            if not isinstance(self._definition['minProperties'], int):
                raise JsonSchemaDefinitionException('minProperties must be a number')
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minProperties}:'):
                self.l('raise JsonSchemaException("{name} must contain at least {minProperties} properties")')

    def generate_max_properties(self):
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            if not isinstance(self._definition['maxProperties'], int):
                raise JsonSchemaDefinitionException('maxProperties must be a number')
            self.create_variable_with_length()
            with self.l('if {variable}_len > {maxProperties}:'):
                self.l('raise JsonSchemaException("{name} must contain less than or equal to {maxProperties} properties")')

    def generate_required(self):
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            if not isinstance(self._definition['required'], (list, tuple)):
                raise JsonSchemaDefinitionException('required must be an array')
            self.create_variable_with_length()
            with self.l('if not all(prop in {variable} for prop in {required}):'):
                self.l('raise JsonSchemaException("{name} must contain {required} properties")')

    def generate_properties(self):
        """
        Means object with defined keys.

        .. code-block:: python

            {
                'properties': {
                    'key': {'type': 'number'},
                },
            }

        Valid object is containing key called 'key' and value any number.
        """
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
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
                if isinstance(prop_definition, dict) and 'default' in prop_definition:
                    self.l('else: {variable}["{}"] = {}', key, repr(prop_definition['default']))

    def generate_pattern_properties(self):
        """
        Means object with defined keys as patterns.

        .. code-block:: python

            {
                'patternProperties': {
                    '^x': {'type': 'number'},
                },
            }

        Valid object is containing key starting with a 'x' and value any number.
        """
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_keys()
            for pattern, definition in self._definition['patternProperties'].items():
                self._compile_regexps['{}'.format(pattern)] = re.compile(pattern)
            with self.l('for {variable}_key, {variable}_val in {variable}.items():'):
                for pattern, definition in self._definition['patternProperties'].items():
                    with self.l('if REGEX_PATTERNS["{}"].search({variable}_key):', pattern):
                        with self.l('if {variable}_key in {variable}_keys:'):
                            self.l('{variable}_keys.remove({variable}_key)')
                        self.generate_func_code_block(
                            definition,
                            '{}_val'.format(self._variable),
                            '{}.{{{}_key}}'.format(self._variable_name, self._variable),
                        )

    def generate_additional_properties(self):
        """
        Means object with keys with values defined by definition.

        .. code-block:: python

            {
                'properties': {
                    'key': {'type': 'number'},
                }
                'additionalProperties': {'type': 'string'},
            }

        Valid object is containing key called 'key' and it's value any number and
        any other key with any string.
        """
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_keys()
            add_prop_definition = self._definition["additionalProperties"]
            if add_prop_definition:
                properties_keys = list(self._definition.get("properties", {}).keys())
                with self.l('for {variable}_key in {variable}_keys:'):
                    with self.l('if {variable}_key not in {}:', properties_keys):
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
        """
        Means when object has property, it needs to have also other property.

        .. code-block:: python

            {
                'dependencies': {
                    'bar': ['foo'],
                },
            }

        Valid object is containing only foo, both bar and foo or none of them, but not
        object with only bar.

        Since draft 06 definition can be boolean or empty array. True and empty array
        means nothing, False means that key cannot be there at all.
        """
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_keys()
            for key, values in self._definition["dependencies"].items():
                if values == [] or values is True:
                    continue
                with self.l('if "{}" in {variable}_keys:', key):
                    if values is False:
                        self.l('raise JsonSchemaException("{} in {name} must not be there")', key)
                    elif isinstance(values, list):
                        for value in values:
                            with self.l('if "{}" not in {variable}_keys:', value):
                                self.l('raise JsonSchemaException("{name} missing dependency {} for {}")', value, key)
                    else:
                        self.generate_func_code_block(values, self._variable, self._variable_name, clear_variables=True)
