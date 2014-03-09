
from app import app
from flask import render_template
import config
from file_system import FileSystem

source_file_system = FileSystem(config.source_directory)

@app.route('/')
@app.route('/index')
def index():

    return render_template("main.html", files=source_file_system.get_file_list())


