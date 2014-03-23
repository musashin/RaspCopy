__author__ = 'Nicolas'



from threading import Thread


class BackgroundJob(Thread):

    def __init__(self, name, job, *args, **kwargs):

        Thread.__init__(self)
        self.name = name
        self.job = job
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.job(*self.args , **self.kwargs)


def async(f):
    def wrapper(*args, **kwargs):
        thr = BackgroundJob(name='tt', job=f, *args, **kwargs)
        thr.start()
    return wrapper


if __name__ == "__main__":

    import time

    @async
    def print_time(init_count, delay):
        counter = init_count
        while counter:

            time.sleep(delay)
            print time.ctime(time.time())
            counter -= 1

    print_time(init_count=10, delay=1)
    #job = BackgroundJob('test', print_time, init_count=10, delay=1)

    #job.start()

    while True:
        pass