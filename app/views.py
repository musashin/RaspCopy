
from app import app
from flask import render_template, request, jsonify, flash
import config
from file_system import FileSystem, mount_device, copy_files, get_copy_status, delete_files, create_dir, unmount, delete_folder
from async_task import get_failed_job, get_background_status
import json
import time

file_system = dict()
file_system['source'] = FileSystem(config.source)
file_system['destination'] = FileSystem(config.destination)
conf = {'source': config.source, 'destination': config.destination }


@app.route('/')
@app.route('/index')
def index():

    return render_template("main.html")


@app.route('/select_file', methods=['POST'])
def select_file():

    return file_system[request.form['side']].add_selected_file(request.form['file_name'])

@app.route('/deselect_file', methods=['POST'])
def deselect_file():

    return file_system[request.form['side']].remove_selected_file(request.form['file_name'])

@app.route('/clear', methods=['POST'])
def clear_selection():

    return file_system[request.form['side']].clear_selected_file()

@app.route('/copy_status')
def get_copy_job_status():

    copy_status = get_copy_status()

    failed_jobs = get_failed_job()
    if failed_jobs:
        return jsonify(error=True,
                       complete=False,
                       message='Error Executing Operation \''+failed_jobs[0]+'\'',
                       error_details=str(failed_jobs[1]))
    elif copy_status:
        return jsonify(error=False,
                       complete=False,
                       copy_status=copy_status[0],
                       file_percent=copy_status[1],
                       overall_percent=copy_status[2])
    else:
        return jsonify(error=False, complete=True)


@app.route('/job_status')
def job_status():

    status = get_background_status(request.args['job_name'])

    if status:
        return jsonify(error=False,
                       complete=False,
                       status=status['status'])
    else:
        failed_jobs = get_failed_job()
        if failed_jobs:
            return jsonify(error=True,
                           complete=False,
                           message='Error Executing Operation \''+failed_jobs[0]+'\'',
                           error_details=str(failed_jobs[1]))
        else:
            return jsonify(error=False,
                           complete=True)


@app.route('/copy', methods=['POST'])
def copy():
    #TODO, prevent multiple operations!!
    try:
        copy_files(files_to_copy=file_system['source'].selected_files,
                   destination_folder=file_system['destination'].current_folder,
                   overwrite=True)
    except Exception as e:
        return jsonify(error=True, message='Copy Error', error_details=str(e))

    else:
        return jsonify(error=False)

@app.route('/selectedFiles', methods=['GET'])
def selected_files():
       return render_template("file_list.html",
                               files=file_system[request.args['side']].selected_files)

def get_piechart_data(side):

    side_disk_usage = file_system[side].get_statistics()

    used = side_disk_usage.used/1024.0/1024.0/1024.0
    free = side_disk_usage.free/1024.0/1024.0/1024.0

    if side == 'source':
        chart = [ { 'value': float("{0:.2f}".format(used)),
                        'color':"#F7464A",
                        'highlight': "#FF5A5E",
                        'label': "Used (GB)"
                    },
                    {
                        'value': float("{0:.2f}".format(free)),
                        'color': "#46BFBD",
                        'highlight': "#5AD3D1",
                        'label': "Free (GB)"
                    }
                ]
    else:

        copied = file_system['source'].get_selected_size_raw()/1024.0/1024.0/1024.0

        free -= copied
        if free<0: free = 0

        chart = [ { 'value': float("{0:.2f}".format(used)),
                        'color':"#F7464A",
                        'highlight': "#FF5A5E",
                        'label': "Used (GB)"
                    },
                    {
                        'value': float("{0:.2f}".format(free)),
                        'color': "#46BFBD",
                        'highlight': "#5AD3D1",
                        'label': "Free (GB)"
                    }
                    ,
                    {
                        'value': float("{0:.2f}".format(copied)),
                        'color': "#FDB45C",
                        'highlight': "#FFC870",
                        'label': "Copied (GB)"
                    }
                ]

    return chart

@app.route('/diskUsage', methods=['GET'])
def disk_usage():
        return json.dumps(get_piechart_data(request.args['side']))

