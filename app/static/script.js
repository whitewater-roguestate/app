const API_URL = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;

let paddlers = [];



// Handle authentication API post
async function handleLogin() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;
    
    try {
        const response = await fetch(`${API_URL}/api/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: user, password: pass })
        });

        if (response.ok) {
            document.getElementById("login-screen").style.display = "none";
            document.getElementById("dashboard-screen").style.display = "block";
            await loadPaddlers();
            loadGroupPaddlers();
            loadSavedGroups();
        } else {
            document.getElementById("error-msg").innerText = "Invalid username or password credentials.";
        }
    } catch (err) {
        document.getElementById("error-msg").innerText = "Cannot connect to backend server API.";
    }
}

fetch('/api/login/login-page-init');


// Handles layout adjustments across tabs without calling the backend repeatedly
function switchTab(index) {
    document.querySelectorAll('.tab-btn').forEach((btn, i) => {
        if(i === index) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach((tab, i) => {
        if(i === index) tab.classList.add('active');
        else tab.classList.remove('active');
    });
    
    // If they click Tab Index 2 (Saved Groups)
    if (index === 2) {
        loadSavedGroups();
    }
    
    // If they click Tab Index 3 (Trip Log)
    if (index === 3) {
        loadTripLog();
    }

}

// Build the profile loop using the data columns you provided
async function loadPaddlers() {
    const listDiv = document.getElementById("paddler-list");
    listDiv.innerHTML = "<p class='loading-message'>Loading paddlers...</p>";
    
    const response = await fetch(`${API_URL}/api/paddlers`);
    paddlers = await response.json();
    
    
    listDiv.innerHTML = ""; 
    paddlers.forEach((p, idx) => {
        listDiv.innerHTML += `
            <div class="paddler-card">
                <div class="card-header">
                    <div>
                        <div class="paddler-name">${p.name}</div>
                        <div class="paddler-meta">Age: ${p.age} | Experience Level: ${p.experience} | Priority: ${p.priority} | Trips: ${p.trips}</div>
                    </div>
                    <button class="expand-btn" onclick="toggleComments(${idx})">Comments</button>
                </div>
                <div id="drawer-${idx}" class="comments-drawer">${p.comments}</div>
            </div>
        `;
    });
}

// Standard JavaScript view-toggle logic 
function toggleComments(idx) {
    const drawer = document.getElementById(`drawer-${idx}`);
    drawer.style.display = drawer.style.display === "block" ? "none" : "block";
}


// Show the group selection list
function loadGroupPaddlers() {
    const listDiv = document.getElementById("group-paddler-list");
    
    listDiv.innerHTML = "";
    
    paddlers.forEach((p, idx) => {
    listDiv.innerHTML += `
        <div class="group-paddler">
            <input 
                type="checkbox"
                id="group-paddler-${idx}"
                value="${idx}"
            >
            
            <label for="group-paddler-${idx}">
                <strong>${p.name}</strong>
                - age: ${p.age}
                - experience: ${p.experience}
            </label>
        </div>
    `;
    });
}


// Create a new group
async function createGroup() {
    // 1. Get the group name input element safely
    const groupNameInput = document.getElementById("group-name");
    
    // Safety guard: If the HTML input element is missing, initialize a fallback string
    let groupName = groupNameInput ? groupNameInput.value.trim() : "";

    // 2. Find all the checkboxes inside the list that are currently ticked
    const checkedBoxes = document.querySelectorAll('#group-paddler-list input[type="checkbox"]:checked');
    
    // Safety Check: Make sure they picked at least one person
    if (checkedBoxes.length === 0) {
        alert("Please select at least one paddler to build a group.");
        return;
    }

    // 3. Loop over the checked boxes, look at their value (the index), and get the real name
    const selectedMembers = Array.from(checkedBoxes).map(box => {
        const idx = parseInt(box.value);
        return paddlers[idx].name; // Looks up the name from your master paddlers list
    });
    
    // Safety Check: If group name is blank, auto-generate one from selected member names
    if (!groupName) {
        groupName = selectedMembers.join(", ");
    }

    // 4. Package the data up into a clean JSON bundle
    const payload = {
        group_name: groupName,
        member_names: selectedMembers
    };
    
    showGroupLoading();
    
    try {
        // 5. Send the POST request to your FastAPI backend
        const response = await fetch(`${API_URL}/api/groups`, {
            method: "POST", // Tells the server we are sending data, not getting it
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload) // Converts our Javascript object into raw text
        });

        if (response.ok) {
            const result = await response.json();
            alert(result.message || "Group saved successfully!");
            
            // 6. Reset the form fields so it's clean for the next group
            if (groupNameInput) groupNameInput.value = "";
            loadGroupPaddlers();
            
            // Automatically switch over to the 'Saved Groups' tab (index 2)
            switchTab(2); 
            hideGroupLoading();
        } else {
            const errData = await response.json();
            hideGroupLoading();
            alert("Server error: " + (errData.detail || "Could not save group."));
        }
    } catch (err) {
        console.error(err);
        hideGroupLoading();
        alert("Could not connect to the backend server API.");
    }
}


//Show the saved groups
// Show the saved groups with an appearing/disappearing delete toggle button
async function loadSavedGroups() {
    const listDiv = document.getElementById("saved-groups-list");
    listDiv.innerHTML = "<p class='loading-message'>Loading groups from sheet...</p>";

    try {
        const response = await fetch(`${API_URL}/api/groups`);
        if (!response.ok) throw new Error("Failed to fetch groups");

        const data = await response.json();
        const groups = data.groups;

        listDiv.innerHTML = ""; // Clear out loading text

        if (groups.length === 0) {
            listDiv.innerHTML = "<p class='loading-message'>No groups created yet!</p>";
            return;
        }

        // Loop through each group and create a card container
        groups.forEach((g, idx) => {
            const name = g.group_name || g.group_names || g.Name || g.name || "Unnamed Group";
            const code = g.code || g.Code || "N/A";
            const members = g.members;
            
            // Using group code as a unique parameter reference identifier if it exists
            const recordId = g.code || idx; 

            listDiv.innerHTML += `
                <div class="paddler-card" id="group-card-${recordId}" data-idx="${code}">
                    
                    <!-- Hidden Alert Box Prompt Confirmation Sheet Overlay -->
                    <div id="confirm-overlay-${recordId}" class="delete-confirm-overlay" style="display: none;">
                        <p>Are you sure you want to delete this group?</p>
                        <div class="confirm-btn-row">
                            <button class="btn-yes" onclick="executeDeleteGroup('${recordId}')">Yes</button>
                            <button class="btn-no" onclick="closeDeleteConfirmation('${recordId}')">No</button>
                        </div>
                    </div>

                    <div class="card-header">
                        <div>
                            <div class="paddler-name">${name}</div>
                            <div class="paddler-meta">Group Code: #${code}</div>
                            <div class="paddler-meta">${members}</div>
                        </div>
                        
                        <!-- Actions Wrapper to sit side-by-side on the right -->
                        <div class="card-actions-wrapper">
                            <!-- The Swapped Red Delete Trigger Option (Hidden by default to the left) -->
                            <button id="del-${recordId}" class="btn-delete-action" style="display: none;" onclick="openDeleteConfirmation('${recordId}')">Delete</button>
                            
                            <!-- The Options Trigger [ ... ] Button Layout Element -->
                            <button id="options-${recordId}" class="options-btn" onclick="toggleDeleteButton('${recordId}')">...</button>
                        </div>
                    </div>
                </div>
            `;
        });
    } catch (err) {
        console.error(err);
        listDiv.innerHTML = "<p class='error-message'>Error loading saved groups</p>";
    }
}

// 1. Toggles the red delete button into view to the left of the clicked ... button
function toggleDeleteButton(recordId) {
    const deleteBtn = document.getElementById(`del-${recordId}`);
    
    if (deleteBtn) {
        if (deleteBtn.style.display === "none") {
            deleteBtn.style.display = "block";
        } else {
            deleteBtn.style.display = "none";
        }
    }
}

// 2. Opens up the black prompt confirmation layer
function openDeleteConfirmation(recordId) {
    const overlay = document.getElementById(`confirm-overlay-${recordId}`);
    if (overlay) overlay.style.display = "flex";
}

// 3. Closes out confirmation window and automatically hides the red delete menu option
function closeDeleteConfirmation(recordId) {
    const overlay = document.getElementById(`confirm-overlay-${recordId}`);
    const deleteBtn = document.getElementById(`del-${recordId}`);
    
    if (overlay) overlay.style.display = "none";
    if (deleteBtn) deleteBtn.style.display = "none"; // Hides delete button after choosing No
}

// 4. Instantly drops the card layout elements entirely from the front-end page markup
async function executeDeleteGroup(recordId) {
    const targetCard = document.getElementById(`group-card-${recordId}`);
    if (targetCard) {
        targetCard.remove();
        console.log(`Group card #${recordId} dropped completely from frontend workspace markup.`);
        
        const groupIdx = targetCard.getAttribute('data-idx');
        try {
            // Sends the request exactly how FastAPI expects it (?idx=3)
            const response = await fetch(`${API_URL}/api/groups?group_id=${groupIdx}`, { 
                method: 'DELETE' 
            });

            if (!response.ok) {
                throw new Error('Failed to delete on the server side spreadsheet update.');
            } 
            loadGroupPaddlers();
            loadSavedGroups(); 
            
            } catch (error) {  // <-- Ensure this catch block is present right after the try block closes
                console.error('Error deleting group:', error);
                alert('Could not complete deletion. Please try again.');
            }
        }
}
// Global click listener to close open delete buttons AND confirmation overlays when clicking outside
document.addEventListener('click', function(event) {
    
    // --- 1. Handle Saved Group Cards ---
    const groupCards = document.querySelectorAll('#saved-groups-list .paddler-card');
    groupCards.forEach(card => {
        const recordId = card.id.replace('group-card-', '');
        const deleteBtn = document.getElementById(`del-${recordId}`);
        const dotsBtn = document.getElementById(`options-${recordId}`);
        const overlay = document.getElementById(`confirm-overlay-${recordId}`);
        
        // If either the delete button or the confirmation overlay is active...
        if ((deleteBtn && deleteBtn.style.display === "block") || (overlay && overlay.style.display === "flex")) {
            // Check if the click happened completely outside the card actions and dots button
            if (!deleteBtn.contains(event.target) && !dotsBtn.contains(event.target) && !overlay.contains(event.target)) {
                if (deleteBtn) deleteBtn.style.display = "none";
                if (overlay) overlay.style.display = "none";
            }
        }
    });

    // --- 2. Handle Trip Log Cards ---
    const tripCards = document.querySelectorAll('#trip-log .paddler-card');
    tripCards.forEach(card => {
        const tripId = card.id.replace('trip-card-', '');
        const deleteBtn = document.getElementById(`trip-del-${tripId}`);
        const dotsBtn = document.getElementById(`trip-options-${tripId}`);
        const overlay = document.getElementById(`trip-confirm-overlay-${tripId}`);
        
        // If either the trip delete button or the trip confirmation overlay is active...
        if ((deleteBtn && deleteBtn.style.display === "block") || (overlay && overlay.style.display === "flex")) {
            // Check if the click happened completely outside the card actions and dots button
            if (!deleteBtn.contains(event.target) && !dotsBtn.contains(event.target) && !overlay.contains(event.target)) {
                if (deleteBtn) deleteBtn.style.display = "none";
                if (overlay) overlay.style.display = "none";
            }
        }
    });
});

