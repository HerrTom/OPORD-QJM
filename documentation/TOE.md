# TO&E Documentation
Tables of Organization and Equipment (TO&E) determine the organization and equipment of a formation.  The TO&E is composed some or all of the following elements:

 * Subunits
 * Personnel
 * Line Item Numbers (LIN)

## 1. Subunits
Subunits are smaller units that form out the TO&E. For example, a Rifle Platoon TO&E will include (typically) the following subunits:

  1. Platoon Headquarters
  2. Rifle Squad
  3. Rifle Squad
  4. Rifle Squad

## 2. Personnel
The TO&E also includes the personnel in the unit. This is broken down by rank and role. For the TO&E file the role is purely descriptive, it does not have any role in the QJM simulation.  Using the Rifle Squad in the above example, the squad may have:

 * Squad Commander: Sgt
 * Antitank Grenadier: Pvt
 * Assistant Grenadier: Pvt
 * Machine Gunner: Pvt
 * Senior Rifleman: Cpl
 * Rifleman: Pvt
 * Gunner-Operator: Pvt
 * Driver-Mechanic: Pvt

## 3. Line Item Numbers (LIN)
Line Item Numbers indicate a specific category of equipment that fulfills a role in the organization. Using the Rifle Squad in the example above, there may be LINs for:

 * 9881056 (Rifle)
 * 9881057 (Carbine)
 * 9889011 (Antitank Rocket Launcher)
 * 5101001 (Infantry Fighting Vehicle)

This is further refined by issuance per person in the unit.  See the following examples:

 * Squad Commander: Sgt
   * LIN 9881056 (Rifle)
 * Antitank Grenadier: Pvt
   * LIN 9881056 (Rifle)
   * LIN 9889011 (Antitank Rocket Launcher)
 * Gunner-Operator: Pvt
   * LIN 9881056 (Rifle)
 * Driver-Mechanic: Pvt
   * 9881057 (Carbine)

Additionally, specific equipment may have a crew associated with it:
 * 5101001 (Infantry Fighting Vehicle):
   * Gunner-Operator
   * Driver-Mechanic


## 4. TO&E File Format
The TO&E file format is a YAML file containing the following information:
```
name: string    # Name of the TO&E to be used for display
sidc: string    # Single Identifier Code, used to generate the APP-6D standard symbol
nation: string  # Name of the nationality of the unit
id: string      # ID code that can be referenced by other formations
subunits: # List of ID codes that this TO&E uses as a subunit. May be blank. Example below:
    - RURIFLEPLTHQ: Platoon HQ # First subunit, with display name after
    - RURIFLESQD: 1. Rifle Squad # Second subunit, may be identical to others,
                                    # with display name after
    - RURIFLESQD: 2. Rifle Squad # Third subunit, may be identical to others,
                                    # with display name after
personnel: # List of personnel roles and their ranks. This can be blank. Example below:
    - Squad Commander:
        rank: Sergeant
        equipment:
            - 9881056
    - Antitank Grenadier:
        rank: Private
        equipment: 
            - 9881056
            - 9889011
    - Gunner-Operator:
        rank: Private
        equipment:
            - 9881056
    - Driver-Mechanic:
        rank: Private
        equipment:
            - 9881057
crews: # list of equipment with crews. This can be blank. Example below:
    - 501001: # This is the Infantry Fighting Vehicle line item number.
        - Gunner-Operator # Note that this matches a UNIQUE descriptor from above
        - Driver-Mechanic # Note that this matches a UNIQUE descriptor from above

````