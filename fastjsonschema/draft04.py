import re

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


# pylint: disable=line-too-long
FORMAT_REGEXS = {
    'date-time': r'^\d{4}-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d\.\d+(?:[+-][0-2]\d:[0-5]\d|Z)?$',
    'uri': r'^\w+:(\/?\/?)[^\s]+$',
    'email': r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
    'ipv4': r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    'ipv6': r'^(?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)$',
    'hostname': r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]{1,62}[A-Za-z0-9])$',
}


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class CodeGeneratorDraft04(CodeGenerator):
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
        python_types = ', '.join(JSON_TYPE_TO_PYTHON_TYPE.get(t) for t in types)

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

        Valid values for this definitions are 3, 5, 6, ... but not 15 for example.
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
            self._compile_regexps['{}'.format(self._definition['pattern'])] = re.compile(self._definition['pattern'])
            with self.l('if not REGEX_PATTERNS["{}"].search({variable}):', self._definition['pattern']):
                self.l('raise JsonSchemaException("{name} must match pattern {pattern}")')

    def generate_format(self):
        with self.l('if isinstance({variable}, str):'):
            format_ = self._definition['format']
            if format_ in FORMAT_REGEXS:
                format_regex = FORMAT_REGEXS[format_]
                self._generate_format(format_, format_ + '_re_pattern', format_regex)
            # format regex is used only in meta schemas
            elif format_ == 'regex':
                with self.l('try:'):
                    self.l('re.compile({variable})')
                with self.l('except Exception:'):
                    self.l('raise JsonSchemaException("{name} must be a valid regex")')

    def _generate_format(self, format_name, regexp_name, regexp):
        if self._definition['format'] == format_name:
            if not regexp_name in self._compile_regexps:
                self._compile_regexps[regexp_name] = re.compile(regexp)
            with self.l('if not REGEX_PATTERNS["{}"].match({variable}):', regexp_name):
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
        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minItems}:'):
                self.l('raise JsonSchemaException("{name} must contain at least {minItems} items")')

    def generate_max_items(self):
        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
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
        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            self.create_variable_with_length()
            if isinstance(self._definition['items'], list):
                for idx, item_definition in enumerate(self._definition['items']):
                    with self.l('if {variable}_len > {}:', idx):
                        self.l('{variable}_{0} = {variable}[{0}]', idx)
                        self.generate_func_code_block(
                            item_definition,
                            '{}_{}'.format(self._variable, idx),
                            '{}[{}]'.format(self._variable_name, idx),
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
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_with_length()
            with self.l('if {variable}_len < {minProperties}:'):
                self.l('raise JsonSchemaException("{name} must contain at least {minProperties} properties")')

    def generate_max_properties(self):
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_with_length()
            with self.l('if {variable}_len > {maxProperties}:'):
                self.l('raise JsonSchemaException("{name} must contain less than or equal to {maxProperties} properties")')

    def generate_required(self):
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_with_length()
            with self.l('if not all(prop in {variable} for prop in {required}):'):
                self.l('raise JsonSchemaException("{name} must contain {required} properties")')

    def generate_properties(self):
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
                if 'default' in prop_definition:
                    self.l('else: {variable}["{}"] = {}', key, repr(prop_definition['default']))

    def generate_pattern_properties(self):
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_keys()
            for pattern, definition in self._definition['patternProperties'].items():
                self._compile_regexps['{}'.format(pattern)] = re.compile(pattern)
            with self.l('for key, val in {variable}.items():'):
                for pattern, definition in self._definition['patternProperties'].items():
                    with self.l('if REGEX_PATTERNS["{}"].search(key):', pattern):
                        with self.l('if key in {variable}_keys:'):
                            self.l('{variable}_keys.remove(key)')
                        self.generate_func_code_block(
                            definition,
                            'val',
                            '{}.{{key}}'.format(self._variable_name),
                        )

    def generate_additional_properties(self):
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
        self.create_variable_is_dict()
        with self.l('if {variable}_is_dict:'):
            self.create_variable_keys()
            for key, values in self._definition["dependencies"].items():
                with self.l('if "{}" in {variable}_keys:', key):
                    if isinstance(values, list):
                        for value in values:
                            with self.l('if "{}" not in {variable}_keys:', value):
                                self.l('raise JsonSchemaException("{name} missing dependency {} for {}")', value, key)
                    else:
                        self.generate_func_code_block(values, self._variable, self._variable_name, clear_variables=True)
