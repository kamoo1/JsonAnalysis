#!/usr/bin/env python3
import sys
import json
import types
import logging
import argparse
from abc import abstractmethod

"""
    Instances of BaseParse becomes one of [DictParse, ListParse, ValueParse]
    Instances of ValueParse becomes one of [BoolParse, IntParse, FloatParse, StrParse, NullParse]
    
    ## ====== Metas =======
    BaseParse._meta = 
    {
        "$count": value,
        "$count_falsy": value
    }
    
    
    ## ====== Parses ======
    ValueParse._parse = value
    
    ListParse._parse = 
    [
        BaseParse,  # BaseParse instances should not share the same child class.
        BaseParse,
        ...
    ]
    
    DictParse._parse =
    [
        KeyValueParse, # KayValueParse instances should not share same lhs (.get_type())
        KeyValueParse,
        ...
    ]
    
    # Note: after merging, a key in a dict may encounter different types of value,
    # each type is represented by a BaseParse
    KeyValueParse._parse = ListParse._parse = 
    [
        BaseParse,  # BaseParse instances should not share the same child class. 
        BaseParse,
        ...
    ]
    
    ## ====== Vars ======
    # Describes parse tree in json
    ValueParse.vars() = 
    {
        "$parse": value,        // from self._parse
        "$count": value,        // from self._meta
        "$count_falsy": value   // from self._meta
    }
    
    KeyValueParse.vars() = 
    {
        "$parse": KeyValueParse._parse
        "$count": value,
        "$count_falsy": value
    }
    
    DictParse.vars() = 
    {
        "$count": value,
        "$count_falsy": value,
        "$parse": {
            KeyValueParse.get_type(): KeyValueParse.vars(), // KeyValueParse.get_type() == lhs
            ...
        }
    }
    
    ListParse.vars() =
    {
        "$count": value,
        "$count_falsy": value,
        "$parse": {
            BaseParse.get_type(): BaseParse.vars(),
            BaseParse.get_type(): BaseParse.vars(),
            ...
        }
    }
"""

DEBUG = False
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def check_same_type(func):
    """
    Check wrapper for debugging
    last two args should share same type
    :param func:
    :return:
    """

    def inner(*args, **kwargs):
        if DEBUG:
            assert type(args[-1]) == type(args[-2])
        return func(*args, **kwargs)

    return inner


def check_is_type(type_):
    """
    Check wrapper for debugging
    type checking for last arg
    :param type_:
    :return:
    """

    def wrapper(func):
        def inner(*args, **kwargs):
            if DEBUG:
                assert isinstance(args[-1], type_)
            return func(*args, **kwargs)

        return inner

    return wrapper


def list_to_dict(list_, comp):
    """
    Transform a list into dict, item as val, comp(item) as key,
    items in each given list should yield unique value by calling comp(item).
    :param list_:
    :param comp:
    :return:
    """
    dict_ = {}
    for item in list_:
        item_type = comp(item)
        if DEBUG and dict_.get(item_type):
            raise TypeError("Two items with same type occurred in single list.")
        dict_[item_type] = item
    return dict_


def merge_dict(this, other, cb):
    """
    Merge dicts by key
    :param this:
    :param other:
    :param cb:
    :return:
    """
    # assert isinstance(this, dict)
    # assert isinstance(other, dict)

    result = {}
    result.update(this)
    result.update(other)
    for key in this.keys() & other:
        ret = cb(this[key], other[key])
        result[key] = ret
    return result


def merge_list(this, other, cb, comp=lambda o: type(o)):
    """
    Merge two lists by their children's type,
    for each given list, their children must be unique in type.
    :param this:
    :param other:
    :param cb:
    :param comp: a function to get children's type, defaults to type()
    :return:
    """

    # assert isinstance(this, list)
    # assert isinstance(other, list)

    result = []
    dict_this = list_to_dict(this, comp)
    dict_other = list_to_dict(other, comp)

    ret = merge_dict(dict_this, dict_other, cb)
    for value in ret.values():
        result.append(value)

    return result


