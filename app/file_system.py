__author__ = 'Nicolas'


from os import listdir
from os.path import isfile, getsize, join
from utils.hurry import filesize


class FileSystem:


    def __init__(self, root):

        self.root = root
        self.current_folder = root

    def get_file_list(self):

        files = [f for f in listdir( self.current_folder) if isfile(join( self.current_folder,f))]
        return [{'filename': f,
                 'filesize_human': filesize.size(self.safe_file_size( self.current_folder, f)),
                 'filesize_bytes': self.safe_file_size(self.current_folder, f)} for f in files]


    def safe_file_size(self, path, file):

        try:
            size = getsize(join(path, file))
        except:
            size = 0

        return size

