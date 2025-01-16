async function fetchAirUnits() {
  const response = await fetch('/qjm/get_air_units');
  const data = await response.json();
  // log data to console for debug
  console.log(data);
  return data;
}

async function initAirUnits() {
  const airUnitsData = await fetchAirUnits();
  const airFactionsContainer = document.getElementById('air_factions');
  // const factions = [
  //   { name: 'Faction 1', units: [
  //     {'id': '7', 'name': 'MiG-21PFM (2x S-13)', 'sidc': '30030100001101040000'}, 
  //     {'id': '8', 'name': 'Su-25 (6x FAB-100)', 'sidc': '30030100001101020000'}
  //   ]},
  //   { name: 'Faction 2', units: [
  //     {'id': '9', 'name': 'MiG-21PFM (4x S-5)', 'sidc': '30030100001101040000'}, 
  //     {'id': '10', 'name': 'Su-25 (4x FAB-100, 2x S-25)', 'sidc': '30030100001101020000'}
  //   ]},
  //   { name: 'Faction 3', units: [
  //     {'id': '11', 'name': 'MiG-21PFM (2x S-8)', 'sidc': '30030100001101040000'}, 
  //     {'id': '12', 'name': 'Su-25 (4x FAB-250)', 'sidc': '30030100001101020000'}
  //   ]}
  // ];

  airUnitsData.forEach(faction => {
    const factionDiv = document.createElement('div');
    factionDiv.innerHTML = `<h3>${faction.name} (Air)</h3>`;
    factionDiv.className = 'font-extrabold grid-cols-1 droppable';
    factionDiv.id = `${faction.name}-air`;
    faction.units.forEach(unit => {
      const unitDiv = createUnitDiv(unit, `${faction.name} (Air)`, `${faction.name}-air`, true);
      factionDiv.appendChild(unitDiv);
    });
    airFactionsContainer.appendChild(factionDiv);
  });
}

function createUnitDiv(unit, factionName, parent, isAirUnit = false) {
  const unitDiv = document.createElement('div');
  unitDiv.className = 'draggable border m-1 p-1 font-normal flex justify-between';
  unitDiv.dataset.unitId = unit.id;
  unitDiv.dataset.originalParent = parent;
  unitDiv.draggable = true;
  // Mark original parent identifier at creation
  unitDiv.setAttribute('data-initial-parent-id', factionName);
  var symbol = new ms.Symbol(unit.sidc, {size: 20, outlineWidth: 2, fillColor: unit.color}).asCanvas().toDataURL();
  unitDiv.innerHTML = isAirUnit
    ? `<div><img src=${symbol} style="display: inline"/> ${unit.name} </div><input class="input input-sm" type="number" value="0" size="8"></input>`
    : `<div><img src=${symbol} style="display: inline"/> ${unit.name} </div><button class="btn btn-xs m-2 justify-self-end" onclick="showFormationDetails('${unit.id}');formationModal.showModal()">More</button>`;
  addDragEventListeners(unitDiv);
  return unitDiv;
}


function showFormationDetails(unitId) {
  // Fetch the formation data from the server or use a preloaded JavaScript object
  fetch(`/get_formation/${unitId}`)
    .then(response => response.json())
    .then(data => {
      const formationDetails = document.getElementById('formationDetails');
      formationDetails.innerHTML = ''; // Clear existing details

      // Populate the modal with formation data
      const nameDiv = document.createElement('div');
      nameDiv.innerHTML = `<strong>Name:</strong> <input type="text" value="${data.name}" id="formationName" class="input input-bordered w-full"/>`;
      formationDetails.appendChild(nameDiv);

      const factionDiv = document.createElement('div');
      factionDiv.innerHTML = `<strong>Faction:</strong> <input type="text" value="${data.faction}" id="formationFaction" class="input input-bordered w-full"/>`;
      formationDetails.appendChild(factionDiv);

      const personnelDiv = document.createElement('div');
      personnelDiv.innerHTML = `<strong>Personnel:</strong> <input type="number" value="${data.personnel}" id="formationPersonnel" class="input input-bordered w-full" disabled/>`;
      formationDetails.appendChild(personnelDiv);

      const oliDiv = document.createElement('div');
      oliDiv.innerHTML = `<strong>OLI:</strong> <input type="number" value="${data.oli.toFixed(0)}" id="formationOLI" class="input input-bordered w-full" disabled/>`;
      formationDetails.appendChild(oliDiv);

      // Show the modal
      document.getElementById('formationModal').classList.remove('hidden');
    })
    .catch(error => console.error('Error fetching formation details:', error));
};