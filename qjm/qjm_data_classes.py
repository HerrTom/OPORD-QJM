from dataclasses import dataclass, field
from enum import Enum

""" DATA CLASSES AND CONTAINERS """
@dataclass
class CasualtyRates:
    """Container for the casualty rates in a qjm battle resolution."""
    personnel: float
    armour: float
    artillery: float
    attacker: bool


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

    def calc_total(self):
        return (self.small_arms + self.machine_guns + self.heavy_weapons
              + self.antitank + self.artillery + self.antiair + self.armour
              + self.aircraft)

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


@dataclass
class BattleData:
    # Input Data
    terrain: str
    weather: str
    season: str
    posture: str
    air_superiority: str
    atk_surprise: str
    atk_surprise_days: int
    atkcev: float
    defcev: float
    attackers: list
    air_attackers: list
    defenders: list
    air_defenders: list
    
    # Calculated Metrics
    atk_oli: FormationOLI = field(default_factory=FormationOLI)
    def_oli: FormationOLI = field(default_factory=FormationOLI)
    Na: int = 0
    Nd: int = 0
    Nia: int = 0
    Nid: int = 0
    Ja: int = 0
    Jd: int = 0
    atk_S: float = 0.0
    def_S: float = 0.0
    atk_m: float = 0.0
    def_m: float = 1.0
    atk_V: float = 0.0
    def_V: float = 0.0
    atk_v: float = 1.0
    def_v: float = 1.0
    atk_P: float = 0.0
    def_P: float = 0.0
    PRatio: float = 0.0

    # Results
    powerRatio: float = 0.0
    powerAtk: float = 0.0
    powerDef: float = 0.0
    atkPersCasualtyRate: float = 0.0
    atkTankCasualtyRate: float = 0.0
    defPersCasualtyRate: float = 0.0
    defTankCasualtyRate: float = 0.0


class LossRateFactors:
    """Container for the loss rate factors in a qjm battle resolution."""
    apc = 1.0
    tanks = 1.0
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
    infantry = 'infantry'  # used for crew served weapons typically
    unknown = 'unknown'


""" HELPER FUNCTIONS """