// Dark screen overlay while creating a group
function showGroupLoading() {
    document.getElementById("group-loading-overlay").style.display = "block";
}
function hideGroupLoading() {
    document.getElementById("group-loading-overlay").style.display = "none";
}    

// Load the trip log history
async function loadTripLog() {
    const listDiv = document.getElementById("trip-log");
    listDiv.innerHTML = "<p class='loading-message'>Loading trip log...</p>";
    
    try {
        const response = await fetch(`${API_URL}/api/trip-log`);
        if (!response.ok) throw new Error("Failed to fetch trip log");

        const data = await response.json();
        const trips = data.trips;
        const files = data.files;
        
        listDiv.innerHTML = ""; // Clear out loading text
        trips.forEach((t, idx) => {
            // Using the trip date string or unique index to give each item its own ID context
            const tripId = t.date; 

            const expectedFileName = `${t.date}.png`;
            const imageExists = files.some(file => file.name === expectedFileName);
            const imageHtml = imageExists 
            ? `<img src="/static/trip_photos/${expectedFileName}" alt="Trip Photo" style="max-width: 100%; margin-top: 10px; border-radius: 4px;">`
            : ''; // Leaves it completely empty if no photo is found
            
            listDiv.innerHTML += `
                <div class="paddler-card" id="trip-card-${tripId}" data-trip-ref="${tripId}">
                    
                    <!-- Hidden Alert Box Prompt Confirmation Overlay Canvas -->
                    <div id="trip-confirm-overlay-${tripId}" class="delete-confirm-overlay" style="display: none;">
                        <p>Are you sure you want to delete this trip log?</p>
                        <div class="confirm-btn-row">
                            <button class="btn-yes" onclick="executeDeleteTrip('${tripId}')">Yes</button>
                            <button class="btn-no" onclick="closeTripDeleteConfirmation('${tripId}')">No</button>
                        </div>
                    </div>

                    <div class="card-header">
                        <div>
                            <div class="paddler-meta">${t.date.slice(0,8)}:</div>
                            <div class="paddler-name">${t.location}</div>
                            <div class="paddler-meta">${t.message}</div>
                            ${imageHtml}
                            <div class="paddler-name" style="text-align: right;">${t.members}</div>
                        </div>
                        
                        <!-- Side-by-side actions configuration layout on the right -->
                        <div class="card-actions-wrapper" style="position: absolute; top: 15px; right: 15px;">
                            <!-- Swapped Red Delete Button -->
                            <button id="trip-del-${tripId}" class="btn-delete-action" style="display: none;" onclick="openTripDeleteConfirmation('${tripId}')">Delete</button>
    
                            <!-- The Options Trigger [ ... ] Button -->
                            <button id="trip-options-${tripId}" class="options-btn" onclick="toggleTripDeleteButton('${tripId}')">...</button>
                        </div>
                        </div>
                    </div>
                </div>
            `;
        });
        
    } catch (err) {
        console.error(err);
        listDiv.innerHTML = "<p class='error-message'>Error loading trip log</p>";
    }
}