class BaseParse(object):
    def __new__(cls, value, *args, **kwargs):
        # logger.debug("BaseParse.__new__ is called with cls = %s" % cls)
        if cls != BaseParse:
            return object.__new__(cls)

        if isinstance(value, (list, types.GeneratorType)):
            return object.__new__(ListParse)

        elif isinstance(value, dict):
            return object.__new__(DictParse)

        else:
            return ValueParse.__new__(ValueParse, value, *args, **kwargs)

    def __init__(self, value):
        # logger.debug("BaseParse.__init__ is called with self = %s" % self)
        if isinstance(self, (ListParse, DictParse)):
            self._parse = []
        else:
            # ValueParse, KeyValueParse
            self._parse = None

        self._meta = {
            "$count": None,
            "$count_falsy": None,
        }
        self._set_meta(value)
        self._set_parse(value)

    @abstractmethod
    def _set_parse(self, value):
        pass

    def _set_meta(self, value):
        self._meta = {
            "$count": 1,
            "$count_falsy": 0 if value else 1
        }

    @check_same_type
    def merge(self, other):
        self._merge_meta(other.get_meta())
        self._merge_parse(other.get_parse())

    @abstractmethod
    def _merge_parse(self, other_parse):
        pass

    def _merge_meta(self, other_meta):
        self._meta["$count"] += other_meta["$count"]
        self._meta["$count_falsy"] += other_meta["$count_falsy"]

    @abstractmethod
    def vars(self):
        pass

    @abstractmethod
    def get_type(self):
        pass

    def get_meta(self):
        return self._meta

    def get_parse(self):
        return self._parse


class ValueParse(BaseParse):
    def __new__(cls, value, *args, **kwargs):
        # logger.debug("ValueParse.__new__ is called with cls = %s" % cls)

        # if cls != ValueParse:
        #     # return super(ValueParse, cls).__new__(cls, value)
        #     return object.__new__(cls)

        # TODO code replication.
        if isinstance(value, bool):
            return object.__new__(BoolParse)

        elif isinstance(value, int):
            return object.__new__(IntParse)

        elif isinstance(value, float):
            return object.__new__(FloatParse)

        elif isinstance(value, str):
            return object.__new__(StrParse)

        elif value is None:
            return object.__new__(NoneParse)

        else:
            # Work as type assertion.
            raise ValueError("invalid type - {}".format(value))

    def __init__(self, value):
        # logger.debug("ValueParse.__init__ is called with self = %s" % self)
        super(ValueParse, self).__init__(value)

    def _set_parse(self, value):
        self._parse = value

    def _merge_parse(self, other_parse):
        self._parse = self._parse if self._parse else other_parse

    def vars(self):
        ret = dict()
        ret.update(self._meta)
        ret["$parse"] = self._parse
        return ret

    def get_type(self):
        if isinstance(self, BoolParse):
            return "$bool"
        elif isinstance(self, IntParse):
            return "$int"
        elif isinstance(self, FloatParse):
            return "$float"
        elif isinstance(self, StrParse):
            return "$str"
        elif isinstance(self, NoneParse):
            return "$none"


class BoolParse(ValueParse): pass


class IntParse(ValueParse):
    def _merge_parse(self, other_parse):
        self._parse = self._parse if self._parse > other_parse else other_parse


class FloatParse(ValueParse):
    def _merge_parse(self, other_parse):
        self._parse = self._parse if self._parse > other_parse else other_parse


class StrParse(ValueParse): pass


class NoneParse(ValueParse): pass


class KeyValueParse(BaseParse):
    """
    This class cannot be created by BaseParse(value)
    """

    def __init__(self, key, value):
        self._lhs = key
        super(KeyValueParse, self).__init__(value)

    def _set_parse(self, value):
        self._parse = [BaseParse(value)]

    @staticmethod
    @check_same_type
    def _merge_parse_cb(this_, other_):
        # Two instances of BaseParse that share same type
        this_.merge(other_)
        return this_

    def _merge_parse(self, other_parse):
        self._parse = merge_list(self._parse, other_parse, self._merge_parse_cb)

    def vars(self):
        ret_parse = dict()
        for base_parse in self._parse:
            ret_parse[base_parse.get_type()] = base_parse.vars()
        ret = dict()
        # TODO what's that?
        ret.update(self._meta)
        ret["$parse"] = ret_parse
        return ret

    def get_type(self):
        return self._lhs


