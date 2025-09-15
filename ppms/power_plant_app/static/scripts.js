$(document).ready(function() {
    let currentModuleId = null;
    let currentModuleCategory = null;

    // --- Hover (Tooltip) Functionality ---
    $('.module-block').hover(
        function(e) { // Mouse enter
            const category = $(this).data('category');
            const moduleName = $(this).find('.module-name').text();
            const data = categorizedModuleData[category][moduleName];
            const tooltip = $('#module-tooltip');

            if (data) {
                $('#tooltip-module-name').text(moduleName);
                $('#tooltip-status').text(data.status);

                let detailsHtml = '';
                for (const key in data) {
                    if (key !== 'status') {
                        let formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                        detailsHtml += `<p><strong>${formattedKey}:</strong> ${data[key]}</p>`;
                    }
                }
                $('#tooltip-details').html(detailsHtml);

                tooltip.css({
                    left: e.pageX + 15,
                    top: e.pageY + 15,
                }).fadeIn(100);
            }
        },
        function() { // Mouse leave
            $('#module-tooltip').fadeOut(100);
        }
    );

    // --- Right-Click (Context Menu) Functionality ---
    $('.module-block').on('contextmenu', function(e) {
        e.preventDefault();
        currentModuleId = $(this).attr('id');
        currentModuleCategory = $(this).data('category');
        const contextMenu = $('#context-menu');

        contextMenu.html(''); // Clear previous menu items

        // Build the menu based on the module's category
        if (currentModuleCategory === "Operation Module") {
            contextMenu.append('<a href="#" class="menu-item" data-action="start">Start Module</a>');
            contextMenu.append('<a href="#" class="menu-item" data-action="stop">Stop Module</a>');
            contextMenu.append('<a href="#" class="menu-item" data-action="low_power_mode">Low Power Mode</a>');
        } else if (currentModuleCategory === "Safety Module") {
            contextMenu.append('<a href="#" class="menu-item" data-action="start">Start Module</a>');
            contextMenu.append('<a href="#" class="menu-item" data-action="stop">Stop Module</a>');
        } else if (currentModuleCategory === "Environmental & Compliance Module") {
            // No functionality, so we don't show the menu
            return;
        }

        contextMenu.css({
            left: e.pageX,
            top: e.pageY,
        }).show();
    });

    // Hide context menu when clicking elsewhere
    $(document).on('click', function() {
        $('#context-menu').hide();
    });

    // Handle context menu item clicks (delegated event)
    $('#context-menu').on('click', '.menu-item', function(e) {
        e.preventDefault();
        const action = $(this).data('action');
        performModuleAction(currentModuleId, action);
        $('#context-menu').hide();
    });

    function performModuleAction(moduleId, action) {
    if (!moduleId) return;
    $.ajax({
        url: '/module_action',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ module_id: moduleId, action: action }),
        success: function(response) {
            alert(`Success: ${response.message}`); // You can keep or remove this alert

            // --- ADD THIS LOGIC TO UPDATE THE UI ---
            const moduleBlock = $(`#${moduleId}`); // Find the specific module block
            let newStatus = moduleBlock.attr('data-status'); // Get current status

            // Update status based on the action
            if (action === 'start') {
                newStatus = 'online';
            } else if (action === 'stop') {
                newStatus = 'offline';
            } else if (action === 'low_power_mode') {
                newStatus = 'standby'; // Or any other status you want
            }

            // Apply the new status to the block
            moduleBlock.attr('data-status', newStatus);
            // --- END OF ADDED LOGIC ---

        },
        error: function(error) {
            console.error("Error performing action:", error);
            alert(`Failed to perform action on ${moduleId}.`);
        }
    });
}
function fetchAndUpdateData() {
        $.ajax({
            url: '/api/plant_data',
            type: 'GET',
            success: function(newData) {
                // 1. Update the global JavaScript variable with the new data
                window.categorizedModuleData = newData;

                // 2. Update the visual status of each block on the page
                $('.module-block').each(function() {
                    const block = $(this);
                    const category = block.data('category');
                    const moduleName = block.find('.module-name').text();
                    const moduleData = newData[category][moduleName];
                    if (moduleData) {
                        block.attr('data-status', moduleData.status.toLowerCase());
                    }
                });
                console.log("Dashboard updated with live data at:", new Date().toLocaleTimeString());
            },
            error: function(error) {
                console.error("Failed to fetch live data:", error);
            }
        });
    }

    // --- NEW: Start the 10-second update interval ---
    setInterval(fetchAndUpdateData, 5000);

});