// Grab the overlay container DOM elements
const modalOverlay = document.getElementById("form-modal-overlay");
const openModalBtn = document.getElementById("open-modal-btn");
const closeModalBtn = document.getElementById("close-modal-btn");

// Open Modal Window: Rebuilds dropdown options fresh, then displays the overlay
openModalBtn.addEventListener("click", () => {
    populateTripGroupDropdown(); // Step 2 Part 2: Dynamically updates options before opening
    modalOverlay.style.display = "flex";
    document.getElementById("form-status").textContent = ""; // Clear any past status text
});

// Close Modal Window function (Deliberately wipes the form state clean)
function hideModal() {
    modalOverlay.style.display = "none";
    document.getElementById("trip-form").reset(); // Step 2 Part 3: Wipes input boxes & images cleanly
}

closeModalBtn.addEventListener("click", hideModal);

// Close Modal if the user clicks outside the form box card onto the dark backdrop directly
modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
        hideModal();
    }
});

// Hook into your Form Submission handler

document.getElementById("trip-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = e.currentTarget;
    const statusText = document.getElementById("form-status");
    const submitBtn = form.querySelector('[type="submit"]');

    statusText.textContent = "Uploading trip entry...";
    statusText.style.color = "orange";

    if (submitBtn) submitBtn.disabled = true;

    const formData = new FormData();
    formData.append(
        "location",
        document.getElementById("form-location").value
    );
    formData.append(
        "message",
        document.getElementById("form-message").value
    );
    formData.append(
        "group",
        document.getElementById("form-group-select").value || ""
    );

    const photoInput = document.getElementById("form-photo");

    if (photoInput.files.length > 0) {
        formData.append("photo", photoInput.files[0]);
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 30000);

    try {
        console.log("Trip upload starting", {
            hasPhoto: photoInput.files.length > 0,
            photoSize: photoInput.files[0]?.size ?? 0
        });

        const response = await fetch(
            `${API_URL}/api/trip-log`,
            {
                method: "POST",
                body: formData,
                signal: controller.signal
            }
        );

        console.log("Trip upload response:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Server returned ${response.status}: ${errorText}`
            );
        }

        statusText.style.color = "green";
        statusText.textContent = "Trip saved successfully!";

        setTimeout(() => {
            hideModal();
            loadTripLog();
        }, 1000);

    } catch (err) {
        console.error("Trip upload failed:", err);

        statusText.style.color = "red";

        if (err.name === "AbortError") {
            statusText.textContent =
                "Upload timed out after 30 seconds. Check your connection and try again.";
        } else {
            statusText.textContent =
                `Upload failed: ${err.message}`;
        }
    } finally {
        clearTimeout(timeout);
        if (submitBtn) submitBtn.disabled = false;
    }
});

