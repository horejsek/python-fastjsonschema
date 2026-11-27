from collections import OrderedDict

from .draft07 import CodeGeneratorDraft07
from .exceptions import JsonSchemaDefinitionException
from .generator import VALIDATION_EXCEPTIONS


class CodeGeneratorDraft2019(CodeGeneratorDraft07):
    FORMAT_REGEXS = dict(CodeGeneratorDraft07.FORMAT_REGEXS, **{
        'uuid': r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\Z',
        # ISO 8601 duration from RFC 3339 Appendix A
        'duration': (
            r'^P(?!$)'
            r'(?:'
            r'[0-9]+W'
            r'|(?:[0-9]+Y)?(?:[0-9]+M)?(?:[0-9]+D)?(?:T(?=[0-9])(?:[0-9]+H)?(?:[0-9]+M)?(?:[0-9]+S)?)?'
            r')\Z'
        ),
    })

    def __init__(
        self,
        definition,
        resolver=None,
        formats={},
        use_default=True,
        use_formats=True,
        detailed_exceptions=True,
        fast_fail=True
    ):
        super().__init__(definition, resolver, formats, use_default, use_formats, detailed_exceptions, fast_fail)
        # Like dependencies, check them before properties generates default values.
        keywords = list(self._json_keywords_to_function.items())
        index = [key for key, _ in keywords].index('dependencies') + 1
        keywords[index:index] = [
            ('dependentRequired', self.generate_dependent_required),
            ('dependentSchemas', self.generate_dependent_schemas),
        ]
        self._json_keywords_to_function = OrderedDict(keywords)

    def generate_dependent_required(self):
        """
        Means when object has property, it needs to have also other properties.

        .. code-block:: python

            {
                'dependentRequired': {
                    'bar': ['foo'],
                },
            }

        Valid object is containing only foo, both bar and foo or none of them, but not
        object with only bar.
        """
        self._generate_dependencies('dependentRequired')

    def generate_dependent_schemas(self):
        """
        Means when object has property, the whole object needs to be valid against
        the schema.

        .. code-block:: python

            {
                'dependentSchemas': {
                    'bar': {'required': ['foo']},
                },
            }
        """
        self._generate_dependencies('dependentSchemas')

    def generate_contains(self):
        """
        Means that array must contain at least ``minContains`` (default 1) and at most
        ``maxContains`` (default unlimited) items valid against the contains definition.

        .. code-block:: python

            {
                'contains': {'type': 'number'},
                'minContains': 2,
                'maxContains': 3,
            }

        Valid array is any with two or three numbers. With ``minContains`` set to 0,
        an array without any number (also an empty one) is valid too.
        """
        min_contains = self._definition.get('minContains', 1)
        max_contains = self._definition.get('maxContains')
        for keyword, value in (('minContains', min_contains), ('maxContains', max_contains)):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or value != int(value)
            ):
                raise JsonSchemaDefinitionException('{} must be a non-negative integer'.format(keyword))

        if min_contains == 1 and max_contains is None:
            # Plain contains: at least one valid item, as in earlier drafts.
            super().generate_contains()
            return

        self.create_variable_is_list()
        with self.l('if {variable}_is_list:'):
            contains_definition = self._definition['contains']

            if contains_definition is False:
                self.l('{variable}_contains = 0')
            elif contains_definition is True:
                self.create_variable_with_length()
                self.l('{variable}_contains = {variable}_len')
            else:
                self.l('{variable}_contains = 0')
                with self.l('for {variable}_key in {variable}:'):
                    with self.l('try:'):
                        with self.trial_validation():
                            self.generate_func_code_block(
                                contains_definition,
                                '{}_key'.format(self._variable),
                                self._variable_name,
                                clear_variables=True,
                            )
                        self.l('{variable}_contains += 1')
                    self.l('except {}: pass', VALIDATION_EXCEPTIONS)

            with self.l('if {variable}_contains < {}:', min_contains):
                self.exc(
                    '{name} must contain at least {} items valid against contains definition',
                    min_contains,
                    rule='minContains',
                )
            if max_contains is not None:
                with self.l('if {variable}_contains > {}:', max_contains):
                    self.exc(
                        '{name} must contain at most {} items valid against contains definition',
                        max_contains,
                        rule='maxContains',
                    )
