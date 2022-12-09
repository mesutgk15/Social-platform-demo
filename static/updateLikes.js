function updateLike(post_id)
{
    let httpx = new XMLHttpRequest();

    httpx.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200)
        {
            let response_obj = JSON.parse(this.response);
            console.log(response_obj);
            let like_count = response_obj['like_count'];
            let dislike_count = response_obj['dislike_count'];
            let like_status = response_obj['like_status']
            $("#like-count-"+post_id).text(like_count);
            $("#dislike-count-"+post_id).text(dislike_count);
            if (like_status == "LIKE")
            {
                $("#like-icon-liked-"+post_id).removeAttr("hidden");
                $("#like-icon-def-"+post_id).attr("hidden", true);
                $("#dislike-icon-disliked-"+post_id).attr("hidden", true);
                $("#dislike-icon-def-"+post_id).removeAttr("hidden");
            }
            else if (like_status == "DISLIKE")
            {
                $("#like-icon-liked-"+post_id).attr("hidden", true);
                $("#like-icon-def-"+post_id).removeAttr("hidden");
                $("#dislike-icon-disliked-"+post_id).removeAttr("hidden");
                $("#dislike-icon-def-"+post_id).attr("hidden", true);
            }
            else 
            {
                $("#like-icon-liked-"+post_id).attr("hidden", true);
                $("#like-icon-def-"+post_id).removeAttr("hidden");
                $("#dislike-icon-disliked-"+post_id).attr("hidden", true);
                $("#dislike-icon-def-"+post_id).removeAttr("hidden");
            }
        }
    }

    httpx.open("GET", "/update-likes/?like_dislike=like&post-id="+post_id);
    httpx.send();
}

function updateDislike(post_id)
{
    let httpx = new XMLHttpRequest();

    httpx.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200)
        {
            let response_obj = JSON.parse(this.response);
            console.log(response_obj);
            let like_count = response_obj['like_count'];
            let dislike_count = response_obj['dislike_count'];
            let like_status = response_obj['like_status']
            $("#like-count-"+post_id).text(like_count);
            $("#dislike-count-"+post_id).text(dislike_count);
            if (like_status == "LIKE")
            {
                $("#like-icon-liked-"+post_id).removeAttr("hidden");
                $("#like-icon-def-"+post_id).attr("hidden", true);
                $("#dislike-icon-disliked-"+post_id).attr("hidden", true);
                $("#dislike-icon-def-"+post_id).removeAttr("hidden");
            }
            else if (like_status == "DISLIKE")
            {
                $("#like-icon-liked-"+post_id).attr("hidden", true);
                $("#like-icon-def-"+post_id).removeAttr("hidden");
                $("#dislike-icon-disliked-"+post_id).removeAttr("hidden");
                $("#dislike-icon-def-"+post_id).attr("hidden", true);
            }
            else 
            {
                $("#like-icon-liked-"+post_id).attr("hidden", true);
                $("#like-icon-def-"+post_id).removeAttr("hidden");
                $("#dislike-icon-disliked-"+post_id).attr("hidden", true);
                $("#dislike-icon-def-"+post_id).removeAttr("hidden");
            }
        }
    }

    httpx.open("GET", "/update-likes/?like_dislike=dislike&post-id="+post_id);
    httpx.send();
}