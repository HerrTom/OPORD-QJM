import socket
import json
import yaml
import logging
from glob import glob
from uuid import uuid1
import numpy as np

from toe import Formation, TOE_Database

from .weapon import Weapon
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
    STRENGTH_SIZE_ARMOUR_FACTORS)
from .qjm_data_classes import (CasualtyRates,
                               FormationOLI,
                               EquipmentOLICategory,
                               VehicleCategory)


# Setup debug logging to an empty file
logging.basicConfig(filename='debug.log', level=logging.DEBUG)
with open('debug.log', 'w') as f:
    f.write('')


GLOBAL_TOE_DATABASE = TOE_Database()
GLOBAL_TOE_DATABASE.load_database()

class Wargame:
    def __init__(self):
        # import the database info
        self.equipment_database = EquipmentDatabase('./database/weapons', './database/vehicles')
        
        # init the formation container
        self.formations = {}
        self.formationsByName = {}
        self.formationsById = {}

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
            print(self.formations)
            self.scenario_loaded = True
        return True

    def get_formations(self):
        response = []
        for faction in self.formations:
            print(faction)
            faction_response = {'name': faction, 'units': []}
            for form in self.formations[faction]:
                faction_response['units'].append({'id': form.id, 'name': form.name, 'sidc': form.sidc, 'color': form.color})
            response.append(faction_response)
        return response
    
    def export_orbatmapper(self, filename):
        """Exports the current scenario to Orbatmapper format."""
        units = [self.formationsById[x] for x in self.formationsById]
        GLOBAL_TOE_DATABASE.to_orbatmapper(filename, units=units)
        return True
    
    def simulate_battle(self, battleData, commit=False):
        """Simulates the battle using the QJM method.

        Args:
            battleData (dict): Dictionary with all battle data information (TBD)
        """

        atk_land_units = battleData['attackers']
        atk_sorties = battleData['air_attackers']
        def_land_units = battleData['defenders']
        def_sorties = battleData['air_defenders']

        # calculate force strength
        # S = ((Ws + Wmg + Whw) * r_n) + (Wgi * rn) + ((Wg + Wgy) * (rwg * hwg * zwg * wyg)) + (Wi * rwi * hwi) + (Wy * rwy * hwy * zyw * wyy)
        atk_oli = FormationOLI()
        def_oli = FormationOLI()
        
        Na = 0 # personnel strength
        Nd = 0 # personnel strength
        Nia = 0 # armour strength
        Nid = 0 # armour strength
        Ja = 0 # vehicle strength
        Jd = 0 # vehicle strength

        # J factors (only vehicles other than tanks):
        J_unarmoured = 1
        J_armoured = 2
        J_air = 10 # only organic
        
        # gather OLI values from each formation
        for a in atk_land_units:
            atk_oli += self.formationsById[a].get_oli()
            # calculate Na
            Na += self.formationsById[a].count_personnel()
            # Calculate Ja
            for equip in self.formationsById[a].get_qjm_equipment():
                if type(equip) == Vehicle:
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
            oli = self.formationsById[d].get_oli()
            def_oli += oli
            # calculate Nd
            Nd += self.formationsById[d].count_personnel()
            # Calculate Jd
            for equip in self.formationsById[a].get_qjm_equipment():
                print(equip)
                if type(equip) == Vehicle:
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
        # correct values of antitank, antiaircraft, and aircraft by enemy values
        if atk_oli.antitank > def_oli.armour:
            atk_oli.antitank = def_oli.armour + 0.5 * (atk_oli.antitank - def_oli.armour)
        if def_oli.antitank > atk_oli.armour:
            def_oli.antitank = atk_oli.armour + 0.5 * (def_oli.antitank - atk_oli.armour)
        if atk_oli.antiair > def_oli.aircraft:
            atk_oli.antiair = def_oli.aircraft + 0.5 * (atk_oli.antiair - def_oli.aircraft)
        if def_oli.antiair > atk_oli.aircraft:
            def_oli.antiair = atk_oli.aircraft + 0.5 * (def_oli.antiair - atk_oli.aircraft)
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
        rm  = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Mobility (r_m)')
        rua  = 1.0
        rud  = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Defense Position (r_u)')
        rn  = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Infantry Weapons (r_n)')
        rwg = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Artillery (r_wg)')
        rwy = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Air (r_wy)')
        rwi = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Tanks (r_wt)')
        rc  = TERRAIN_FACTORS.get(battleData['terrain'],
                                  'Casualty (r_c)')
        # Weather Factors
        hm  = WEATHER_FACTORS.get(battleData['weather'],
                              'Mobility (h_m)')
        hua = WEATHER_FACTORS.get(battleData['weather'],
                              'Attack (h_ua)')
        hud = 1.0
        hwg = WEATHER_FACTORS.get(battleData['weather'],
                              'Artillery (h_wg)')
        hwy = WEATHER_FACTORS.get(battleData['weather'],
                              'Air (h_wy)')
        hwi = WEATHER_FACTORS.get(battleData['weather'],
                              'Tanks (h_wt)')
        hc  = WEATHER_FACTORS.get(battleData['weather'],
                              'Casualties (h_c)')
        # Season Factors
        zua = SEASON_FACTORS.get(battleData['season'],
                             'Attack (z_u)')
        zud = 1.0
        zwg = SEASON_FACTORS.get(battleData['season'],
                             'Artillery (z_wg)')
        zwy = SEASON_FACTORS.get(battleData['season'],
                             'Air (z_wy)')
        # Posture Factors
        usa = 1.0
        usd = POSTURE_FACTORS.get(battleData['posture'],
                              'Strength (u_s)')
        uva = 1.0
        uvd = POSTURE_FACTORS.get(battleData['posture'],
                              'Vulnerability (u_v)')
        uca = POSTURE_FACTORS.get(battleData['posture'],
                              'Attack Casualties (u_ca)')
        ucd = POSTURE_FACTORS.get(battleData['posture'],
                              'Defense Casualties (u_cd)')
        # Surprise Factors
        eraSurpriseFactor = 1.33 # 1.33 post 1966
        Msur  = SURPRISE_FACTORS.get(battleData['atksurprise'],
                                     'Mobility Characteristics (Msur)'
                                     ) * eraSurpriseFactor
        Vsura = SURPRISE_FACTORS.get(battleData['atksurprise'],
                                     'Vulnerability (Vsur)'
                                     ) * eraSurpriseFactor
        Vsurd = SURPRISE_FACTORS.get(battleData['atksurprise'],
                                     'Surprised Vulnerability (Vsurd)'
                                     ) * eraSurpriseFactor
        su_c  = SURPRISE_FACTORS.get(battleData['atksurprise'],
                                     'Surprised Vulnerability (Vsurd)'
                                     ) * eraSurpriseFactor
        su_ct = SURPRISE_FACTORS.get(battleData['atksurprise'],
                                     'Surprised Vulnerability (Vsurd)'
                                     ) * eraSurpriseFactor
        surprise_days = int(battleData['atksurprisedays'])
        # Update surprise factors for duration, all trend to 1.0 and reduce by 1/3 for each day
        Msur  = 1.0 + (Msur-1.0) * (3-surprise_days)/3
        Vsura = 1.0 + (Vsura-1.0) * (3-surprise_days)/3
        Vsurd = 1.0 + (Vsurd-1.0) * (3-surprise_days)/3
        su_c  = 1.0 + (su_c-1.0) * (3-surprise_days)/3
        su_ct = 1.0 + (su_ct-1.0) * (3-surprise_days)/3


        # TODO Obstacle Factors
        vr = 1.0 # TODO ADD ADDITIONAL DATA FOR SHORELINE VULNERABILITY
        


        # Air Superiority Factors
        if battleData['airsuperiority'] == 'Air Superiority':
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
        elif battleData['airsuperiority'] == 'Air Inferiority':
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

        atk_P = atk_S * atk_m * usa * rua * hua * zua * atk_v * float(battleData['atkcev'])
        def_P = def_S * def_m * usd * rud * hud * zud * def_v * float(battleData['defcev'])

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
        ca  = 0.028 * rc * hc * uca * ca_strength * ca_power
        # TODO - factor in Attrition is 0.04, 0.028 in NPW, why?
        cia = ca * 6.0 * ca_arm * float(battleData['defcev'])
        cga = ca * float(battleData['defcev'])

        cd  = 0.015 * rc * hc * ucd * cd_strength * cd_power * su_c
        # TODO - factor in Attrition is 0.04, 0.015 in NPW, why?
        cid = cd * 3.0 * cd_arm * su_ct * float(battleData['atkcev'])
        cgd = cd * float(battleData['atkcev'])

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
              '             {:,.0f}/{:,.0f} personnel | {:,.0f}/{:,.0f} armour\n'.format(cd*Nd, Nd, cid*Nid, Nid)
              )
        
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
                            }
            return battleResults
