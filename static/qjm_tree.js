async function fetchUnits() {
    const response = await fetch('/qjm/get_units');
    const data = await response.json();
    // log data to console for debug
    console.log(data);
    return data;
}

async function initTree() {
    const unitsData = await fetchUnits();
    renderTreeList("unit-tree-container", unitsData);
    renderTreeList("map-units-list", unitsData); // Populate map-units-list
    setupDragDrop();
}

let draggable = false;

function renderTreeList(containerId, data) {
    const container = document.getElementById(containerId);

    function createNode(nodeData, parentID = 'unit-tree-container') {
        // Create the list item for the current node
        const li = document.createElement('li');
        li.classList.add('node', 'draggable');
        li.setAttribute('id', nodeData.id); // Set unique ID
        li.setAttribute('data-unit-id', nodeData.id); // Set unique data-unit-id
        li.setAttribute('data-initial-parent-id', parentID); // Set initial parent ID
        // Store SIDC as a data attribute
        li.setAttribute('data-sidc', nodeData.sidc || "30031000000000000000");
        li.setAttribute('data-shortname', nodeData.shortname);

        // Toggle functionality to expand/collapse children
        li.addEventListener('click', (event) => {
            event.stopPropagation();  // Prevent triggering toggle on parent nodes
            const childUl = li.querySelector('ul');
            if (childUl) {
                childUl.style.display = childUl.style.display === 'none' ? 'block' : 'none';
            }
        });

        // Add MilSymbol image based on SIDC
        const img = document.createElement('img');
        const symbol = new ms.Symbol(nodeData.sidc || "30031000000000000000", { size: 20, outlineWidth: 2});
        img.src = symbol.asCanvas().toDataURL();
        img.style.verticalAlign = 'middle';
        img.style.marginRight = '5px';

        // Add the text for the node
        const text = document.createElement('span');
        text.textContent = nodeData.name;
        text.style.verticalAlign = 'middle';

        // Create a container for symbol and text for inline alignment
        const symbolContainer = document.createElement('div');
        symbolContainer.style.display = 'inline-flex';
        symbolContainer.style.alignItems = 'center';

        // Append symbol image and text to the container
        symbolContainer.appendChild(img);
        symbolContainer.appendChild(text);

        // Add the container to the list item
        li.appendChild(symbolContainer);

        // If the node has children, create a nested ul element
        if (nodeData.children && nodeData.children.length > 0) {
            const ul = document.createElement('ul');
            ul.classList.add('children-list');
            ul.style.display = 'none';  // Initially hide children

            // Recursively create child nodes
            nodeData.children.forEach(child => {
                ul.appendChild(createNode(child, nodeData.id));
            });

            li.appendChild(ul);
        }

        // Make the list item draggable
        li.setAttribute('draggable', true);
        addDragEventListeners(li);

        return li;
    }

    // Create the top-level UL element for the tree
    const ul = document.createElement('ul');
    ul.classList.add('tree-list');

    // Generate nodes for each faction
    data.forEach(faction => {
        ul.appendChild(createNode(faction));
    });

    // Append the tree to the container
    container.appendChild(ul);
}

function addDragEventListeners(unitDiv) {
    unitDiv.addEventListener('dragstart', (e) => {
        e.stopPropagation(); // Prevent event bubbling to parent droppables
        e.dataTransfer.setData('unitId', unitDiv.dataset.unitId);
        const parentId = unitDiv.parentElement.id;
        e.dataTransfer.setData('originalParentId', parentId); // Set originalParentId
        e.dataTransfer.setData('sidc', unitDiv.dataset.sidc);
        e.dataTransfer.setData('shortname', unitDiv.dataset.shortname);
        console.log(`Drag Start - Unit ID: ${unitDiv.dataset.unitId}, SIDC: ${unitDiv.dataset.sidc || 'N/A'}`);
    });

    unitDiv.addEventListener('dragend', (e) => {
        e.stopPropagation(); // Prevent event bubbling to parent droppables
        const droppedOnValidArea = draggable;
        const originalParentId = e.dataTransfer.getData('originalParentId');

        if (!droppedOnValidArea) {
            console.log('Resetting unit position');
            // Handle case where originalParentId might be null
            if (originalParentId) {
                const originalParent = originalParentId === 'tree' ? document.getElementById('unit-tree-container') : document.getElementById(originalParentId);
                const unitId = e.dataTransfer.getData('unitId');
                const unit = document.querySelector(`[data-unit-id="${unitId}"]`);
                if (unit && originalParent) unit.parentElement.appendChild(unit);
            } else {
                console.warn('originalParentId is null. Cannot reset unit position.');
            }
        }
        resetDropHighlight();
    });
}

function setupDragDrop() {
    const droppables = document.querySelectorAll('.droppable');
    droppables.forEach(droppable => {
        droppable.addEventListener('dragover', (e) => {
            e.preventDefault();
            draggable = true;
            droppable.classList.add('accepts-drop');
        });

        droppable.addEventListener('dragenter', (e) => {
            e.preventDefault();
            draggable = true;
            droppable.classList.add('accepts-drop');
        });

        droppable.addEventListener('dragleave', (e) => {
            draggable = false;
            droppable.classList.remove('accepts-drop');
        });

        droppable.addEventListener('drop', (e) => {
            e.preventDefault();
            const unitId = e.dataTransfer.getData('unitId');
            console.log('Drop - Unit ID:', unitId);
            const unit = document.querySelector(`.draggable[data-unit-id="${unitId}"]`);
            if (unit) {
                draggable = true;
                droppable.appendChild(unit);
                droppable.classList.remove('accepts-drop');
                console.log(`Dropped Unit ID: ${unitId} into ${droppable.id}`);
            }
            getPersonnelCount();
            resetDropHighlight();
        });
    });
}

// Reset drop highlight classes
function resetDropHighlight() {
    document.querySelectorAll('.droppable').forEach(drop => {
        drop.classList.remove('accepts-drop', 'hover');
    });
}