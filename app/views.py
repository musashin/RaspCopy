
from app import app
from flask import render_template, request, jsonify
import config
from file_system import FileSystem, mount, copy_files, get_copy_status, delete_files, create_dir, unmount, delete_folder
from async_task import get_failed_job, get_background_status
import json

file_system = dict()
file_system['source'] = FileSystem(config.source)
file_system['destination'] = FileSystem(config.destination)
conf = {'source': config.source, 'destination': config.destination }


@app.route('/')
@app.route('/index')
def index():
    """
        brief: return the index page.
    """
    return render_template("main.html")


@app.route('/select_file', methods=['POST'])
def select_file():
    """
        brief: Select a file in the side current folder.
    """
    return file_system[request.form['side']].add_selected_file(request.form['file_name'])

@app.route('/deselect_file', methods=['POST'])
def deselect_file():
    """
        brief: Deselect a file in the side current folder.
    """
    return file_system[request.form['side']].remove_selected_file(request.form['file_name'])


@app.route('/clear', methods=['POST'])
def clear_selection():
    """
        brief: Clear all selected files a file system side.
    """

    return file_system[request.form['side']].clear_selected_file()

@app.route('/copy_status')
def get_copy_job_status():
    """
        brief: obtain the status of a file copy thread.

        details:
            3 possibilities:
            - There are no copy thread active: the function returns
            a JSON with that indicates the copy job is done.
            - There is a failed copy job in the queue: the function
            return a JSON with a failed indication and error details.
            - There is a copy job on going. The function returns details
            in a JSON file, including:
                - string indicating the current operation.
                - a progress (string in %) for the current file copy.
                - a progress (string in %) for the overall copy job.
    """

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
def get_job_status():

    """
        brief: obtain a status for a specific job.

        details:
            3 possibilities:
            - There are no background thread active: the function returns
            a JSON with that indicates the  job is done.
            - There is a failed job for the queried name in the queue: the function
            return a JSON with a failed indication and error details.
            - There is a copy job on going. The function returns details
            in a JSON file, including:
                - string indicating the current operation.
                - a progress (string in %) for the current file copy.
                - a progress (string in %) for the overall copy job.
    """
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


def execute_with_error_handling(method_to_execute, error_string):
    """
        brief: execute a method and return a json file with its result

        details
            If them method succeeds, the JSON simply contains error with the false
            value. If it fails, it also contains an error message and additional
            details (the later corresponds to the exception message).
    """
    try:
        method_to_execute()
    except Exception as e:
        return jsonify(error=True, message=error_string, error_details=str(e))
    else:
        return jsonify(error=False)


@app.route('/copy', methods=['POST'])
def copy_selected_files_request():
    """
        brief: request to copy the selected files to the destination folder.

    """
    try:
        copy_files(files_to_copy=file_system['source'].selected_files,
                   destination_folder=file_system['destination'].current_folder,
                   overwrite=True)
    except Exception as e:
        return jsonify(error=True, message='Copy Error', error_details=str(e))

    else:
        return jsonify(error=False)

@app.route('/selectedFiles', methods=['GET'])
def get_selected_files():
    """
        brief: get an HTML file containing a list of the selected files
        on a given side.

    """
    return render_template("file_list.html",
                           files=file_system[request.args['side']].selected_files)

def get_piechart_data(side):
    """
        brief: return a list of dictionary with the data required
        to populate a chart.js piechart.

        details:
        If the selected side is source, there are 2 data elements:
        - the used space in red.
        - the free space in green.

        If the file system is 'destination' there is an additional
        entry (in orange) corresponding to the total size of the selected
        files in the 'source' file system (those who will be copied by the next
        copy request.)

    """

    side_disk_usage = file_system[side].get_statistics()

    used = side_disk_usage.used/1024.0/1024.0/1024.0
    free = side_disk_usage.free/1024.0/1024.0/1024.0

    if side == 'source':
        chart = [{'value': float("{0:.2f}".format(used)),
                  'color': "#F7464A",
                  'highlight': "#FF5A5E",
                  'label': "Used (GB)"},
                 {'value': float("{0:.2f}".format(free)),
                  'color': "#46BFBD",
                  'highlight': "#5AD3D1",
                  'label': "Free (GB)"}]
    else:

        copied = file_system['source'].get_selected_size_raw()/1024.0/1024.0/1024.0

        free -= copied
        if free < 0: free = 0

        chart = [{'value': float("{0:.2f}".format(used)),
                  'color': "#F7464A",
                  'highlight': "#FF5A5E",
                  'label': "Used (GB)"},
                 {'value': float("{0:.2f}".format(free)),
                  'color': "#46BFBD",
                  'highlight': "#5AD3D1",
                  'label': "Free (GB)"},
                 {'value': float("{0:.2f}".format(copied)),
                  'color': "#FDB45C",
                  'highlight': "#FFC870",
                  'label': "Copied (GB)"}]

    return chart

