import logging
from glob import glob
from .weapon import Weapon
from .vehicle import Vehicle


class EquipmentDatabase:
    def __init__(self, weapon_dir, vehicle_dir):
        self.weapon_dir = weapon_dir
        self.vehicle_dir = vehicle_dir
        self.weapons = {}
        self.vehicles = {}

        self.load_weapons()
        self.load_vehicles()

    def load_weapons(self):
        # Load all weapon YAML files from the weapon directory
        logging.info('Loading weapons from {}'.format(self.weapon_dir))
        weapon_files = glob(f'{self.weapon_dir}/**/*.yaml', recursive=True) \
                    + glob(f'{self.weapon_dir}/**/*.yml', recursive=True)
        for file in weapon_files:
            try:
                weapon = Weapon(file)
                self.weapons[weapon.name] = weapon
                logging.info('Weapon {} loaded.'.format(weapon.name))
            except Exception as e:
                logging.error(f'Failed to load weapon from {file}: {str(e)}')

    def load_vehicles(self):
        # Load all vehicle YAML files from the vehicle directory
        logging.info('Loading vehicles from {}'.format(self.vehicle_dir))
        vehicle_files = glob(f'{self.vehicle_dir}/**/*.yaml', recursive=True) \
                    + glob(f'{self.vehicle_dir}/**/*.yml', recursive=True)
        for file in vehicle_files:
            try:
                vehicle = Vehicle(file, list(self.weapons.values()))
                self.vehicles[vehicle.name] = vehicle
                logging.info('Vehicle {} loaded.'.format(vehicle.name))
            except Exception as e:
                logging.error(f'Failed to load vehicle from {file}: {str(e)}')

    def get_weapon(self, name):
        # Retrieve a weapon by its name
        if name in self.weapons:
            return self.weapons[name]
        else:
            # logging.debug(f'Weapon {name} not found in database.')
            return None

    def get_vehicle(self, name):
        # Retrieve a vehicle by its name
        if name in self.vehicles:
            return self.vehicles[name]
        else:
            # logging.debug(f'Vehicle {name} not found in database.')
            return None

    def initialize(self):
        # Initialize and load all equipment
        logging.info('Initializing EquipmentDatabase...')
        self.load_weapons()
        self.load_vehicles()
        logging.info('EquipmentDatabase initialized.')

    def __repr__(self):
        return f"EquipmentDatabase({len(self.weapons)} Weapons & {len(self.vehicles)} Vehicles)"
