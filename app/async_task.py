
from threading import *

_background_jobs_status = dict()
_status_lock = Lock()
_max_background_job_count = 1

def is_job_running(job_name):
    return any(t for t in enumerate() if t.name == job_name)

def get_background_status(job_name):

    job_status = None

    try:
        _status_lock.acquire()
        job_status = _background_jobs_status[job_name]
        _status_lock.release()
    except:
        try:
            _status_lock.release()      # let's make sure it is always released!
        except:
            pass

    return job_status


class BackgroundJob(Thread):

    job_count = 0

    def __init__(self, name, job, *args, **kwargs):

        Thread.__init__(self, name=name)
        self.name = name
        self.job = job
        self.args = args
        self.kwargs = kwargs
        self.status = dict()
        if self.job_count < _max_background_job_count:
            _background_jobs_status[self.name] = self.status
            self.job_count += 1
        else:
            raise Exception('Only {0!s} job supported'.format(_max_background_job_count))

    def run(self):

        named_args = self.kwargs
        named_args['execution_thread']= self
        self.job(*self.args, **self.kwargs)

    def report_status(self, status, percent):

        _status_lock.acquire()
        self.status['status'] = str(status)
        self.status['percent'] = percent
        _status_lock.release()

    def remove_from_jobs(self):
        del _background_jobs_status[self.name]
        self.job_count -= 1

def async(f):
    def wrapper(*args, **kwargs):
        thr = BackgroundJob(name=f.__name__, job=f, *args, **kwargs)

        thr.start()

    return wrapper

if __name__ == "__main__":

    import time

    @async
    def print_time(init_count, delay, execution_thread=None):
        counter = init_count
        while counter:

            try:
                execution_thread.report_status(status='count is {}'.format(str(counter)),
                                               percent=str((init_count-counter/init_count * 100.0)))
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

    while True:
        time.sleep(0.5)
        print get_background_status('print_time')


