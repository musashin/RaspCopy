 var gCurrentSide = 'source'
    var gStatusRefreshPeriodMs = 1000;

    function refresh(side){

        if(side)
        {
            set_folder(side,'');
        }
        else
        {
            set_folder('source','')
            set_folder('destination','')
        }
    }

    function set_folder(side,folder){

        $("#"+side+"_file_table").load('/open_folder',{side: side, folder: folder});
    }

    function select_file(side,file_name){

        $("#selected_size_id_"+side).load('/select_file',{side: side, file_name: file_name});
    }

    function deselect_file(side,file_name){

        $("#selected_size_id_"+side).load('/deselect_file',{side: side, file_name: file_name});

    }

    function clear_selected_files(side){

     $("#selected_size_id_"+side).load('/clear',{side: side});

 }

 function mount_file_system(side){

    $.post("/mount",
    {
        side: side
    },function(data){
        if(data.error){
            $("#errorDialogMessage").html("<p>"+data.message+"</p>");
            $("#errorDialogMessageDetails").text(data.error_details);

            $('#errorDialog').modal('show');
        }
        else {

            setTimeout(function() { indicate_action_in_progress('mount',side,true)}, gStatusRefreshPeriodMs);
        }
    });

}

function moveup(side){

  $.post("/moveup",
  {
    side: side
},function(data,status){
    refresh(side);
});
}

function movedown(side){

 $.post("/movedown",
 {
    side: side
},function(data,status){
    refresh(side);
});

}

function unmount_file_system(side){

    $.post("/unmount",
    {
        side: side
    },function(data){
        if(data.error){
            $("#errorDialogMessage").html("<p>"+data.message+"</p>");
            $("#errorDialogMessageDetails").text(data.error_details);

            $('#errorDialog').modal('show');
        }
        else {

            setTimeout(function() { indicate_action_in_progress('unmount',side,true)}, gStatusRefreshPeriodMs);
        }
    });
}

var copy_job_status_str = ''
function update_copy_status()
{

    $.getJSON("/copy_status",function(result){

        if(result.error){

            $('#StatusPane').collapse('hide');

            set_folder('destination','')

            $("#errorDialogMessage").html("<p>"+result.message+"</p>");
            $("#errorDialogMessageDetails").text(result.error_details);

            $('#errorDialog').modal('show');
        }
        else if(!result.complete){

            $('#StatusPane').collapse('show');

            $('#fileCopyProgress').css('width', result.file_percent+'%').attr('aria-valuenow', result.file_percent);

            $('#fileCopyProgress').text(result.copy_status + ' : ' + result.file_percent.toString()+'%');

            $('#overallCopyProgress').css('width', result.overall_percent+'%').attr('aria-valuenow', result.overall_percent);

            $('#overallCopyProgress').text('Overall Status: ' + result.overall_percent.toString()+'%');

            if(copy_job_status_str != result.copy_status)
            {
                refresh('destination');
                copy_job_status_str = result.copy_status;
            }


            setTimeout('update_copy_status()', gStatusRefreshPeriodMs);
        }
        else {

            $('#StatusPane').collapse('hide');

            set_folder('destination','')
        }
    })

}

function createDirectory(side){

    $.post("/create_dir",{'name': $('#directory_name').val(),'side': side},function(data ){

        if(data.error){
            $("#errorDialogMessage").html("<p>"+data.message+"</p>");
            $("#errorDialogMessageDetails").text(data.error_details);

            $('#errorDialog').modal('show');
        }
        else {

            setTimeout(function() { indicate_action_in_progress('create_dir',side,true)}, gStatusRefreshPeriodMs);
        }

    });
}

function deleteCurrentFolder(side)
{
   $.post("/deleteFolder",{side: side},function(data ){

    if(data.error){
        $("#errorDialogMessage").html("<p>"+data.message+"</p>");
        $("#errorDialogMessageDetails").text(data.error_details);

        $('#errorDialog').modal('show');
    }
    else {

        set_folder(side,'..')

        setTimeout(function() { indicate_action_in_progress('delete_folder',side,true)}, gStatusRefreshPeriodMs);
    }

});
}

function deleteSelectedFiles(side){

    $.post("/deleteFiles",{side: side},function(data ){

        if(data.error){
            $("#errorDialogMessage").html("<p>"+data.message+"</p>");
            $("#errorDialogMessageDetails").text(data.error_details);

            $('#errorDialog').modal('show');
        }
        else {

            setTimeout(function() { indicate_action_in_progress('delete_files',side,true,function(){clear_selected_files(side);})}, gStatusRefreshPeriodMs);
        }

    });
}

function animate(turnOn, baseID, side)
{
    spinnerID = baseID + '_spin_' + side;
    iconID = baseID + '_icon_' + side;

    if(turnOn)
    {
        $('#'+spinnerID).show();
        $('#'+iconID).hide();
    }
    else
    {
        $('#'+spinnerID).hide();
        $('#'+iconID).show();
    }
}


var background_job_status_str = ''
function indicate_action_in_progress(background_job_name,side,start,finish_function)
{


  $.getJSON("/job_status",{job_name: background_job_name}, function(result){

    if(result.error){

        $("#errorDialogMessage").html("<p>"+result.message+"</p>");
        $("#errorDialogMessageDetails").text(result.error_details);

        $('#errorDialog').modal('show');

    }
    else if(!result.complete){

        if(result.status != background_job_status_str)
        {
            set_folder(side,'');
            background_job_status_str = result.status
        }

        animate(true, background_job_name, side);


        setTimeout(function() { indicate_action_in_progress(background_job_name,side,false,finish_function)}, gStatusRefreshPeriodMs);
    }
    else {

       animate(false, background_job_name, side);
       set_folder(side,'')


       if(finish_function)
       {
        finish_function();
    }
}
})
}