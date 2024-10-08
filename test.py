import logging
from qjm import EquipmentDatabase, CasualtyRates

# set a file to write the debug data into
logging.basicConfig(filename='debug.log', level=logging.DEBUG)

# clear the debug file before starting
with open('debug.log', 'w') as f:
    f.write('')

# Load the equipment database
edb = EquipmentDatabase('database/weapons', 'database/vehicles')

# Load the TOE database
from toe import TOE_Database  # Move this import here to avoid circular import
db = TOE_Database()
db.load_database()
print('--------------------------------------')

unit_nsns = ['MPi-KM', 'MPi-KMS', 'BMP-1', 'T-55A', 'ZSU-23-4V', '9K35 Strela-10']

from toe import Formation  # Move this import here to avoid circular import
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

db.to_orbatmapper('toe.json', toe_ids=['TOEEG003001'], units=[])

print(edb)