from __future__ import annotations
import sys
import multiprocessing
from typing import TYPE_CHECKING, TypeVar, Any
if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from multiprocessing.sharedctypes import Synchronized


_current: Synchronized[int]
_total: Synchronized[int]


def _init(current: Synchronized[int], total: Synchronized[int]):
    global _current
    global _total
    _current = current
    _total = total


T = TypeVar('T')


def _wrapped_func(func_and_args: tuple[Callable[..., T], Any, *tuple[Any, ...]]) -> T:
    func = func_and_args[0]
    args = func_and_args[1:]

    with _current.get_lock():
        _current.value += 1
    sys.stdout.write('\r\t{} of {}'.format(_current.value, _total.value))
    sys.stdout.flush()

    return func(*args)


def parallel_map(func: Callable[[Any], T], iterable: Sequence, processes: int, *args: object) -> list[T]:
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
