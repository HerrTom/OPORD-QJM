from flask import Flask, render_template, jsonify, request, redirect
from flask_socketio import SocketIO

from qjm import Wargame

app = Flask(__name__)
socketio = SocketIO(app)
wargame = Wargame()


@app.route("/")
def default_page():
    return render_template('index.htm')


@app.route("/qjm/")
def qjm_setup():  # Communicate with qjm.py to get formation data
    print(wargame.current_date.strftime('%Y-%m-%d'))
    return render_template('qjm.htm', battle_date=wargame.current_date.strftime('%Y-%m-%d'))


@app.route('/load_scenario/<scenario>')
def load_scenario(scenario):
    loaded = wargame.load_scenario(scenario)
    if loaded:
        return redirect("/qjm/", code=302)
    else:
        # TODO: Make a better error page
        return redirect("/", code=302)


@app.route("/qjm/get_units", methods=['GET'])
def get_units():
    formations = wargame.get_formations_as_tree()
    return jsonify(formations)


@app.route('/simulate_battle', methods=['POST'])
def simulate_battle():
    data = request.json
    # run the simulation function
    results = wargame.simulate_battle(data, recursive=False)
    return jsonify(results)


@app.route('/commit_battle', methods=['POST'])
def commit_battle():
    data = request.json
    # run the simulation function
    wargame.simulate_battle(data, recursive=False, commit=True)
    return jsonify({'status': 'committed'})


@app.route('/export_orbatmapper', methods=['POST'])
def export_orbatmapper():
    status = wargame.export_orbatmapper('toe.json')
    return jsonify({'status': status})


@app.route('/save_scenario_state', methods=['POST'])
def save_scenario_state():
    wargame.save_sim_state('./wargames/saves/scenario_save.sav')
    return jsonify({'status': True})


@app.route('/load_scenario_state')
def load_scenario_state():
    wargame.load_sim_state('./wargames/saves/scenario_save.sav')
    return redirect("/qjm/", code=302)


@app.route('/get_personnel', methods=['POST'])
def get_personnel():
    data = request.json
    defenders = 0
    attackers = 0
    for u in data['defenders']:
        defender = wargame.get_formation(formation_id=u)
        if defender is not None:
            defenders += defender.count_personnel(recursive=False)
    for u in data['attackers']:
        attacker = wargame.get_formation(formation_id=u)
        if attacker is not None:
            attackers += attacker.count_personnel(recursive=False)
    return jsonify({'defenders': defenders, 'attackers': attackers})


@app.route('/get_formation/<unit_id>', methods=['GET'])
def get_formation(unit_id):
    formation = wargame.formationsById.get(unit_id)
    if formation:
        oli = formation.get_oli()
        return jsonify({
            'name': formation.name,
            'oli': oli.calc_total(),
            'faction': formation.faction,
            'personnel': formation.count_personnel(),
            'sidc': formation.sidc,            
            'shortname': formation.shortname,
            'unit_id': formation.id,
        })
    else:
        return jsonify({'error': 'Formation not found'}), 404


@app.route('/update_formation', methods=['POST'])
def update_formation():
    data = request.json
    formation = wargame.formationsByName.get(data['name'])
    if formation:
        formation.personnel = int(data['personnel'])

        return jsonify({'status': 'success'})
    else:
        return jsonify({'error': 'Formation not found'}), 404


@app.route('/snapshot', methods=['POST'])
def snapshot():
    data = request.json
    battle_date = data.get('date')
    unit_locations = data.get('unitLocations', [])
    if battle_date:
        success = wargame.formation_snapshot(battle_date, unit_locations)
        if success:
            return jsonify({'status': 'success'})
    
    return jsonify({'status': 'failure'}), 400


@app.route('/get_snapshots/<date>')
def get_snapshots(date):
    snapshots = wargame.get_snapshots(date)
    return jsonify(snapshots)


if __name__ == "__main__":
    app.run(app, debug=True)
