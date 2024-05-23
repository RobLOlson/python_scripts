import time


def perf_timer(debug: bool = False):
    def inner(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            val = func(*args, **kwargs)
            stop = time.perf_counter()
            if debug:
                print(f"Ran {func.__name__} in {stop - start:.3f} sec.")

            return val

    return inner
