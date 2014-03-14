__author__ = 'Nicolas'


from os import listdir,walk
from os.path import isfile, getsize, join
from utils.hurry import filesize


class FileSystem:


    def __init__(self, root):

        self.root = root
        self.current_folder = root
        self.selected_files = []

    def add_selected_file(self, filename):

        self.selected_files.append({'filename': filename, 'folder': self.current_folder,
                                    'size':  self.safe_file_size(self.current_folder, filename)})

        return filesize.size(sum([f['size'] for f in self.selected_files]))

    def select_root(self):
         self.current_folder = self.root

    def select_up(self):
         pass

    def select_subfolder(self, folder):

        if folder == "root":
            self.current_folder = self.root
        else:
            self.current_folder = join(self.current_folder, folder)

    def get_file_list(self):

        return [{'filename': f,
                 'filesize_human': filesize.size(self.safe_file_size(self.current_folder, f)),
                 'filesize_bytes': self.safe_file_size(self.current_folder, f),
                 'isfile':  isfile(join(self.current_folder, f))} for f in listdir(self.current_folder)]

    def get_folder_size(self, start_path='.'):
        total_size = 0
        for dirpath, dirnames, filenames in walk(start_path):
            for f in filenames:
                fp = join(dirpath, f)
                total_size += getsize(fp)
        return total_size

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

