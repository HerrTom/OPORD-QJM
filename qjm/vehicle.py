import csv
import yaml
import numpy as np
import logging

from qjm import EquipmentOLICategory, VehicleCategory


# load in interpolation arrays
RFE_ROF = []
RFE_RF = []
with open('./database/tables/RFE.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        RFE_ROF.append(float(row[0]))
        RFE_RF.append(float(row[1]))
ASE_AMMO = []
ASE_ASE = []
with open('./database/tables/ASE.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        ASE_AMMO.append(float(row[0]))
        ASE_ASE.append(float(row[1]))

class Vehicle:
    def __init__(self, file, weapons):
        with open(file) as f:
            data = yaml.full_load(f)

        self.name = data.get('name', 'Unknown')
        self.description = data.get('description', 'No Description')
        self.crew = data.get('crew', 0)
        self.vehicle_type = data.get('vehicle_type', 'unknown')
        self.category = data.get('category', 'unknown')
        self.d_sp_arty = None  # to solve error in casualty calculation
        d_weapons = data.get('weapons', [])
        d_speed = data.get('speed', 0)
        d_range = data.get('op_range', 0)
        d_weight = data.get('weight', 0)
        d_FCE = data.get('fce', 0)
        d_ammo = data.get('ammo', 0)
        d_wheel = data.get('mobility', 'unknown')
        d_amphibious = data.get('amphibious', 'unknown')
        d_ceiling = data.get('ceiling', 0)

        # set the OLI category
        if self.category == 'small arms':
            self.oli_category = EquipmentOLICategory.small_arms
        elif self.category == 'machine gun':
            self.oli_category = EquipmentOLICategory.machine_gun
        elif self.category == 'heavy weapon':
            self.oli_category = EquipmentOLICategory.heavy_weapon
        elif self.category == 'antitank':
            self.oli_category = EquipmentOLICategory.antitank
        elif self.category == 'artillery':
            self.oli_category = EquipmentOLICategory.artillery
        elif self.category == 'antiair':
            self.oli_category = EquipmentOLICategory.antiair
        elif self.category == 'armour':
            self.oli_category = EquipmentOLICategory.armour
        elif self.category == 'aircraft':
            self.oli_category = EquipmentOLICategory.aircraft
        else:
            self.oli_category = EquipmentOLICategory.unknown
            logging.error(f'Weapon {self.name} has unknown category {self.category}')

        # set the vehicle category
        if self.vehicle_type == 'tank':
            self.qjm_vehicle_category = VehicleCategory.tank
        elif self.vehicle_type == 'armoured car':
            self.qjm_vehicle_category = VehicleCategory.armoured_car
        elif self.vehicle_type == 'truck':
            self.qjm_vehicle_category = VehicleCategory.truck
        elif self.vehicle_type == 'artillery':
            self.qjm_vehicle_category = VehicleCategory.artillery
        elif self.vehicle_type == 'arv':
            self.qjm_vehicle_category = VehicleCategory.arv
        elif self.vehicle_type == 'ifv':
            self.qjm_vehicle_category = VehicleCategory.ifv
        elif self.vehicle_type == 'apc':
            self.qjm_vehicle_category = VehicleCategory.apc
        elif self.vehicle_type == 'cas':
            self.qjm_vehicle_category = VehicleCategory.combat_air_support
        elif self.vehicle_type == 'fighter':
            self.qjm_vehicle_category = VehicleCategory.fighter
        elif self.vehicle_type == 'bomber':
            self.qjm_vehicle_category = VehicleCategory.bomber
        elif self.vehicle_type == 'helicopter':
            self.qjm_vehicle_category = VehicleCategory.helicopter
        else:
            self.qjm_vehicle_category = VehicleCategory.unknown
            logging.error(f'Vehicle {self.name} has unknown category {self.vehicle_type}')

        # calculated values
        # sum up weapon values
        d_weaps = []
        q_weaps = 0
        if d_weapons is not None:
            for dw in d_weapons:
                for w in weapons:
                    if dw == w.name:
                        d_weaps.append(w)
        
            for i, w in enumerate(d_weaps):
                q_weaps += w.q_OLI * 1/(1+i)


        # mobility effect (MOF)
        if self.vehicle_type == 'cas':
            q_MOF = 0
        else:
            q_MOF = 0.15 * d_speed**0.5
        
        # radius of action factor (RA)
        q_RA = 0.08 * d_range**0.5

        # Punishment factor (PF)
        if self.vehicle_type in ['tank', 'armoured car', 'arv']:
            q_PF = d_weight / 4 * (2 * d_weight)**0.5
        else:
            q_PF = q_PF = d_weight / 8 * (2 * d_weight)**0.5
        
        # rapidity of fire effect (RFE)
        # uses primary weapon of vehicle
        if len(d_weaps) > 0:
            ROF = d_weaps[0].q_RF
        else:
            ROF = 0
        q_RFE = np.interp(float(ROF), RFE_ROF, RFE_RF)

        # fire control effect (FCE) - arbitrary
        q_FCE = d_FCE

        # ammo suply factor (ASE) - uses primary weapon
        if ROF > 0:
            ammo_ratio = ROF / d_ammo
        else:
            ammo_ratio = 0
        q_ASE = np.interp(float(ammo_ratio), ASE_AMMO, ASE_ASE)

        # wheel halftrack effect (WHT)
        if d_wheel == 'wheeled':
            q_WHT = 0.90
        elif d_wheel == 'halftrack':
            q_WHT = 0.95
        else:
            q_WHT = 1.00
        
        # amphibious effect (AME)
        if d_amphibious == 'amphibious':
            q_AME = 1.10
        elif d_amphibious == 'snorkel':
            q_AME = 1.05
        else:
            q_AME = 1.00

        if self.vehicle_type == 'helicopter':
            q_CL = 0.6
        elif self.vehicle_type in ['cas', 'fighter', 'bomber']:
            if d_ceiling <= 30000:
                q_CL = 1.0 - 0.02*(30000 - d_ceiling/1000)
            else:
                q_CL = 1.0 + 0.005 * (d_ceiling / 1000)
        else:
            q_CL = 1.0

        if self.vehicle_type == 'helicopter':
            q_W = ((q_weaps * q_MOF * q_RA + q_PF) + q_weaps) / 2
        else:
            q_W = (q_weaps * q_MOF * q_RA + q_PF)
        self.q_OLI = q_W * q_RFE * q_FCE * q_ASE * \
            q_AME * q_CL * q_WHT
        
        logging.info('Vehicle Loaded: {:} | {:,.0f}'.format(self.name, self.q_OLI, q_W))

    def __repr__(self):
        return "Vehicle({})".format(self.name)