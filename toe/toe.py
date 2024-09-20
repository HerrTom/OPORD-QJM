import yaml
import json
import secrets 
import string
from enum import Enum
from pprint import pp
from glob import glob

class DuplicateIDError(Exception):
    """Custom exception for duplicate TO&E or LIN IDs."""
    pass

# TODO: Probably should move enums into own file
class ElementStatus(Enum):
    UNDEFINED   = 0
    ACTIVE      = 1
    DAMAGED     = 2
    DESTROYED   = 3

class Formation:
    def __init__(self, name: str, shortname: str, parent_shortname: str, toe, nsns: list = None):
        self.name = name
        self.shortname = shortname
        self.parent_shortname = parent_shortname
        self.nation = toe.nation
        self.sidc = toe.sidc
        self.id = name

        if nsns is None: # Avoiding mutable default argument
            nsns = []
        print(nsns)

        # now we copy the TO&E from lower level units
        self.subunits = []
        self.vehicles = []
        self.personnel = []
        if len(toe.subunits) > 0:
            count = 1
            for sub in toe.subunits:
                new_sub = self.copy_toe(str(count)+'/'+shortname, str(count)+'/'+shortname, sub, nsns)
                self.subunits.append(new_sub)
                count += 1
        else:
            # add personnel and equipment
            for veh in toe.vehicles:
                new_crew = []
                for crew in veh.crew:
                    crewman = Personnel(crew.name, crew.rank, crew.equipment)
                    crewman.set_status(ElementStatus.ACTIVE) # Unit is active by default
                    crewman.assign_equipment(nsns)
                    new_crew.append(crewman)
                new_veh = Vehicle(veh.name, veh.equipment, new_crew)
                new_veh.set_status(ElementStatus.ACTIVE) # Unit is active by default
                new_veh.assign_equipment(nsns)
                self.vehicles.append(new_veh)
            for pers in toe.personnel:
                new_pers = Personnel(pers.name, pers.rank, pers.equipment)
                new_pers.set_status(ElementStatus.ACTIVE) # Unit is active by default
                new_pers.assign_equipment(nsns)
                self.personnel.append(new_pers)

    def __repr__(self,):
        return f'Formation({self.shortname}/{self.parent_shortname}, {self.nation})'

    def copy_toe(self, name, shortname, toe, nsns):
        return Formation(name, shortname, self.shortname, toe, nsns)
    
    def get_all_equipment(self,):
        all_equipment = []
        # add subunit equipment
        for sub in self.subunits:
            sub_equip = sub.get_all_equipment()
            all_equipment += sub_equip
        for pers in self.personnel:
            all_equipment += pers.equipment
        for veh in self.vehicles:
            all_equipment += [veh.equipment] # vehicles have singular equipment
            for crew in veh.crew:
                all_equipment += crew.equipment
        return all_equipment

    def get_all_personnel(self,):
        all_personnel = []
        # add subunit equipment
        for sub in self.subunits:
            sub_personnel = sub.get_all_personnel()
            all_personnel += sub_personnel
        for pers in self.personnel:
            all_personnel += [pers]
        for veh in self.vehicles:
            for crew in veh.crew:
                all_personnel += [crew]
        return all_personnel
    
    # FUNCTIONS FOR QJM INTEGRATION
    def count_personnel(self,):
        N_personnel = 0
        personnel = self.get_all_personnel()
        for p in personnel:
            if p.status == ElementStatus.ACTIVE:
                N_personnel += 1
        return N_personnel
    
    def count_vehicles(self,):
        vehicles = {}
        # TODO: Need to get equipment by vehicle types
        return vehicles
    
    def count_equipment(self,):
        equipment = {}

        return equipment
    
    def get_oli(self,):
        # returns OLI statistics about formation
        oli = {'Ws': 0, 'Wmg': 0, 'Whw': 0, 'Wgi': 0,
                'Wg': 0, 'Wgy': 0, 'Wi': 0, 'Wy': 0}
        return oli

