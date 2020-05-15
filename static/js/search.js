var translate_input = document.getElementById("id_search");
let typingTimer;
let doneTypingInterval = 500;

translate_input.addEventListener('keyup', () => {
    clearTimeout(typingTimer);
    if (translate_input.value) {
        typingTimer = setTimeout(doneTyping, doneTypingInterval);
    }
});

function doneTyping() {
    var gif = ['clear_dance.gif', 'fail_dance.gif', 'play_dance.gif'];
    const rand_gif = gif[Math.floor(Math.random() * gif.length)];
    $(".profile_border").hide();
    $(".loader_anim").attr("src", "/static/img/loading/" + rand_gif);
    $(".loader>.loader_anim").show();
    //translate_input.addEventListener("change", function(){
    data = new FormData();
    data.append('steam_id', translate_input.value);

    fetch('api/user/search', {
        method: 'POST',
        mode: 'cors',
        body: data
    })
    .then((response) => response.json())
    .then((result) => {
        $(".loader>.loader_anim").hide();
        $(".profile_border").show();
        result = result['result'];
        if(result != null){
            $(".profile_border .img").attr("src", result['avatarfull']);
            $(".preview_info .id").text(result['steamid']);
            $(".preview_info .name").text(result['personaname']);
        }
        else{
            //존재하지 않는 유저입니다.
        }
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}

$('.profile_border').on('click', function(){
    steam_id = $(".preview_info>.id")[0].innerHTML;
    window.location = "user/" + steam_id;
});
