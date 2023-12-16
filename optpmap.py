import sys
import multiprocessing


_current = None
_total = None


def _init(current, total):
    global _current
    global _total
    _current = current
    _total = total


def _wrapped_func(func_and_args):
    func = func_and_args[0]
    args = func_and_args[1:]

    with _current.get_lock():
        _current.value += 1
    sys.stdout.write('\r\t{} of {}'.format(_current.value, _total.value))
    sys.stdout.flush()

    return func(*args)


def pmap(func, iterable, processes, *args, **kwargs):
    """
    A parallel map function that reports on its progress.

    Applies `func` to every item of `iterable` and return a list of the
    results. If `processes` is greater than one, a process pool is used to run
    the functions in parallel.
    """
    global _current
    global _total
    _current = multiprocessing.Value('i', 0)
    _total = multiprocessing.Value('i', len(iterable))

    func_and_args = [(func, it_arg, *args) for it_arg in iterable]
    if processes == 1:
        result = list(map(_wrapped_func, func_and_args))
    else:
        pool = multiprocessing.Pool(initializer=_init,
                                    initargs=(_current, _total,),
                                    processes=processes,
                                    maxtasksperchild=2)
        result = pool.map(_wrapped_func, func_and_args)
        pool.close()
        pool.join()

    sys.stdout.write('\n')
    return result