class TOE:
    def __init__(self, name: str, nation: str, sidc: str, toe_id: str,
                 subunits: list, personnel: list, vehicles: list):
        # default blank TO&E
        self.name = name
        self.nation = nation
        self.sidc = sidc
        self.id = toe_id
        self.subunit_entries = subunits
        self.subunits = []
        self.personnel_entries = personnel
        self.personnel = []
        self.vehicle_entries = vehicles
        self.vehicles = []

        self.is_built = False
        
    def __repr__(self,):
        return 'TO&E({}: {}, {})'.format(self.id, self.name, self.nation)

class LIN:
    def __init__(self, lin: str, name: str, items: list):
        self.lin = lin
        self.name = name
        self.item_entries = items

    def assign_equipment(self, nsns: list):
        """_summary_

        Args:
            nsns (list): List of available NSNs to choose from. If none of the NSNs
                in this list are available to this LIN, it will return the highest priority item.
                TODO: Should this return the *lowest* priority instead?

        Returns:
            str: Accepted NSN of given equipment
        """
        available = []
        for nsn in nsns:
            if nsn in self.item_entries:
                available.append(nsn)
        # For now, we will choose the first found NSN. TODO: do actual sorting for highest priority
        if len(available) > 0:
            equipment = available[0]
        else:
            equipment = self.item_entries[0]

        return equipment

    def __repr__(self,):
        return 'LIN {} ({})'.format(self.lin, self.name)

class Element:
    def __init__(self, name: str):
        # an element is a person or a vehicle in a TO&E role
        self.name   = name
        self.status = ElementStatus.UNDEFINED
        self.assigned_equipment = None
    
    def set_status(self, status: ElementStatus):
        """Set an Element's current status.

        Args:
            status (ElementStatus): New status to set the Element to
        """
        self.status = status

    def assign_equipment(self, nsns: list):
        print(f'---Attention: Assign_equipemnt is not overwritten for this Element type! {self}')
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"
    
class Personnel(Element):
    def __init__(self, name: str, rank: str, equipment: list):
        super().__init__(name)
        self.rank = rank  # Specific to Person
        self.equipment = equipment

    def assign_equipment(self, nsns: list):
        self.assigned_equipment = []
        for e in self.equipment:
            self.assigned_equipment.append(e.assign_equipment(nsns))

    def __repr__(self):
        return f"Personnel({self.name}. {self.rank})"

class Vehicle(Element):
    # Represents vehicles or crew served weapon roles
    def __init__(self, name: str, equipment: str, crew: list):
        super().__init__(name)
        self.equipment = equipment # the LIN of the vehicle this represents
        self.crew = crew # list of elements

    def assign_equipment(self, nsns: list):
        self.assigned_equipment = [self.equipment.assign_equipment(nsns)]

