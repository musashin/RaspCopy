"""
    This provides all the necessary function to display, navigate,
    and get statistics, on a file system.
    Additionnally, this provides methods to:
     - maintain a lis tof selected files
     - create folder
     - mount/unmount
     - copy files
     - delete files or folders
"""

from __future__ import division
from os import listdir, walk, sep, stat, remove, mkdir, rmdir
from os.path import isfile, getsize, join, normpath, basename
from utils.hurry import filesize
from async_task import async, get_background_status
import subprocess
import psutil
import time

copy_in_progress = False    # true when a file copy operation is in progress
copy_percent = 0
_MAX_ENTRIES_IN_LIST = 6    # max entry in file system file list view
_JUMP = 2                   #
_FILE_BLOCK_SIZE = 16384    # file block size (used during file copy)
_FORCE_DELAYS = True        # force delays during background task (for debugging)


class FileSystem:
    """
        This class is the data behind a file system 'view'
        It contains the methods required to navigate, list files
        and get statistic about a file system.
        Also manitain  a list of selected files.
    """

    def __init__(self, file_system_config):
        """
            Constructor:
                - current folder is the config home folder.
                - No selected files.
        """

        self.home_folder = normpath(file_system_config['directory'])

        self.current_folder = self.home_folder
        self.selected_files = []
        self.config = file_system_config
        self.current_index = 0

    def get_selected_size(self):
        """
            Get a string (with units!) representing the total size of
            all selected files.
        """
        return filesize.size(sum([f['size'] for f in self.selected_files]))

    def get_selected_size_raw(self):
        """
            Get the total size (in bytes) of all selected files
        """
        return sum([f['size'] for f in self.selected_files])

    def add_selected_file(self, filename):
        """
            Add a new selected file in the current folder
        """
        self.selected_files.append({'filename': filename, 'folder': self.current_folder,
                                    'size':  self.safe_file_size(self.current_folder, filename)})

        return self.get_selected_size()

    def clear_selected_file(self):
        """
            clear all selected files
        """

        self.selected_files = []

        return self.get_selected_size()

    def remove_selected_file(self, filename):
        """
            Remove a selected file in the current folder
        """
        self.selected_files = [f for f in self.selected_files
                               if not(f['filename'] == filename and f['folder'] == self.current_folder)]

        return self.get_selected_size()

    def is_selected(self, filename, folder):
        """
            Give a file and ant its containing folder, return True if this
            file is selected.
        """
        return any(f['filename'] == filename and f['folder'] == folder for f in self.selected_files)

    def select_home(self):
        """
            Set the current folder as the home folder
        """
        self.current_index = 0
        self.current_folder = self.home_folder

    def get_current_folder_size(self):
        """
            Get the total size (in bytes) of the current folder
        """
        return sum([file['filesize_bytes'] for file in self.get_file_list(filtered=False)])

    def select_parent_folder(self):
        """
            Set the current folder as the parent of the current folder.
        """
        self.current_index = 0
        if len(self.current_folder) > len(self.home_folder):
            self.current_folder = sep.join(self.current_folder.split(sep)[0:-1])

    def select_subfolder(self, folder):
        """
            Set the current folder as a subfolder of the current folder.
        """
        if folder != self.current_folder:
            self.current_index = 0

        if folder == "root":
            self.current_folder = self.home_folder
        else:
            self.current_folder = join(self.current_folder, folder)

    def get_statistics(self):
        """
            Get statistics (used, free space...) for the file system
        """
        return psutil.disk_usage(self.home_folder)

    def get_file_list(self, filtered=True):
        """
            Return a list describing the content of the current folder.
             If filtered is true, ony a portion of the list (define by _MAX_ENTRIES_IN_LIST
             and self.current_index is returned).
        """
        file_list = [{'filename': f,
                      'filesize_human': filesize.size(self.safe_file_size(self.current_folder, f)),
                      'filesize_bytes': self.safe_file_size(self.current_folder, f),
                      'isfile':  isfile(join(self.current_folder, f)),
                      'isselected':  self.is_selected(f, self.current_folder)}
                       for f in listdir(unicode(self.current_folder))]

        if len(self.current_folder) > len(self.home_folder):
            file_list.insert(0, {'filename': '..',
                                 'filesize_human': '-',
                                 'filesize_bytes': 0,
                                 'isfile':  False,
                                 'isselected':  False})
        if filtered:
            return file_list[self.current_index : self.current_index+_MAX_ENTRIES_IN_LIST]
        else:
            return file_list

    def moveup(self):
        """
            If 
        """
        self.current_index -= _JUMP
        self.current_index = max(self.current_index, 0)

    def movedown(self):
        self.current_index += _JUMP
        self.current_index = min(self.current_index, max(0, len(self.get_file_list(False))-1))

    def files_before(self):
        return self.current_index > 0

    def files_after(self):
        return (self.current_index +_MAX_ENTRIES_IN_LIST)<=len(self.get_file_list(False))

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
def mount(command, post_delay=0, execution_thread=None):

    if execution_thread:
        execution_thread.report_status(status='mounting',
                                       percent='0')

    subprocess.call(command)
    time.sleep(post_delay)

    if _FORCE_DELAYS:
        time.sleep(30)

    execution_thread.report_status(status='mounted',
                                   percent='100')
    if execution_thread:
        execution_thread.remove_from_jobs()

