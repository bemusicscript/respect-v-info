$(".user_info").click(function(){
    var user_id = $(this).attr('user_id');
    var button = $(this).attr('button');
    get_user_history(user_id, button);
});

$(".refresh_button").click(function(){
    user_update();
})

function user_update(){
    $(".refresh_button").prop("disabled", true);
    $("body").css("cursor", "wait");
    url = "/api/user/update";
    $.getJSON(url)
        .done(function (data) {
            if(data['status'] == true){
                document.location.reload();
            }
            else{
                alert("갱신 요청에 실패했습니다. 갱신 요청은 마지막 갱신 시각으로부터 최소 10분이 지난 후 가능합니다.");
            }
            $(".refresh_button").prop("disabled", false);
            $("body").css("cursor", "auto");
        })
        .fail(function (jqXHR, textStatus, err) {
            console.log(err);
        })
        .always(function () { });
}

function get_user_history(user_id, button){
    $(".no_data").hide();
    $(".loader_anim").show();
    $(".statistics").show();
    url = "/api/user/history/" + user_id + '/' + button;
    $.getJSON(url)
        .done(function (data) {
            draw_rank_value(data['rank']);
            draw_user_histories(data['history']);
            draw_statistics(data['statistics']);
        })
        .fail(function (jqXHR, textStatus, err) {
            $(".no_data").show();
            $('.history_test').text('Error: ' + err);
        })
        .always(function () { $(".loader_anim").hide(); });
}

function draw_rank_value(rank) {
    $(".header_profile>.rank").text("Rank #" + rank['user_rank']);
    $(".header_profile>.sub_script").text("/" + rank['user_count']);
}

function draw_user_histories(data){
    accordion_html = "";
    for(i in data){
        var index_id = data[i]['_id'];
        var u = data[i]['_source'];
        accordion_html += write_accordion(index_id, u);
    }
    histories_obj = document.getElementById('user_histories');
    histories_obj.innerHTML = accordion_html;

    document.getElementById('history_' + index_id);

}

function get_wdl_result(user_score, opponent_score){
    if(user_score > opponent_score){
        return "Win"
    }
    else if(user_score == opponent_score){
        return "Draw"
    }
    else{
        return "Lose"
    }
}

function write_history_table(user){
    inner_table_html = "<tr>\n" +
        "<td class=\"round\">{}</td>\n" +
        "<td class=\"song\"><img src=\"/static/img/song/{}.png\" width='50px' height='50px'/></td>\n" +
        "<td class=\"p1_score\">{} ({}%)</td>\n" +
        "<td class=\"p2_score\">{} ({}%)</td>\n" +
        "<td class=\"win_lose\">{}</td>\n" +
        "</tr>\n";

    inner_rows = "";
    for(i=0; i<user.match.song.length; i++){
        var round = i+1;
        inner_rows += inner_table_html.format(
            round,
            user.match.song[i],
            user.match.user_score[i],
            user.match.user_accuracy[i],
            user.match.opponent_score[i],
            user.match.opponent_accuracy[i],
            get_wdl_result(user.match.user_score[i], user.match.opponent_score[i])
        );
    }
    if(user.hard_match){
        inner_rows += inner_table_html.format(
            3,
            user.hard_match.song,
            user.hard_match.user_score,
            user.hard_match.user_accuracy,
            user.hard_match.opponent_score,
            user.hard_match.opponent_accuracy,
            get_wdl_result(user.hard_match.user_score, user.hard_match.opponent_score)
        );
    }


    table_base = "<table class=\"display table table-responsive history_list\" id=\"songs\" style=\"width:100%\">\n" +
        "                            <thead>\n" +
        "                                <tr>\n" +
        "                                    <th class=\"round\">Round</th>\n" +
        "                                    <th class=\"song\">Song</th>\n" +
        "                                    <th class=\"p1_score\">User Score</th>\n" +
        "                                    <th class=\"p2_score\">Opponent Score</th>\n" +
        "                                    <th class=\"win_lose\">W/L</th>\n" +
        "                                </tr>\n" +
        "                            </thead>\n" +
        "                            <tbody>\n" +
        "                               {}\n" +
        "                            </tbody>\n" +
        "                        </table>";

    table_base = table_base.format(inner_rows);

    return table_base


}

