import csv
import yaml
import numpy as np
import logging

from qjm import EquipmentOLICategory, VehicleCategory

GLOBAL_DISPERSION = 4000

# load in interpolation arrays
RF_CAL = []
RF_RF = []
with open('./database/tables/RF.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        RF_CAL.append(float(row[0]))
        RF_RF.append(float(row[1]))
PTS_CAL = []
PTS_PTS = []
with open('./database/tables/PTS.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        PTS_CAL.append(float(row[0]))
        PTS_PTS.append(float(row[1]))        


class Weapon:
    def __init__(self, file):
        with open(file) as f:
            data = yaml.full_load(f)

        # raw data read in from yml data
        self.name = data.get('name', 'Unknown')
        self.category = data.get('category', 'Unknown')
        self.description = data.get('description', 'No Description')
        self.crew = data.get('crew', 0)
        self.d_calibre = data.get('calibre', 0)  # calibre in mm of weapon
        self.d_weap_type = data.get('weap_type', 'unknown')  # type of weapon, can be:
                         # gun, mortar, missile, bomb
        self.d_ROF_type = data.get('rof_type', 'unknown')  # one of six options:
                       # crewed; handheld; aircraft; calibre; mortar;
        self.d_ROF = data.get('ROF', 0)  # Rate of fire (cyclic per minute)
        self.d_PTS = data.get('PTS', 0)  # if 0, use calibre calculation
        self.d_RIE = data.get('RIE', 1)  # relative incapacitation, usually 1 except
                 # for small arms - 0.8 seems normal for most rifles
        self.d_eff_range = data.get('eff_range', 0)
        self.d_muzzle_vel = data.get('muzzle_vel', 0)
        self.d_accuracy = data.get('accuracy', 0)
        self.d_reliability = data.get('reliability', 0)
        self.d_sp_arty = data.get('sp_arty', 'none') 
        self.d_missile_guidance = data.get('guidance', 'no')  # Guided can be no, beam, wire, command, radar
        self.d_barrels = data.get('barrels', 1)
        self.d_charges = data.get('arty_charges', 0)

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
        self.qjm_vehicle_category = VehicleCategory.infantry

        # calculated values
        if self.d_ROF_type == 'crewed':
            self.q_RF = 4 * self.d_ROF
        elif self.d_ROF_type == 'calibre':
            self.q_RF = np.interp(float(self.d_calibre), RF_CAL, RF_RF)
        elif self.d_ROF_type == 'mortar':
            self.q_RF = 1.2 * np.interp(float(self.d_calibre), RF_CAL, RF_RF)
        else:
            self.q_RF = 2 * self.d_ROF

        if self.d_PTS == 0:
            self.q_PTS = np.interp(float(self.d_calibre), PTS_CAL, PTS_PTS)
        else:
            self.q_PTS = self.d_PTS

        # range effect
        RN_rng = 1 + (0.001 * self.d_eff_range)**0.5
        RN_mv = 0.007 * self.d_muzzle_vel * 0.1 * self.d_calibre
        if self.d_weap_type == 'bomb':
            self.q_RN = 0.007 * 250 * 0.1 * self.d_calibre
        elif self.d_weap_type == 'rocket' or self.d_weap_type == 'mortar':
            self.q_RN = max(RN_rng, RN_mv)
        else:
            if RN_rng > RN_mv:
                self.q_RN = (RN_rng + RN_mv) / 2
            else:
                self.q_RN = RN_mv
            
        if self.q_RN < 1:
            self.q_RN = 1

        self.q_RIE = self.d_RIE

        # Accuracy effect (A)
        self.q_A = self.d_accuracy

        # Reliability effect (RL)
        self.q_RL = self.d_reliability

        # Self propelled artillery factor (SME)
        if self.d_sp_arty == 'enclosed':
            self.q_SME = 1.10
        elif self.d_sp_arty == 'open':
            self.q_SME = 1.05
        else:
            self.q_SME = 1.00

        # Missile Guidance Effect (GE)
        if self.d_missile_guidance == 'wire':
            self.q_GE = 1.5
        elif self.d_missile_guidance == 'radar':
            self.q_GE = 1.5
        elif self.d_missile_guidance == 'beam':
            self.q_GE = 2.0
        elif self.d_missile_guidance == 'fire and forget':
            self.q_GE = 2.0
        else:
            self.q_GE = 1.0
        
        # Multiple barrel weapons effect (MBE)
        self.q_MBE = 0
        for i in range(self.d_barrels):
            self.q_MBE += 1/(i+1)

        # Multiple Charge Artillery Effect (MCE)
        self.q_MCE = 1.0
        if self.d_charges > 2:
            for i in range(self.d_charges-2):
                self.q_MCE += max(0.05 - 0.01*i, 0.01)
            if self.q_MCE > 1.15:
                self.q_MCE = 1.15

        self.q_OLI = (self.q_RF * self.q_PTS * self.q_RIE * self.q_RN * \
                        self.q_A * self.q_RL * self.q_SME * self.q_MBE * \
                        self.q_MCE * self.q_GE / GLOBAL_DISPERSION)

        logging.info('Weapon Loaded: {:} | {:,.1f}'.format(self.name, self.q_OLI))

    def __repr__(self):
        return "Weapon({})".format(self.name)
