__author__ = 'Nicolas'



from threading import Thread


my_background_jobs = dict()



class BackgroundJob(Thread):

    def __init__(self, name, job, *args, **kwargs):

        Thread.__init__(self)
        self.name = name
        self.job = job
        self.args = args
        self.kwargs = kwargs
        self.status = dict()
        #TODO do not authorise duplicates!!
        my_background_jobs[self.name] = self.status

    def run(self):
        self.job(self.status, *self.args , **self.kwargs)


def async(f):
    def wrapper(*args, **kwargs):
        thr = BackgroundJob(name=f.__name__, job=f, *args, **kwargs)

        thr.start()
    return wrapper


if __name__ == "__main__":

    import time

    @async
    def print_time(status, init_count, delay):
        counter = init_count
        while counter:

            status['status'] = 'count is {}'.format(str(counter))
            status['percent'] = str((init_count-counter/init_count * 100.0))

            time.sleep(delay)
            print time.ctime(time.time())
            counter -= 1

    print_time(init_count=10, delay=1)
    #job = BackgroundJob('test', print_time, init_count=10, delay=1)

    #job.start()

    while True:
        time.sleep(0.5)
        print my_background_jobs['print_time']['status']