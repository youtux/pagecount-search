# pagecounts-search
Search through ordered wikimedia pagecounts

## Pre-requisites
This project has been tested only in Python 3.5. May work with Python 3.4, but `pathlib` must be installed separately.

## Installation
    pip install git+https://github.com/youtux/pagecounts-search.git

## Usage
### As a library
```python
import pagecountssearch

f = pagecountssearch.Finder(source_dir='/path/to/sorted/counts/folder')
print(f.search('en', 'Albert_Einstein'))
```

### As a command line tool
```bash
$ pagecounts-search /path/to/sorted/counts/folder search en Albert_Einstein
20140101-000000 300 25645681
20140101-010000 246 21173395
20140101-020000 276 23558819
20140101-030000 234 17418623
20140101-040000 283 21449007
20140101-050000 289 23254304
20140101-060000 331 27369512
[...]
```
