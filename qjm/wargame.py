import pickle
import yaml
import logging
from glob import glob
import datetime

from toe import Formation, TOE_Database

from .vehicle import Vehicle
from .equipment_database import EquipmentDatabase
from .factors import (
    TERRAIN_FACTORS,
    WEATHER_FACTORS,
    SEASON_FACTORS,
    POSTURE_FACTORS,
    SURPRISE_FACTORS,
    AIR_SUPERIORITY_FACTORS,
    OPPOSITION_FACTORS,
    STRENGTH_SIZE_FACTORS,
    STRENGTH_SIZE_ARMOUR_FACTORS,
    ADVANCE_RATE)
from .qjm_data_classes import (CasualtyRates,
                               FormationOLI,
                               VehicleCategory,
                               BattleData)
from .utils import gist

# Setup debug logging to an empty file
logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s/%(funcName)s - %(message)s'
)
with open('debug.log', 'w') as f:
    f.write('')


GLOBAL_TOE_DATABASE = TOE_Database()
GLOBAL_TOE_DATABASE.load_database()


class Wargame:
    def __init__(self):
        # import the database info
        self.equipment_database = EquipmentDatabase('./database/weapons',
                                                    './database/vehicles')

        # init the formation container
        self.formations = {}
        self.formationsByName = {}
        self.formationsById = {}

        # Init scenario data
        self.scenario_name = None
        self.current_date = datetime.datetime.now() # This gets updated
        self.dispersion = 1000


        # flag for scenario loading
        self.scenario_loaded = False

    def load_scenario(self, scenario):
        if self.scenario_loaded:
            # clear the formations
            self.formations = {}
            self.formationsByName = {}
            self.formationsById = {}
        # update scenario string to subdirectory
        scenario = './wargames/' + scenario
        self.scenario_name = scenario   # saves the name for future loading
        # load the scenario
        try:
            with open(scenario+'/wargame.yml') as f:
                wargameRules = yaml.full_load(f)
        except FileNotFoundError:
            logging.error(f'Scenario {scenario} not found')
            return False
        factions = wargameRules['factions']
        colors = [factions[x]['color'] for x in factions]
        self.dispersion = wargameRules['dispersion_factor']
        # Set the scenario date
        self.current_date = wargameRules['start_date']
        # load formations
        for f in glob(scenario+'/formations/**/*.yml', recursive=True):
            # Extract parameters from yaml file for better readability
            with open(f, 'r', encoding='utf-8') as g:
                data = yaml.safe_load(g)
            name = str(data.get('name', 'Unknown'))
            shortname = str(data.get('shortname', '!'))
            toe = str(data.get('toe', None))
            nsns = data.get('nsns', [])
            position = data.get('position', None)
            faction = data.get('faction', 'Unknown')
            form = Formation(name, shortname, position, GLOBAL_TOE_DATABASE.get_TOE(toe),
                             nsns, faction)
            form.add_qjm_weapons(self.equipment_database)
            if form.faction in colors:
                form.color = colors[form.faction]
            if form.faction not in self.formations:
                self.formations.update({form.faction: [form]})
            else:
                self.formations[form.faction].append(form)
            self.formationsByName.update({form.name: form})
            self.formationsById.update({form.id: form})
            # Add subunits to the formationsById dictionary
            for subunit in form.subunits:
                self._add_subunits(subunit)
        # Load in aircraft
        aircraft = {}
        for faction in wargameRules['factions']:
            aircraft[faction] = wargameRules['factions'][faction]['aircraft']
        # Create a dictionary of QJM vehicles for the aircraft
        self.aircraft = {}
        id_n = 0
        for faction in aircraft:
            self.aircraft[faction] = []
            for a in aircraft[faction]:
                # Search the equipment database for the aircraft
                veh = self.equipment_database.get_vehicle(a)
                if veh is not None:
                    self.aircraft[faction].append({'name': veh.name,
                                                   'sidc': '130301000011010500000000000000',
                                                   'vehicle': veh,
                                                   'color': wargameRules['factions'][faction]['color'],
                                                   'id': f'AIR{id_n:04d}'})
                    id_n += 1
        # Flag the scenario as loaded!
        self.scenario_loaded = True
        return True

    def _add_subunits(self, formation):
        """Recursively adds subunits to the formationsById dictionary."""
        self.formationsById.update({formation.id: formation})
        for subunit in formation.subunits:
            self._add_subunits(subunit)

    def get_formation(self, formation_id=None):
        if formation_id is not None:
            return self.formationsById.get(formation_id, None)
        else:
            return None

    def get_formations(self):
        response = []
        for faction in self.formations:
            print(faction)
            faction_response = {'name': faction, 'units': []}
            for form in self.formations[faction]:
                faction_response['units'].append({'id': form.id,
                                                  'name': form.name,
                                                  'sidc': form.sidc,
                                                  'color': form.color})
            response.append(faction_response)
        return response

    def get_formations_as_tree(self):
        tree = []
        DEFAULT_SIDC = "30031000000000000000"  # Default SIDC for factions

        # Loop through factions
        for faction_name, formations in self.formations.items():
            # Initialize faction node
            faction_node = {
                "name": faction_name,
                "shortname": faction_name,
                "sidc": DEFAULT_SIDC,
                "children": [],
                "id": "faction-" + faction_name,
            }

            # Add each top-level formation in the faction
            for formation in formations:
                formation_node = self._build_formation_node(formation)
                faction_node["children"].append(formation_node)

            tree.append(faction_node)

        return tree

    def _build_formation_node(self, formation):
        """Recursively builds a formation node and its subunits."""
        node = {
            "id": formation.id,
            "name": formation.name,
            "shortname": formation.shortname,
            "sidc": formation.sidc,
            "children": []
        }

        # Recursively add subunits
        for subunit in formation.subunits:
            subunit_node = self._build_formation_node(subunit)
            node["children"].append(subunit_node)

        return node

    def export_orbatmapper(self, filename):
        """Exports the current scenario to Orbatmapper format."""
        # units are just the top level formations
        units = [self.formations[faction] for faction in self.formations]
        # flatten the units list
        units = [item for sublist in units for item in sublist]
        GLOBAL_TOE_DATABASE.to_orbatmapper(filename, units=units, 
                                           start_time=self.current_date,
                                           name=self.scenario_name)
        # Also upload the gist
        with open(filename, 'r') as f:
            content = f.read()
        gist(content)
        return True

    def simulate_battle(self, battle_input, recursive=True, commit=False):
        """Simulates the battle using the QJM method.

        Args:
            battle_input (dict): Dictionary with all battle data information
            recursive (bool): If True, the function will include all subunits in the battle
            commit (bool): If True, the function will commit the losses to the formations
        """

        atk_land_units = battle_input['attackers']
        atk_sorties = battle_input['air_attackers']
        def_land_units = battle_input['defenders']
        def_sorties = battle_input['air_defenders']

        print(atk_sorties)
        print(def_sorties)

        # Get air units from the sorties
        aircraft_by_id = {}
        for fac in self.aircraft:
            for a in self.aircraft[fac]:
                aircraft_by_id[a['id']] = a
        atk_air = []
        def_air = []
        
        for a in atk_sorties:
            atk_air.append({'aircraft': aircraft_by_id[a['id']]['vehicle'], 'sorties': a['sorties']})
        for d in def_sorties:
            def_air.append({'aircraft': aircraft_by_id[d['id']]['vehicle'], 'sorties': d['sorties']})

        print(atk_air, def_air)

        # TODO: Use battle_data in calculations
        battle_data = BattleData(
            terrain=battle_input['terrain'],
            weather=battle_input['weather'],
            season=battle_input['season'],
            posture=battle_input['posture'],
            air_superiority=battle_input['airsuperiority'],
            atk_surprise=battle_input['atksurprise'],
            atk_surprise_days=battle_input['atksurprisedays'],
            atkcev=battle_input['atkcev'],
            defcev=battle_input['defcev'],
            attackers=battle_input['attackers'],
            air_attackers=battle_input.get('air_attackers', []),
            defenders=battle_input['defenders'],
            air_defenders=battle_input.get('air_defenders', [])
            )

        # calculate force strength
        # S = ((Ws + Wmg + Whw) * r_n) + (Wgi * rn) +
        # ((Wg + Wgy) * (rwg * hwg * zwg * wyg)) + 
        # (Wi * rwi * hwi) + (Wy * rwy * hwy * zyw * wyy)
        atk_oli = FormationOLI()
        def_oli = FormationOLI()
        
        Na = 0  # personnel strength
        Nd = 0  # personnel strength
        Nia = 0  # armour strength
        Nid = 0  # armour strength
        Ja = 0  # vehicle strength
        Jd = 0  # vehicle strength

        # J factors (only vehicles other than tanks):
        J_unarmoured = 1
        J_armoured = 2
        J_air = 10  # only organic
        
        # gather OLI values from each formation
        for a in atk_land_units:
            atk_oli += self.formationsById[a].get_oli(recursive=recursive)
            # calculate Na
            Na += self.formationsById[a].count_personnel(recursive=recursive)
            # Calculate Ja
            for equip in self.formationsById[a].get_qjm_equipment(recursive=recursive):
                if isinstance(equip, Vehicle):
                    if equip.qjm_vehicle_category in [VehicleCategory.armoured_car,
                                                      VehicleCategory.truck,
                                                      VehicleCategory.arv]:
                        Ja += J_unarmoured
                    elif equip.qjm_vehicle_category in [VehicleCategory.apc,
                                                        VehicleCategory.ifv,
                                                        VehicleCategory.artillery]:
                        Ja += J_armoured
                    elif equip.qjm_vehicle_category in [VehicleCategory.combat_air_support,
                                                        VehicleCategory.fighter,
                                                        VehicleCategory.bomber,
                                                        VehicleCategory.helicopter]:
                        # only count organic aviation assets
                        Ja += J_air
                    elif equip.qjm_vehicle_category in [VehicleCategory.tank]:
                        Nia += 1
 
        for d in def_land_units:
            oli = self.formationsById[d].get_oli(recursive=recursive)
            def_oli += oli
            # calculate Nd
            Nd += self.formationsById[d].count_personnel(recursive=recursive)
            # Calculate Jd
            for equip in self.formationsById[a].get_qjm_equipment(recursive=recursive):
                if isinstance(equip, Vehicle):
                    if equip.qjm_vehicle_category in [VehicleCategory.armoured_car,
                                                      VehicleCategory.truck,
                                                      VehicleCategory.arv]:
                        Jd += J_unarmoured
                    elif equip.qjm_vehicle_category in [VehicleCategory.apc,
                                                 VehicleCategory.ifv,
                                                 VehicleCategory.artillery]:
                        Jd += J_armoured
                    elif equip.qjm_vehicle_category in [VehicleCategory.combat_air_support,
                                                 VehicleCategory.fighter,
                                                 VehicleCategory.bomber,
                                                 VehicleCategory.helicopter]:
                        # only count organic aviation assets
                        Jd += J_air
                    elif equip.qjm_vehicle_category in [VehicleCategory.tank]:
                        Nid += 1

        # Add aircraft sorties
        for a in atk_air:
            atk_oli.aircraft += a['aircraft'].q_OLI * a['sorties']
        for d in def_air:
            def_oli.aircraft += d['aircraft'].q_OLI * d['sorties']

        # correct values of antitank, antiaircraft, and aircraft by enemy values
        if atk_oli.antitank > def_oli.armour:
            atk_oli.antitank = def_oli.armour + 0.5 * (atk_oli.antitank -
                                                       def_oli.armour)
        if def_oli.antitank > atk_oli.armour:
            def_oli.antitank = atk_oli.armour + 0.5 * (def_oli.antitank -
                                                       atk_oli.armour)
        if atk_oli.antiair > def_oli.aircraft:
            atk_oli.antiair = def_oli.aircraft + 0.5 * (atk_oli.antiair -
                                                        def_oli.aircraft)
        if def_oli.antiair > atk_oli.aircraft:
            def_oli.antiair = atk_oli.aircraft + 0.5 * (def_oli.antiair -
                                                        atk_oli.aircraft)
        atk_ground_firepower = atk_oli.calc_total() - atk_oli.aircraft
        def_ground_firepower = def_oli.calc_total() - def_oli.aircraft

        if atk_oli.aircraft > atk_ground_firepower:
            atk_oli.aircraft = atk_ground_firepower + 0.5 * (atk_oli.aircraft - atk_ground_firepower)
        if atk_oli.aircraft > 3 * atk_ground_firepower:
            atk_oli.aircraft = 3 * atk_ground_firepower

        if def_oli.aircraft > def_ground_firepower:
            def_oli.aircraft = def_ground_firepower + 0.5 * (def_oli.aircraft - def_ground_firepower)
        if def_oli.aircraft > 3 * def_ground_firepower:
            def_oli.aircraft = 3 * def_ground_firepower

        # Attacker variables
        # Terrain Factors
        rm  = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Mobility (r_m)')
        rua  = 1.0
        rud  = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Defense Position (r_u)')
        rn  = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Infantry Weapons (r_n)')
        rwg = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Artillery (r_wg)')
        rwy = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Air (r_wy)')
        rwi = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Tanks (r_wt)')
        rc  = TERRAIN_FACTORS.get(battle_input['terrain'],
                                  'Casualty (r_c)')
        # Weather Factors
        hm  = WEATHER_FACTORS.get(battle_input['weather'],
                              'Mobility (h_m)')
        hua = WEATHER_FACTORS.get(battle_input['weather'],
                              'Attack (h_ua)')
        hud = 1.0
        hwg = WEATHER_FACTORS.get(battle_input['weather'],
                              'Artillery (h_wg)')
        hwy = WEATHER_FACTORS.get(battle_input['weather'],
                              'Air (h_wy)')
        hwi = WEATHER_FACTORS.get(battle_input['weather'],
                              'Tanks (h_wt)')
        hc  = WEATHER_FACTORS.get(battle_input['weather'],
                              'Casualties (h_c)')
        # Season Factors
        zua = SEASON_FACTORS.get(battle_input['season'],
                             'Attack (z_u)')
        zud = 1.0
        zwg = SEASON_FACTORS.get(battle_input['season'],
                             'Artillery (z_wg)')
        zwy = SEASON_FACTORS.get(battle_input['season'],
                             'Air (z_wy)')
        # Posture Factors
        usa = 1.0
        usd = POSTURE_FACTORS.get(battle_input['posture'],
                              'Strength (u_s)')
        uva = 1.0
        uvd = POSTURE_FACTORS.get(battle_input['posture'],
                              'Vulnerability (u_v)')
        uca = POSTURE_FACTORS.get(battle_input['posture'],
                              'Attack Casualties (u_ca)')
        ucd = POSTURE_FACTORS.get(battle_input['posture'],
                              'Defense Casualties (u_cd)')
        # Surprise Factors
        eraSurpriseFactor = 1.33 # 1.33 post 1966
        Msur  = SURPRISE_FACTORS.get(battle_input['atksurprise'],
                                     'Mobility Characteristics (Msur)'
                                     ) * eraSurpriseFactor
        Vsura = SURPRISE_FACTORS.get(battle_input['atksurprise'],
                                     'Vulnerability (Vsur)'
                                     ) * eraSurpriseFactor
        Vsurd = SURPRISE_FACTORS.get(battle_input['atksurprise'],
                                     'Surprised Vulnerability (Vsurd)'
                                     ) * eraSurpriseFactor
        su_c  = SURPRISE_FACTORS.get(battle_input['atksurprise'],
                                     'Surprised Vulnerability (Vsurd)'
                                     ) * eraSurpriseFactor
        su_ct = SURPRISE_FACTORS.get(battle_input['atksurprise'],
                                     'Surprised Vulnerability (Vsurd)'
                                     ) * eraSurpriseFactor
        surprise_days = int(battle_input['atksurprisedays'])
        # Update surprise factors for duration, all trend to 1.0 and reduce by 1/3 for each day
        Msur  = 1.0 + (Msur-1.0) * (3-surprise_days)/3
        Vsura = 1.0 + (Vsura-1.0) * (3-surprise_days)/3
        Vsurd = 1.0 + (Vsurd-1.0) * (3-surprise_days)/3
        su_c  = 1.0 + (su_c-1.0) * (3-surprise_days)/3
        su_ct = 1.0 + (su_ct-1.0) * (3-surprise_days)/3


        # TODO Obstacle Factors
        vr = 1.0 # TODO ADD ADDITIONAL DATA FOR SHORELINE VULNERABILITY
        


        # Air Superiority Factors
        if battle_input['airsuperiority'] == 'Air Superiority':
            if hwy > 0.5:
                atk_my = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Mobility (m_yd)')
                def_my = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Mobility (m_yd)')
            else:
                atk_my = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Mobility (m_yw)')
                def_my = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Mobility (m_yw)')
            wyga = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Artillery (w_yg)')
            wygd = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Artillery (w_yg)')
            wyya = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Air (w_yy)')
            wyyd = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Air (w_yy)')
            vya  = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Vulnerability (v_y)')
            vyd  = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Vulnerability (v_y)')
        elif battle_input['airsuperiority'] == 'Air Inferiority':
            if hwy > 0.5:
                atk_my = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Mobility (m_yd)')
                def_my = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Mobility (m_yd)')
            else:
                atk_my = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Mobility (m_yw)')
                def_my = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Mobility (m_yw)')
            wyga = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Artillery (w_yg)')
            wygd = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Artillery (w_yg)')
            wyya = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Air (w_yy)')
            wyyd = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Air (w_yy)')
            vya  = AIR_SUPERIORITY_FACTORS.get('Air Inferiority',
                                                     'Vulnerability (v_y)')
            vyd  = AIR_SUPERIORITY_FACTORS.get('Air Superiority',
                                                     'Vulnerability (v_y)')
        else:
            if hwy > 0.5:
                atk_my = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Mobility (m_yd)')
                def_my = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Mobility (m_yd)')
            else:
                atk_my = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Mobility (m_yw)')
                def_my = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Mobility (m_yw)')
            wyga = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Artillery (w_yg)')
            wygd = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Artillery (w_yg)')
            wyya = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Air (w_yy)')
            wyyd = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Air (w_yy)')
            vya  = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Vulnerability (v_y)')
            vyd  = AIR_SUPERIORITY_FACTORS.get('Air Equality',
                                                     'Vulnerability (v_y)')

        # Era factor:
        JFactor = 15 # 20 for WW2, 15 for 1970s
        # Attacker strength calculation
        atk_S = (((atk_oli.small_arms + atk_oli.machine_guns + atk_oli.heavy_weapons) * rn)
                + (atk_oli.antitank * rn)
                + ((atk_oli.artillery + atk_oli.antiair) * (rwg * hwg * zwg * wyga))
                + (atk_oli.armour * rwi * hwi)
                + (atk_oli.aircraft * rwy * hwy * zwy * wyya))
        
        # Defender strength calculation
        def_S = (((def_oli.small_arms + def_oli.machine_guns + def_oli.heavy_weapons) * rn)
                + (def_oli.antitank * rn)
                + ((def_oli.artillery + def_oli.antiair) * (rwg * hwg * zwg * wygd))
                + (def_oli.armour * rwi * hwi)
                + (def_oli.aircraft * rwy * hwy * zwy * wyyd))

        # Attacker mobility calculation
        atk_M = (((Na + JFactor*Ja + atk_oli.armour) * atk_my / Na) / ((Nd + JFactor*Jd + def_oli.armour) * def_my / Nd))**0.5 * Msur
        atk_m = atk_M - (1-rm*hm)*(atk_M-1) # operational mobility, different than M

        # Defender mobility calculation
        def_m = 1.0

        atk_V = Na * uva/rua * (def_S/atk_S)**0.5 * vya * vr * Vsura
        def_V = Nd * uvd/rud * (atk_S/def_S)**0.5 * vyd * vr * Vsurd

        if atk_V / atk_S > 0.3:
            atk_VS = 0.3 + 0.1*(atk_V/atk_S - 0.3)
        else:
            atk_VS = atk_V/atk_S
        if def_V / def_S > 0.3:
            def_VS = 0.3 + 0.1*(def_V/def_S - 0.3)
        else:
            def_VS = def_V/def_S
        atk_v = 1 - atk_VS * self.dispersion/3000
        def_v = 1 - def_VS * self.dispersion/3000

        if atk_v < 0.6:
            atk_v = 0.6
        if def_v < 0.6:
            def_v = 0.6

        atk_P = atk_S * atk_m * usa * rua * hua * zua * atk_v * float(battle_input['atkcev'])
        def_P = def_S * def_m * usd * rud * hud * zud * def_v * float(battle_input['defcev'])

        PRatio = atk_P / def_P

        # calculate casualty factors
        # power ratio factor for casualties
        ca_power    = OPPOSITION_FACTORS.interpolate(PRatio)
        # power ratio factor for casualties
        cd_power    = OPPOSITION_FACTORS.interpolate(1/PRatio)
        # personnel strength factor for casualties
        ca_strength = STRENGTH_SIZE_FACTORS.interpolate(Na)
        # personnel strength factor for casualties
        cd_strength = STRENGTH_SIZE_FACTORS.interpolate(Nd)
        # armour strength factor for casualties
        ca_arm      = STRENGTH_SIZE_ARMOUR_FACTORS.interpolate(Nia)
        # armour strength factor for casualties
        cd_arm      = STRENGTH_SIZE_ARMOUR_FACTORS.interpolate(Nid)
        # TODO - factor in Attrition is 0.04, 0.028 in NPW, why?
        ca  = 0.028 * rc * hc * uca * ca_strength * ca_power
        cia = ca * 6.0 * ca_arm * float(battle_input['defcev'])
        cga = ca * float(battle_input['defcev'])

        # TODO - factor in Attrition is 0.04, 0.015 in NPW, why?
        cd  = 0.015 * rc * hc * ucd * cd_strength * cd_power * su_c
        cid = cd * 3.0 * cd_arm * su_ct * float(battle_input['atkcev'])
        cgd = cd * float(battle_input['atkcev'])

        # Calculate the advance rate
        # Advance rate depends on the defense type
        if battle_input['posture'] == 'Prepared Defense':
            def_type = 'Prepared Defense'
        elif battle_input['posture'] == 'Fortified Defense':
            def_type = 'Fortified Defense'
        else:
            # Default to hasty defense
            def_type = 'Hasty Defense'
        adv = ADVANCE_RATE.get_advance_rate(PRatio, def_type,)

        # Print combat data
        print('###### COMBAT RESULTS ########\n' +
              'Power Ratio: {:,.1f}\n'.format(PRatio) +
              '  Attacker: P:{:,.1f} m:{:,.1f} v:{:,.1f}\n'.format(atk_P, atk_m, atk_v) +
              '  Defender: P:{:,.1f} m:{:,.1f} v:{:,.1f}\n'.format(def_P, def_m, def_v) +
              'Casualty Rates:\n' +
              '  Attacker: {:.2f}% pers {:.2f}% tanks {:.2f}% artillery\n'.format(ca*100, cia*100, cga*100) +
              '             {:,.0f}/{:,.0f} personnel | {:,.0f}/{:,.0f} armour\n'.format(ca*Na, Na, cia*Nia, Nia) +
              '      Factors: P{:,.2f} S{:,.2f} Arm{:,.2f}\n'.format(ca_power, ca_strength, ca_arm, Nia) +
              '  Defender: {:.2f}% pers {:.2f}% tanks {:.2f}% artillery\n'.format(cd*100, cid*100, cgd*100) +
              '      Factors: P{:,.2f} S{:,.2f} Arm{:,.2f}\n'.format(cd_power, cd_strength, cd_arm) +
              '             {:,.0f}/{:,.0f} personnel | {:,.0f}/{:,.0f} armour\n'.format(cd*Nd, Nd, cid*Nid, Nid) +
              'Advance Rates:'
              )
        for key in adv:
            print('  {}: {:.1f} km/day'.format(key, adv[key]))
        
        if commit:
            # send casualty data to the formations
            atkCas = CasualtyRates(ca, cia, cga, True)
            defCas = CasualtyRates(cd, cid, cgd, False)
            for a in atk_land_units:
                self.formationsById[a].inflict_losses(atkCas)
            for d in def_land_units:
                self.formationsById[d].inflict_losses(defCas)

        else:
            # return data to the caller
            battleResults = {'powerRatio': PRatio,
                             'powerAtk': atk_P,
                             'powerDef': def_P,
                             'atkPersCasualtyRate': ca,
                             'atkTankCasualtyRate': cia,
                             'defPersCasualtyRate': cd,
                             'defTankCasualtyRate': cid,
                             'advanceRate': adv,
                            }
            return battleResults

    def save_sim_state(self, filename):
        logging.info(f'Saving simulation state to {filename}')
        state = {
            'scenario_name': self.scenario_name,
            'formations': self.formations,
            'formationsByName': self.formationsByName,
            'formationsById': self.formationsById,
            'dispersion': self.dispersion,
        }
        with open(filename, 'wb') as f:
            pickle.dump(state, f)
        logging.info(f'Succesfully saved simulation state to {filename}')

    def load_sim_state(self, filename):
        logging.info(f'Loading simulation state from {filename}')
        with open(filename, 'rb') as f:
            state = pickle.load(f)
            self.formations = state['formations']
            self.formationsByName = state['formationsByName']
            self.formationsById = state['formationsById']
            self.dispersion = state['dispersion']
            self.scenario_loaded = True
        logging.info(f'Successfully loaded simulation state from {filename}')


    def log_sitrep(self, battle_input, results):
        """Generates a structured SITREP based on standard military reporting format."""
        
        # Helper functions to approximate enemy information
        def approximate_strength(personnel_count):
            if personnel_count < 100:
                return "few"
            elif personnel_count < 500:
                return "a moderate number of"
            else:
                return "many"
        
        def approximate_vehicle_strength(vehicle_count):
            if vehicle_count < 5:
                return "minimal"
            elif vehicle_count < 15:
                return "moderate"
            else:
                return "substantial"
        
        def describe_casualties(casualty_rate):
            if casualty_rate < 0.1:
                return "light casualties"
            elif casualty_rate < 0.25:
                return "moderate casualties"
            else:
                return "heavy casualties"

        # Get date and time in DTG format
        dtg = datetime.datetime.now().strftime("%d%H%MZ %b %y")
        
        # Generate the SITREP
        sitrep = []
        sitrep.append("### Situation Report ###")
        sitrep.append(f"LINE 1 - DATE AND TIME: {dtg}")

        # Line 2: Unit Making Report
        unit_reporting = "Reporting Unit Name"  # replace with actual data source
        sitrep.append(f"LINE 2 — UNIT: {unit_reporting}")

        # Line 3: Reference Information
        sitrep.append("LINE 3 — REFERENCE: (SITREP Report, Originator, and DTG)")
        
        # Line 4: Originating Unit
        sitrep.append(f"LINE 4 — ORIGINATOR: {unit_reporting}")
        
        # Line 5: Reported Unit
        sitrep.append("LINE 5 — REPORTED UNIT: (UIC of Reported Unit)")
        
        # Line 6: Home Location
        sitrep.append("LINE 6 — HOME LOCATION: (UTM or MGRS Coordinates)")
        
        # Line 7: Present Location
        sitrep.append("LINE 7 — PRESENT LOCATION: (UTM or MGRS Coordinates)")
        
        # Line 8: Activity - Brief description of reported unit’s current activity
        activity = "Engaged in combat operations against opposing forces in a defensive posture."
        sitrep.append(f"LINE 8 — ACTIVITY: {activity}")
        
        # Line 9: Combat Effectiveness
        effectiveness = "Effective" if results['powerRatio'] > 1.0 else "Degraded"
        sitrep.append(f"LINE 9 — EFFECTIVE: {effectiveness}")
        
        # Line 10: Own Situation Disposition/Status
        own_situation = "Unit is positioned on forward lines with moderate personnel and vehicle strength. Preparing for further engagements as needed."
        sitrep.append(f"LINE 10 — OWN SITUATION DISPOSITION/STATUS: {own_situation}")
        
        # Line 11: Location (Current unit location; simulated here)
        sitrep.append("LINE 11 — LOCATION: (UTM or MGRS Coordinates)")
        
        # Line 12: Situation Overview
        overview = "Engaged with enemy forces of uncertain strength in adverse weather conditions. Unit reports substantial engagement activity with no significant degradation in operational capability."
        sitrep.append(f"LINE 12 — SITUATION OVERVIEW: {overview}")
        
        # Line 13: Operations Summary
        operations_summary = ("Offensive operations initiated against an estimated enemy force of "
                            f"{approximate_strength(battle_input['defenders'][0])} personnel with {approximate_vehicle_strength(len(self.formationsById[battle_input['defenders'][0]].vehicles))} vehicle support. "
                            f"Enemy forces encountered {describe_casualties(results['defPersCasualtyRate'])} and displayed {describe_casualties(results['defTankCasualtyRate'])} in armored units.")
        sitrep.append(f"LINE 13 — OPERATIONS:  {operations_summary}")
        
        # Line 14: Intelligence/Reconnaissance
        intel = "Previous reconnaissance suggests enemy forces have limited armor support and light aerial assets. "
        sitrep.append(f"LINE 14 — INTELLIGENCE/RECONNAISSANCE: {intel}")
        
        # Line 15: Logistics Summary
        logistics = "Logistics and supply routes remain operational with no immediate deficiencies reported. Ammunition resupply anticipated within 24 hours."
        sitrep.append(f"LINE 15 — LOGISTICS {logistics}")
        
        # Line 16: Communications/Connectivity
        comms = "No significant communication outages reported. Internal networks functioning within acceptable parameters."
        sitrep.append("LINE 16 — COMMUNICATIONS/CONNECTIVITY: {intel}")
        
        # Line 17: Personnel Summary
        atk_personnel = self.formationsById[battle_input['attackers'][0]].count_personnel()
        def_personnel_casualty_desc = describe_casualties(results['defPersCasualtyRate'])
        sitrep.append(f"LINE 17 — PERSONNEL_________________________________ Estimated attacker personnel: {atk_personnel}. Enemy personnel have suffered {def_personnel_casualty_desc}.")
        
        # Save the SITREP to a log file
        sitrep_file = f"{dtg}_sitrep.txt"
        with open(f"./wargames/saves/sitrep/{sitrep_file}", "a+") as file:
            file.write("\n".join(sitrep) + "\n\n")

    def formation_snapshot(self, battle_date, unit_locations):
        for formation in self.formationsById.values():
            # Check the unit_locations report to see if any match the formation
            location = None
            for unit in unit_locations:
                if unit['id'] == formation.id:
                    location = unit['coordinates']
                    break
            formation.snapshot(battle_date, location)
            # Update the scenario date
            self.current_date = datetime.datetime.fromisoformat(battle_date)
        return True

    def get_snapshots(self, battle_date):
        """Retrieve snapshots for all formations on a specific battle_date."""
        snapshots = []
        for formation in self.formationsById.values():
            snapshot = formation.get_snapshot(battle_date)
            if snapshot is not None:
                if snapshot['location'] is not None:
                    snapshots.append({
                        'id': formation.id,
                        'location': snapshot['location']
                    })
        return {'formations': snapshots}