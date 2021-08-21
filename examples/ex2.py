from tqdm import tqdm

import random
import multiprocess_profiler as mpp

def MyFunction(n):
    profiler = mpp.Profiler()
    profiler.start() # Start to measure here
    f = 1
    profiler.pause() # Pause the timer for this part
    if random.random() < 0.1:
        raise Exception("This is a random exception")
    profiler.resume() # Resume the timer
    for i in range(1,n+1):
            f = f*i
    profiler.stop() # Stops measuring here (if this line was omitted, the measurement would stop when the profiler was cleaned by python garbage collector)
    return f

test_list = [random.randint(70000,120000) for _ in range(50)]
with tqdm(total=len(test_list), desc="Processing") as pbar:
    for value in test_list:
        MyFunction(value)
        pbar.update(1)