// Monitor the dropdown selection changes
document.getElementById('form-group-select').addEventListener('change', function() {
    if (this.value === 'NEW_GROUP_REDIRECT') {
        // Hide the trip modal overlay without clearing the form state
        document.getElementById('form-modal-overlay').style.display = 'none';
        
        // Reset the selector position back to default hint item
        this.value = '';
        
        // Switch user over to the Create Group tab (Index 1)
        switchTab(1);
    }
});

// Helper function to build the dropdown options
function populateTripGroupDropdown() {
    const selectDropdown = document.getElementById('form-group-select');
    if (!selectDropdown) return;

    // Reset layout with placeholder hint item
    selectDropdown.innerHTML = `<option value="">-- Choose a Saved Group --</option>`;

    // Access groups stored in your app context state
    // (If your groups data isn't globally available, we can grab them from loadSavedGroups)
    const savedGroupsList = document.querySelectorAll('#saved-groups-list .paddler-card');
    
    savedGroupsList.forEach((card) => {
        const nameEl = card.querySelector('.paddler-name');
        const groupCode = card.getAttribute('data-idx');
        
        if (nameEl && groupCode.length) {
            const option = document.createElement('option');

            // Store the group code, not the members' names
            option.value = groupCode;
            option.textContent = nameEl.innerText.trim();

            selectDropdown.appendChild(option);
        }
    });

    // Append the special action option trigger at the very bottom
    const newGroupOption = document.createElement('option');
    newGroupOption.value = 'NEW_GROUP_REDIRECT';
    newGroupOption.textContent = '* CREATE NEW GROUP *';
    newGroupOption.style.fontWeight = 'bold';
    selectDropdown.appendChild(newGroupOption);
}

