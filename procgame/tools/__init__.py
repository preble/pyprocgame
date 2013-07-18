__all__ = [
	'tools',
	]

import yaml as _yaml
import pinproc as _pinproc

def machine_type_from_yaml(config_path):
	config = _yaml.load(open(config_path, 'r'))
	machine_type = config['PRGame']['machineType']
	return _pinproc.normalize_machine_type(machine_type)
