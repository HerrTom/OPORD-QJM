# Specific Notes on QJM Model:
## Duration
 * Combat Duration Less than a Day: Casualties are reduced in a linear fashion, up to a minimum of 1/6 of a day (4 hours)

# Vehicle TLI Factors
 * TNDM Newsletter V1N6 and V2N2 has a better factor for heavier armoured vehicles:
    * AFV OLI = (Total OLIs) * BMF * RAF * VPF * VAF * VSF
        * BMF = 0.04 * sqrt(Horsepower/Weight) * Speed / GroundPressure
            * BMF: Battlefield Mobility Factor, based on Horsepower, Weight, Speed, and Ground Pressure
            * Horsepower: Horsepower of vehicle engine (Watts)
            * Weight: Weight of vehicle (kg)
            * Speed: Speed of vehicle (kph)
            * GroundPressure: Ground Pressure of vehicle, in kg/cm^2
        * RAF = 0.6 * sqrt(Range)
            * RAF: Radius of Action Factor
            * Range: Combat radius of vehicle
        * VPF = 1.2 * ArmorType * Weight / (2.0 * Height * Length)
            * VPF: Punishment Factor, based on Armor Type, Weight, Height, and Length
            * Units??
        * VAF = sqrt(VisF * LLCF * TravF * SGF * RgFF * FCCFs)
            * VAF: Vehicle Attack Factor
            * VisF: Visibility Factor. 0.9 for enclosed vehicles, 1.0 for open-topped
            * LLCF: Low-Light Capability Factor, goes from 1.0 to 1.1
            * TravF: Turret Traverse Factor. 0.9 for fixed mount, 1.0 for manual traverse, 1.1 for powered traverse
            * SGF: Stabilized Main Gun Factor. 1.0 for unstabilized, 1.1 for stabilized.
            * RgFF: Range Finder Factor. 1.0 for stadiametric, 1.2 for laser
            * FCFFs: Fire Control Factors. Multiplied, 1.05 each for: Cant, Ammunition Type, Crosswind, Barrel Condition.
        * VSF = sqrt(6.0 * Load / ((6.0 * Load) + FiringRate))
            * VSF: Vehicle Supply Factor
            * Load: Ammunition load of main gun
            * FiringRate: Firing Rate of main gun

## Aircraft
 * Suspended aircraft ordnance: Use number of bombs (e.g.) carried as Rate of Fire, with ASE of 1.0

## Rules of Thumb:
| Weapon Type                       | Estimated Accuracy    |
|-----------------------------------|-----------------------|
| Small Arms                        | 0.85                  |
| Automatic Weapons                 | 0.70                  |
| Mortars                           | 0.75                  |
| Rockets (unguided)                | 0.50                  |
| Bombs (unguided)                  | 0.40                  |
| Standard Rifled Artillery Weapons | 0.85                  |
| Standard Smootbore Weapons        | 0.60                  |
| High Velocity Guns                | 0.90                  |


## ATGMs
 Special rules are applied to the calculation of ATGM OLIs with respect to: accuracy, and additional factors

1.  The following factors relating accuracy to guidance are used for ATGMs
    - Wire guidance (daylight only) 0.80
    - Wire guidance (day or night) 0.85
    - Standard radio command 0.85
    - Radar Beam 0.90
    - Laser Beam 0.95

2.  Additional factors applied to calculation of ATGM OLIs are:
    1. Minimum range factor (MRN). Standard minimum distance before arming is is assumed to be 100 meters. MRN = 1 - [.19MinRnge - 100)/100]
    2.  Penetration factor (PEN). Standard penetration is assumed to be 500mm. PEN = 1 + [.01 x SQR(penetration - 500)]
    3. Velocity factor (VEL). Standard velocity is assumed to be 400 m/s. VEL = 1 + [.001(velocity - 400)]
    4. Enhancement factor (EN). Total value cannot exceed 1.4. There are two kinds of enhancement:
        - Accuracy enhancement (ENa): IF CEP is less than standrad ENa is >1.0 and <1.3. If ph is above standard ENa is >1.0 and <1.3
        - Other enhancement (ENo). Currently applies only to ability to track through obscurants, or other countermeasures. Value is judgemental, betwen 1.0 and 1.3.