function saveDoc() {
    $.post( saveurl, { content:editor.getCode(), filename:filename, project:project, modified:modified }, function(data){
        if( data.result == 'ok' ) {
            showStatus( data.status );
            modified = data.modified;
        } else {
            alert( data.status );
        }
    }, 'json' );
}

function showStatus( str ) {
    $("p#statusbar").html( str );
    setTimeout(function(){
        $("p#statusbar").html("ready for actions");
    }, 3000);
}

$(document).ready(function(){
    // check editor
    //editor.focus();

});
