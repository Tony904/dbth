import os


class Parsr:
    def __init__(self, path=os.getcwd() + '/settings.txt'):
        self.settings = {}
        self.path = path
        if os.path.exists(path):
            with open(self.path, 'r') as file:
                lines = file.readlines()
            lines = self.clean_lines(lines)
            self._parse_lines(lines)
        else:
            print(f'{path} does not exist.')

    @staticmethod
    def clean_lines(lines):
        lst = []
        for line in lines:
            stripped = line.strip()
            if stripped != '':
                if stripped[0] == '#':
                    continue
                lst.append(stripped)
        return lst
    
    def _parse_lines(self, lines :list):
        for line in lines:
            k, v = self._get_kv(line)
            if k is not None:
                if k not in self.settings:
                    self.settings[k] = v
                else:
                    print(f'WARNING: Duplicate parameter {k} found. Ignoring.')

    def get(self, key :str, type_str :str = 'int', default=0, required=False):
        if key not in self.settings:
            if required:
                raise KeyError(f'{key} parameter required but not found in {self.path}')
            print(f'WARNING: Parameter ({key}) does not exist in {self.path}.')
            return self.str2type(str(default), type_str)
        return self.str2type(self.settings[key], type_str)

    @staticmethod
    def str2type(val_str :str, type_str :str):
        if type_str == 'str':
            return val_str
        if type_str == 'bool':
            if 'true' == val_str.lower() or val_str == '1':
                return True
            elif 'false' == val_str.lower() or val_str == '0':
                return False
            raise ValueError(f'Invalid boolean value ({val_str})')
        if type_str == 'int':
            return int(val_str)
        if type_str == 'float':
            return float(val_str)
        raise TypeError(f'Invalid type ({type_str}).')

    @staticmethod
    def _get_kv(line):
        if '=' not in line:
            return None, None
        kv = line.split('=')
        k = kv[0].strip()
        v = kv[1].strip()
        return k, v