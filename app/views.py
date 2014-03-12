
from app import app
from flask import render_template,request
import config
from file_system import FileSystem

file_system= {}
file_system['source'] = FileSystem(config.source_directory)
file_system['destination'] = FileSystem(config.destination_directory)

@app.route('/')
@app.route('/index')
def index():

    return render_template("main.html")


@app.route('/open_folder', methods=['POST'])
def open_folder():

    file_system[request.form['side']].select_subfolder(request.form['folder'])

    return render_template("file_table.html", files=file_system[request.form['side']].get_file_list(),
                           side=request.form['side'],
                           folder_selector_class="folder_selector_"+request.form['side'],
                           file_selector_class="file_selector_"+request.form['side'])
