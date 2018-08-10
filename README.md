# JSONAnalysis
Helps you summarize JSONL data structure.

## Usage
```sh
usage: json_analysis.py [-h] [-f FD_IN] [-t] [-p] [-v]

optional arguments:
  -h, --help     show this help message and exit
  -f FD_IN       Input jsonl path, defaults to stdin.
  -t, --table    Tab separated format, preempts -p -v.
  -p, --pretty   Prettify result.
  -v, --verbose  More descriptive result.

```
## Example
```sh
$ cat sample.jsonl
{"_id": 123, "meta": {"note": "this is note"}, "unfix_type": 123, "arr": [{"param_a": "param_a_xxxxx"}]}  
{"_id": 124, "meta": {"note": "this is note"}, "unfix_type": 456, "arr": [{"param_b": "param_b_xxxxx"}]}  
{"_id": 125, "meta": {"note": "this is note"}, "unfix_type": "", "arr": [{"param_a": ""}]}  
{"_id": 126, "meta": {"note": "", "note_extra": "extra note"}, "unfix_type": false}  
{"_id": 127, "meta": {"note": "", "note_extra": "extra note"}, "unfix_type": true}
```

```sh
$ cat sample.jsonl | ./json_analysis.py -p
[
    {
        "$count": 5,
        "$count_falsy": 0,
        "$parse": 126,
        "$type": "dict.int",
        "$key": "_id"
    },
    {
        "$count": 5,
        "$count_falsy": 2,
        "$parse": "this is note",
        "$type": "dict.dict.str",
        "$key": "meta.note"
    },
    {
        "$count": 2,
        "$count_falsy": 0,
        "$parse": "extra note",
        "$type": "dict.dict.str",
        "$key": "meta.note_extra"
    },
    {
        "$count": 2,
        "$count_falsy": 0,
        "$parse": 456,
        "$type": "dict.int",
        "$key": "unfix_type"
    },
    {
        "$count": 1,
        "$count_falsy": 1,
        "$parse": "",
        "$type": "dict.str",
        "$key": "unfix_type"
    },
    {
        "$count": 2,
        "$count_falsy": 1,
        "$parse": true,
        "$type": "dict.bool",
        "$key": "unfix_type"
    },
    {
        "$count": 2,
        "$count_falsy": 1,
        "$parse": "param_a_xxxxx",
        "$type": "dict.list.dict.str",
        "$key": "arr.param_a"
    },
    {
        "$count": 1,
        "$count_falsy": 0,
        "$parse": "param_b_xxxxx",
        "$type": "dict.list.dict.str",
        "$key": "arr.param_b"
    }
]
```
