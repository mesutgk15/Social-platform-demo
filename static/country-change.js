// Call the route to receive the query from database to list the cities for input country     
function getCities(country)
{
    let httpx = new XMLHttpRequest();

    httpx.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            // Store the JSON response from server in a new array
            let newArrray = JSON.parse(this.response)

            $(".city-op").children().not(".saved").remove()
            $.each(newArrray, function(key, val) {
                // Titlecase each string before create select option
                let city = toTitleCase(val.city)
                $(".city-op").append("<option value="+city+">"+city+"</option>")
            }
            )
        }
    }
    httpx.open("GET", "/get-city/?country="+country)
    httpx.send()
}

// To return title cased string

function toTitleCase(str) {
    return str.replace(
      /\w\S*/g,
      function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
      }
    );
  }