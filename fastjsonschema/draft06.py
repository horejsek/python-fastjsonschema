from .draft04 import CodeGeneratorDraft04


class CodeGeneratorDraft06(CodeGeneratorDraft04):
    def __init__(self, definition, resolver=None):
        super().__init__(definition, resolver)
        self._json_keywords_to_function.update((
            ('exclusiveMinimum', self.generate_exclusive_minimum),
            ('exclusiveMaximum', self.generate_exclusive_maximum),
            ('propertyNames', self.generate_property_names),
            ('contains', self.generate_contains),
            ('const', self.generate_const),
        ))

    def generate_exclusive_minimum(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            with self.l('if {variable} <= {exclusiveMinimum}:'):
                self.l('raise JsonSchemaException("{name} must be bigger than {exclusiveMinimum}")')

    def generate_exclusive_maximum(self):
        with self.l('if isinstance({variable}, (int, float)):'):
            with self.l('if {variable} >= {exclusiveMaximum}:'):
                self.l('raise JsonSchemaException("{name} must be smaller than {exclusiveMaximum}")')

    def generate_property_names(self):
        """
        Means that keys of object must to follow this definition.

        .. code-block:: python

            {
                'propertyNames': {
                    'maxLength': 3,
                },
            }

        Valid keys of object for this definition are foo, bar, ... but not foobar for example.
        """
        property_names_definition = self._definition.get('propertyNames', {})
        if property_names_definition is True:
            pass
        elif property_names_definition is False:
            self.create_variable_keys()
            with self.l('if {variable}_keys:'):
                self.l('raise JsonSchemaException("{name} must not be there")')
        else:
            self.create_variable_is_dict()
            with self.l('if {variable}_is_dict:'):
                self.create_variable_with_length()
                with self.l('if {variable}_len != 0:'):
                    self.l('{variable}_property_names = True')
                    with self.l('for key in {variable}:'):
                        with self.l('try:'):
                            self.generate_func_code_block(
                                property_names_definition,
                                'key',
                                self._variable_name,
                                clear_variables=True,
                            )
                        with self.l('except JsonSchemaException:'):
                            self.l('{variable}_property_names = False')
                    with self.l('if not {variable}_property_names:'):
                        self.l('raise JsonSchemaException("{name} must be named by propertyName definition")')

    def generate_contains(self):
        """
        Means that array must contain at least one defined item.

        .. code-block:: python

            {
                'contains': {
                    'type': 'number',
                },
            }

        Valid array is any with at least one number.
        """
        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            contains_definition = self._definition['contains']

            if contains_definition is False:
                self.l('raise JsonSchemaException("{name} is always invalid")')
            elif contains_definition is True:
                with self.l('if not {variable}:'):
                    self.l('raise JsonSchemaException("{name} must not be empty")')
            else:
                self.l('{variable}_contains = False')
                with self.l('for key in {variable}:'):
                    with self.l('try:'):
                        self.generate_func_code_block(
                            contains_definition,
                            'key',
                            self._variable_name,
                            clear_variables=True,
                        )
                        self.l('{variable}_contains = True')
                        self.l('break')
                    self.l('except JsonSchemaException: pass')

                with self.l('if not {variable}_contains:'):
                    self.l('raise JsonSchemaException("{name} must contain one of contains definition")')

    def generate_const(self):
        """
        Means that value is valid when is equeal to const definition.

        .. code-block:: python

            {
                'const': 42,
            }

        Only valid value is 42 in this example.
        """
        with self.l('if {variable} != {}:', self._definition['const']):
            self.l('raise JsonSchemaException("{name} must be same as const definition")')
