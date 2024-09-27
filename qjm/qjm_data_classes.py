from dataclasses import dataclass
from enum import Enum

""" DATA CLASSES AND CONTAINERS """
@dataclass
class CasualtyRates:
    """Container for the casualty rates in a qjm battle resolution."""
    personnel: float
    armour: float
    artillery: float


class FormationOLI:
    """Container for the OLI (Operational Lethality Index) of a formation."""
    def __init__(self, small_arms=0.0, machine_guns=0.0, heavy_weapons=0.0, antitank=0.0,
                 artillery=0.0, antiair=0.0, armour=0.0, aircraft=0.0):
        self.small_arms = small_arms
        self.machine_guns = machine_guns
        self.heavy_weapons = heavy_weapons
        self.antitank = antitank
        self.artillery = artillery
        self.antiair = antiair
        self.armour = armour
        self.aircraft = aircraft

    def __add__(self, other):
        return FormationOLI(self.small_arms + other.small_arms,
                             self.machine_guns + other.machine_guns,
                             self.heavy_weapons + other.heavy_weapons,
                             self.antitank + other.antitank,
                             self.artillery + other.artillery,
                             self.antiair + other.antiair,
                             self.armour + other.armour,
                             self.aircraft + other.aircraft)
    def __repr__(self):
        return f"FormationOLI(small_arms={self.small_arms}, machine_guns={self.machine_guns}, " \
               f"heavy_weapons={self.heavy_weapons}, antitank={self.antitank}, artillery={self.artillery}, " \
               f"antiair={self.antiair}, armour={self.armour}, aircraft={self.aircraft})"


class LossRateFactors:
    """Container for the loss rate factors in a qjm battle resolution."""
    apc = 1.0
    infantry_weaps = 1.5
    antitank = 1.0
    fixed_wing = 1.0
    rotary_wing = 2.0
    vehicles = 0.5  # general vehicles like trucks
    artillery_towed = 0.1
    artillery_self_propelled = 0.3


class RecoveryRatesAttacker:
    """Container for the attacker's recovery rates
        in a qjm battle resolution."""
    personnel = 0.75
    antitank = 1.0
    artillery_towed = 0.5
    artillery_self_propelled = 0.5
    tanks = 0.5
    apc = 0.5
    infantry_weaps = 0.25
    antitank = 0.25
    fixed_wing = 0.25
    rotary_wing = 0.25
    vehicles = 0.5


class RecoveryRatesDefender:
    """Container for the attacker's recovery rates
        in a qjm battle resolution."""
    personnel = 0.75
    antitank = 1.0
    artillery_towed = 0.5
    artillery_self_propelled = 0.5
    tanks = 0.3
    apc = 0.3
    infantry_weaps = 0.15
    antitank = 0.15
    fixed_wing = 0.15
    rotary_wing = 0.15
    vehicles = 0.5


""" ENUMS """
class EquipmentOLICategory(Enum):
    """Enum for the QJM OLI categories of equipment in qjm."""
    small_arms = 'small arms'
    machine_gun = 'machine gun'
    heavy_weapon = 'heavy weapon'
    antitank = 'antitank'
    artillery = 'artillery'
    antiair = 'antiair'
    armour = 'armour'
    aircraft = 'aircraft'
    unknown = 'unknown'


class VehicleCategory(Enum):
    """Enum for the QJM vehicle categories."""
    tank = 'tank'
    armoured_car = 'armoured car'
    truck = 'truck'
    artillery = 'artillery'
    arv = 'arv'
    ifv = 'ifv'
    apc = 'apc'
    combat_air_support = 'cas'
    fighter = 'fighter'
    bomber = 'bomber'
    helicopter = 'helicopter'
    unknown = 'unknown'


""" HELPER FUNCTIONS """