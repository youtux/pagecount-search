import pagecountssearch
import pathlib

import datetime

now = datetime.datetime.utcnow

f = pagecountssearch.Finder(pathlib.Path('./dataset'))

tic = now()
assert len(f.slow_search('ace', 'Seumayang_gurhana')) == 1
assert len(f.slow_search('ace', 'Seulat_malaka')) == 13
assert len(f.slow_search('ace', 'Seulanga')) == 463
toc = now()

print('slow search:', toc - tic)

tic = now()
with f:
    assert len(f.search('ace', 'Seulanga')) == 463
    assert len(f.search('ace', 'Seulanga')) == 463
    assert len(f.search('ace', 'Seulat_malaka')) == 13
    assert len(f.search('ace', 'Seumayang_gurhana')) == 1
toc = now()

print('fast search:', toc - tic)
