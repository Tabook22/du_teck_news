let previousTopNewsRadio = null;  // Store the previously checked Top News radio button
let currentTopNewsRadio = null;    // Store the current "Top News" radio being selected

// Function to handle Top News selection
function handleTopNewsSelection(newsId, currentRadio) {
    if (previousTopNewsRadio && previousTopNewsRadio !== currentRadio) {
        // Store the current radio button temporarily
        currentTopNewsRadio = currentRadio;

        // Show the Bootstrap modal for confirmation
        $('#topNewsConfirmationModal').modal('show');
    } else {
        // If no previous selection, set this as the Top News radio
        previousTopNewsRadio = currentRadio;
    }
}

// Function to confirm changing "Top News"
function confirmTopNewsChange() {
    // Uncheck the previous "Top News" and reset its corresponding checkbox and background
    if (previousTopNewsRadio) {
        previousTopNewsRadio.checked = false;

        // Find the corresponding checkbox for the previous "Top News" and uncheck it
        const previousNewsId = previousTopNewsRadio.name.split('-')[1];
        const previousCheckbox = document.getElementById('checkbox-' + previousNewsId);
        if (previousCheckbox) {
            previousCheckbox.checked = false;

            // Reset the background color of the parent div
            const previousParentDiv = previousCheckbox.closest('.news-item');
            if (previousParentDiv) {
                previousParentDiv.style.backgroundColor = 'white';
            }
        }
    }

    // Set the current selection as the new "Top News"
    if (currentTopNewsRadio) {
        currentTopNewsRadio.checked = true;

        // Ensure the checkbox for the new "Top News" is checked
        const currentNewsId = currentTopNewsRadio.name.split('-')[1];
        const currentCheckbox = document.getElementById('checkbox-' + currentNewsId);
        if (currentCheckbox) {
            currentCheckbox.checked = true;

            // Set the background color of the parent div to light gray
            const currentParentDiv = currentCheckbox.closest('.news-item');
            if (currentParentDiv) {
                currentParentDiv.style.backgroundColor = '#f3f3f3';
            }
        }

        // Update the reference to the newly selected "Top News"
        previousTopNewsRadio = currentTopNewsRadio;
    }

    // Close the modal
    $('#topNewsConfirmationModal').modal('hide');
}

// Function to cancel the change
function cancelTopNewsChange() {
    if (currentTopNewsRadio) {
        currentTopNewsRadio.checked = false;
    }
    $('#topNewsConfirmationModal').modal('hide');
}

// Adding event listeners to radio buttons
document.addEventListener('DOMContentLoaded', function() {
    const radioButtons = document.querySelectorAll('input[type="radio"][value="Top News"]');

    // Check if any Top News radio button is already checked on page load
    radioButtons.forEach(radio => {
        if (radio.checked) {
            previousTopNewsRadio = radio;  // Set the previously checked radio button
        }

        // Add event listener to handle the radio button change event
        radio.addEventListener('change', function() {
            const newsId = this.name.split('-')[1];  // Extract newsId from radio button name
            handleTopNewsSelection(newsId, this);  // Pass the current radio element
        });
    });
});
