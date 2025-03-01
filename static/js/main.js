// Function to check the checkbox when a radio button is selected
function checkCheckbox(newsId) {
    document.getElementById('checkbox-' + newsId).checked = true;
}

// Function to create AI News Magazine
function createAIMagazine() {
    const selectedNews = [];
    const newsLocations = {};

    // Collect the selected checkboxes and radio button values
    $('.select-checkbox:checked').each(function() {
        const newsId = $(this).val();
        selectedNews.push(newsId);

        // Get the selected location from the radio buttons for each news item
        const selectedLocation = $(`input[name="location-${newsId}"]:checked`).val();
        if (selectedLocation) {
            newsLocations[newsId] = selectedLocation;
        } else {
            alert('Please select a location for all selected news.');
            return;
        }
    });

    if (selectedNews.length === 0) {
        alert('Please select news to create the magazine.');
        return;
    }

    // AJAX call to create AI News Magazine
    $.ajax({
        url: '/create-ai-magazine',
        type: 'POST',
        data: { 
            selectedNews: selectedNews, 
            newsLocations: JSON.stringify(newsLocations)  // Send as a JSON string
        },
        success: function(response) {
            // Show a success message
            $("#alert-message").html(response.message).show();
            setTimeout(() => {
                $("#alert-message").hide();
            }, 3000);
        },
        error: function(xhr) {
            alert('Failed to create the AI News Magazine');
        }
    });
}

// Individual news removal function
function removeNews(newsId) {
    if (!confirm('Are you sure you want to remove this news item?')) return;

    $.ajax({
        url: '/remove-news',
        type: 'POST',
        data: {
            news_id: newsId  // Make sure you're sending the news_id correctly
        },
        success: function(response) {
            // Remove the news item from the list
            $("#news-" + newsId).remove();

            // Show success alert
            $("#alert-message").html(response.message).show();

            // Hide the alert message after 3 seconds
            setTimeout(function() {
                $("#alert-message").hide();
            }, 3000);

            // Update the total saved news count
            updateTotalSavedNewsCount(response.total_saved_news);
        },
        error: function(xhr) {
            alert('Failed to remove the news');
        }
    });
}

// Function to update the total saved news count
function updateTotalSavedNewsCount(count) {
    document.getElementById('totalSavedNews').innerText = count;
}

// Select or Deselect all checkboxes
$('#select-all').on('click', function () {
    const checked = this.checked;
    $('.select-checkbox').each(function () {
        this.checked = checked;
    });
});

// Function to open confirmation modal
function confirmDelete(type, newsId = null, newsTitle = null) {
    deleteType = type;
    newsIdToRemove = newsId;

    if (type === 'multiple') {
        const selectedCount = $('.select-checkbox:checked').length;
        if (selectedCount === 0) {
            alert('No news selected');
            return;
        }
        document.getElementById('delete-message').innerHTML = `You are about to delete ${selectedCount} selected news. Are you sure?`;
    } else if (type === 'single') {
        document.getElementById('delete-message').innerHTML = `You are about to delete "${newsTitle}". Are you sure?`;
    }

    // Show the confirmation modal
    $('#confirmModal').modal('show');
}

// Confirm delete action
$('#confirmDeleteBtn').on('click', function () {
    if (deleteType === 'single') {
        removeNews(newsIdToRemove);  // Call removeNews with the selected news ID
    } else if (deleteType === 'multiple') {
        deleteSelectedNews();  // Call deleteSelectedNews for multiple news items
    }
});

// Function to delete selected news
function deleteSelectedNews() {
    const selectedNews = [];
    $('.select-checkbox:checked').each(function () {
        selectedNews.push($(this).val());
    });

    if (selectedNews.length === 0) {
        alert("No news selected for deletion.");
        return;
    }

    // AJAX call to delete selected news
    $.ajax({
        url: '/delete_selected_news',
        type: 'POST',
        data: { selectedNews: selectedNews },
        success: function (response) {
            // Remove selected news from the DOM
            selectedNews.forEach(id => {
                $('#news-' + id).remove();
            });

            // Update total news count and show message
            handleResponse(response);

            // Hide the modal after successful deletion
            $('#confirmModal').modal('hide');
        },
        error: function (xhr) {
            alert('Failed to delete selected news');
        }
    });
}

// Function to handle the response after deleting or adding news
function handleResponse(response) {
    const message = response.message;
    const totalSavedNews = response.total_saved_news;

    // Update the total saved news count
    updateTotalSavedNewsCount(totalSavedNews);

    // Show success or failure message
    $("#alert-message").html(message).show();

    // Hide the message after a few seconds
    setTimeout(() => {
        $("#alert-message").hide();
    }, 3000);
}

// Function to handle checkbox change
$(document).ready(function() {
    // Listen for changes on checkboxes with the class "select-checkbox"
    $('.select-checkbox').on('change', function() {
        // Find the parent div with class "news-item"
        var parentDiv = $(this).closest('.news-item');
        
        // If checkbox is checked, change background to light gray
        if ($(this).is(':checked')) {
            parentDiv.css('background-color', '#f3f3f3');
        } 
        // If checkbox is unchecked, revert the background to white
        else {
            parentDiv.css('background-color', 'white');
        }
    });
});

// Search for any checkbox if it is checked then its parent background will turn to light gray:
window.onload = function() {
    // Get all checkboxes with the class "select-checkbox"
    const checkboxes = document.querySelectorAll('.select-checkbox');

    // Loop through all checkboxes
    checkboxes.forEach(function(checkbox) {
        // Check if the checkbox is checked
        if (checkbox.checked) {
            // Find the parent div with the class "news-item" and set its background to light gray
            checkbox.closest('.news-item').style.backgroundColor = '#f3f3f3';
        }
    });
};

// Function to uncheck the radio buttons when the checkbox is unchecked
function toggleCheckbox(newsId) {
    var checkbox = document.getElementById('checkbox-' + newsId);

    // If the checkbox is unchecked, uncheck all the corresponding radio buttons
    if (!checkbox.checked) {
        var radioButtons = document.querySelectorAll('input[name="location-' + newsId + '"]');
        
        radioButtons.forEach(function(radio) {
            radio.checked = false;
        });
        
        // Optionally, reset the background color
        var newsItemDiv = checkbox.closest('.news-item');
        if (newsItemDiv) {
            newsItemDiv.style.backgroundColor = '#fff'; // Reset to white or original color
        }
    }
}

// On page load, check the corresponding checkbox if any radio button is checked
$(document).ready(function() {
    $('.news-item').each(function() {
        var newsId = $(this).attr('id').split('-')[1];
        if ($('input[name="location-' + newsId + '"]:checked').length > 0) {
            $('#checkbox-' + newsId).prop('checked', true);
        }
    });
});
