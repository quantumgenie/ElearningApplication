// add course AJAX request for the API POST endpoint
function submitCourseForm(event) {
        event.preventDefault();

        // collecting form data
        const formData = {
            title: document.getElementById('title').value,
            level: document.getElementById('level').value,
            description: document.getElementById('description').value,
            start_date: document.getElementById('start_date').value,
            end_date: document.getElementById('end_date').value,
        };
        console.log(formData);
        // handling POST request and messages for success/error
        fetch('/api/add_course/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(formData)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(error => {
                        throw new Error(`Error: ${error.detail || 'Unknown error'}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.course_id) {

                    document.getElementById('message').innerHTML = 'Course added successfully!';
                } else {
                    console.error('Error:', data);
                    document.getElementById('message').innerHTML = 'Error adding the course.';
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                document.getElementById('message').innerHTML = 'An error occurred while adding the course.';
            });
}

// delete added material from the course:

function deleteCourse(courseId) {
    // retrieve CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    if (confirm("Are you sure you want to delete this course?")) {
        fetch(`/api/course/delete/${courseId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                console.log('Course deleted successfully.');
                // remove the material from the HTML page
                document.getElementById(`course-${courseId}`).remove();
            } else {
                console.error('Failed to delete course.');
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        // If the user cancels, log a message or take other actions
        console.log('Course deletion cancelled.');
    }
}

// delete added material from the course:

function deleteMaterial(materialId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    if (confirm("Are you sure you want to delete this material?")) {
        fetch(`/api/material/delete/${materialId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                console.log('Material deleted successfully.');
                // remove the material from the HTML page
                document.getElementById(`material-${materialId}`).remove();
            } else {
                console.error('Failed to delete material.');
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        // if cancelled log message
        console.log('Material deletion cancelled.');
    }
}

// un-enroll from course

function unEnrollCourse(enrollmentId) {
    // retrieve CSRF token
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    if (confirm("Are you sure you want to un-enroll from this course?")) {
        fetch(`/api/course/un-enroll/${enrollmentId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                console.log('Course un-enrolled successfully.');
                // remove the material from the HTML page
                document.getElementById(`enrolled_course-${enrollmentId}`).remove();
            } else {
                console.error('Failed to un-enroll course.');
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        // If the user cancels, log a message or take other actions
        console.log('Course un-enrollment cancelled.');
    }
}

// teacher: remove student from course 

function removeStudent(enrollmentId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    if (confirm("Are you sure you want to remove this student?")) {
        fetch(`/api/course/student/remove/${enrollmentId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                console.log('Student removed successfully.');
                const removedStudentMessage = document.getElementById(`enrollment-${enrollmentId}`);
                removedStudentMessage.innerHTML = `Student removed from course`;
            } else {
                console.error('Failed to remove student.');
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

//  teacher: block student from course 

function blockStudent(enrollmentId, isBlocked) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    // if student is not blocked, block access to the couse
    if (!isBlocked) {
        if (confirm("Are you sure you want to Block this student?")) {
            fetch(`/api/course/student/block/${enrollmentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ blocked: true })
            })
            .then(response => {
                if (response.ok) {
                    console.log('Student Blocked successfully.');
                    const blockButtonName = document.getElementById(`button-enrollment-${enrollmentId}`);
                    blockButtonName.innerHTML = `Un-Block`;
                } else {
                    console.error('Failed to Block student.');
                }
            })
            .catch(error => console.error('Error:', error));
        }
    // if student is blocked, un-block the student from course
    } else {
        if (confirm("Are you sure you want to Un-Block this student?")) {
            fetch(`/api/course/student/block/${enrollmentId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ blocked: false })
            })
            .then(response => {
                if (response.ok) {
                    console.log('Student Un-Blocked successfully.');
                    const blockButtonName = document.getElementById(`button-enrollment-${enrollmentId}`);
                    blockButtonName.innerHTML = `Block`;
                } else {
                    console.error('Failed to Un-Block student.');
                }
            })
            .catch(error => console.error('Error:', error));
        }
    }
}

// student & teacher:  event listener to handle WebSocket notifications
document.addEventListener('DOMContentLoaded', function () {
    // initializing the WebSocket for notifications
    const notificationSocket = new WebSocket('ws://' + window.location.host + '/ws/notifications/');

    notificationSocket.onopen = function(e) {
        console.log('WebSocket Notifications connection opened');
    };

    notificationSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('SCRIPT - OnMessage: this is your message: ' + data.message);
        const notificationBadge = document.getElementById(`notification-badge`);
        displayNotification(data.message);
        updateNotificationCount(data.unread_count);
    };

    notificationSocket.onclose = function(e) {
        console.error('Notification socket closed unexpectedly');
    };
});

// displaying notification within page as alert message
function displayNotification(message) {
    const notificationContainer = document.getElementById('notification-container');

    if (notificationContainer) {
        const newNotification = document.createElement('div');
        newNotification.className = 'alert alert-success';
        newNotification.role = 'alert'
        newNotification.innerText = message;

        notificationContainer.appendChild(newNotification);

        // Optionally, remove the notification after some time
        setTimeout(() => {
            notificationContainer.removeChild(newNotification);
        }, 5000);
    } else {
        alert('New Notification: ' + message);
    }
}
// update number of notificaitons in the count badge
function updateNotificationCount(count) {
    const notificationCountElement = document.getElementById('notification-count');
    if (notificationCountElement) {
        notificationCountElement.textContent = count;
    }
}

// student & teacher: mark all notifications read 

function markNotificationsRead() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    if (confirm("Confirm marking all notifications as read")) {
        fetch('/api/user/mark_notifications_as_read/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                console.log('All notifications marked as read.');
                // reload page after success
                location.reload();
            } else {
                console.error('Failed to mark notifications as read.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}


// student & teachear: event listener to handle entering a chat room
document.addEventListener('DOMContentLoaded', function () {
    // Check if the input element exists
    const roomNameInput = document.querySelector('#room-name-input');
    
    if (roomNameInput) {
    // focus on the input field
        roomNameInput.focus();
        // releasing Enter key will act like a click on the submit button
        document.querySelector('#room-name-input').onkeyup = function (e) {
            if (e.keyCode === 13) { // enter key code
                document.querySelector('#room-name-submit').click();
            }
        };
        // on clicking the submit button user will redirect to inserted room page
        document.querySelector('#room-name-submit').onclick = function (e) {
            var roomName = document.querySelector('#room-name-input').value;
            window.location.pathname = '/live_chat/' + roomName + '/';
        };
    }
});

// student & teacher : event listener for the live chat WebSocket

document.addEventListener('DOMContentLoaded', function () {
    const chatMessageInput = document.querySelector('#chat-message-input');
    
    if (chatMessageInput) {
        const roomNameElement = document.getElementById('room-name');
        const roomName = JSON.parse(roomNameElement.textContent);
        const userGroup = document.getElementById("chat-user-group").value;
        const username = document.getElementById("chat-username").value; 

        const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/live_chat/' + roomName + '/');

        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            document.querySelector('#chat-log').value += (data.message + '\n');
        };

        chatSocket.onclose = function (e) {
            console.error('Chat socket closed unexpectedly');
        }

        chatMessageInput.focus();
        document.querySelector('#chat-message-input').onkeyup = function (e) {
            if (e.keyCode === 13) { //enter key code
                document.querySelector('#chat-message-submit').click();
            }
        };
        document.querySelector('#chat-message-submit').onclick = function (e) {
            const messageInputDom = document.querySelector('#chat-message-input');
            const message = messageInputDom.value;
            const formattedMessage = `${userGroup}[${username}] :: ${message}`;

            chatSocket.send(JSON.stringify({
                'message': formattedMessage
            }));
            messageInputDom.value = '';
        };
    }
});


// student: send course feedback

function sendCourseFeedback(courseId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const message = document.getElementById('feedback-input').value;
    console.log('This is your message : ' + message);
    if (message.trim() === '') {
        alert('Please enter your feedback.');
        return;
    }
    // send feedback using the Fetch API
    fetch('/api/course/send_feedback/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            course: courseId,
            message: message
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById('feedback-input').value = '';
            location.reload();

        } else {
            console.error('Error:', data);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// student & teachear: collect data from page and update user profile

function collectAndUpdateProfile(firstName, lastName, email, dateOfBirth, bio, status) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    // check for each field if input has been added
    newFirstName = document.getElementById('input-first_name').value.trim();
    if (newFirstName){
        firstName = newFirstName
    }
    newLastName = document.getElementById('input-last_name').value.trim();
    if (newLastName){
        lastName = newLastName
    }
    newEmail = document.getElementById('input-email').value.trim();
    if (newEmail){
        email = newEmail
    }
    newDateOfBirth = document.getElementById('input-date_of_birth').value.trim();
    if (newDateOfBirth && newDateOfBirth !== "None"){
        dateOfBirth = newDateOfBirth
    }
    newBio = document.getElementById('input-bio').value.trim();
    if (newBio && newBio !== "None"){
        bio = newBio
    }
    newStatus = document.getElementById('input-status').value.trim();
    if (newStatus && newStatus !== "None"){
        status = newStatus
    }

    const userData = {
        first_name: firstName,
        last_name: lastName,
        email: email,
    };
    const appUserData = {
        date_of_birth: dateOfBirth,
        bio: bio,
        status: status,
    };
    console.log(userData);
    console.log(appUserData);
    // update user profile
    updateUserProfile(userData, appUserData, csrfToken)
}

// update user profile with collected data
function updateUserProfile(userData, appUserData, csrfToken) {
    fetch('/api/user/profile/update/', {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken 
        },
        body: JSON.stringify({
            user: userData,
            app_user: appUserData
        }),
    })
    .then(response => {
        if (!response.ok){
            throw new Error('Network response was not ok');
        }
        return response.json()
    })
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
        } else {
            console.log('User and AppUser updated successfully:', data);
            location.reload();
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

// student & teachear: update user status

function updateUserStatus() {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const status = document.getElementById('new-status-input').value;
    console.log('This is your status : ' + status);
    if (status.trim() === '') {
        alert('Please enter your status update first.');
        return;
    }
    // send feedback using the Fetch API
    fetch('/api/user/status/update/', {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            status: status
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            document.getElementById('new-status-input').value = '';
            location.reload();

        } else {
            console.error('Error:', data);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}