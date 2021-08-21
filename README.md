# Multiprocess Profiler

## What does it do?

- Time measurement;
- PID and parent PID annotation;
- Error tracking;

---

## What is unique about it?

- It allows profiling over multiple threads or processes at once;
- The output is a csv file with all the necessary information so you can do the most fitting analysis;
- Thread / Multiprocessing safe;

---

## How does this output csv looks like?

Each row represents a measurement that could have been made from any instance of the profiler from any process or thread.

Columns on the csv are:

- __id [string]:__ An identifier representing the a measurement. It is automatically named as the function where the profiler was instantiated or it can be set by the user to any string;
- __time [float]:__ Time measured until the end or until an untreated exception was raised;
- __pid [int]:__ PID where the profiler finished his measurement;
- __ppid [int]:__ Parent PID, same as described on PID;
- __process_name [string]:__ Name of the process with the given PID;
- __parent_process_name [string]:__ Name of the parent process with the given PPID;
- __broken [bool]:__ Flag informing of an untreated exception was raised during measurement, resulting on it finishing before expected (only meaningful for context manager and decorator)
- __error_type [string]:__ If broken is set to true, this represents the error type;
- __error_value [string]:__ If broken is set to true, this represents the error value;
- __traceback:__ If broken is set to true, this represents the error traceback;

---

## How does it work?

There are 3 ways to use it:

### 1. __With a context manager:__

Encapsulate what you want to measure using the pythons `with` keyword.

Example:

```python
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

```

The example above would result in a CSV where every row has an id "MyFunction" (since it's the only thing measured) and we can check how much time each process on the pool took to run it as well as see if it breaks.

### 2. __Manually control where it start and stops to measure, as well when to pause and continue if necessary:__

If you have an application where you need to measure time on some steps but ignore others, you can use a manual control as the following example:

```python
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
        try:
            MyFunction(value)
        except Exception as e:
            pbar.write("An error just happened! {}".format(repr(e)))
        pbar.update(1)
```

Note: pause and resume functionality also works using the with statement (doing something similar to `with mpp.Profiler() as profiler`).

### 3. __As a decorator:__

This is the easiest way to use the profiler, but due to the serialization of functions made during multiprocessing, this may or may not work on such cases. If it doesn't work just encapsulate your function as described in 1.

Example:

```python
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
```

---

## Can I customize it?

The profiler accepts the following arguments on the constructor:

- __id\___: Identifier that will be used in the csv;
- __timeout__ [default=10]: Maximum time (seconds) waiting for the file lock to write on the CSV file (to make sure it won't couse any deadlock);
- __ignore_timeout__ [default=True]: If set to true, a ProfilerError will be raised in order to alert about the timeout, if false the timeout will be handled internally but no exception will be raised;
- __verbose__ [default=False]: If true time and PIDs will be logged using the log_function;
- __log_function__ [default=print]: Any callable that receives a string as argument. Used only when verbose is set to true;
- __allow_formating__ [default=True]: If true and verbose is also true, format the messages to not have more then 30 characters;
- __result_path__ [default='./profile']: String or Path object (pathlib) where the results will be saved (no need to specify extension since .csv is always assumed);
- __autonaming__ [default=True]: If true and no id is specified it will attempt to create an id using the function name (or the last function call registered in the stack);