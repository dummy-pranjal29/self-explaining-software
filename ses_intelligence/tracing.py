import time
import inspect

def trace_behavior(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        caller = inspect.stack()[1].function

        print(
            f"[SES-FUNC] "
            f"func={func.__name__} "
            f"called_by={caller} "
            f"duration={duration:.4f}s"
        )

        return result
    return wrapper
