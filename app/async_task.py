__author__ = 'Nicolas'



from threading import *


my_background_jobs = dict()

_status_lock = Lock()

def is_job_running(job_name):
    return any(t for t in enumerate() if t.name == job_name)

def get_status(job_name):

    job_status = None

    try:
        _status_lock.acquire()
        job_status =  my_background_jobs[job_name]
        _status_lock.release()
    except:
        try:
            _status_lock.release()      # let's make sure it is always released!
        except:
            pass

    return job_status

class BackgroundJob(Thread):

    def __init__(self, name, job, *args, **kwargs):

        Thread.__init__(self,name=name)
        self.name = name
        self.job = job
        self.args = args
        self.kwargs = kwargs
        self.status = dict()
        #TODO do not authorise duplicates!!
        my_background_jobs[self.name] = self.status

    def run(self):
        self.job(self, *self.args, **self.kwargs)

    def  report_status(self, status, percent):

        _status_lock.acquire()
        self.status['status'] = str(status)
        self.status['percent'] = str(percent)
        _status_lock.release()

    def remove_from_jobs(self):
        del my_background_jobs[self.name]

def async(f):
    def wrapper(*args, **kwargs):
        thr = BackgroundJob(name=f.__name__, job=f, *args, **kwargs)

        thr.start()

    return wrapper


if __name__ == "__main__":

    import time

    @async
    def print_time(execution_thread, init_count, delay):
        counter = init_count
        while counter:

            try:
                execution_thread.report_status(status='count is {}'.format(str(counter)),
                                               percent=str((init_count-counter/init_count * 100.0)))
                #status['status'] = 'count is {}'.format(str(counter))
                #status['percent'] = str((init_count-counter/init_count * 100.0))
            except:
                pass

            time.sleep(delay)
            print time.ctime(time.time())
            counter -= 1

        try:
            execution_thread.remove_from_jobs()
        except:
            pass

    print_time(init_count=10, delay=1)
    #job = BackgroundJob('test', print_time, init_count=10, delay=1)

    #job.start()

    while True:
        time.sleep(0.5)
        print get_status('print_time')


