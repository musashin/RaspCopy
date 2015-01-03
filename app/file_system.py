__author__ = 'Nicolas'


from os import listdir, walk, sep, stat
from os.path import isfile, getsize, join, normpath, basename
from utils.hurry import filesize
from async_task import async, get_background_status
import subprocess

copy_in_progress = False
copy_percent = 0


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

    print command
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

def copy_file(source_file, destination_file, overwrite, report_delegate=None):

    if report_delegate:
        report_delegate(status='starting file copy',
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

            if report_delegate:
                report_delegate(status='copying' + basename(source_file),
                                percent=round(float(cur_block_pos)/float(src_size)*100.0))

            if not cur_block:
                break
            else:
                dest.write(cur_block)


@async
def copy_folder(source_folder, destination_folder, overwrite, execution_thread=None):

    all_files_in_source = [f for f in listdir(source_folder) if isfile(join(source_folder, f))]

    for file_to_copy in all_files_in_source:
        copy_file(source_file=join(source_folder, file_to_copy),
                  destination_file=join(destination_folder, file_to_copy),
                  overwrite=overwrite,
                  report_delegate=lambda status, percent: execution_thread.report_status(status, percent))

    if execution_thread:
        execution_thread.remove_from_jobs()

@async
def copy_files(files_to_copy, destination_folder, overwrite, execution_thread=None):

    global copy_in_progress, copy_percent

    copy_in_progress = True

    file_count = 0

    try:
        for file_to_copy in files_to_copy:

            file_count += 1

            copy_percent = round(float(file_count)/float(len(files_to_copy))*100.0)

            print file_count

            print len(files_to_copy)

            print copy_percent

            copy_file(source_file=join(file_to_copy['folder'], file_to_copy['filename']),
                      destination_file=join(destination_folder, file_to_copy['filename']),
                      overwrite=overwrite,
                      report_delegate=lambda status, percent: execution_thread.report_status(status, percent))

    finally:
        if execution_thread:
            copy_in_progress = False
            execution_thread.remove_from_jobs()

def get_copy_status():

    if copy_in_progress:
        file_copy_status = get_background_status('copy_files')
        return file_copy_status['status'], file_copy_status['percent'], copy_percent
    else:
        return None


if __name__ == '__main__':

    import config
    import time

    #copy_file(source_file='C:\\temp\\source\\output.txt', destination_file='C:\\temp\\dest\\output.txt', overwrite=True)

    #copy_file(source_file='C:\\temp\\source\\wildlife.wmv', destination_file='C:\\temp\\dest\\output.txt', overwrite=True)


    #copy_folder(source_folder='C:\\temp\\source\\',
    #            destination_folder='C:\\temp\\dest\\',
    #            overwrite=True)

    mount_device(command=config.destination['mount_command'], post_delay=10)

    #umount_device(command=config.source['unmount_command'], post_delay=10)

    while True:
        time.sleep(0.5)
        print get_background_status('copy_folder')

