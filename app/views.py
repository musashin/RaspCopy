
from app import app
from flask import render_template, request
import config
from file_system import FileSystem

file_system = dict()
file_system['source'] = FileSystem(config.source['directory'])
file_system['destination'] = FileSystem(config.destination['directory'])
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


@app.route('/mount', methods=['POST'])
def mount():

    print "mounting "+ request.form['side']



@app.route('/open_folder', methods=['POST'])
def open_folder():

    try:
        if request.form['folder'] == 'home':
            file_system[request.form['side']].select_home()
        elif request.form['folder'] == '..':
            file_system[request.form['side']].select_up()
        else:
            file_system[request.form['side']].select_subfolder(request.form['folder'])

        file_list = file_system[request.form['side']].get_file_list()

    except Exception as e:

        print conf[request.form['side']]['mount_command']
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
