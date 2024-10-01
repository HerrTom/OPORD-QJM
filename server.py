from flask import Flask, render_template, jsonify, request, redirect
from flask_socketio import SocketIO, emit
import socket
import json

from qjm import Wargame

app = Flask(__name__)
socketio = SocketIO(app)
wargame = Wargame()
wargame.load_scenario('NextWarPoland')

@app.route("/")
def default_page():
    return "<a href='./qjm/'>QJM Simulation</a>"

@app.route("/qjm/")
def qjm_setup():# Communicate with qjm.py to get formation data
    return render_template('qjm.htm')

@app.route('/load_scenario', methods=['POST'])
def load_scenario():
    scenario_name = request.json.get('scenario')
    loaded = wargame.load_scenario(scenario_name)
    if loaded:
        return redirect("/qjm/", code=302)
    else:
        return jsonify({'error': 'Scenario not found'}), 404

@app.route("/qjm/get_units", methods=['GET'])
def get_units():
    formations = wargame.get_formations()
    # formations = json.loads(response)
    print(formations)
    return formations

@app.route('/simulate_battle', methods=['POST'])
def simulate_battle():
    data = request.json
    # run the simulation function
    results = wargame.simulate_battle(data)
    return jsonify(results)

@app.route('/commit_battle', methods=['POST'])
def commit_battle():
    data = request.json
    # run the simulation function
    wargame.simulate_battle(data, commit=True)
    return jsonify({'status': 'committed'})

@app.route('/get_personnel', methods=['POST'])
def get_personnel():
    data = request.json
    # Process the data as needed
    print(data)  # For debugging
    defenders = 0
    attackers = 0
    for u in data['defenders']:
        defenders += wargame.formationsById[u].personnel
    for u in data['attackers']:
        attackers += wargame.formationsById[u].personnel
    return jsonify({'defenders': defenders, 'attackers': attackers})

@app.route('/get_formation/<unit_id>', methods=['GET'])
def get_formation(unit_id):
    formation = wargame.formationsById.get(unit_id)
    if formation:
        oli = formation.get_OLI()
        return jsonify({
            'name': formation.name,
            'oli': sum([oli[x] for x in oli]),
            'faction': formation.faction,
            'personnel': formation.get_personnel(),
            'equipment': {equip.name: formation.get_equip_status(equip) for equip in formation.equipment}
        })
    else:
        return jsonify({'error': 'Formation not found'}), 404

@app.route('/update_formation', methods=['POST'])
def update_formation():
    data = request.json
    formation = wargame.formationsByName.get(data['name'])
    print(data)
    if formation:
        # Update formation details
        # formation.name = data['name'] # This is in the data but should not change.
        # formation.faction = data['faction'] # This is in the data but should not change.
        formation.personnel = int(data['personnel'])

        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Formation not found'}), 404


if __name__ == "__main__":
    app.run(app, debug=True)