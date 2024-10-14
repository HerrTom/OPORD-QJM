import yaml
import logging
from random import random
from uuid import uuid1

class Formation():
    def __init__(self, file, weapon_dict, color=None):
        with open(file) as f:
            data = yaml.full_load(f)

        self.name = data['name']
        self.id = str(uuid1())
        self.faction = data['faction']
        self.sidc = data['sidc']
        self.personnel = 0
        if color is None:
            self.color = '#5ea6f2'
        else:
            self.color = color

        equip = data['equipment']

        self.equipment = {}
        for key in equip:
            # first search the weapons database
            # allotted, active, damaged, destroyed
            if key in weapon_dict:
                self.equipment.update({weapon_dict[key]: [equip[key], equip[key], 0, 0]})
            else:
                logging.warning('Formation.py: {} not found in database!'.format(key))
        self.calc_personnel()


        logging.info(f'Loaded Formation: {self.name} w/ {self.personnel:,.0f} personnel @ {self.get_OLI():,.0f}')

    def __repr__(self,):
        return ('Formation({} [{}])'.format(self.name, self.faction))

    def calc_personnel(self):
        # calculate personnel of formation
        self.personnel = 0
        for e in self.equipment:
            # index 1 is active equipment
            self.personnel += e.crew * self.equipment[e][1]

    def get_equip_status(self, e):
        # returns a dict with the status of the given equipment item
        status = {'Allocated': self.equipment[e][0],
                  'Active': self.equipment[e][1],
                  'Damaged': self.equipment[e][2],
                  'Destroyed': self.equipment[e][3],}
        return status
    
    def get_OLI(self):
        # returns OLI statistics about formation
        OLI = {'Ws': 0, 'Wmg': 0, 'Whw': 0, 'Wgi': 0,
                'Wg': 0, 'Wgy': 0, 'Wi': 0, 'Wy': 0}
        # loop through equipment and categorize and multiply OLI by active items
        for equip in self.equipment:
            if equip.category == 'small arms':
                OLI['Ws'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'machine gun':
                OLI['Wmg'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'heavy weapon':
                OLI['Whw'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'antitank':
                OLI['Wgi'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'artillery':
                OLI['Wg'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'antiair':
                OLI['Wgy'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'armour':
                OLI['Wi'] += equip.q_OLI * self.equipment[equip][1]
            elif equip.category == 'aircraft':
                OLI['Wy'] += equip.q_OLI * self.equipment[equip][1]
            else:
                logging.warning('Unknown category: {}'.format(equip.category))
        return OLI
    
    def inflict_losses(self, C, C_Arm, C_Arty, isAttacker):
        # base rates:
        CF_APC = 1.0
        CF_InfantryWeaps = 1.5
        CF_Antitank = 1.0
        CF_FixedWing = 1.0
        CF_RotaryWing = 2.0
        CF_Vehicles = 0.5 # general vehicles like trucks
        CF_ArtyTowed = 0.1
        CF_ArtySP = 0.3

        # Recovery rates
        if isAttacker:
            RF_Tank = 0.5
        else:
            RF_Tank = 0.3
        RF_ArtyTowed = 0.5
        RF_ArtySP = 0.5
        RF_APC = 1.0 * RF_Tank
        RF_InfantryWeaps = 0.5 * RF_Tank
        RF_Antitank = 0.5 * RF_Tank
        RF_FixedWing = 0.5 * RF_Tank
        RF_RotaryWing = 0.5 * RF_Tank
        RF_Vehicles = RF_ArtySP

        # loss rates by category
        C_APC = CF_APC * C_Arm
        C_InfantryWeaps = CF_InfantryWeaps * C
        C_Antitank = CF_Antitank * C
        C_FixedWing = CF_FixedWing * C
        C_RotaryWing = CF_RotaryWing * C
        C_Vehicles = CF_Vehicles * C
        C_ArtyTowed = CF_ArtyTowed * C_Arty
        C_ArtySP = CF_ArtySP * C_Arty

        # Run through equipment and inflict losses
        for e in self.equipment:
            if e.category in ['small arms']:
                CR = C
                RR = 0.75
            elif e.category in ['machine gun']:
                CR = C_InfantryWeaps
                RR = RF_InfantryWeaps
            elif e.category in ['antitank']:
                CR = C_Antitank
                RR = RF_Antitank
            elif e.category in ['artillery', 'antiair']:
                if e.d_sp_arty is None:
                    CR = C_ArtyTowed
                    RR = RF_ArtyTowed
                else:
                    CR = C_ArtySP
                    RR = RF_ArtySP
            elif e.category in ['heavy weapon', 'armour', 'close air support']:
                # this is a vehicle
                # tank, armoured car, arv, ifv, apc, cas, fighter, bomber
                if e.vehicle_type == 'tank':
                    CR = C_Arm
                    RR = RF_Tank
                elif e.vehicle_type == 'armoured car':
                    CR = C_Vehicles
                    RR = RF_Vehicles
                elif e.vehicle_type in ['ifv', 'apc']:
                    CR = C_APC
                    RR = RF_APC
                elif e.vehicle_type in ['cas', 'fighter', 'bomber']:
                    CR = C_FixedWing
                    RR = RF_FixedWing
                elif e.vehicle_type in ['helicopter']:
                    CR = C_RotaryWing
                    RR = RF_RotaryWing
                else:
                    CR = C_Vehicles
                    RR = RF_Vehicles
            else:
                CR = C_Vehicles
                RR = RF_Vehicles
            
            self.casualty(e, CR, RR)


    def casualty(self, e, CR, RR):
        # inflict casualties according to a rate
        for x in range(self.equipment[e][1]):
            rollC = random()
            rollR = random()
            if rollC < CR:
                # roll was lower than casualty rate, reduce count by one
                self.equipment[e][1] -= 1
                if rollR < RR:
                    # roll was lower than recovery rate, equipment is damaged
                    self.equipment[e][2] += 1
                else:
                    # equipment is not recovered, destroyed
                    self.equipment[e][3] += 1
    def print_status(self):
        print(self.name)
        for e in self.equipment:
            status = self.get_equip_status(e)
            print('{:>15s}: {:5,.0f}/{:5,.0f} ({:.0f} DAM | {:.0f} DES)'.format(
                e.name, status['Active'], status['Allocated'], status['Damaged'], status['Destroyed']))
            
    ## getter functions
    def get_personnel(self):
        self.calc_personnel()
        return self.personnel