class DictParse(BaseParse):
    @check_is_type(dict)
    def __init__(self, value):
        super(DictParse, self).__init__(value)

    def _set_parse(self, value):
        for lhs, rhs in value.items():
            # lhs are unique, its okay to append.
            self._parse.append(KeyValueParse(lhs, rhs))

    @staticmethod
    @check_same_type
    def _merge_parse_cb(this_, other_):
        # Two instances of KeyValueParse that share same lhs according to .get_type()
        this_.merge(other_)
        return this_

    def _merge_parse(self, other_parse):
        self._parse = merge_list(self._parse, other_parse,
                                 self._merge_parse_cb, comp=lambda o: o.get_type())

    def vars(self):
        ret_parse = dict()
        for key_value_parse in self._parse:
            ret_parse[key_value_parse.get_type()] = key_value_parse.vars()
        ret = dict()
        ret.update(self._meta)
        ret["$parse"] = ret_parse
        return ret

    def get_type(self):
        return "$dict"


class ListParse(BaseParse):
    @check_is_type((list, types.GeneratorType))
    def __init__(self, value):
        super(ListParse, self).__init__(value)

    def _set_parse(self, value):
        for item in value:
            if len(self._parse) == 0:
                self._parse.append(BaseParse(item))
            else:
                item_parse = ListParse([item])
                self.merge(item_parse)

    @staticmethod
    @check_same_type
    def _merge_parse_cb(this_, other_):
        # Two instances of BaseParse that share same type
        this_.merge(other_)
        return this_

    def _merge_parse(self, other_parse):
        self._parse = merge_list(self._parse, other_parse, self._merge_parse_cb)

    def vars(self):
        ret_parse = dict()
        for base_parse in self._parse:
            ret_parse[base_parse.get_type()] = base_parse.vars()
        ret = {
            "$parse": ret_parse
        }
        ret.update(self._meta)
        return ret

    def get_type(self):
        return "$list"


def flat_vars(doc):
    """
    Flat given nested dict, but keep the last layer of dict object unchanged.
    :param doc: nested dict object, consisted solely by dict objects.
    :return: flattened dict, with only last layer of dict un-flattened.
    """
    me = {}
    has_next_layer = False
    for key, value in doc.items():
        if isinstance(value, dict):
            has_next_layer = True
            child, is_final_layer = flat_vars(value)
            if is_final_layer:
                me[key] = child
            else:
                for child_key, child_value in child.items():
                    me["%s.%s" % (key, child_key)] = child_value
        else:
            me[key] = value
    return me, not has_next_layer


def brief_vars(vars_):
    vars_flat, _ = flat_vars(vars_)
    briefs = []
    for k, v in vars_flat.items():
        if isinstance(v, dict) and v:
            path_type = []
            path_name = []
            for node in k.split("."):
                if node == "$parse":
                    continue
                elif node.startswith("$"):
                    path_type.append(node.lstrip("$"))
                else:
                    path_name.append(node)
            v["$type"] = ".".join(path_type)
            v["$key"] = ".".join(path_name)
            briefs.append(v)
    return briefs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", type=argparse.FileType(mode="r", encoding="utf-8"),
                        default=sys.stdin, dest="fd_in",
                        help="Input jsonl path, defaults to stdin.")
    parser.add_argument("-t", "--table", dest="table", action="store_true",
                        help="Tab separated format, preempts -p -v.")
    parser.add_argument("-p", "--pretty", dest="pretty", action="store_true",
                        help="Prettify result.")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="More descriptive result.")
    opts = parser.parse_args()

    list_object = (json.loads(line.rstrip("\n")) for line in opts.fd_in)
    list_parse = BaseParse(list_object)
    list_parse_vars = list_parse.vars()

    if opts.table or not opts.verbose:
        result = brief_vars(list_parse_vars)
    else:
        result = list_parse_vars

    if opts.table:
        out = "\t".join(result[0].keys()) + "\n"
        for row in result:
            out += "\t".join(str(cell) for cell in row.values()) + "\n"
        print(out)
    elif opts.pretty:
        print(json.dumps(result, ensure_ascii=False, indent=4))
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
