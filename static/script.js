// 'use strict';

// window.addEventListener('load', function () {
//     // Fetch all the forms we want to apply custom Bootstrap validation styles to
//     var forms = document.getElementsByClassName('needs-validation');
//     // Loop over them and prevent submission
//     var validation = Array.prototype.filter.call(forms, function (form) {
//         form.addEventListener('submit', function (event) {
//             if (form.checkValidity() === false) {
//                 event.preventDefault();
//                 event.stopPropagation();
//             }
//             form.classList.add('was-validated');
//         }, false);
//     });
// }, false);

// +=============================================================+
// |                                                             |
// |                        Form Handling                        |
// |                                                             |
// +=============================================================+

// Login
$("#loginSubmit").click(function(){
    $.ajax({
        url: "login",
        method: "POST",
        data: {
            email: $("#loginModalEmail").val(),
            password: $("#loginModalPassword").val()
        },
        beforeSend: function() {
            $("#loginStatus").html('<div class="alert alert-secondary"><div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div></div>')
        },
        error: function(data) {
            if(data.responseText.startsWith("Too")) {
                $("#loginStatus").html("<div class=\"alert alert-warning\">" + data.responseText + "</div>")
            }
            else {
                $("#loginStatus").html("<div class=\"alert alert-danger\">" + data.responseText + "</div>")
            }
        },
        success: function(data) {
            $("#loginStatus").html("<div class=\"alert alert-success\">" + data + "</div>")
            location.reload()
        }
    })
});

// Signup
$("#signupSubmit").click(function(){
    $.ajax({
        url: "signup",
        method: "POST",
        data: {
            email: $("#signupEmail").val(),
            password: $("#signupPassword").val(),
            firstName: $("#signupFirstName").val(),
            lastName: $("#signupLastName").val(),
            username: $("#signupUsername").val(),
        },
        beforeSend: function() {
            $("#signupStatus").html('<div class="alert alert-secondary"><div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div></div>')
        },
        error: function(data) {
            if(data.responseText.startsWith("Email")) {
                $("#signupStatus").html("<div class=\"alert alert-warning\">" + data.responseText + "</div>")
            }
            else {
                $("#signupStatus").html("<div class=\"alert alert-danger\">" + data.responseText + "</div>")
            }
        },
        success: function(data) {
            $("#signupStatus").html('<div class=\"alert alert-success\">' + data + ', continue to <a href= "#" data-toggle="modal" data-target="#loginModal" onclick=hideModal("signupModal")>Login</a></div>')
        }
    })
});

// Forgot password
$("#forgotPasswordSubmit").click(function(){
    $.ajax({
        url: "forgotpassword",
        method: "POST",
        data: {
            email: $("#forgotPasswordEmail").val(),
        },
        beforeSend: function() {
            $("#forgotPasswordStatus").html('<div class="alert alert-secondary"><div class="d-flex justify-content-center"><div class="spinner-border" role="status"><span class="sr-only">Loading...</span></div></div></div>')
        },
        error: function(data) {
            if(data.responseText.startsWith("Email")) {
                $("#forgotPasswordStatus").html("<div class=\"alert alert-warning\">" + data.responseText + "</div>")
            }
            else {
                $("#forgotPasswordStatus").html("<div class=\"alert alert-danger\">" + data.responseText + "</div>")
            }
        },
        success: function(data) {
            $("#forgotPasswordStatus").html("<div class=\"alert alert-success\">" + data + "</div>")
        }
    })
});

// +=============================================================+
// |                                                             |
// |                       Modal Handling                        |
// |                                                             |
// +=============================================================+

function hideModal(modalID) {
    $("#"+modalID).modal('hide');
}

function showModal(modalID) {
    $("#"+modalID).modal('show')
}