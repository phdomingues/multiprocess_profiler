from tqdm import tqdm
from multiprocessing import Pool

import random
import multiprocess_profiler.profiler as mpp

def MyFunction(n):
    # Here we want to monitor this whole function
    with mpp.Profiler():
        f = 1
        if random.random() < 0.05:
            raise Exception("This is a random exception, you should check profile.csv to see what happened")
        for i in range(1,n+1):
                f = f*i
        return f

test_list = [random.randint(70000,120000) for _ in range(50)]
with Pool() as executor:
    with tqdm(total=len(test_list), desc="Processing") as pbar:
        result_futures = []
        for value in test_list:
                result_futures.append(executor.apply_async(MyFunction, (value,)))
        for result in result_futures:
            result.get()
            pbar.update(1)
