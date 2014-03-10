
from app import app
from flask import render_template,request
import config
from file_system import FileSystem

source_file_system = FileSystem(config.source_directory)

@app.route('/')
@app.route('/index')
def index():

    return render_template("main.html")


@app.route('/open_folder', methods=['POST'])
def open_folder():
    print request.form['side']
    if request.form['side'] == 'source':
        source_file_system.set_current_folder(request.form['folder'])
        print source_file_system.get_file_list()
        return render_template("file_table.html", files=source_file_system.get_file_list())