class TOE_Database:
    # Database containing all TO&E structures
    def __init__(self,):
        self.TOE = {}
        self.LIN = {}
        self.all_personnel = []

    def load_database(self,):
        # hardcoded for now
        raw_toe_files = glob('./database/toe/**/*.yaml', recursive=True)
        raw_lin_files = glob('./database/lin_equipment/**/*.yaml', recursive=True)

        # load in and process the Line Item Numbers
        for filename in raw_lin_files:
            with open(filename, 'r') as f:
                data = yaml.safe_load(f)
            for lin in data:
                if lin in self.LIN:
                    raise DuplicateIDError(f"Duplicate LIN ID found: {lin} in {filename}")
                line_item = LIN(lin, data[lin]['name'], data[lin]['items'])
                self.LIN.update({lin: line_item})

        for filename in raw_toe_files:
            with open(filename, 'r') as f:
                data = yaml.safe_load(f)
            if data['id'] in self.TOE:
                raise DuplicateIDError(f"Duplicate TO&E ID found: {data['id']} in {filename}")
            toe_entry = TOE(data['name'], data['nation'], data['sidc'], data['id'],
                            data['subunits'], data['personnel'], data['vehicles'])
            self.TOE.update({toe_entry.id: toe_entry})

        self.build_TOE()

    def build_TOE_entry(self, toe_id):
        toe_entry = self.TOE[toe_id]
        if not toe_entry.is_built:
            # check if this TOE has subunits
            if toe_entry.subunit_entries is not None:
                for subunit in toe_entry.subunit_entries:
                    # build each TOE entry if it isn't already
                    self.build_TOE_entry(subunit)
                    # add the TOE entries to the subunit
                    toe_entry.subunits.append(self.TOE[subunit])
            
            # Create Personnel entries
            if toe_entry.personnel_entries is not None:
                for p in toe_entry.personnel_entries:
                    pers_name = list(p.keys())[0]
                    equipment = [self.LIN[x] for x in p[pers_name]['equipment']]
                    pers = Personnel(pers_name, p[pers_name]['rank'],
                                equipment)
                    toe_entry.personnel.append(pers)
                    # also add the rank into the personnel pool
                    if p[pers_name]['rank'] not in self.all_personnel:
                        self.all_personnel.append(p[pers_name]['rank'])

            # create crew entries
            if toe_entry.vehicle_entries is not None:
                for veh in toe_entry.vehicle_entries:
                    vehicle_lin = self.LIN[list(veh.keys())[0]]
                    crewmembers = []
                    for lin in veh:
                        for crewman in veh[lin]:
                            # create an Element entry for this crewman
                            crewname = list(crewman.keys())[0]
                            print(toe_entry, crewman)
                            equipment = [self.LIN[x] for x in crewman[crewname]['equipment']]
                            pers = Personnel(crewname, crewman[crewname]['rank'],
                                           equipment)
                            crewmembers.append(pers)
                            # Commented for now - Don't add the personnel entry for the crewmembers to make it easier to track crew!
                            # toe_entry.personnel.append(pers)
                    vehicle = Vehicle(vehicle_lin.name, vehicle_lin, crewmembers)
                    toe_entry.vehicles.append(vehicle)

            # set built flag to TOE entry
            print('Built {}'.format(toe_entry))
            toe_entry.is_built = True

    def get_TOE(self, toe_id):
        return self.TOE[toe_id]
    
    def gen_id(self, le=10):
        # generates a random ID string
        alphabet = string.ascii_letters + string.digits 
        internal_id = ''.join(secrets.choice(alphabet) for i in range(le))
        return internal_id
        
    def build_TOE(self,):
        # fills out TOE entries with objects
        for toe in self.TOE:
            # check if this entry is built already:
            self.build_TOE_entry(toe)

    def make_unit_json(self, toe_entry, parent_json_id, group_json_id, side_json_id):
        subunits = []
        unit_json_id = self.gen_id()
        for u in toe_entry.subunits:
            subunits.append(self.make_unit_json(u, unit_json_id, group_json_id, side_json_id))
        # Create equipment for the unit
        equip = []
        equip_dict = {}
        for el in toe_entry.personnel:
            if el.assigned_equipment is None:
                for eq in el.equipment:
                    eq_item = eq.name
                    if eq_item in equip_dict:
                        equip_dict[eq_item] += 1
                    else:
                        equip_dict[eq_item] = 1
            else:
                for eq in el.assigned_equipment:
                    if eq in equip_dict:
                        equip_dict[eq] += 1
                    else:
                        equip_dict[eq] = 1

        # add crewed equipment
        for veh in toe_entry.vehicles:
            if veh.assigned_equipment is None:
                eq_item = veh.equipment.name
            else:
                eq_item = veh.assigned_equipment[0]
            if eq_item in equip_dict:
                equip_dict[eq_item] += 1
            else:
                equip_dict[eq_item] = 1
                
        for eq in equip_dict:
            equip.append({'name': eq,
                          'count': equip_dict[eq]})

        # Create the personnel listing for the unit 
        personnel = []
        personnel_dict = {}
        for pers in toe_entry.personnel:
            rank = pers.rank
            if rank in personnel_dict:
                personnel_dict[rank] += 1
            else:
                personnel_dict[rank] = 1
        for veh in toe_entry.vehicles:
            for crew in veh.crew:
                rank = crew.rank
                if rank in personnel_dict:
                    personnel_dict[rank] += 1
                else:
                    personnel_dict[rank] = 1
        for rank in personnel_dict:
            personnel.append({'name': rank,
                              'count': personnel_dict[rank]})
        # Handling for Formations
        if isinstance(toe_entry, Formation):
            short_name = toe_entry.shortname
            higher_formation = toe_entry.parent_shortname
        else:
            short_name = ''
            higher_formation = ''
                    
        unit_json = {'id': unit_json_id,
                     'name': toe_entry.name,
                     'sidc': toe_entry.sidc,
                     '_pid': parent_json_id, # This is the parent ID
                     '_gid': group_json_id, # this is the group's ID
                     '_sid': side_json_id, # this is the side's ID
                     'state': [],
                     '_state': None,
                     '_isOpen': False,
                     'subUnits': subunits,
                     'equipment': equip,
                     'personnel': personnel,
                     'shortName': short_name,
                     'textAmplifiers': {
                         'higherFormation': higher_formation
                        }
                     }
        
        
        # pp(unit_json)
        
        return unit_json

    def to_orbatmapper(self, filename: str, toe_ids: list = [], units: list = []):
        """_summary_

        Args:
            filename (str): name of the file to export.
            toe_ids (list, optional): List of TO&E IDs to export, all Strings. Defaults to [].
            units (list, optional): List of specific Formations to export, all Formation. Defaults to [].
        """

        from datetime import datetime, timezone

        # Open the template
        with open('./database/toe/orbat_mapper_template.json', 'r') as f:
            orbatmapper = json.loads(f.read())

        # set the modified dates
        now = datetime.now(timezone.utc).isoformat().replace('+00:00', '') + 'Z'
        print(now)
        orbatmapper['meta']['createdDate'] = now
        orbatmapper['meta']['lastModifiedDate'] = now
        orbatmapper['meta']['exportedDate'] = now
        
        # add the new equipment types
        equips = []
        for x in self.LIN:
            lin = self.LIN[x]
            # add a generic equipment type
            equips.append({'name': lin.name, 'description': f'{lin.lin}: {lin.item_entries[0]}'})
            # add specific equipment types
            for item in lin.item_entries:
                equips.append({'name': item, 'description': f'{lin.lin}: {lin.name}'})

        orbatmapper['equipment'] = equips

        # add the new personnel types
        personnel = []
        for p in self.all_personnel:
            personnel.append({'name': p, 'description': p[5:]})

        orbatmapper['personnel'] = sorted(personnel, key=lambda x: x['name'])

        nations = []
        units_to_export = []
        for unit in toe_ids:
            units_to_export.append(self.TOE[unit])
            if self.TOE[unit].nation not in nations:
                nations.append(self.TOE[unit].nation)
        
        for unit in units: # units are standalone TO&Es
            units_to_export.append(unit)
            if unit.nation not in nations:
                nations.append(unit.nation)
        
        # create the sides
        sides = []
        for n in nations:
            nation_id = self.gen_id()
            group_id = self.gen_id()
            subunits = []
            for unit in units_to_export:
                if unit.nation == n:
                    subunit = self.make_unit_json(unit, group_id, group_id, nation_id)
                    subunits.append(subunit)
            nation = {'id': nation_id,
                      'name': n,
                      'standardIdentity': '3', # preset, 3 for friendly
                      'symbolOptions': {},
                      'groups': [ # for now, put all exported units in a group
                          {'id': group_id,
                           'name': 'TO&E',
                           '_pid': nation_id,
                           'subUnits': subunits
                           },
                      ],
                      }
            sides.append(nation)

        orbatmapper['sides'] = sides

        # write the new file
        with open(filename, 'w+') as f:
            f.write(json.dumps(orbatmapper, indent=2))


if __name__ == '__main__':
    db = TOE_Database()
    db.load_database()    
    print('--------------------------------------')
    unit_nsns = ['MPi-KM', 'MPi-KMS', 'BMP-1', 'T-55A', 'ZSU-23-4V', '9K35 Strela-10']
    MSR_332 = Formation('332 Motor Rifle Regiment', '332', 'EG', db.get_TOE('TOEEG020001'), unit_nsns)
    MSR_332_equip = MSR_332.get_all_equipment()
    eq = {}
    for e in MSR_332_equip:
        if e.item_entries[0] not in eq:
            eq[e.item_entries[0]] = 1
        else:
            eq[e.item_entries[0]] += 1
    print(eq)
    print(MSR_332.count_personnel())
    db.to_orbatmapper('toe.json',
                      toe_ids=['TOEEG020001', 'TOEEG020002', 'TOEEG020003', 'TOEWG000005'],
                      units=[MSR_332])
