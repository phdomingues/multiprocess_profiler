from distutils.core import setup
setup(
  name = 'multiprocess_profiler',
  packages = ['multiprocess_profiler'],
  version = '0.1',
  license='MIT',
  description = 'Profile your code, measuring times, calls per function, errors...',
  author = 'Pedro Henrique Silva Domingues',
  author_email = '12pedro07@gmail.com',
  url = 'https://github.com/12pedro07/multiprocess_profiler',
  download_url = 'https://github.com/12pedro07/multiprocess_profiler/archive/refs/tags/v_01.tar.gz',
  keywords = ['Time', 'Profiler', 'Multiprocess', 'Multithread'],
  install_requires=[            # I get to this in a second
          'psutil',
          'pathlib',
          'filelock',
          'typing;python_version<"3.5"'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)