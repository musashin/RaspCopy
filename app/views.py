
from app import app
from flask import render_template
from config import config
from os import listdir
from os.path import isfile, join, getsize, join
from utils.hurry import filesize

@app.route('/')
@app.route('/index')

def index():

    return render_template("main.html", files=get_file_list())


def get_file_list():

    files = [f for f in listdir(config.source_directory) if isfile(join(config.source_directory,f))]
    return [{'filename': f,
             'filesize_human': filesize.size(safe_file_size(config.source_directory, f)),
             'filesize_bytes': safe_file_size(config.source_directory, f)} for f in files]


def safe_file_size(path, file):

    try:
        size = getsize(join(path, file))
    except:
        size = 0

    return size

