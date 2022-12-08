function getCities(country)
{
    let httpx = new XMLHttpRequest();

    httpx.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            let newArrray = JSON.parse(this.response)
            $(".city-op").children().not(".saved").remove()
            $.each(newArrray, function(key, val) {
                let city = toTitleCase(val.city)
                $(".city-op").append("<option value="+city+">"+city+"</option>")
            }
            )
        }
    }
    console.log(httpx)

    httpx.open("GET", "/get-city/?country="+country)
    httpx.send()
}

function toTitleCase(str) {
    return str.replace(
      /\w\S*/g,
      function(txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
      }
    );
  }