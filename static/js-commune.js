let city = document.querySelector(".city");
let country = document.querySelector("#country");
let list = city.classList;
country.addEventListener("change", (event) => {list.remove("form-select")});