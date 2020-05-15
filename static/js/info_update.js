function image_submit(){
    var ValidImageTypes = ["image/gif", "image/jpeg", "image/png"];
    var img = document.getElementById('image_upload').files[0];
    if(img == null){
        alert("이미지를 쳐넣어라");
        return;
    }
    if($.inArray(img.type, ValidImageTypes) < 0){
        alert("이미지만 쳐넣으라고");
        return;
    }
    if(img.size > 3 * 1024 * 1024){
        alert("이미지 크기가 너무 크다(<3MB)");
        return;
    }
    var formData = new FormData();
    formData.append("img", img);
   
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/djmax/handler");
    xhr.send(formData);
    xhr.onload=function(){
        console.log(xhr.responseText);
    }
      /*   

    $.post({
        url:'/djmax/handler',
        data:formData,
        success:function(evt){console.log(evt);}
    });
*/

    console.log("done");
}


$(document).ready(function(e) {
    //
});
