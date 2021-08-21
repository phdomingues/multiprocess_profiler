import os
import csv
import time
import psutil
import inspect
import traceback
from typing import Any
from pathlib import Path 
from filelock import FileLock, Timeout

class ProfileError(Exception):
    """Error raised when a profiling step could not finish"""
    def __init__(self, message=""):
        super().__init__(message)

class Profiler:
    """
    Measures time and save the results to a csv file named 'profiler.csv'. 
    
    NOTE: If the file exists, it is not cleaned, the results are just appended to it.

    - Arguments:
        - id_ [any]: name or identifier saved on the csv for future reference;
        - timeout [float|default=10]: maximum time waiting the lock to write on the csv file;
        - ignore_timeout [bool|default=False]: if False, raises ProfileError after timeout;
        - verbose [bool|default=False]: if True aditionally to the csv, also log time and errors to stdout;
        - log_function [callable|default=print]: If you have a diferent log function specify here, it must receive only the message string as 
                                                 a mandatory parameter;
        - allow_formating [bool|default=True]: if True, the class will try to make fixed size strings and add '...' whenever it can't fit a message;
        - result_path [Path/str|default=./timeprofile.csv]: path and file to output, should be a string or a pathlib Path object
        - autonaming [bool|default=True]: if no id is provided, it will attempt to name id as the function name (or the last function registered in the stack)

    - Usage: Call this class using a with statement, as a decorator or by instancing an object and using the methods start, pause, resume and stop;

    - Raises: ProfileError;

    - Results: CSV file named 'profiler.csv' containing the following columns:
        - id: Reference name passed as argument;
        - time: Execution time;
        - broken: Boolean indicating if the code stopped earlier due to some exception (does not consider any ProfileError);
        - pid: Pid from the process where the execution finished;
        - ppid: Parent pid;
        - process_name: String indicating the process name vinculated to this pid;
        - parent_process_name: String indicating the process name vinculated to the ppid;

    - Examples:

    #1. Using a with statement

    def foo():
        with Profiler("measuring_foo_1"):
            #do stuff
        with Profiler("measuring_foo_2"):
            #do stuff
        with Profiler(123):
            #do stuff
    
    #2. Using as decorator

    @Profiler() 
    def bar():
        #do stuff

    #3. Manually

    tp = Profiler("Hello World", verbose=True)
    tp.start()
    #do stuff
    tp.pause()
    #Don't wan't to take this part into account
    tp.resume()
    #finish my stuff
    tp.close()

    """
    def __init__(self, 
        id_: Any = None, 
        timeout: float = 10, 
        ignore_timeout: bool = True, 
        verbose: bool = False, 
        log_function: callable = print, 
        allow_formating: bool = True,
        result_path: Path or str = "profile",
        autonaming: bool = True
    ):
        # Due to race conditions on unix the lock file is not deleted, so /tmp is used for automatic cleaning
        self.__result_path = Path(result_path)
        self.__lock_path = Path("/","tmp",str(self.__result_path).replace(os.path.sep,'_')+".profiler_lock") # Lock doesn't have a unique name, so it is shared between every process running this script
        self.__timeout = timeout if timeout > 0 else 0 # Seconds waiting for the lock file
        self.__id = id_ #if id_ is not None else ""
        self.__verbose = verbose
        self.__ignore_timeout = ignore_timeout
        self.__log = log_function
        self.__format = allow_formating
        self.__autonaming = autonaming

        self.__header = ["id", "time", "pid", "ppid", "process_name", "parent_process_name", "broken", "error_type", "error_value", "traceback"]
        self.__reset_attributes()

        self.__caller_index = 1 # [0] is __exit__, so [1] is by default the caller of __exit__, but it could be the wrapper when using as decorator, in this case the name is determined on __call__
        self.__finished = False

    def __reset_attributes(self):
        self.__started = False
        self.__reference_time = 0
        self.__is_paused = False
        self.__paused_time = 0
        self.__pause_reference = 0

    def __enter__(self):
        self.__check_started("Profiler is already started")
        self.__started = True
        self.__finished = False
        self.__reference_time = time.time()
        return self

    def __del__(self):
        if not self.__finished:
            self.__exit__(None, None, None)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.__check_not_started("Profiler was not started")
        if self.__is_paused: self.resume() # In case the user paused but never resumed
        measured_time = time.time() - self.__reference_time - self.__paused_time # Measures the time since __enter__ was called
        broken = exc_traceback is not None # If some exception was raised inside the with statement, mark broken as true
        if self.__id is None and self.__autonaming:
            try:
                self.__id = inspect.stack()[self.__caller_index].function
            except:
                self.__id = "Failed Autonaming"
        # Prepare process data that will be marked on the csv
        pid = os.getpid()
        ppid = os.getppid() # Parent pid
        pname = psutil.Process(pid).name() # Process name
        ppname = psutil.Process(ppid).name() # Parent process name
        # Log result if set to verbose
        if self.__verbose:
            try:
                self.__log("[Profiler] {:<30} - {:<23} - process {}/{} {}".format(
                    str(self.__id)[:27]+'...' if len(str(self.__id)) > 30 and self.__format else self.__id , 
                    "{:.5f} seconds".format(measured_time), 
                    pname,
                    pid,
                    '(broken)' if broken else '')
                )
            except Exception as e:
                raise ProfileError("Exception raised while calling the log function") from e
        # Save the results in a multiprocess safe manner
        lock = FileLock(str(self.__lock_path), timeout=self.__timeout)
        try:
            lock.acquire()
            # Write the results on csv
            with open(self.__result_path.with_suffix(".csv"), 'a+') as f:
                # Create writer and reader objects
                writer = csv.writer(f)
                reader = csv.reader(f)

                try:
                    f.seek(0,0) # Move the cursor to the begining
                    next(reader) # Test if the file is not empty
                    f.seek(0,2) # Move the cursor back to EOF so we can append data
                except StopIteration:
                    writer.writerow(self.__header) # File is empty - write the header
                finally:
                    writer.writerow([self.__id, measured_time, pid, ppid, pname, ppname, broken, exc_type, exc_value, traceback.format_exc()]) # write content
        except Timeout:
            # Timeout 
            if not self.__ignore_timeout:
                raise ProfileError("Timed out waiting for csv lock") from None
            if self.__verbose:
                try:
                    self.__log("[Profiler] skipped saving results from {} ({} / pid {}), csv lock timed out after {:.5f} seconds".format(
                        self.__id, 
                        pname,
                        pid,
                        self.__timeout)
                    )
                except Exception as e:
                    raise ProfileError("Exception raised while calling the log function after a lock timeout") from e
        finally:
            lock.release()

        self.__reset_attributes()
        self.__finished = True
        return False # Reraises exception if there is one

    # Method to use the class as a decorator
    def __call__(self, f):
        # Capture function name since we can't do that using the stack if we wrap the function
        if self.__id is None and self.__autonaming:
            self.__id = f.__qualname__ 
        def wrapper(*args, **kwargs): 
            with Profiler(self.__id) as tp: # Can't use self as the time profiler, since it would be share by all processes started with this decorator
                result = f(*args, **kwargs)
            return result
        return wrapper

    def start(self):
        if self.__verbose:
            self.__log("Using start method to initialize profiler, exception handling will be disabled")
        self.__enter__()

    def pause(self):
        """Pauses the time measuring"""
        if not self.__is_paused:
            self.__pause_reference = time.time()
            self.__check_not_started("Can't pause profiler if it is not running")
            self.__is_paused = True

    def resume(self):
        """Resumes the time measuring"""
        self.__check_not_started("Can't resume if profiler if it was not started")
        if self.__is_paused:
            self.__paused_time += time.time() - self.__pause_reference
            self.__is_paused = False

    def stop(self):
        self.__exit__(None, None, None)

    def __check_not_started(self, error_message):
        if not self.__started:
            raise ProfileError(error_message)
    
    def __check_started(self, error_message):
        if self.__started:
            raise ProfileError(error_message)