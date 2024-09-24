import socket
import json
import yaml
import logging
from glob import glob
from uuid import uuid1
import numpy as np

from .weapon import Weapon
from .vehicle import Vehicle
from .formation import Formation
from .factors import *  # imports all lookup tables


class Wargame:
    def __init__(self):
        # import the database info
        weapfiles = glob('./database/weapons/*.yml')
        weapons = []
        for f in weapfiles:
            weapons.append(Weapon(f))

        vehfiles = glob('./database/vehicles/*.yml')
        vehicles = []
        for f in vehfiles:
            vehicles.append(Vehicle(f, weapons))

        # create a dict for the weapons
        self.weapDict = {}
        for w in weapons:
            self.weapDict.update({w.name: w})
        for v in vehicles:
            self.weapDict.update({v.name: v})
        
        # init the formation container
        self.formations = {}
        self.formationsByName = {}
        self.formationsById = {}
    
    def load_scenario(self, scenario):
        # update scenario string to subdirectory
        scenario = './wargames/' + scenario
        # load the scenario
        with open(scenario+'/wargame.yml') as f:
            wargameRules = yaml.full_load(f)
        colors = wargameRules['factions']
        self.dispersion = wargameRules['dispersion_factor']
        # load formations
        for f in glob(scenario+'/formations/**/*.yml', recursive=True):
            form = Formation(f, self.weapDict)
            if form.faction in colors:
                form.color = colors[form.faction]
            if form.faction not in self.formations:
                self.formations.update({form.faction: [form]})
            else:
                self.formations[form.faction].append(form)
            self.formationsByName.update({form.name: form})
            self.formationsById.update({form.id: form})

    def get_formations(self):
        response = []
        for faction in self.formations:
            faction_response = {'name': faction, 'units': []}
            for form in self.formations[faction]:
                faction_response['units'].append({'id': form.id, 'name': form.name, 'sidc': form.sidc, 'color': form.color})
            response.append(faction_response)
        return response
    
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
        atk_oli = {'Ws': 0, 'Wmg': 0, 'Whw': 0, 'Wgi': 0,
                   'Wg': 0, 'Wgy': 0, 'Wi': 0, 'Wy': 0}
        def_oli = {'Ws': 0, 'Wmg': 0, 'Whw': 0, 'Wgi': 0,
                   'Wg': 0, 'Wgy': 0, 'Wi': 0, 'Wy': 0}
        
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
            oli = self.formationsById[a].get_OLI()
            for cat in oli:
                atk_oli[cat] += oli[cat]
            # calculate Na
            Na += self.formationsById[a].personnel
            # Calculate Ja
            for equip in self.formationsById[a].equipment:
                if type(equip) == Vehicle:
                    equip_num = self.formationsById[a].equipment[equip][1]
                    if equip.vehicle_type in ['armoured car', 'truck', 'arv']:
                        Ja += equip_num * J_unarmoured
                    elif equip.vehicle_type in ['apc', 'ifv', 'artillery']:
                        Ja += equip_num * J_armoured
                    elif equip.vehicle_type in ['cas', 'fighter', 'bomber', 'helicopter']:
                        # only count organic aviation assets
                        Ja += equip_num * J_air
                    elif equip.vehicle_type in ['tank']:
                        Nia += equip_num
 
        for d in def_land_units:
            oli = self.formationsById[d].get_OLI()
            for cat in oli:
                def_oli[cat] += oli[cat]
            # calculate Na
            Nd += self.formationsById[d].personnel
            # Calculate Ja
            for equip in self.formationsById[d].equipment:
                if type(equip) == Vehicle:
                    equip_num = self.formationsById[d].equipment[equip][1]
                    if equip.vehicle_type in ['armoured car', 'truck', 'arv']:
                        Jd += equip_num * J_unarmoured
                    elif equip.vehicle_type in ['apc', 'ifv', 'artillery']:
                        Jd += equip_num * J_armoured
                    elif equip.vehicle_type in ['cas', 'fighter', 'bomber', 'helicopter']:
                        # only count organic aviation assets
                        Jd += equip_num * J_air
                    elif equip.vehicle_type in ['tank']:
                        Nid += equip_num

        # correct values of antitank, antiaircraft, and aircraft by enemy values
        if atk_oli['Wgi'] > def_oli['Wi']:
            atk_oli['Wgi'] = def_oli['Wi'] + 0.5 * (atk_oli['Wgi'] - def_oli['Wi'])
        if def_oli['Wgi'] > def_oli['Wi']:
            def_oli['Wgi'] = atk_oli['Wi'] + 0.5 * (def_oli['Wgi'] - atk_oli['Wi'])
        if atk_oli['Wgy'] > def_oli['Wy']:
            atk_oli['Wgy'] = def_oli['Wy'] + 0.5 * (atk_oli['Wgy'] - def_oli['Wy'])
        if def_oli['Wgy'] > def_oli['Wy']:
            def_oli['Wgy'] = atk_oli['Wy'] + 0.5 * (def_oli['Wgy'] - atk_oli['Wy'])
        atk_ground_firepower = sum([atk_oli[x] for x in atk_oli if x != 'Wy'])
        def_ground_firepower = sum([def_oli[x] for x in def_oli if x != 'Wy'])

        if atk_oli['Wy'] > atk_ground_firepower:
            atk_oli['Wy'] = atk_ground_firepower + 0.5 * (atk_oli['Wy'] - atk_ground_firepower)
        if atk_oli['Wy'] > 3*atk_ground_firepower:
            atk_oli['Wy'] = 3*atk_ground_firepower

        if def_oli['Wy'] > def_ground_firepower:
            def_oli['Wy'] = def_ground_firepower + 0.5 * (def_oli['Wy'] - def_ground_firepower)
        if def_oli['Wy'] > 3*def_ground_firepower:
            def_oli['Wy'] = 3*def_ground_firepower

        # Attacker variables
        # Terrain Factors
        rm  = TERRAIN_DATA[battleData['terrain']][0] # Mobility
        rua  = 1.0
        rud  = TERRAIN_DATA[battleData['terrain']][1] # Defense Position
        rn  = TERRAIN_DATA[battleData['terrain']][2] # Infantry
        rwg = TERRAIN_DATA[battleData['terrain']][3] # Artillery
        rwy = TERRAIN_DATA[battleData['terrain']][4] # Air
        rwi = TERRAIN_DATA[battleData['terrain']][5] # Tanks
        rc  = TERRAIN_DATA[battleData['terrain']][6] # Casualties
        # Weather Factors
        hm  = WEATHER_DATA[battleData['weather']][0] # Mobility
        hua = WEATHER_DATA[battleData['weather']][1] # Attack
        hud = 1.0
        hwg = WEATHER_DATA[battleData['weather']][2] # Artillery
        hwy = WEATHER_DATA[battleData['weather']][3] # Air
        hwi = WEATHER_DATA[battleData['weather']][4] # Tanks
        hc  = WEATHER_DATA[battleData['weather']][5] # Casualties
        # Season Factors
        zua = SEASON_DATA[battleData['season']][0] # Attack factor
        zud = 1.0
        zwg = SEASON_DATA[battleData['season']][1] # Artillery
        zwy = SEASON_DATA[battleData['season']][2] # Air
        # Posture Factors
        usa = 1.0
        usd = DEFENSE_DATA[battleData['posture']][0]
        uva = 1.0
        uvd = DEFENSE_DATA[battleData['posture']][1]
        uca = DEFENSE_DATA[battleData['posture']][2]
        ucd = DEFENSE_DATA[battleData['posture']][3]
        # Surprise Factors
        eraSurpriseFactor = 1.33 # 1.33 post 1966
        Msur  = SURPRISE_DATA[battleData['atksurprise']][0] * eraSurpriseFactor
        Vsura = SURPRISE_DATA[battleData['atksurprise']][1] * eraSurpriseFactor
        Vsurd = SURPRISE_DATA[battleData['atksurprise']][2] * eraSurpriseFactor
        su_c  = SURPRISE_DATA[battleData['atksurprise']][3] * eraSurpriseFactor
        su_ct = SURPRISE_DATA[battleData['atksurprise']][4] * eraSurpriseFactor
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
                atk_my = AIRSUPERIORITY_DATA['Air Superiority'][0]
                def_my = AIRSUPERIORITY_DATA['Air Inferiority'][0]
            else:
                atk_my = AIRSUPERIORITY_DATA['Air Superiority'][1]
                def_my = AIRSUPERIORITY_DATA['Air Inferiority'][1]
            wyga = AIRSUPERIORITY_DATA['Air Superiority'][2] # Artillery
            wygd = AIRSUPERIORITY_DATA['Air Inferiority'][2] # Artillery
            wyya = AIRSUPERIORITY_DATA['Air Superiority'][2] # Air
            wyyd = AIRSUPERIORITY_DATA['Air Inferiority'][2] # Air
            vya  = AIRSUPERIORITY_DATA['Air Superiority'][2] # Vulnerability
            vyd  = AIRSUPERIORITY_DATA['Air Inferiority'][2] # Vulnerability
        elif battleData['airsuperiority'] == 'Air Inferiority':
            if hwy > 0.5:
                atk_my = AIRSUPERIORITY_DATA['Air Inferiority'][0]
                def_my = AIRSUPERIORITY_DATA['Air Superiority'][0]
            else:
                atk_my = AIRSUPERIORITY_DATA['Air Inferiority'][1]
                def_my = AIRSUPERIORITY_DATA['Air Superiority'][1]
            wyga = AIRSUPERIORITY_DATA['Air Inferiority'][2] # Artillery
            wygd = AIRSUPERIORITY_DATA['Air Superiority'][2] # Artillery
            wyya = AIRSUPERIORITY_DATA['Air Inferiority'][2] # Air
            wyyd = AIRSUPERIORITY_DATA['Air Superiority'][2] # Air
            vya  = AIRSUPERIORITY_DATA['Air Inferiority'][2] # Vulnerability
            vyd  = AIRSUPERIORITY_DATA['Air Superiority'][2] # Vulnerability
        else:
            if hwy > 0.5:
                atk_my = AIRSUPERIORITY_DATA['Air Equality'][0]
                def_my = AIRSUPERIORITY_DATA['Air Equality'][0]
            else:
                atk_my = AIRSUPERIORITY_DATA['Air Equality'][1]
                def_my = AIRSUPERIORITY_DATA['Air Equality'][1]
            wyga = AIRSUPERIORITY_DATA['Air Equality'][2] # Artillery
            wygd = AIRSUPERIORITY_DATA['Air Equality'][2] # Artillery
            wyya = AIRSUPERIORITY_DATA['Air Equality'][2] # Air
            wyyd = AIRSUPERIORITY_DATA['Air Equality'][2] # Air
            vya  = AIRSUPERIORITY_DATA['Air Equality'][2] # Vulnerability
            vyd  = AIRSUPERIORITY_DATA['Air Equality'][2] # Vulnerability

        # Era factor:
        JFactor = 15 # 20 for WW2, 15 for 1970s
        # Attacker strength calculation
        atk_S = ((atk_oli['Ws'] + atk_oli['Wmg'] + atk_oli['Whw']) * rn) + (atk_oli['Ws'] * rn) + \
                ((atk_oli['Wg'] + atk_oli['Wgy']) * (rwg * hwg * zwg * wyga)) + \
                (atk_oli['Wi'] * rwi * hwi) + (atk_oli['Wy'] * rwy * hwy * zwy * wyya)
        
        # Defender strength calculation
        def_S = ((def_oli['Ws'] + def_oli['Wmg'] + def_oli['Whw']) * rn) + (def_oli['Ws'] * rn) + \
                ((def_oli['Wg'] + def_oli['Wgy']) * (rwg * hwg * zwg * wygd)) + \
                (def_oli['Wi'] * rwi * hwi) + (def_oli['Wy'] * rwy * hwy * zwy * wyyd)


        # Attacker mobility calculation
        atk_M = (((Na + JFactor*Ja + atk_oli['Wi']) * atk_my / Na) / ((Nd + JFactor*Jd + def_oli['Wi']) * def_my / Nd))**0.5 * Msur
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
        ca_power    = np.interp(PRatio, OP_RATIO, OP_FACTOR) # power ratio factor for casualties
        cd_power    = np.interp(1/PRatio, OP_RATIO, OP_FACTOR) # power ratio factor for casualties
        ca_strength = np.interp(Na, STR_PERS, STR_PERS_FACTOR) # personnel strength factor for casualties
        cd_strength = np.interp(Nd, STR_PERS, STR_PERS_FACTOR) # personnel strength factor for casualties
        ca_arm      = np.interp(Nia, STR_ARM, STR_ARM_FACTOR) # armour strength factor for casualties
        cd_arm      = np.interp(Nid, STR_ARM, STR_ARM_FACTOR) # armour strength factor for casualties

        ca  = 0.028 * rc * hc * uca * ca_strength * ca_power # TODO - factor in Attrition is 0.04, 0.028 in NPW, why?
        cia = ca * 6.0 * ca_arm * float(battleData['defcev'])
        cga = ca * float(battleData['defcev'])

        cd  = 0.015 * rc * hc * ucd * cd_strength * cd_power * su_c # TODO - factor in Attrition is 0.04, 0.015 in NPW, why?
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
            for a in atk_land_units:
                self.formationsById[a].inflict_losses(ca, cia, cga, True)
            for d in def_land_units:
                self.formationsById[d].inflict_losses(cd, cid, cgd, False)

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
        
        


def handle_client_connection(client_socket):
    data = client_socket.recv(1024).decode('utf-8')
    request = json.loads(data)

    wg = Wargame()
    wg.load_scenario('NextWarPoland') # TODO: Un-hardcode this!
    logging.info(wg.formations)

    if request['command'] == 'load_formations':
        response = []
        for faction in wg.formations:
            faction_response = {'name': faction, 'units': []}
            for form in wg.formations[faction]:
                id = str(uuid1())
                faction_response['units'].append({'id': id, 'name': form.name, 'sidc': form.sidc, 'color': form.color})
            response.append(faction_response)
        client_socket.sendall(json.dumps(response).encode('utf-8'))

if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)  # max backlog of connections

    logging.info("Listening on port 9999")
    while True:
        client_sock, address = server.accept()
        handle_client_connection(client_sock)
        client_sock.close()