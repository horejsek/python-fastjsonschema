from collections import OrderedDict

from .draft07 import CodeGeneratorDraft07


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
