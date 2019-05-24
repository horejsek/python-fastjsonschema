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


def test_clear_variables(asserter):
    value = {
        'bar': {'baz': 'foo'}
    }
    asserter({
        'type': 'object',
        'patternProperties': {
            'foo': {'type': 'object', 'required': ['baz']},
            'bar': {'type': 'object', 'required': ['baz']}
        }
    }, value, value)
