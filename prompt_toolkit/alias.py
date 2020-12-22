"""
Implementations for the set of input aliases
"""
import copy
import json
import os
import re
import shlex
from typing import Dict, List, Type

__all__ = [
    "AliasList",
    "InMemoryAliasList",
    "FileAliasList"
]


class AliasList:
    """
    Base ``Alias`` class.

    Aliases serve as a way to reduce the data needed to complete a full input.  For instance, a common input
    might be "command --option1 x --option2 y --option3 z".  An alias named "cmd" with text
    "command --option1 {1} --option2 {2} --option3 {3}" would resolve to
    "command --option1 x --option2 y --option3 z" with the simple input "cmd x y z"

    Includes methods for adding an alias, resolving an alias, and merging another list
    """

    def __init__(self) -> None:
        self._loaded = False
        self._loaded_aliases: Dict[str, List[str]] = {}
        self._argregex = r"\{(.*?)\}"

    def add(self, name: str, text: str, replace: bool = False) -> None:
        if name not in self._loaded_aliases:
            self._loaded_aliases.setdefault(name, [])
        count = self._count_args(text)
        while len(self._loaded_aliases[name]) <= count:
            self._loaded_aliases[name].append('')
        if replace or self._loaded_aliases[name][count] == '':
            self._loaded_aliases[name][count] = text
        self._loaded = True

    def load_dict(self, data: Dict[str, List[str]]):
        for name in data:
            for value in data[name]:
                self.add(name, value, True)
        self._loaded = True

    def resolve(self, text: str) -> str:
        if not text:
            return ''
        parts = shlex.split(text)
        name = parts[0]
        if name not in self._loaded_aliases:
            return text
        if len(parts) > len(self._loaded_aliases[name]):
            return text
        try:
            value = self._loaded_aliases[name][len(parts) - 1]
        except IndexError:
            return text
        for i in range(len(parts)):
            part = parts[i]
            if ' ' in part:
                part = '"%s"' % part
            value = value.replace('{%s}' % i, part)
        return value

    def merge(self, other: 'AliasList', replace: bool = False) -> None:
        for name in other._loaded_aliases:
            if name not in self._loaded_aliases:
                self._loaded_aliases[name] = copy.copy(other._loaded_aliases[name])
            else:
                for i in range(len(other._loaded_aliases[name])):
                    while len(self._loaded_aliases[name]) <= i:
                        self._loaded_aliases[name].append('')
                    if replace or self._loaded_aliases[name][i] == '':
                        self._loaded_aliases[name][i] = other._loaded_aliases[name][i]

    def _count_args(self, text: str) -> int:
        argcount = 0
        matches = re.finditer(self._argregex, text)
        for num, match in enumerate(matches):
            argnum = int(match.group(1))
            argcount = argnum if argnum > argcount else argcount
        return argcount


class InMemoryAliasList(AliasList):
    def __init__(self, aliases: Dict[str, List[str]]) -> None:
        super().__init__()
        self.load_dict(aliases)


class FileAliasList(AliasList):
    def __init__(self, filename: str) -> None:
        super().__init__()
        if os.path.exists(filename):
            with open(filename) as file:
                data = json.load(file)
                self.load_dict(data)
