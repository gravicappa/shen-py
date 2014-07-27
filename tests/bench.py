import time
tests = {}
times = 1

def case(x = None, **keys):
    def mkfunc(fn):
        def func(*args):
            start = time.time()
            for x in xrange(times):
                r = fn(*args)
            t = time.time() - start
            print("  {:.4}ms {} {}".format((t * 1000), fn.__name__, r))
        func.__name__ = fn.__name__
        if keys.get('register', True):
            tests[fn.__name__] = func
        return func
    if callable(x):
        return mkfunc(x)
    return mkfunc

def run(n = None):
    global times
    if n:
        times = n
    for x in tests:
        tests[x]()