@app.route('/diskUsage', methods=['GET'])
def disk_usage():
    """
    brief:  Return (in a JSON file),the data reguired to populate
    a chart.js pie chart.

    handled methods:
        - GET: get the size of the current folder for the selected size.
    """
    return json.dumps(get_piechart_data(request.args['side']))

@app.route('/currentFolderSize', methods=['GET'])
def get_current_folder_size():
    """
    brief:  Get a string, representing the size (with units) of the current folder.

    handled methods:
        - GET: get the size of the current folder for the selected size.
    """
    return str(file_system[request.args['side']].get_current_folder_size())

@app.route('/create_dir',  methods=['GET', 'POST'])
def create_directory_request():
    """
    brief:  Create a directory

    handled methods:
        - POST: launch a directory creation background job. Both name and sides are parameters
        of the request.
        - GET: populate a directory name picker dialog box.
    """
    if request.method == 'POST':
        side = request.form['side']
        return execute_with_error_handling(lambda:  create_dir(parent_directory=file_system[side].current_folder,
                                                               name_of_new_directory=request.form['name']),
                                           'Could not create directory')
    else:
        return render_template("choose_dir_name.html")

@app.route('/deleteFiles', methods=['POST'])
def delete_files_request():
    """
    brief:  Delete the files currently selected

    handled methods:
        - POST: launch a delete files background job. Sides is a parameter
        of the request.
    """
    side = request.form['side']
    return execute_with_error_handling(lambda:  delete_files(files_to_delete=file_system[side].selected_files),
                                       'Delete Error')


@app.route('/deleteFolder', methods=['POST'])
def delete_folder_request():
    """
    brief:  Delete the current folder

    handled methods:
        - POST: launch a delete folder background job on the selected side current folder. Side is a parameter
        of the request.
    """
    side = request.form['side']
    return execute_with_error_handling(lambda:  delete_folder(folder_to_delete=file_system[side].current_folder,
                                                              home_folder=file_system[side].home_folder),
                                       'Delete Error')

@app.route('/unmount', methods=['POST'])
def unmount_request():
    """
    brief:  Launch the unmount background job

    handled methods:
        - POST: launch an unmount background job (the actual system command is selected
        in the configuration file). Side is a parameter of the request.
    """
    side = request.form['side']
    return execute_with_error_handling(lambda:  unmount(command=conf[side]['unmount_command'], post_delay=1),
                                       'Delete Error')

@app.route('/mount', methods=['POST'])
def mount_request():
    """
    brief:  Launch the mount background job

    handled methods:
        - POST: launch an mount background job (the actual system command is selected
        in the configuration file). Side is a parameter of the request.
    """
    side = request.form['side']
    return execute_with_error_handling(lambda: mount(command=conf[side]['mount_command'], post_delay=1),
                                       'Delete Error')

@app.route('/prevfiles', methods=['POST'])
def previous_files_request():
    """
    brief:  Select the previous files in the current view.

    handled methods:
        - POST: Select the previous files in the current view. Side is a parameter of the request.
    """

    file_system[request.form['side']].moveup()

    return 'OK'

@app.route('/nextfiles', methods=['POST'])
def next_files_request():
    """
    brief:  Select the next files in the current view.

    handled methods:
        - POST: Select the next files in the current view. Side is a parameter of the request.
    """
    file_system[request.form['side']].movedown()

    return 'OK'


@app.route('/open_folder', methods=['POST'])
def open_folder_request():
    """
    brief:  open a folder and return a file list (in HTML) representing a portion
            of the files selected in the current folder.

    details
        The folder opened will vary with the 'folder' parameter:
            -  home : will load the home/root folder for the selected side.
            -  .. : will select folder immediately higher
            -  x : will open subfolder 'x'

            If the folder parameter is not specified, the current folder is returned
            again (useful for refresh!)

    handled methods:
        - POST: Select the next files in the current view. Side and folder are parameters
         of the request.
    """

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
                               action={'refresh': "refresh_"+request.form['side']},
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
