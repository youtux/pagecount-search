import argparse
import collections
import datetime
import functools
import io
import itertools
import subprocess
import sys
from urllib.parse import quote, unquote

import pathlib
from .sortedcollection import SortedCollection

__all__ = ('Finder', 'search', 'build_index')

DATETIME_PATTERN = '%Y%m%d-%H%M%S'

Record = collections.namedtuple(
    'Record',
    'project page timestamp count bytes_trans',
)

IndexRecord = collections.namedtuple(
    'IndexRecord',
    'file_name project page',
)


class Finder:
    """Look for the given entry in the dataset."""

    def __init__(self, source_dir, index_path=None, auto_index=True):
        """Initialize the search engine."""
        self.source_dir = source_dir
        if index_path is None:
            index_path = default_index_path(source_dir)

        if not index_path.exists() and auto_index:
            print('Building index... ', end='', flush=True, file=sys.stderr)
            build_index(source_dir, index_path)
            print('Done!', flush=True, file=sys.stderr)

        if not index_path.exists():
            raise ValueError('Index file does not exists.')

        self.index = read_index(index_path)

    def search(self, project, page):
        """Search for the given project and page."""
        return search(self.source_dir, self.index, project, page)


def default_index_path(source_dir):
    return source_dir/'index'


def parse_timestamp(timestamp):
    return datetime.datetime.strptime(timestamp, DATETIME_PATTERN)

parse_timestamp_cached = functools.lru_cache(maxsize=10000)(parse_timestamp)
quote_cached = functools.lru_cache(maxsize=10000)(quote)
unquote_cached = functools.lru_cache(maxsize=10000)(unquote)


def gzip_open(file_path):
    f = subprocess.Popen(['gzip', '-cd', file_path], stdout=subprocess.PIPE)
    w = io.TextIOWrapper(f.stdout, encoding='utf-8')
    return w


def parse_line(line):
    project, page, timestamp, count, bytes_trans = line[:-1].split(' ')

    page = unquote_cached(page)

    timestamp = parse_timestamp_cached(timestamp)
    count = int(count)
    bytes_trans = int(bytes_trans)

    return Record(project, page, timestamp, count, bytes_trans)


def parse_index_line(line):
    part_file_path, project, page = line[:-1].split(' ')
    page = unquote(page)

    return IndexRecord(part_file_path, project, page)


def search(source_dir, index, project, page):
    part_file_name = index.find_le((project, page)).file_name

    part_file_path = source_dir/part_file_name

    part_file = gzip_open(str(part_file_path))

    with part_file:
        records = (parse_line(line) for line in part_file)

        grouped_records = itertools.groupby(
            records,
            key=lambda record: (record[0], record[1]),
        )

        for key, records_group in grouped_records:
            if key < (project, page):
                continue
            if key > (project, page):
                break

            return [
                (timestamp, count, bytes_trans)
                for _, _, timestamp, count, bytes_trans in records_group
            ]

    return []


def build_index(source_dir, output_path):
    with output_path.open('wt', encoding='utf-8') as index_f:
        for part_file_path in sorted(source_dir.glob('part-*.gz')):
            part_file = gzip_open(str(part_file_path))
            with part_file:
                line = part_file.readline()
                record = parse_line(line)
                print(
                    part_file_path.name,
                    record.project,
                    quote(record.page),
                    file=index_f)


def read_index(index_path):
    index_file = index_path.open('rt', encoding='utf-8')
    with index_file:
        return SortedCollection(
            (parse_index_line(l) for l in index_file),
            key=lambda x: x[1:]
        )


def parse_args():
    parser = argparse.ArgumentParser(
        prog="pagecounts-search",
        description="Search through sorted wikimedia pagecounts data.",
    )
    parser.add_argument(
        'source_dir',
        metavar='SOURCE_DIR',
        type=pathlib.Path,
        help="Directory containing pagecounts data files",
    )
    parser.add_argument(
        '--index-path', '-i',
        metavar='INDEX_PATH',
        required=False,
        type=pathlib.Path,
        help="Index file path",
    )
    subparsers = parser.add_subparsers(
        help='sub-commands help',
        dest='command')

    search_parser = subparsers.add_parser(
        'search',
        help='Search for the given entry',
    )
    search_parser.add_argument(
        'project',
    )
    search_parser.add_argument(
        'page',
    )

    build_index_parser = subparsers.add_parser(
        'build-index',
        help='Build the index for the dataset',
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.index_path is None:
        args.index_path = default_index_path(args.source_dir)

    if args.command == 'search':
        f = Finder(args.source_dir, args.index_path)
        for timestamp, count, bytes_trans in f.search(args.project, args.page):
            print(
                timestamp.strftime(DATETIME_PATTERN),
                count,
                bytes_trans,
            )
    if args.command == 'build-index':
        build_index(args.source_dir, args.index_path)


if __name__ == '__main__':
    main()
