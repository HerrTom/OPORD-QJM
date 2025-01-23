import yaml
import json
import secrets
import string
import logging
from glob import glob
from uuid import uuid4
import html

from .enums import ElementStatus
from .exceptions import DuplicateIDError
from .lin import LIN
from .element import Personnel, Vehicle
from qjm import FormationOLI, EquipmentOLICategory


class Formation:
    def __init__(self, name: str, shortname: str, parent_shortname: str, toe=None,
                 nsns: list=None, faction=None, custom_data=None):
        self.name = name
        self.shortname = shortname
        self.parent_shortname = parent_shortname if parent_shortname else ''
        # Update fullshortname to include parent's shortname if it exists
        self.fullshortname = f'{shortname}/{self.parent_shortname}' if self.parent_shortname else shortname
        self.id = str(uuid4())
        self.faction = faction
        if toe is None:
            self.nation = custom_data['nation']
            self.sidc = custom_data['sidc']
        else:
            self.nation = toe.nation
            self.sidc = toe.sidc

        # This is set when the formation is loaded into the wargame
        self.color = None

        if nsns is None: # Avoiding mutable default argument
            nsns = []

        # now we copy the TO&E from lower level units
        self.subunits = []
        self.vehicles = []
        self.personnel = []
        if toe is None:
            self.subunits = custom_data['subunits']
        else:
            if len(toe.subunits) > 0:
                count = 1
                for sub in toe.subunits:
                    # Use sub.shortname if available, otherwise use count
                    if hasattr(sub, 'shortname') and sub.shortname:
                        unit_shortname = sub.shortname
                    else:
                        unit_shortname = str(count)
                        count += 1
                    new_sub = self.copy_toe(unit_shortname+'/'+shortname, unit_shortname, sub, nsns)
                    self.subunits.append(new_sub)
                    
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

        self.status_history = {}

    def __repr__(self,):
        return f'Formation({self.shortname}/{self.parent_shortname}, {self.nation})'

    def copy_toe(self, name, shortname, toe, nsns):
        # Pass current formation's shortname as the parent_shortname for subunits
        return Formation(name, shortname, self.shortname, toe, nsns, self.faction)
    
    def add_qjm_weapons(self, equipment_db):
        """ Assign QJM equipment to all personnel and vehicles in the formation. """
        for veh in self.vehicles:
            veh.assign_qjm_equipment(equipment_db)
            for crew in veh.crew:
                crew.assign_qjm_equipment(equipment_db)
        for weap in self.personnel:
            weap.assign_qjm_equipment(equipment_db)

        for sub in self.subunits:
            sub.add_qjm_weapons(equipment_db)

    def inflict_losses(self, cr):
        """ Inflict casualties on the formation based on the casualty rates. """
        for veh in self.vehicles:
            veh.test_casualty(cr)
        for pers in self.personnel:
            pers.test_casualty(cr)
        for sub in self.subunits:
            sub.inflict_losses(cr)
    
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
    
    def get_qjm_equipment(self, recursive=True):
        """ Get all QJM equipment in the formation. """
        qjm_equipment = []
        for veh in self.vehicles:
            qjm_equipment += veh.get_qjm_equipment()
            for crew in veh.crew:
                qjm_equipment += crew.get_qjm_equipment()
        for pers in self.personnel:
            qjm_equipment += pers.get_qjm_equipment()
        if recursive:
            for sub in self.subunits:
                qjm_equipment += sub.get_qjm_equipment()
        return qjm_equipment

    def get_all_personnel(self, recursive=True):
        all_personnel = []
        if recursive:
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
    def count_personnel(self, recursive=True):
        N_personnel = 0
        personnel = self.get_all_personnel(recursive)
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
        # TODO: Need to get equipment by type
        return equipment
    
    def get_oli(self, recursive=True):
        # returns OLI statistics about formation
        oli = FormationOLI()  # Default is all zeros
        for veh in self.vehicles:
            oli += veh.get_oli()
            for crew in veh.crew:
                oli += crew.get_oli()
        for pers in self.personnel:
            logging.debug(f'{pers.name} has OLI {pers.get_oli()}')
            oli += pers.get_oli()
        if recursive:
            for sub in self.subunits:
                oli += sub.get_oli()
        return oli

    def snapshot(self, datecode: str, location: dict = None):
        """Capture the current status of the formation."""
        self.status_history[datecode] = {
            'personnel': {},
            'equipment': {},
            'location': location
        }

        # Capture Personnel status
        for pers in self.personnel:
            type_key = pers.rank
            if type_key not in self.status_history[datecode]['personnel']:
                self.status_history[datecode]['personnel'][type_key] = {'assigned': 0, 'available': 0}
            if pers.status == ElementStatus.ACTIVE:
                self.status_history[datecode]['personnel'][type_key]['available'] += 1
            # Assigned include all personnel in the unit, active or not
            self.status_history[datecode]['personnel'][type_key]['available'] += 1

        # Capture equipment status
        for pers in self.personnel:
            for eq in pers.assigned_equipment:
                if eq not in self.status_history[datecode]['equipment']:
                    self.status_history[datecode]['equipment'][eq] = {'assigned': 0, 'available': 0}
                self.status_history[datecode]['equipment'][eq]['assigned'] += 1
                if pers.status == ElementStatus.ACTIVE:
                    self.status_history[datecode]['equipment'][eq]['available'] += 1
        for veh in self.vehicles:
            for eq in veh.assigned_equipment:
                if eq not in self.status_history[datecode]['equipment']:
                    self.status_history[datecode]['equipment'][eq] = {'assigned': 0, 'available': 0}
                if veh.status == ElementStatus.ACTIVE:
                    self.status_history[datecode]['equipment'][eq]['available'] += 1
                # Assigned includes all vehicles in the unit, active or not
                self.status_history[datecode]['equipment'][eq]['assigned'] += 1

        # Recursively capture status for subunits
        for sub in self.subunits:
            sub.snapshot(datecode)

    def get_snapshot(self, datecode: str):
        """Retrieve the status of the formation at a specific datecode."""
        snap = self.status_history.get(datecode, None)
        # Debugging logic
        if snap is not None:
            if snap['location'] is not None:
                logging.debug(f"{self.shortname} is located at {snap['location']} on {datecode}")
        return snap