@app.route('/currentFolderSize', methods=['GET'])
def currentFolderSize():
    return str(file_system[request.args['side']].get_current_folder_size())

@app.route('/create_dir',  methods=['GET', 'POST'])
def create_directory():
    if request.method == 'POST':
        #TODO use generic method!!
        try:

            create_dir(parent_directory=file_system[request.form['side']].current_folder,
                       name_of_new_directory=request.form['name'])
        except Exception as e:
            return jsonify(error=True, message='Could not create directory', error_details=str(e))
        else:
            return jsonify(error=False)
    else:
        return render_template("choose_dir_name.html")



@app.route('/deleteFiles', methods=['POST'])
def deleteFiles():
     #TODO, prevent multiple operations!!
    try:
        delete_files(files_to_delete=file_system[request.form['side']].selected_files)
    except Exception as e:
        return jsonify(error=True, message='Delete Error', error_details=str(e))
    else:
        return jsonify(error=False)

@app.route('/deleteFolder', methods=['POST'])
def deleteFolder():
     #TODO, prevent multiple operations!!
    try:
        delete_folder(folder_to_delete=file_system[request.form['side']].current_folder,
                      home_folder=file_system[request.form['side']].home_folder)
    except Exception as e:
        return jsonify(error=True, message='Delete Error', error_details=str(e))
    else:
        return jsonify(error=False)

@app.route('/unmount', methods=['POST'])
def unmount_method():
     #TODO, prevent multiple operations!!
    try:
        unmount(command=conf[request.form['side']]['unmount_command'], post_delay=1)
    except Exception as e:
        return jsonify(error=True, message='cannot eject', error_details=str(e))
    else:
        return jsonify(error=False)

@app.route('/mount', methods=['POST'])
def mount():

    try:

        mount_device(command=conf[request.form['side']]['mount_command'], post_delay=1)

        file_list = file_system[request.form['side']].get_file_list()

    except Exception as e:

        return render_template("file_error.html",
                               error_message=str(e),
                               side=request.form['side'],
                               action={'mount': "mount_"+request.form['side'],
                                       'refresh': "refresh_"+request.form['side']},
                               config=conf[request.form['side']])

    else:

        return render_template("file_table.html", files=file_list,
                               side=request.form['side'],
                               selector_classes={'folder': "folder_selector_"+request.form['side'],
                                                 'file': "file_selector_"+request.form['side']},
                               select_size_id="selected_size_id_"+request.form['side'],
                               current_folder=file_system[request.form['side']].get_current_folder_relative(),
                               filesBefore=file_system[request.form['side']].files_before(),
                               filesAfter=file_system[request.form['side']].files_after())

@app.route('/moveup', methods=['POST'])
def moveup():

    file_system[request.form['side']].moveup()

    return 'OK'



@app.route('/movedown', methods=['POST'])
def movedown():

    file_system[request.form['side']].movedown()

    return 'OK'


@app.route('/open_folder', methods=['POST'])
def open_folder():

    try:
        if request.form['folder'] == 'home':
            file_system[request.form['side']].select_home()
        elif request.form['folder'] == '..':
            file_system[request.form['side']].select_up()
        elif not request.form['folder']:
            file_system[request.form['side']].select_subfolder(file_system[request.form['side']].current_folder)
        else:
            file_system[request.form['side']].select_subfolder(request.form['folder'])

        file_list = file_system[request.form['side']].get_file_list()

    except Exception as e:

        return render_template("file_error.html",
                               error_message=str(e),
                               side=request.form['side'],
                               action={'mount': "mount_"+request.form['side'],
                                       'refresh': "refresh_"+request.form['side']},
                               config=conf[request.form['side']])

    else:

        return render_template("file_table.html", files=file_list,
                               side=request.form['side'],
                               selector_classes={'folder': "folder_selector_"+request.form['side'],
                                                 'file': "file_selector_"+request.form['side']},
                               select_size_id="selected_size_id_"+request.form['side'],
                               current_folder=file_system[request.form['side']].get_current_folder_relative(),
                               config=conf[request.form['side']],
                               filesBefore=file_system[request.form['side']].files_before(),
                               filesAfter=file_system[request.form['side']].files_after())
