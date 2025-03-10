
// Toggles the hamburger menu with click

document.querySelector('.hamburger').addEventListener('click', function() {
    var navRight = document.getElementById('navbarRight');
    if (navRight.style.left === "0px") {
        navRight.style.left = "-100%"; // Slide out
    } else {
        navRight.style.left = "0"; // Slide in
    }
});

document.querySelector('.hamburger').addEventListener('click', function() {
    document.getElementById('navbarRight').style.left = "0"; // Slide in
});

document.querySelector('.closebtn').addEventListener('click', function() {
    document.getElementById('navbarRight').style.left = "-100%"; // Slide out
});




// Toggles the dropdown menu with click

const dropBtn = document.getElementById('dropBtn');
if (dropBtn) { // Check if the element actually exists
    const dropdownContent = document.querySelector('.dropdown-content');

    dropBtn.addEventListener('click', function() {
        console.log('clicked');
        if (dropdownContent.style.display === "none") {
            dropdownContent.style.display = "block";
        } else {
            dropdownContent.style.display = "none";
        }
        console.log(dropdownContent);
    });
}


/*
Store uid in memory (not in localStorage. It can be modifired there - NOT secured).
TO-DO: Whem migrating to a modern framework, store it in something like React Context,
to maintain access across the app.
*/
let userId = null

async function fetchUserId(){
    const response = await fetch('/api/me', {credentials: "include"}) //Ensure cookies are sent with the request
    if (response.ok){
        const data = await response.json()
        userId = data.uid; // Now userId is correctly assigned
        console.log("User ID set:", userId);
    } else {
        console.error("Failed to fetch user ID");
    }
}
// Fetch userId before anything else
window.onload = async function(){
    document.getElementById('queryFormSubmitBtn').disabled = true; // Disable submit button until userId is fetched
    await fetchUserId();
    document.getElementById('queryFormSubmitBtn').disabled = false;
}


//add a query to firestore collection
document.getElementById('queryForm').addEventListener('submit', async function (event) {
    event.preventDefault();

     // Create an object from the form data
     const formData = new FormData(event.target);
     const queryData = {
         name: formData.get('query_name'),
         text: formData.get('query_text')
     };
     
     // Send the data as JSON
     const res = await fetch(`/api/users/${userId}/queries`, {
         method: 'POST',
         headers: {
             'Content-Type': 'application/json',
         },
         credentials: 'same-origin',  // Ensures cookies are sent with the request
         body: JSON.stringify(queryData)
     });
    const msg = document.getElementById('error-message');
    msg.textContent = res.ok ? 'Success!' : 'Error!';
});