class TOE:
    def __init__(self, name: str, nation: str, sidc: str, toe_id: str,
                 subunits: list, personnel: list, vehicles: list, shortname: str = None):
        """
        Initialize a new TO&E (Table of Organization and Equipment).

        Args:
            name (str): The name of the TO&E.
            nation (str): The nation to which the TO&E belongs.
            sidc (str): The Symbol Identification Code (SIDC) for the TO&E.
            toe_id (str): The unique identifier for the TO&E.
            subunits (list): A list of subunit entries.
            personnel (list): A list of personnel entries.
            vehicles (list): A list of vehicle entries.
            shortname (str, optional): Custom short name for the unit.
        """
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
        self.shortname = shortname

        self.is_built = False
        
    def __repr__(self,):
        return 'TO&E({}: {}, {})'.format(self.id, self.name, self.nation)

class TOE_Database:
    """
    A database containing all TO&E (Table of Organization and Equipment) structures.
    """
    def __init__(self,):
        """
        Initialize a new TOEDatabase instance.
        """
        self.TOE = {}
        self.LIN = {}
        self.all_personnel = []

    def load_database(self,):
        """
        Load the TO&E and LIN data from YAML files into the database.
        
        Raises:
            DuplicateIDError: If a duplicate TO&E or LIN ID is found.
        """
        # hardcoded for now
        raw_toe_files = glob('./database/toe/**/*.yaml', recursive=True)
        raw_lin_files = glob('./database/lin_equipment/**/*.yaml', recursive=True)

        # load in and process the Line Item Numbers
        for filename in raw_lin_files:
            with open(filename, 'r') as f:
                data = yaml.safe_load(f)
            for lin in data:
                if lin in self.LIN:
                    logging.error(f"Duplicate LIN ID found: {lin} in {filename}")
                    raise DuplicateIDError(f"Duplicate LIN ID found: {lin} in {filename}")
                line_item = LIN(lin, data[lin]['name'], data[lin]['items'])
                self.LIN.update({lin: line_item})

        for filename in raw_toe_files:
            with open(filename, 'r') as f:
                data = yaml.safe_load(f)
            if data['id'] in self.TOE:
                logging.error(f"Duplicate TO&E ID found: {data['id']} in {filename}")            
                raise DuplicateIDError(f"Duplicate TO&E ID found: {data['id']} in {filename}")
            toe_entry = TOE(data['name'], data['nation'], data['sidc'], data['id'],
                            data['subunits'], data['personnel'], data['vehicles'],
                            shortname=data.get('shortname', None))
            self.TOE.update({toe_entry.id: toe_entry})

        self.build_TOE()

    def build_TOE_entry(self, toe_id: str, visited=None, chain=None):
        """
        Build a TO&E entry by its ID.

        Args:
            toe_id (str): The ID of the TO&E entry to build.
        """
        if visited is None:
            visited = set()
        if chain is None:
            chain = []

        if toe_id in visited:
            raise Exception(f"Recursion detected in TO&E build. Chain: {chain + [toe_id]}")

        visited.add(toe_id)
        chain.append(toe_id)

        toe_entry = self.TOE[toe_id]
        if not toe_entry.is_built:
            # check if this TOE has subunits
            if toe_entry.subunit_entries is not None:
                for subunit in toe_entry.subunit_entries:
                    # build each TOE entry if it isn't already
                    self.build_TOE_entry(subunit, visited, chain)
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
                            equipment = [self.LIN[x] for x in crewman[crewname]['equipment']]
                            pers = Personnel(crewname, crewman[crewname]['rank'],
                                           equipment)
                            crewmembers.append(pers)
                            # Commented for now - Don't add the personnel entry for the crewmembers to make it easier to track crew!
                            # toe_entry.personnel.append(pers)
                    vehicle = Vehicle(vehicle_lin.name, vehicle_lin, crewmembers)
                    toe_entry.vehicles.append(vehicle)

            # set built flag to TOE entry
            logging.info('Built {}'.format(toe_entry))
            toe_entry.is_built = True

        chain.pop()
        visited.remove(toe_id)

    def get_TOE(self, toe_id: str):
        """
        Get a TO&E entry by its ID.

        Args:
            toe_id (str): The ID of the TO&E entry to retrieve.

        Returns:
            TOE: The TO&E entry with the specified ID.
        """
        return self.TOE[toe_id]
    
    def gen_id(self, le=10):
        """
        Generate a random ID string.

        Args:
            le (int, optional): The length of the ID string. Defaults to 10.

        Returns:
            str: A randomly generated ID string.
        """
        # generates a random ID string
        alphabet = string.ascii_letters + string.digits 
        internal_id = ''.join(secrets.choice(alphabet) for i in range(le))
        return internal_id
        
    def build_TOE(self,):
        """
        Build all TO&E entries in the database.
        """
        for toe in self.TOE:
            self.build_TOE_entry(toe, visited=set(), chain=[])

    def make_unit_json(self, toe_entry, parent_shortname, group_json_id, side_json_id):
        """
        Create a JSON representation of a TO&E entry.

        Args:
            toe_entry (TOE): The TO&E entry to convert to JSON.
            parent_shortname (str): The shortname of the parent formation.
            group_json_id (str): The group JSON ID.
            side_json_id (str): The side JSON ID.

        Returns:
            dict: A JSON representation of the TO&E entry.
        """
        subunits = []
        unit_json_id = self.gen_id()
        for u in toe_entry.subunits:
            # Pass the current unit's shortname as the parent for its subunits
            if isinstance(toe_entry, Formation):
                parent = toe_entry.shortname
            else:
                parent = ''
            subunits.append(self.make_unit_json(u, parent, group_json_id, side_json_id))
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
            else: # this should be a standard formation
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
            if pers.status == ElementStatus.ACTIVE or pers.status == ElementStatus.UNDEFINED:
                rank = pers.rank
                if rank in personnel_dict:
                    personnel_dict[rank] += 1
                else:
                    personnel_dict[rank] = 1
        for veh in toe_entry.vehicles:
            for crew in veh.crew:
                if crew.status == ElementStatus.ACTIVE or crew.status == ElementStatus.UNDEFINED:
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

        # Catch null higherFormation values
        if higher_formation is None:
            higher_formation = ''

        # Create the state list if the unit is a Formation
        state = []
        if isinstance(toe_entry, Formation):
            for t, entry in toe_entry.status_history.items():
                if entry['location'] is not None:
                    lat, lon = entry['location']['lat'], entry['location']['lng']
                else:
                    lat, lon = None, None
                eq_update = []
                for eq, st in entry['equipment'].items():
                    eq_update.append({'name': eq,
                                      'onHand': st['available'],})
                pers_update = []
                for pers, st in entry['personnel'].items():
                    pers_update.append({'name': pers,
                                        'onHand': st['available'],})
                state_entry = {'id': self.gen_id(),
                               't': t + 'Z'}
                if lat is not None:
                    state_entry.update({'location': [lon, lat],})
                if len(eq_update) > 0 or len(pers_update) > 0:
                    state_entry.update({'update': {'equipment': eq_update,
                                        'personnel': pers_update}})
                state.append(state_entry)
        
        unit_json = {'id': unit_json_id,
                     'name': html.escape(toe_entry.name),
                     'sidc': toe_entry.sidc,
                     'subUnits': subunits,
                     'equipment': equip,
                     'personnel': personnel,
                     'shortName': short_name,
                     'textAmplifiers': {
                         'higherFormation': higher_formation
                        },
                     'state': state,
                     'reinforcedStatus': 'None',
                     'symbolOptions': {},
                     }
        
        
        # pp(unit_json)
        
        return unit_json

    def to_orbatmapper(self, filename: str, toe_ids: list = [], units: list = [],
                       start_time = None, name=None, maplayers=None, layers=None):
        """
        Export the TO&E database to an OrbatMapper JSON file.

        Args:
            filename (str): The name of the file to export.
            toe_ids (list, optional): List of TO&E IDs to export. Defaults to [].
            units (list, optional): List of specific Formations to export. Defaults to [].
        """

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        if start_time is None:
            start_time = now

        if name is None:
            name = 'OPORD-QJM'
        
        version = "0.37.0"

        # TEMPLATE #
        orbatmapper = {
            "id": "zRHXbiph4w", # ID is fixed
            "type": "ORBAT-mapper",
            "version": version,
            "meta": {
                "createdDate": now.isoformat().replace('+00:00', '') + 'Z',
                "exportedDate": now.isoformat().replace('+00:00', '') + 'Z'
            },
            "name": name,
            "startTime": start_time.isoformat().replace('+00:00','') + 'Z',
            "timeZone": "Europe/London",
            "description": "OPORD-QJM Export",
            "symbologyStandard": "app6",
            "sides": [],
            "layers": [
                {
                "name": "Features",
                "id": "3cNAokn3OJ",
                "features": [],
                }
            ],
            "events": [],
            "mapLayers": [],
            "equipment": [],
            "personnel": [],
            "supplyCategories": [],
            "settings": {
                "rangeRingGroups": [
                {
                    "name": "GR1"
                },
                {
                    "name": "GR2"
                }
                ],
                "statuses": [],
                "supplyClasses": [],
                "supplyUoMs": [],
                "map": {
                    "baseMapId": "osm"
                }
            }
        }

        # set the modified dates
        logging.info(f'Created OrbatMapper file dated {now}')
        
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

        # Add the map layers
        if maplayers is not None:
            for layer in maplayers:
                orbatmapper['mapLayers'].append(layer)
        # Add the features
        if layers is not None:
            for layer in layers:
                orbatmapper['layers'].append(layer)

        # write the new file
        with open(filename, 'w+') as f:
            f.write(json.dumps(orbatmapper, indent=2))
