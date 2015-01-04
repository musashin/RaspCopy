
from app import app
from flask import render_template, request, jsonify, flash
import config
from file_system import FileSystem, mount_device, copy_files, get_copy_status

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

@app.route('/copy_status')
def get_current_user():

    copy_status = get_copy_status()

    if copy_status:
        return jsonify(complete=False,
                       copy_status=copy_status[0],
                       file_percent=copy_status[1],
                       overall_percent=copy_status[2])
    else:
        return jsonify(complete=True)

@app.route('/copy', methods=['POST'])
def copy():

    try:
        copy_files(files_to_copy=file_system['source'].selected_files,
                   destination_folder = file_system['destination'].current_folder,
                   overwrite = True)

    except Exception as e:
        return jsonify(error=True, message='Copy Error', error_details=str(e))

    else:
        return jsonify(error=False)

@app.route('/mount', methods=['POST'])
def mount():

    try:

        print conf[request.form['side']]['mount_command']
        mount_device(command=conf[request.form['side']]['mount_command'], post_delay=10)

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
                               current_folder=file_system[request.form['side']].get_current_folder_relative())



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
                               current_folder=file_system[request.form['side']].get_current_folder_relative())
