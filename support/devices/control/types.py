from enum import Enum

class types(Enum):
    generic = 'generic'
    binary_switch = 'binary_switch'
    int_input = 'int_input'
    access_code_input = 'access_code_input'


class type_generic():

    _get_enpoint = None
    _query_only = False

    _set_endpoint = None
    _network_name = None

    def __init__(self, network_name, **kwargs):
        self._network_name = network_name
        self._type = types.generic
        try:
            self._get_enpoint = kwargs['get_endpoint']
        except KeyError:
            pass
        try:
            self._set_endpoint = kwargs['set_endpoint']
        except KeyError:
            pass
        try:
            self._query_only = kwargs['query_only']
        except KeyError:
            pass

    def _property(self):
        return None

    @property
    def network_name(self):
        return self._network_name

    @property
    def get_endpoint(self):
        return self._get_enpoint

    @property
    def query_only(self):
        return self._query_only

    @property
    def set_endpoint(self):
        return self._set_endpoint

    @property
    def properties(self):
        return self._property()

    @property
    def control_type(self):
        return self._type.value

    @property
    def control(self):
        return_control = dict()
        if self._get_enpoint:
            return_control['get_enpoint'] = self._network_name
            return_control['query_endpoint'] = 'get/{}'.format(self._network_name)

        if self._set_endpoint:
            return_control['set_endpoint'] = self._network_name
        return_control['type'] = self._type.value
        return_control['properties'] = self._property

        return return_control

class type_binary(type_generic):

    def __init__(self, network_name, switch_name, **kwargs):
        type_generic.__init__(self, network_name, **kwargs)
        self._type = types.binary_switch
        try:
            self._low_name = kwargs['low_name']
        except KeyError:
            self._low_name = 'Off'
        try:
            self._high_name = kwargs['high_name']
        except KeyError:
            self._high_name = 'On'
        self._switch_name = switch_name

    def _property(self):
        return {
            'name': self._switch_name,
            'low_name': self._low_name,
            'high_name': self._high_name,
            'state': self.get_endpoint()
        }

class type_int_input(type_generic):
    def __init__(self, network_name, **kwargs):
        type_generic.__init__(self, network_name, **kwargs)
        try:
            self._input_name = kwargs['input_name']
        except KeyError:
            self._input_name = 'Integer Input'
        try:
            self._min_digits = kwargs['min_digits']
        except KeyError:
            self._min_digits = 4
        try:
            self._max_digits = kwargs['max_digits']
        except KeyError:
            self._max_digits = 10

    def _render_digits(self, digits):
        out_string = ''
        for x in range(digits):
            out_string += 'x'
        return out_string
    def _property_init(self):
        return {
            'name' : self._input_name,
            'min_digits' : self._render_digits(self._min_digits),
            'max_digits' : self._render_digits(self._max_digits)
        }

    def _property(self):
        return self._property_init()

class type_access_code_input(type_int_input):
    def __init__(self, network_name, **kwargs):
        type_int_input.__init__(self, network_name, **kwargs)
        self._type = types.access_code_input

    def _property(self):
        values = self._property_init()
        get_values = self.get_endpoint()
        return {**values, **get_values}