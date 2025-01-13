const factionsContainer = document.getElementById('factions');
const airFactionsContainer = document.getElementById('air_factions');
var draggable = false;
function addDragEventListeners(unitDiv) {
unitDiv.addEventListener('dragstart', (e) => {
  e.dataTransfer.setData('text', e.target.dataset.unitId);
});
unitDiv.addEventListener('dragend', (e) => {
  const data = e.dataTransfer.getData('text');
  //const draggedUnit = document.querySelector('.draggable[data-unit-id={$data}]');
  if (!draggable) {
    const draggableUnits = document.querySelectorAll('.draggable');
    draggableUnits.forEach(unit => {
      if (unit.dataset.unitId === data) {
        // Find the original parent based on the dataset
        const originalParentName = unit.dataset.originalParent;
        const originalParents = Array.from(factionsContainer.children).concat(Array.from(airFactionsContainer.children));
        const originalParentDiv = originalParents.find(div => div.querySelector('h3').textContent === originalParentName);
        if (originalParentDiv) {
          originalParentDiv.appendChild(unit);
        }
      }
    });
  }
  draggable = false;
  // reset all droppable styles
  document.querySelectorAll('.droppable').forEach(drop => {
    drop.classList.remove('accepts-drop');
  });
});
}


function setupDragDrop() {
const droppables = document.querySelectorAll('.droppable');
droppables.forEach(droppable => {
  droppable.addEventListener('dragover', (e) => {
    draggable = true;
    droppable.classList.add('accepts-drop');
    e.preventDefault();
  });
  droppable.addEventListener('dragenter', (e) => {
    draggable = false;
    droppable.classList.remove('accepts-drop');
    e.preventDefault();
  });
  droppable.addEventListener('dragleave', (e) => {
    draggable = false;
    droppable.classList.remove('accepts-drop');
    e.preventDefault();
  });
  droppable.addEventListener('drop', (e) => {
    e.preventDefault();
    draggable = true;
    const data = e.dataTransfer.getData('text');
    const unit = document.querySelector(`.draggable[data-unit-id="${data}"]`);
    if (unit) {
      e.target.appendChild(unit);
    }
    getPersonnelCount();
  });
});
const draggables = document.querySelectorAll('.d')
}