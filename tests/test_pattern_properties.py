def test_dont_override_variable_names(asserter):
    value = {
        'foo:bar': {
            'baz': {
                'bat': {},
            },
            'bit': {},
        },
    }
    asserter({
        'type': 'object',
        'patternProperties': {
            '^foo:': {
                'type': 'object',
                'properties': {
                    'baz': {
                        'type': 'object',
                        'patternProperties': {
                            '^b': {'type': 'object'},
                        },
                    },
                    'bit': {'type': 'object'},
                },
            },
        },
    }, value, value)
