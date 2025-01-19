import sys
import os
from pathlib import Path
from glob import glob
import yaml

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import logging
from qjm import EquipmentDatabase, CasualtyRates
from toe import TOE_Database, Formation

# set a file to write the debug data into
logging.basicConfig(filename='./debug.log', level=logging.DEBUG)

# clear the debug file before starting
with open('debug.log', 'w') as f:
    f.write('')

# Load the equipment database
edb = EquipmentDatabase('./database/weapons', './database/vehicles')

# Check for missing NSNs
def check_missing_nsns(unit_nsns, equipment_db):
    db_nsns = set()
    for weapon in equipment_db.weapons.values():
        db_nsns.add(weapon.name)
    for vehicle in equipment_db.vehicles.values():
        db_nsns.add(vehicle.name)
    missing_nsns = set(unit_nsns) - db_nsns
    if missing_nsns:
        print("WARNING: The following NSNs are missing from the database:")
        for nsn in missing_nsns:
            print(f"  - {nsn}")
        logging.warning(f"Missing NSNs: {missing_nsns}")

# Load the TOE database
db = TOE_Database()
db.load_database()
print('--------------------------------------')

all_nsns = set()
nsn_files = glob('./database/lin_equipment/*/*.yaml')
for f in nsn_files:
    with open(f, 'r') as file:
        data = yaml.safe_load(file)
        for lin, lin_data in data.items():
            for nsn in lin_data['items']:
                all_nsns.add(nsn)
check_missing_nsns(all_nsns, edb)

# Check functionality of the Formation class
unit_nsns = ['MPi-KM', 'MPi-KMS', 'BMP-1', 'T-55A', 'ZSU-23-4V', '9K35 Strela-10']
MSR_332 = Formation('332 Motor Rifle Regiment', '332', 'EG', db.get_TOE('TOEEG020001'), unit_nsns)
MSR_332.add_qjm_weapons(edb)
MSR_332_equip = MSR_332.get_all_equipment()
eq = {}
for e in MSR_332_equip:
    if e.item_entries[0] not in eq:
        eq[e.item_entries[0]] = 1
    else:
        eq[e.item_entries[0]] += 1
print(eq)
print(MSR_332.count_personnel())
print(f'{MSR_332.name} has {MSR_332.get_oli()}')
print('-----------------')

MSR_333 = Formation('333 Motor Rifle Regiment', '333', 'EG', db.get_TOE('TOEEG020001'), unit_nsns)
MSR_333.add_qjm_weapons(edb)
cr = CasualtyRates(personnel=1, armour=1, artillery=1, attacker=True)
MSR_333.inflict_losses(cr)

db.to_orbatmapper('toe.json', toe_ids=['TOEWG000007', 'TOEWG000006', 'TOEWG000017'], units=[])

print(edb)