# Copyright 2012 Google Inc.  All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at: http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distrib-
# uted under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied.  See the License for
# specific language governing permissions and limitations under the License.

"""Quick and dirty debugging output for tired programmers.

To print the value of foo, insert this into your program:
    import q; q.q(foo)

To trace a function's arguments and return value, insert this above the def:
    import q
    @q.t

The output will appear in /tmp/q, which you can watch with this shell command:
    tail -f /tmp/q
"""

__author__ = 'Ka-Ping Yee <ping@zesty.ca>'

import ast, inspect, os, pydoc, sys, random, re, time

OUTPUT_PATH = '/tmp/q'

BOLD, NORMAL = '\x1b[1m', '\x1b[0m'
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = ('\x1b[3%dm' % i for i in range(1, 7))

def is_visible(x):
    return not x.startswith('\x1b')

# TODO: Use colour to distinguish '...' elision from actual '...' characters.
# TODO: Show a nicer repr for SRE.Match objects.
# TODO: Show a nicer repr for big multiline strings.

text_repr = pydoc.TextRepr()
def safe_repr(value):
    result = text_repr.repr(value)
    if isinstance(value, basestring) and len(value) > 80:
        # If the string is big, save it to a file for later examination.
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        name = '/tmp/q%08d.txt' % random.randrange(1e8)
        f = open(name, 'w')
        f.write(value)
        f.close()
        result += ' (file://' + name + ')'
    return result

# App Engine's dev_appserver patches 'open' to simulate the production server's
# security restrictions; we circumvent this to write to /tmp/q.
if file.__name__ == 'FakeFile':  # dev_appserver's patched file object
    original_file = file.__bases__[0]
    def open(path, mode='r'):
        if path == OUTPUT_PATH:
            return original_file(path, mode)
        return file(path, mode)

class Writer:
    """Abstract away the output pipe, timestamping, and color support."""

    def __init__(self):
        self.color = True
        self.path = OUTPUT_PATH
        self.gap_seconds = 2
        self.start_time = time.time()
        self.last_write = 0

    def write(self, chunks):
        """Writes out a list of strings as a single timestamped unit."""
        if not self.color:
            chunks = [x for x in chunks if is_visible(x)]
        content = ''.join(chunks)

        now = time.time()
        prefix = '%4.1fs ' % ((now - self.start_time) % 100)
        indent = ' ' * len(prefix)
        if self.color:
            prefix = YELLOW + prefix + NORMAL
        if now - self.last_write >= self.gap_seconds:
            prefix = '\n' + prefix
        self.last_write = now

        output = prefix + content.replace('\n', '\n' + indent)
        if self.path:
            try:
                f = open(self.path, 'a')
                f.write(output + '\n')
                f.close()
            except IOError:
                pass

class Stanza:
    """Abstract away indentation and line-wrapping."""

    def __init__(self, indent=0, width=80 - 7):
        self.chunks = [' '*indent]
        self.indent = indent
        self.column = indent
        self.width = width

    def newline(self):
        if len(self.chunks) > 1:
            self.column = self.width

    def add(self, items, sep='', wrap=True):
        """Adds a list of strings that are to be shown together on one line."""
        items = map(str, items)
        size = sum([len(x) for x in items if is_visible(x)])
        if (wrap and self.column > self.indent and
            self.column + len(sep) + size > self.width):
            self.chunks.append(sep.rstrip() + '\n' + ' '*self.indent)
            self.column = self.indent
        else:
            self.chunks.append(sep)
            self.column += len(sep)
        self.chunks.extend(items)
        self.column += size

writer = Writer()
indent = 0

def get_call_exprs(line):
    """Gets the argument expressions from the source code of a function call."""
    line = line.lstrip()
    for node in ast.walk(ast.parse(line)):
        if isinstance(node, ast.Call):
            offsets = [arg.col_offset for arg in node.args]
            if node.keywords:
                line = line[:node.keywords[0].value.col_offset]
                line = re.sub(r'\w+\s*=\s*$', '', line)
            else:
                line = re.sub(r'\s*\)\s*$', '', line)
            offsets.append(len(line))
            args = []
            for i in range(len(node.args)):
                args.append(line[offsets[i]:offsets[i + 1]].rstrip(', '))
            return args

def show(*args, **kwargs):
    """Prints out some values."""
    info = inspect.getframeinfo(sys._getframe(1))
    exprs = get_call_exprs((info.code_context or [''])[0])
    s = Stanza(indent)
    s.add([GREEN, info.function, NORMAL, ': '])
    if args:
        if exprs:
            sep = ''
            for expr, arg in zip(exprs, args):
                s.add([expr + '=', CYAN, safe_repr(arg), NORMAL], sep)
                sep = ', '
        else:
            sep = ''
            for arg in args:
                s.add([CYAN, safe_repr(arg), NORMAL], sep)
                sep = ', '
    if args and kwargs:
        s.newline()
    if kwargs:
        sep = ''
        for key in sorted(kwargs.keys()):
            s.add([key + '=', CYAN, safe_repr(kwargs[key]), NORMAL], sep)
            sep = ', '
    writer.write(s.chunks)

def unindent(lines):
    """Removes any indentation that is common to all of the given lines."""
    indent = min(len(re.match(r'^ *', line).group()) for line in lines)
    return [line[indent:].rstrip() for line in lines]

def trace(func):
    """Decorator to print out a function's arguments and return value."""

    def wrapper(*args, **kwargs):
        global indent

        # Print out the call to the function with its arguments.
        s = Stanza(indent)
        s.add([GREEN, func.__name__, NORMAL, '('])
        s.indent += 4
        sep = ''
        for arg in args:
            s.add([CYAN, safe_repr(arg), NORMAL], sep)
            sep = ', '
        for name in sorted(kwargs.keys()):
            s.add([name + '=', CYAN, safe_repr(kwargs[name]), NORMAL], sep)
            sep = ', '
        s.add(')', wrap=False)
        writer.write(s.chunks)

        # Call the function.
        indent += 2
        try:
            result = func(*args, **kwargs)
        except:
            # Display an exception.
            indent -= 2
            etype, evalue, etb = sys.exc_info()
            info = inspect.getframeinfo(etb.tb_next, context=3)
            s = Stanza(indent)
            s.add([RED, '! ', safe_repr(evalue), NORMAL])
            s.add(['at ', info.filename, ':', info.lineno], ' ')
            lines = unindent(info.code_context)
            firstlineno = info.lineno - info.index
            fmt = '%' + str(len(str(firstlineno + len(lines)))) + 'd'
            for i, line in enumerate(lines):
                s.newline()
                s.add([i == info.index and MAGENTA or '',
                       fmt % (i + firstlineno),
                       i == info.index and '> ' or ': ', line, NORMAL])
            writer.write(s.chunks)
            raise

        # Display the return value.
        indent -= 2
        s = Stanza(indent)
        s.add([GREEN, '<- ', CYAN, safe_repr(result), NORMAL])
        writer.write(s.chunks)
        return result
    return wrapper

q = show
t = trace
