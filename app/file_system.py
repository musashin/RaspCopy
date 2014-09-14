__author__ = 'Nicolas'


from os import listdir, walk, sep, stat
from os.path import isfile, getsize, join, normpath
from utils.hurry import filesize
from async_task import async, get_status
import subprocess

class FileSystem:

    def __init__(self, config):

        self.home_folder = normpath(config['directory'])
        self.current_folder = self.home_folder
        self.selected_files = []
        self.config = config

    def get_selected_size(self):
        return filesize.size(sum([f['size'] for f in self.selected_files]))

    def add_selected_file(self, filename):

        self.selected_files.append({'filename': filename, 'folder': self.current_folder,
                                    'size':  self.safe_file_size(self.current_folder, filename)})

        return self.get_selected_size()

    def remove_selected_file(self, filename):

        self.selected_files = [f for f in self.selected_files
                               if not(f['filename'] == filename and f['folder'] == self.current_folder)]

        return self.get_selected_size()

    def is_selected(self, filename, folder):

        return any(f['filename'] == filename and f['folder'] == folder for f in self.selected_files)

    def select_home(self):
         self.current_folder = self.home_folder

    def select_up(self):

        if len(self.current_folder) > len(self.home_folder):
            self.current_folder = sep.join(self.current_folder.split(sep)[0:-1])

    def select_subfolder(self, folder):

        if folder == "root":
            self.current_folder = self.home_folder
        else:
            self.current_folder = join(self.current_folder, folder)

    def get_file_list(self):

        file_list = [{'filename': f,
                      'filesize_human': filesize.size(self.safe_file_size(self.current_folder, f)),
                      'filesize_bytes': self.safe_file_size(self.current_folder, f),
                      'isfile':  isfile(join(self.current_folder, f)),
                      'isselected':  self.is_selected(f, self.current_folder)}
                     for f in listdir(self.current_folder)]

        if len(self.current_folder) > len(self.home_folder):
            file_list.insert(0, {'filename': '..',
                                 'filesize_human': '-',
                                 'filesize_bytes': 0,
                                 'isfile':  False,
                                 'isselected':  False})

        return file_list

    def get_folder_size(self, start_path='.'):
        total_size = 0
        for dirpath, dirnames, filenames in walk(start_path):
            for f in filenames:
                fp = join(dirpath, f)
                total_size += getsize(fp)
        return total_size

    def get_current_folder_relative(self):

        return sep.join(self.current_folder.split(sep)[len(self.home_folder.split(sep))-1:])

    def safe_file_size(self, path, current_file):
        try:
            element = join(path, current_file)
            if isfile(element):
                size = getsize(element)
            else:
                size = self.get_folder_size(element)

        except:
            size = 0

        return size


@async
def mount_device(command, post_delay=0, execution_thread=None):

    if execution_thread:
        execution_thread.report_status(status='mounting',
                                       percent='0')

    subprocess.call(command)
    time.sleep(post_delay)
    execution_thread.report_status(status='mounted',
                                   percent='100')
    if execution_thread:
        execution_thread.remove_from_jobs()

@async
def umount_device(command, post_delay=0, execution_thread=None):

    if execution_thread:
        execution_thread.report_status(status='mounting',
                                       percent='0')

    subprocess.call(command)
    time.sleep(post_delay)
    execution_thread.report_status(status='mounted',
                                   percent='100')
    if execution_thread:
        execution_thread.remove_from_jobs()

block_size = 128 #16384

@async
def copy_file(source_file, destination_file, overwrite, execution_thread=None):

    if execution_thread:
        execution_thread.report_status(status='starting file copy',
                                       percent='0')

    if not overwrite:
        if isfile(destination_file):
            raise IOError("File exists, not overwriting")

    with open(source_file, "rb") as src, open(destination_file, "wb") as dest:

        src_size = stat(source_file).st_size

        cur_block_pos = 0  # a running total of current position

        while True:
            cur_block = src.read(block_size)

            cur_block_pos += block_size

            if execution_thread:
                execution_thread.report_status(status='copy in progress',
                                               percent=str(float(cur_block_pos)/float(src_size)*100.0))

            if not cur_block:
                break
            else:
                dest.write(cur_block)

    if execution_thread:
        execution_thread.report_status(status='file copy complete',
                                       percent='100')
        execution_thread.remove_from_jobs()

if __name__ == '__main__':

    import config
    import time

    #copy_file(source_file='C:\\temp\\source\\output.txt', destination_file='C:\\temp\\dest\\output.txt', overwrite=True)

    copy_file(source_file='C:\\temp\\source\\wildlife.wmv', destination_file='C:\\temp\\dest\\output.txt', overwrite=True)

    #mount_device(command=config.source['mount_command'], post_delay=10)

    #umount_device(command=config.source['unmount_command'], post_delay=10)

    while True:
        time.sleep(0.5)
        print get_status('copy_file')

