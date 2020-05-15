$(document).ready(function(e) {

    var j = null;
    var editions = {'resp':'Respect', 
    				'dmp1':'Portable 1', 
    				'dmp2':'Portable 2', 
    				'tril':'Trilogy',
    				'glty':'Guilty Gear', 
    				'czqi':'Clazziquai' }

    var edtkeys = Object.keys(editions);
    $.getJSON("songs.json").done(function(j) {
        var j = j;
        var last_ch = $('#song_table tbody:last');
        for(var k in j){
        	//disk = 
        	//var ecolor = j[k]['edtion']
        	var ecolor = edtkeys[j[k]['edtion']];
        	var title = j[k]['title'];
        	var composer = j[k]['comp'];
        	//var edition = editions[ecolor];
        	var edition = editions[ edtkeys[ j[k]['edtion'] ] ];
        	var nm = j[k]['6nm'];
        	var hd = j[k]['6hd'];
        	var mx = j[k]['6mx'];

        	console.log(j[k]['ed'])

        	console.log(j[k]);

        	tdata = "<tr> \
						<td class=\'disk\'></td> \
						<td class=\'ecolor "+ecolor+"\'></td> \
						<td class=\'title\'>"+title+"</td> \
						<td class=\'composer\'>"+composer+"</td> \
						<td class=\'edition\'>"+edition+"</td> \
						<td class=\'nm\'>"+nm+"</td> \
						<td class=\'hd\'>"+hd+"</td> \
						<td class=\'mx\'>"+mx+"</td> \
					</tr>";
			console.log(tdata);
        	last_ch.append(tdata);
        }
    }).fail(function(jqXHR, status, e) {
        console.log(status, e);
    });
    
});