function write_accordion(index_id, user){
    history_table = write_history_table(user);
    html = `<div id="accordion" role="tablist" aria-multiselectable="true">
        <div class="card" style="border-radius:0; border: 0;">
            <div class="user_history">
                <div class="card-header" role="tab" id="history_panel" style="background-color: {}; border-radius:0;">
                    <h5 class="mb-0">
                        <a class="collapsed title" data-toggle="collapse" data-parent="#accordion" href="#history_{}">
                            <table style="width:100%;">
                                <tr>
                                    <td width=60><b>{}</b></td>
                                    <td>{} vs {}</td>
                                    <td align=right>{}</td>
                                    <td width=80 align=right><b>{} LP</b></td>
                                    </td>
                                </tr>
                            </table>
                        </a>
                    </h5>
                </div>
                <div id="history_{}" class="collapse" role="tabpanel">
                {}
                </div>
            </div>
        </div>
    </div>`
    //format order: bg-color, win/lose, datetime, my_name, opt_name, lp
    formed = html.format(
            (user.win ? "#c9e9f9" : "#e9d9d9"),
            index_id,
            (user.win ? "WIN" : "LOSE"),
            user.user_name,
            user.opponent_name,
            user.datetime,
            (user.gain_lp >= 1 ? '+' + user.gain_lp : user.gain_lp),
            index_id,
            history_table
    );
    return formed;
}

function draw_statistics(stat){
    _draw_total_game_stat(stat);
    _draw_total_normal_round(stat);
    _draw_total_hard_round(stat);
    _draw_pp_rate(stat);
}

function _draw_total_game_stat(stat){
    var total_game_stat = echarts.init(document.getElementById('total_game_stat'));
    var option = {
        title: { text: 'Total Game Stat', subtext: '진행된 전체 래더 승/패 구분', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c} ({d}%)' },
        series: [
            {
                name: 'W/L Type',
                type: 'pie',
                radius: '60%',
                center: ['50%', '50%'],
                data: [
                    {value: stat.total.win, name: 'Win', itemStyle: {color: '#3c9cff'} },
                    {value: stat.total.lose, name: 'Lose', itemStyle: {color: '#ff4645'} },
                ],
                label : { show : false }, labelLine : { show : false },
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }
        ]
    };
    total_game_stat.setOption(option);
}

function _draw_total_normal_round(stat){
    var total_normal_round = echarts.init(document.getElementById('total_normal_round'));
    var option = {
        title: { text: 'Total Normal Games', subtext: '1, 2 라운드의 승/무/패 구분', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c} ({d}%)' },
        series: [
            {
                name: 'W/D/L Type',
                type: 'pie',
                radius: '60%',
                center: ['50%', '50%'],
                data: [
                    {value: stat.round.normal.wl.win, name: 'Win', itemStyle: {color: '#3c9cff'} },
                    {value: stat.round.normal.wl.draw, name: 'Draw', itemStyle: {color: '#ffc029'} },
                    {value: stat.round.normal.wl.lose, name: 'Lose', itemStyle: {color: '#ff4645'} },
                ],
                label : { show : false }, labelLine : { show : false },
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }
        ]
    };
    total_normal_round.setOption(option);
}

function _draw_total_hard_round(stat){
    var total_hard_round = echarts.init(document.getElementById('total_hard_round'));
    var option = {
        title: { text: 'Total Hard Games', subtext: 'Hard Judgement 승/패 구분', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c} ({d}%)' },
        series: [
            {
                name: 'W/L Type',
                type: 'pie',
                radius: '60%',
                center: ['50%', '50%'],
                data: [
                    {value: stat.round.hard.wl.win, name: 'Win', itemStyle: {color: '#3c9cff'} },
                    {value: stat.round.hard.wl.lose, name: 'Lose', itemStyle: {color: '#ff4645'} },
                ],
                label : { show : false }, labelLine : { show : false },
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }
        ]
    };
    total_hard_round.setOption(option);
}

function _draw_pp_rate(stat){
    //임시 방편. 고쳐야함 나중에.. 도저히 왜 normal game이 -값이 나올수있는지? 이거 그냥 크롤러 데몬 문제같음. 나 병신인가 ㅋㅋ
    if(stat.total.pfn.normal < 0) {
        normal_game = 0
    }
    else{
        normal_game = stat.total.pfn.normal;
    }

    var pp_rate = echarts.init(document.getElementById('pp_rate'));
    var option = {
        title: { text: 'Clear Type', subtext: '전체 라운드를 기준으로 PP, MC 구분', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{a} <br/>{b} : {c} ({d}%)' },
        series: [
            {
                name: 'Accuracy Type',
                type: 'pie',
                radius: '60%',
                center: ['50%', '50%'],
                data: [
                    {value: stat.total.pfn.perfect, name: 'Perfect', itemStyle: {color: '#7f17ff'} },
                    {value: stat.total.pfn.maxcombo, name: 'Maxcombo', itemStyle: {color: '#60a8ff'} },
                    {value: normal_game, name: 'Normal', itemStyle: {color: '#ffc029'} },
                ],
                label : { show : false }, labelLine : { show : false },
                emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
            }
        ]
    };
    pp_rate.setOption(option);
}



String.prototype.format = function () {
  var i = 0, args = arguments;
  return this.replace(/{}/g, function () {
    return typeof args[i] != 'undefined' ? args[i++] : '';
  });
};
