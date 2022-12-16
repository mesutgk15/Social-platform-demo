$("#btn-add-selection").on("click", function(){
    rank = $(".selections").children().length;
    if (rank >= 24){
        console.log("max reached")
    }
    else
    {
        html = $("<div class='selection-container d-flex justify-content-center gap-5 mt-2'></div>");
        
        html.append($("<label class='mt-2' for='poll-selection-"+rank+"'>Selection-"+(rank+1)+"</label>)"));
        html.append($("<input type='text' autocomplete='off' name='selection-"+rank+"' class='form-control w-50' id='poll-selection-"+rank+"'></input>"))
        html.append($("<button type='button' class='btn btn-remove-selection btn-sm' value='"+rank+"'>Remove</button>)"));
        
        html.attr("rank", rank)
        $(".selections").append(html);
    }
});

$(document).on("click", ".btn-remove-selection", function(){
    // Get the selection rank from button value, which will be removed 
    const anchor = $(this).val();
    console.log(anchor);
    
    // Check if the selection to be removed is at the last row. If it is remove only 
    if ($(".selections").children().length == (+anchor + 1))
    {
        $("div[rank = "+anchor+"]").remove();
        console.log("a");
    }
    // If removal is from middle rows, degrade all following selection ranks by one to keep the list tiered
    else
    {
        console.log("b");
        $("div[rank = "+anchor+"]").remove();
        for (i = anchor; i <= $(".selections").children().length; i++)
        {
            console.log("m")
            $("div[rank = "+i+"] button[value = "+i+"]").attr("value", (i - 1));
            $("div[rank = "+i+"] label[for = 'poll-selection-"+i+"']").attr("for", "poll-selection-"+(i - 1)+"");
            $("div[rank = "+i+"] label[for = 'poll-selection-"+(i - 1)+"']").html("Selection-"+(i)+"");
            $("div[rank = "+i+"] input").attr("name", "selection-"+(i - 1)+"");
            $("div[rank = "+i+"] input").attr("id", "poll-selection-"+(i - 1)+"");
            $("div[rank = "+i+"]").attr("rank", (i - 1));
        }
    }
    
})



$(".get-poll").on("click", function(){
        
    let poll_id = $(this).val();
    $("#selections"+poll_id+"").empty();
    $.ajax({
        type: 'GET',
        url: '/get_selections/?poll_id='+poll_id,
        dataType: 'json',
        success: function(data) {
            console.log(data);
            console.log(typeof(data));
            console.log(data.length);
            $.each(data, function(key, value){
                console.log(key)

                console.log(key.slice(0,-10))
                if (key.indexOf("voteCount") >= 0){
                    html_voteCount = $("<span value='"+key+"' name='poll"+poll_id+"'>Number of Votes: "+value+"</span>");
                    $(document.getElementsByClassName("poll"+poll_id+"-selection-group-"+key.slice(0,-10)+"")).append(html_voteCount);
                    $(document.getElementsByClassName("poll"+poll_id+"-selection-group-"+key.slice(0,-10)+"")).attr("data-vote-count", value)
                }
                else if (key.indexOf("voteTotal") >= 0){
                    let vote_count = $(document.getElementsByClassName("poll"+poll_id+"-selection-group-"+key.slice(0,-10)+"")).attr("data-vote-count")
                    html_voteTotal = $("<span value='"+key+"' name='poll"+poll_id+"'>%"+Math.floor((vote_count/value)*100)+"</span>");
                    $(document.getElementsByClassName("poll"+poll_id+"-selection-group-"+key.slice(0,-10)+"")).append(html_voteTotal);
                }

                else
                {
                    div = $("<div class='d-flex gap-3 justify-content-between poll"+poll_id+"-selection-group poll"+poll_id+"-selection-group-"+key+"'>");
                    html = $("<input type='checkbox' value='"+key+"' name='poll"+poll_id+"' id='"+key+"'>");
                    html1 = $("<label class='selection-span' for='"+key+"' >"+value+"</label>");
                    div.append(html);
                    div.append(html1);
                    $("#selections"+poll_id+"").append(div);
                }
                
            })       
            
            // Order selections by vote count
            let selection_list = $(document.getElementsByClassName("poll"+poll_id+"-selection-group"))
            selection_list.sort(function(a, b){
                return $(b).data("vote-count")-$(a).data("vote-count")
            });
            $("#selections"+poll_id+"").html(selection_list)
        
            
            $("#vote-button-"+poll_id+"").remove();      

            submit_button = $("<button class='btn btn-sm btn-success mt-3' id='vote-button-"+poll_id+"' type='submit'>Vote</button>");
            $(".selections-form"+poll_id+"").append(submit_button);
            
        }
    })

}
)

function limit_selections (name, limit){

    let limit_var = limit;
    $(document).on("change", "input[name = "+name+"]", function(){
        if ($("input[name = "+name+"]:checked").length > limit_var){
            $(this).prop('checked', false);
        }
    })
}

let forms = $("form")

forms.each(function(index, form){
    console.log(form['name']);
    console.log($(this).attr('max-selection'));
    limit_selections(form['name'], $(this).attr('max-selection'))    
})

// limit_selections(key['name'], key['max-selection'])

// 



// $(document).on("change", "input[type=checkbox]", function(){    
//     console.log($(this).val())
// })
    
    
    
