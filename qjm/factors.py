import csv

# load in constant arrays
TERRAIN_NAME = []
TERRAIN_DATA = {}
with open('./database/tables/TerrainFactors.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        TERRAIN_NAME.append(row[0])
        TERRAIN_DATA.update({row[0]: [float(i) for i in row[1:]]})
WEATHER_NAME = []
WEATHER_DATA = {}
with open('./database/tables/WeatherFactors.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        WEATHER_NAME.append(row[0])
        WEATHER_DATA.update({row[0]: [float(i) for i in row[1:]]})
MORALE_NAME = []
MORALE_DATA = {}
with open('./database/tables/MoraleFactor.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        MORALE_NAME.append(row[0])
        MORALE_DATA.update({row[0]: float(row[1])})

SEASON_NAME = []
SEASON_DATA = {}
with open('./database/tables/SeasonFactors.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        SEASON_NAME.append(row[0])
        SEASON_DATA.update({row[0]: [float(i) for i in row[1:]]})
SURPRISE_NAME = []
SURPRISE_DATA = {}
with open('./database/tables/SurpriseFactors.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        SURPRISE_NAME.append(row[0])
        SURPRISE_DATA.update({row[0]: [float(i) for i in row[1:]]})
DEFENSE_NAME = []
DEFENSE_DATA = {}
with open('./database/tables/PostureFactors.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        DEFENSE_NAME.append(row[0])
        DEFENSE_DATA.update({row[0]: [float(i) for i in row[1:]]})
AIRSUPERIORITY_NAME = []
AIRSUPERIORITY_DATA = {}
with open('./database/tables/AirSuperiorityFactors.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        AIRSUPERIORITY_NAME.append(row[0])
        AIRSUPERIORITY_DATA.update({row[0]: [float(i) for i in row[1:]]})

# load in lookup tables
OP_RATIO = []
OP_FACTOR = []
with open('./database/tables/OppositionFactor.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        OP_RATIO.append(float(row[0]))
        OP_FACTOR.append(float(row[1]))
STR_PERS = []
STR_PERS_FACTOR = []
with open('./database/tables/StrengthSize.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        STR_PERS.append(float(row[0]))
        STR_PERS_FACTOR.append(float(row[1]))
STR_ARM = []
STR_ARM_FACTOR = []
with open('./database/tables/StrengthSizeArmour.csv') as f:
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        STR_ARM.append(float(row[0]))
        STR_ARM_FACTOR.append(float(row[1]))