@async
def unmount(command, post_delay=0, execution_thread=None):

    if execution_thread:
        execution_thread.report_status(status='unmounting',
                                       percent='0')

    subprocess.call(command)
    time.sleep(post_delay)
    if _FORCE_DELAYS:
        time.sleep(5)
    execution_thread.report_status(status='unmounted',
                                   percent='100')
    if execution_thread:
        execution_thread.remove_from_jobs()



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
            cur_block = src.read(_FILE_BLOCK_SIZE)

            cur_block_pos += _FILE_BLOCK_SIZE

            if report_delegate:
                try:
                    report_delegate(status='Copying \'' + basename(source_file) + '\'',
                                    percent=round(float(cur_block_pos)/float(src_size)*100.0))
                except Exception as e:
                    report_delegate(status='Copying \'' + basename(source_file) + '\'',
                                    percent=0.0)

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

    total_size_to_copy=sum([f['size'] for f in files_to_copy])

    copy_in_progress = True

    try:
        for file_to_copy in files_to_copy:

            status_delegate = make_status_update_delegate(thread=execution_thread,
                                                          total_file_size=file_to_copy['size'],
                                                          total_size_to_copy=total_size_to_copy)

            copy_file(source_file=join(file_to_copy['folder'], file_to_copy['filename']),
                      destination_file=join(destination_folder, file_to_copy['filename']),
                      overwrite=overwrite,
                      report_delegate=status_delegate)
    finally:

        copy_in_progress = False

        if execution_thread:
            execution_thread.remove_from_jobs()

@async
def delete_folder(folder_to_delete, home_folder, execution_thread=None):

    if folder_to_delete == home_folder:
        raise Exception('Cannot delete home folder')
    try:
        execution_thread.report_status(status='deleting ' + folder_to_delete,
                                       percent='-')
        rmdir(folder_to_delete)
        time.sleep(0.1)

        if _FORCE_DELAYS:
            time.sleep(5)

    finally:
        if execution_thread:
            execution_thread.remove_from_jobs()

@async
def delete_files(files_to_delete, execution_thread=None):

    try:
        for fileToDelete in files_to_delete:
            execution_thread.report_status(status='deleting ' + fileToDelete['filename'].encode('ascii', 'ignore'),
                                           percent='-')

            remove(join(fileToDelete['folder'], fileToDelete['filename']))
            time.sleep(0.5)
            if _FORCE_DELAYS:
                time.sleep(5)
    finally:
        if execution_thread:
            execution_thread.remove_from_jobs()

@async
def create_dir(parent_directory, name_of_new_directory, execution_thread=None):

    try:
        execution_thread.report_status(status='creating ' + name_of_new_directory.encode('ascii', 'ignore'),
                                       percent='-')

        mkdir(join(parent_directory, name_of_new_directory))
        time.sleep(0.5)
        if _FORCE_DELAYS:
            time.sleep(5)
    finally:
        if execution_thread:
            execution_thread.remove_from_jobs()



def make_status_update_delegate(thread, total_file_size, total_size_to_copy):
    global copy_percent
    original_copy_percent = copy_percent

    def update_copy_status(status, percent):
        global copy_percent

        copy_percent = round(original_copy_percent + ((total_file_size * float(percent) / 100.0)/total_size_to_copy)*100.0)

        thread.report_status(status, percent)
    return update_copy_status

def get_copy_status():

    if copy_in_progress:
        file_copy_status = get_background_status('copy_files')
        return file_copy_status['status'], file_copy_status['percent'], copy_percent
    else:
        return None


if __name__ == '__main__':
    pass
    #import config
    #import time

    #test = FileSystem(config.destination)

    #print test.get_file_list()

    #copy_file(source_file='C:\\temp\\source\\output.txt', destination_file='C:\\temp\\dest\\output.txt', overwrite=True)

    #copy_file(source_file='C:\\temp\\source\\wildlife.wmv', destination_file='C:\\temp\\dest\\output.txt', overwrite=True)


    #copy_folder(source_folder='C:\\temp\\source\\',
    #            destination_folder='C:\\temp\\dest\\',
    #            overwrite=True)

    #mount_device(command=config.destination['mount_command'], post_delay=10)

    #umount_device(command=config.source['unmount_command'], post_delay=10)

    #while True:
    #    time.sleep(0.5)
    #    print get_background_status('copy_folder')