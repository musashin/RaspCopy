__author__ = 'Nicolas'



from threading import *


my_background_jobs = dict()


def is_job_running(name):
    return any(t for t in enumerate() if t.name == name)

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

        #TODO: protect with Mutex!!
        self.status['status'] = str(status)
        self.status['percent'] = str(percent)

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
        print my_background_jobs
        if is_job_running('print_time'):
            #TODO: protect with Mutex!!
            print my_background_jobs['print_time']['status']
