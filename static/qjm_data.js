function sendData(commit=false) {
    // Collect data from inputs
    const data = {
        attackers: Array.from(document.querySelectorAll('#attackers .draggable')).map(el => el.dataset.unitId),
        defenders: Array.from(document.querySelectorAll('#defenders .draggable')).map(el => el.dataset.unitId),
        air_attackers: Array.from(document.querySelectorAll('#air_attackers .draggable')).map(el => {
            const input = el.querySelector('input[type="number"]');
            return { id: el.dataset.unitId, sorties: input ? parseInt(input.value) : 0 };
        }),
        air_defenders: Array.from(document.querySelectorAll('#air_defenders .draggable')).map(el => {
            const input = el.querySelector('input[type="number"]');
            return { id: el.dataset.unitId, sorties: input ? parseInt(input.value) : 0 };
        }),
        terrain: document.getElementById('terrain').value,
        season: document.getElementById('Season').value,
        weather: document.getElementById('weather').value,
        posture: document.getElementById('posture').value,
        defFrontage: document.getElementById('defFrontage').value,
        airsuperiority: document.getElementById('airsuperiority').value,
        atksurprise: document.getElementById('atksurprise').value,
        atksurprisedays: document.getElementById('atksurprisedays').value,
        atkcev: document.getElementById('atkcev').value,
        defcev: document.getElementById('defcev').value,
        // Obstacle info
        roadQuality: document.getElementById('roadQuality').value,
        roadDensity: document.getElementById('roadDensity').value,
        riverObstacle: document.getElementById('riverObstacle').value,
        mineObstacle: document.getElementById('mineObstacle').value,
        shorelineFires: document.getElementById('shorelineFires').value,
        shorelineType: document.getElementById('shorelineType').value,
        battleDate: document.getElementById('battle_date').value,
        battleTime: document.getElementById('battle_time').value,
        battleDuration: document.getElementById('battleDuration').value,
    };

    // Send data to Flask server via AJAX
    console.log(commit)
    if (commit) {
        fetch('/commit_battle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(result => {
        console.log('Success:', result);
        // Handle success response
        })
        .catch(error => {
        console.error('Error:', error);
        // Handle error response
        });

    } else {
        fetch('/simulate_battle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(result => {
        console.log('Success:', result);
        // Handle success response
        // Populate the modal with the simulation results
        const battleResultsContent = document.getElementById('battleResultsContent');
        // loop through result.advanceRate keys and values to present them in the modal
        battleResultsContent.innerHTML = `
            <p><strong>Power Ratio:</strong> ${result.powerRatio.toFixed(2)}</p>
            <p><strong>Attacker Power:</strong> ${result.powerAtk.toLocaleString('en-US', {maximumFractionDigits:0})}</p>
            <p><strong>Defender Power:</strong> ${result.powerDef.toLocaleString('en-US', {maximumFractionDigits:0})}</p>
            <p><strong>Attacker Personnel Casualty Rate:</strong> ${(result.atkPersCasualtyRate*100).toFixed(1)}%</p>
            <p><strong>Attacker Tank Casualty Rate:</strong> ${(result.atkTankCasualtyRate*100).toFixed(1)}%</p>
            <p><strong>Defender Personnel Casualty Rate:</strong> ${(result.defPersCasualtyRate*100).toFixed(1)}%</p>
            <p><strong>Defender Tank Casualty Rate:</strong> ${(result.defTankCasualtyRate*100).toFixed(1)}%</p>
            <p><strong>Advance Rates:</strong></p>
            `;
            for (const [key, value] of Object.entries(result.advanceRate)) {
                battleResultsContent.innerHTML += `<p>${key}: ${value.toFixed(1)} km/day</p>`;
            };
        })
        .catch(error => {
        console.error('Error:', error);
        // Handle error response
        });
    };
}


function getPersonnelCount() {
    const data = {
      attackers: Array.from(document.querySelectorAll('#attackers .draggable')).map(el => el.dataset.unitId),
      defenders: Array.from(document.querySelectorAll('#defenders .draggable')).map(el => el.dataset.unitId),
    };
    console.log("getPersonnelCount for", data);
    // Send data to Flask server via AJAX
    fetch('/get_personnel', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(result => {
      console.log('Success:', result);
      // Handle success response
      // calculate the defender density
      const defFrontage = document.getElementById('defFrontage').value;
      const defDensity = result['defenders'] / (1000 * defFrontage);
      document.getElementById('defDensity').value = defDensity.toFixed(1);
    })
    .catch(error => {
      console.error('Error:', error);
      // Handle error response
    });
}


function saveState() {
    fetch('/save_scenario_state', {method: 'POST'})
      .then(response => response.json())
      .then(result => {
        console.log('Saved scenario state:', result);
        if(result.status) {
            alert('Saved scenario state!');
        } else {
            alert('Failed to save scenario state!');
        };
      })
      .catch(error => console.error('Error exporting to OrbatMapper:', error));
};


function exportOrbatMapper() {
    fetch('/export_orbatmapper', {method: 'POST'})
      .then(response => response.json())
      .then(result => {
        console.log('Exported to OrbatMapper:', result);
        if(result.status) {
            if (window.confirm('Exported OrbatMapper scenario! Click OK to open the scenario in OrbatMapper in a new tab.')) {
                window.open('https://orbat-mapper.app/?loadScenarioURL=https%3A%2F%2Fgist.githubusercontent.com%2FHerrTom%2F937bc859c1f5f7eb69db42373eb665da%2Fraw%2FOPORD-QJM.json', '_blank');
            };
        } else {
            alert('Failed to export OrbatMapper scenario!');
        };
      })
      .catch(error => console.error('Error exporting to OrbatMapper:', error));
  };