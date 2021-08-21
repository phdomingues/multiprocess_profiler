from tqdm import tqdm

import random
import multiprocess_profiler as mpp

@mpp.Profiler() # Decorator will measure the entire function
def MyFunction(n):
    f = 1
    if random.random() < 0.1:
        raise Exception("This is a random exception")
    for i in range(1,n+1):
            f = f*i
    return f

test_list = [random.randint(70000,120000) for _ in range(50)]
with tqdm(total=len(test_list), desc="Processing") as pbar:
    for value in test_list:
        try:
            MyFunction(value)
        except Exception as e:
            pbar.write("An error just happened! {}".format(repr(e)))
        pbar.update(1)