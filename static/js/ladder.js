// 소스 개떡인데 왜보세요
{% load static %}
$(document).ready(function(e) {
    var page = window.location.href;
    page = page.substr(page.lastIndexOf('/') + 1);
    hashed_value = page.split('#');
    if(hashed_value.length > 1){
        page = hashed_value[0];
        var _keys = document.getElementsByName('key');
        for(var i=0; i<_keys.length; i++){
            if(_keys[i].value == hashed_value[1]){
                _keys[i].checked = true
            }
        }
    }
    var major_tier = {
        9: "CHALLENGER",
        8: "GRAND MASTER",
        7: "MASTER",
        6: "DIAMOND",
        5: "PLATINUM",
        4: "GOLD",
        3: "SILVER",
        2: "BRONZE",
        1: "IRON"
    }
    var minor_tier = {
        4: "IV",
        3: "III",
        2: "II",
        1: "I",
        0: ""
    }
    var json_data = "";

    function set_html_by_key(key){
        var html_data = "";
        var key = location.hash.substring(1);
        if(key == "") key = '4';
        var j = json_data[key];
        for(var k in j){
            var user = j[k];
            var win_rate = (user['game_wins'] * 100 / user['game_count']).toFixed(2) + "%";
            var html_name = "<a href=\"https://steamcommunity.com/profiles/[U:1:" + user['id'] + "]\">" + user['name'] + "</a>"
            var tier = major_tier[user['flags']['major_tier']] + " " + minor_tier[user['flags']['minor_tier']];
            if(user['flags']['is_promotion_match'] == 1){
                tier += " (Promo.)";
            }
            var games = user['game_count'];
            games += " (<font color=\"blue\">" + user['game_wins'] + "</font>"
            games += "/<font color=\"red\">" + (user['game_count'] - user['game_wins']) + "</font>)"
            tdata = "<tr> \
                        <td class=\'test\'>" + user['rank'];
            if(page != 'beta'){
                tdata += " <font color=\'red\'>▲100</font>";
            }
            tdata += "</td>\
                        <td class=\'test\'>" + html_name + "</td>\
                        <td class=\'test\'>" + tier + "</td>\
                        <td class=\'test\'>" + user['lp'] + "</td>\
                        <td class=\'test\'>" + games + "</td>\
                        <td class=\'test\'>" + win_rate + "</td>\
                        <td class=\'test\'>" + user['accuracy'] + "%</td>\
                        <td class=\'test\'>" + user['maxcombo'] + '/' + user['perfect'] + "</td>\
                        <td class=\'test\'>" + (user['perfect']/(user['maxcombo'] + user['perfect'])*100).toFixed(2) + "%</td>\
                        <td class=\'test\'>0</td>\
            ";
            html_data += tdata;
        }
        var rank_html = document.getElementById('ranks').getElementsByTagName('tbody')[0];
        rank_html.innerHTML = html_data;
    }
    
    //$.getJSON("../json/ladder/"+ page+ ".json").done(function(j) {
    $.getJSON({% static 'json/pre.json' %}).done(function(j) {
        console.log(j);
        json_data = j;
        set_html_by_key('4');
        document.getElementById('updated_at').innerHTML = "Last Updated: "+ j['updated_at'];
        
    }).fail(function(jqXHR, status, e) {
        console.log(status, e);
    });

    $('input:radio[name="key"]').change(function(){
        var value = ($(this).val());
        window.location.hash = value;
        set_html_by_key(value);
    });
});
