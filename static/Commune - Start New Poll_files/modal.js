$("#update_address").on("click", function() {
    $("#modal-title").text("Update Your Address") 
    $("#modal-title-2").text("Address: ")
    $("#contact-info-update-form").attr("action", "/profile/update/?update=address");
    $("#update-text").attr("name", "address-text") 
    $("#updateModal").modal("show");
});

$("#update_phone_number").on("click", function() {
    $("#modal-title").text("Update Your Phone Number") 
    $("#modal-title-2").text("Phone Number: ")
    $("#contact-info-update-form").attr("action", "/profile/update/?update=phone_number");
    $("#update-text").attr("name", "phone_number") 
    $("#updateModal").modal("show");
});

$("#newPost").on("click", function() {
    $("#newPostModal").modal("show");
});