// 1. Toggles the red delete button to the left of the trip ... button
function toggleTripDeleteButton(tripId) {
    const deleteBtn = document.getElementById(`trip-del-${tripId}`);
    if (deleteBtn) {
        deleteBtn.style.display = deleteBtn.style.display === "none" ? "block" : "none";
    }
}

// 2. Opens up the dark overlay confirmation layer
function openTripDeleteConfirmation(tripId) {
    const overlay = document.getElementById(`trip-confirm-overlay-${tripId}`);
    if (overlay) overlay.style.display = "flex";
}

// 3. Closes confirmation window and hides the red delete option
function closeTripDeleteConfirmation(tripId) {
    const overlay = document.getElementById(`trip-confirm-overlay-${tripId}`);
    const deleteBtn = document.getElementById(`trip-del-${tripId}`);
    
    if (overlay) overlay.style.display = "none";
    if (deleteBtn) deleteBtn.style.display = "none";
}

// 4. Instantly drops the trip card layout completely from the page workspace view

async function executeDeleteTrip(tripRef) {
    const targetCard = document.getElementById(`trip-card-${tripRef}`);

    if (!targetCard) {
        console.error(`Could not find trip card #${tripRef}`);
        return;
    }

    try {
        // Send the unique trip reference to the backend
        const response = await fetch(
            `${API_URL}/api/trip-log?trip_ref=${encodeURIComponent(tripRef)}`,
            { method: "DELETE" }
        );

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(
                `Server deletion failed (${response.status}): ${errorText}`
            );
        }

        // Only remove the card once the server confirms success
        targetCard.remove();
        console.log(`Trip ${tripRef} deleted successfully.`);

    } catch (error) {
        console.error("Error deleting trip:", error);
        alert("Could not delete the trip. Please try again.");
    }
}