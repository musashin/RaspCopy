CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

source = dict()

source['directory'] =  r'C:\temp\source'
source['mount_command'] = 'notepad'
source['unmount_command'] = ''

destination = dict()
destination['directory'] = r'C:\temp\dest'
destination['mount_command'] = 'calc'
destination['unmount_command'] = 'notepad'
