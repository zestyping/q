# Copyright 2012 Google Inc.  All Rights Reserved.
# vim: set ts=4 sw=4 et sts=4 ai:
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

All output goes to /tmp/q, which you can watch with this shell command:

    tail -f /tmp/q

If TMPDIR is set, the output goes to $TMPDIR/q.

To print the value of foo, insert this into your program:

    import q; q(foo)

To print the value of something in the middle of an expression, insert
"q()", "q/", or "q|".  For example, given this statement:

    file.write(prefix + (sep or '').join(items))

...you can print out various values without using any temporary variables:

    file.write(prefix + q(sep or '').join(items))  # prints (sep or '')
    file.write(q/prefix + (sep or '').join(items))  # prints prefix
    file.write(q|prefix + (sep or '').join(items))  # prints the arg to write

To trace a function's arguments and return value, insert this above the def:

    import q
    @q

To start an interactive console at any point in your code, call q.d():

    import q; q.d()
"""

from __future__ import print_function

import sys

__author__ = 'Ka-Ping Yee <ping@zesty.ca>'

# WARNING: Horrible abuse of sys.modules, __call__, __div__, __or__, inspect,
# sys._getframe, and more!  q's behaviour changes depending on the text of the
# source code near its call site.  Don't ever do this in real code!

# These are reused below in both Q and Writer.
ESCAPE_SEQUENCES = ['\x1b[0m'] + ['\x1b[3%dm' % i for i in range(1, 7)]

if sys.version_info >= (3,):
    BASESTRING_TYPES = (str, bytes)
    TEXT_TYPES = (str,)
else:
    BASESTRING_TYPES = (basestring,)  # noqa
    TEXT_TYPES = (unicode,)  # noqa


# When we insert Q() into sys.modules, all the globals become None, so we
# have to keep everything we use inside the Q class.
class Q(object):
    __doc__ = __doc__  # from the module's __doc__ above

    import ast
    import code
    import dis
    import functools
    import inspect
    import os
    import pydoc
    import random
    import re
    import sys
    import tempfile
    import time

    # The debugging log will go to this file; temporary files will also have
    # this path as a prefix, followed by a random number.
    OUTPUT_PATH = os.path.join(tempfile.gettempdir(), 'q')

    NORMAL, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = ESCAPE_SEQUENCES
    TEXT_REPR = pydoc.TextRepr()
    q_max_length = 1000000

    @property
    def short(self):
        cls = self.__class__
        cls.TEXT_REPR = cls.pydoc.TextRepr()

    @property
    def long(self):
        cls = self.__class__
        cls.TEXT_REPR = cls.pydoc.TextRepr()
        cls.TEXT_REPR.maxarray = cls.q_max_length
        cls.TEXT_REPR.maxdeque = cls.q_max_length
        cls.TEXT_REPR.maxdict = cls.q_max_length
        cls.TEXT_REPR.maxfrozenset = cls.q_max_length
        cls.TEXT_REPR.maxlevel = cls.q_max_length
        cls.TEXT_REPR.maxlist = cls.q_max_length
        cls.TEXT_REPR.maxlong = cls.q_max_length
        cls.TEXT_REPR.maxother = cls.q_max_length
        cls.TEXT_REPR.maxset = cls.q_max_length
        cls.TEXT_REPR.maxstring = cls.q_max_length
        cls.TEXT_REPR.maxtuple = cls.q_max_length

    @long.setter
    def long(self, value):
        cls = self.__class__
        cls.q_max_length = value
        self.long

    # For portably converting strings between python2 and python3
    BASESTRING_TYPES = BASESTRING_TYPES
    TEXT_TYPES = TEXT_TYPES

    class FileWriter(object):
        """An object that appends to or overwrites a single file."""
        import sys

        # For portably converting strings between python2 and python3
        BASESTRING_TYPES = BASESTRING_TYPES
        TEXT_TYPES = TEXT_TYPES

        def __init__(self, path):
            self.path = path
            self.open = open
            # App Engine's dev_appserver patches 'open' to simulate security
            # restrictions in production; we circumvent this to write output.
            if open.__name__ == 'FakeFile':  # dev_appserver's patched 'file'
                self.open = open.__bases__[0]  # the original built-in 'file'

        def write(self, mode, content):
            if 'b' not in mode:
                mode = '%sb' % mode
            if (isinstance(content, self.BASESTRING_TYPES) and
                    isinstance(content, self.TEXT_TYPES)):
                content = content.encode('utf-8')
            try:
                f = self.open(self.path, mode)
                f.write(content)
                f.close()
            except IOError:
                pass

    class Writer:
        """Abstract away the output pipe, timestamping, and color support."""

        NORMAL, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN = ESCAPE_SEQUENCES

        def __init__(self, file_writer, time):
            self.color = True
            self.file_writer = file_writer
            self.gap_seconds = 2
            self.time = time  # the 'time' module (needed because no globals)
            self.start_time = self.time.time()
            self.last_write = 0

        def write(self, chunks):
            """Writes out a list of strings as a single timestamped unit."""
            if not self.color:
                chunks = [x for x in chunks if not x.startswith('\x1b')]
            content = ''.join(chunks)

            now = self.time.time()
            prefix = '%4.1fs ' % ((now - self.start_time) % 100)
            indent = ' ' * len(prefix)
            if self.color:
                prefix = self.YELLOW + prefix + self.NORMAL
            if now - self.last_write >= self.gap_seconds:
                prefix = '\n' + prefix
            self.last_write = now

            output = prefix + content.replace('\n', '\n' + indent)
            self.file_writer.write('a', output + '\n')

    class Stanza:
        """Abstract away indentation and line-wrapping."""

        def __init__(self, indent=0, width=80 - 7):
            self.chunks = [' ' * indent]
            self.indent = indent
            self.column = indent
            self.width = width

        def newline(self):
            if len(self.chunks) > 1:
                self.column = self.width

        def add(self, items, sep='', wrap=True):
            """Adds a list of strings that are to be printed on one line."""
            items = list(map(str, items))
            size = sum([len(x) for x in items if not x.startswith('\x1b')])
            if (wrap and self.column > self.indent and
                    self.column + len(sep) + size > self.width):
                self.chunks.append(sep.rstrip() + '\n' + ' ' * self.indent)
                self.column = self.indent
            else:
                self.chunks.append(sep)
                self.column += len(sep)
            self.chunks.extend(items)
            self.column += size

    def __init__(self):
        self.writer = self.Writer(self.FileWriter(self.OUTPUT_PATH), self.time)
        self.indent = 0
        # in_console tracks whether we're in an interactive console.
        # We use it to display the caller as "<console>" instead of "<module>".
        self.in_console = False

    def unindent(self, lines):
        """Removes any indentation that is common to all of the given lines."""
        indent = min(
            len(self.re.match(r'^ *', line).group()) for line in lines)
        return [line[indent:].rstrip() for line in lines]

    def safe_repr(self, value):
        # TODO: Use colour to distinguish '...' elision from actual '...'
        # TODO: Show a nicer repr for SRE.Match objects.
        # TODO: Show a nicer repr for big multiline strings.
        result = self.TEXT_REPR.repr(value)
        if isinstance(value, self.BASESTRING_TYPES) and len(value) > 80:
            # If the string is big, save it to a file for later examination.
            if isinstance(value, self.TEXT_TYPES):
                value = value.encode('utf-8')
            path = self.OUTPUT_PATH + (
                    '%08d.txt' % self.random.randrange(100000000))
            self.FileWriter(path).write('w', value)
            result += ' (file://' + path + ')'
        return result

    class CallVisitor(ast.NodeVisitor):
        def __init__(self, call_position):
            self.current_position = 0
            self.call_position = call_position
            self.call_node = None

        def visit_Call(self, node):
            # Arguments have a lower call position then the function call
            # For instance, in q(q(1) + q(2)),
            # q(1) has position 0, q(2) has position 1,
            # and q(q(1) + q(2)) has position 2
            for arg in node.args:
                self.visit(arg)

            if self.current_position == self.call_position:
                self.call_node = node

            self.current_position += 1

    def get_call_exprs(self, caller_frame, line):
        """Gets the argument expressions from the source of a function call."""
        line = line.lstrip()
        try:
            tree = self.ast.parse(line)
        except SyntaxError:
            return None

        if self.sys.version_info >= (3, 8):
            return self._get_accurate_call_exprs(caller_frame, line, tree)

        return self._get_basic_call_exprs(caller_frame, line, tree)

    def _get_basic_call_exprs(self, caller_frame, line, tree):
        """Gets the argument expressions from the source of a function call.

        Slightly buggy (multiple calls to q() on a single line cause garbled
        output, #67), but works on all Python versions.
        """
        for node in self.ast.walk(tree):
            if isinstance(node, self.ast.Call):
                offsets = []
                for arg in node.args:
                    # In Python 3.4 the col_offset is calculated wrong. See
                    # https://bugs.python.org/issue21295
                    if isinstance(arg, self.ast.Attribute) and (
                            (3, 4, 0) <= self.sys.version_info <= (3, 4, 3)):
                        offsets.append(arg.col_offset - len(arg.value.id) - 1)
                    else:
                        offsets.append(arg.col_offset)
                if node.keywords:
                    line = line[:node.keywords[0].value.col_offset]
                    line = self.re.sub(r'\w+\s*=\s*$', '', line)
                else:
                    line = self.re.sub(r'\s*\)\s*$', '', line)
                offsets.append(len(line))
                args = []
                for i in range(len(node.args)):
                    args.append(line[offsets[i]:offsets[i + 1]].rstrip(', '))
                return args

    def _get_accurate_call_exprs(self, caller_frame, line, tree):
        """Gets the argument expressions from the source of a function call.

        Accurate, but depends on Python 3.8+.
        """
        # There can be multiple function calls on a line
        # (for example: q(1) + q(2)), so in order to show
        # correct output, we need to identify what function call we
        # are getting the call expressions for. To do this, we can
        # use frame data to get the caller's bytecode and the
        # bytecode instruction being executed. We can then
        # count the number of CALL_* opcodes before the condition
        # `instruction.starts_line is not None` is met.
        caller_bytecode = caller_frame.f_code
        call_bytecode_instruction_offset = caller_frame.f_lasti
        bytecode_instructions = \
            tuple(self.dis.get_instructions(caller_bytecode))
        call_bytecode_instruction_index = 0
        for instruction in bytecode_instructions:
            if instruction.offset == call_bytecode_instruction_offset:
                break
            elif instruction.offset > call_bytecode_instruction_offset:
                # It seems sometimes CACHE instructions cause
                # caller_frame.f_lasti to be after the call instruction offset
                call_bytecode_instruction_index -= 1
                break
            call_bytecode_instruction_index += 1

        current_bytecode_instruction = \
            bytecode_instructions[call_bytecode_instruction_index]
        position_of_call_on_line = 0
        instruction_index = call_bytecode_instruction_index
        while current_bytecode_instruction.starts_line is None:
            instruction_index = instruction_index - 1
            current_bytecode_instruction = \
                bytecode_instructions[instruction_index]
            if current_bytecode_instruction.opname.startswith('CALL'):
                position_of_call_on_line += 1

        call_visitor = self.CallVisitor(position_of_call_on_line)
        call_visitor.visit(tree)
        node = call_visitor.call_node

        offsets = []
        for arg in node.args:
            offsets.append(arg.col_offset)
        if node.keywords:
            line = line[:node.keywords[0].value.col_offset]
            line = self.re.sub(r'\w+\s*=\s*$', '', line)
        else:
            line = self.re.sub(r'\s*\)\s*$', '', line)
        offsets.append(node.end_col_offset - 1)
        args = []
        for i in range(len(node.args)):
            args.append(line[offsets[i]:offsets[i + 1]].rstrip(', '))
        return args

    def show(self, func_name, values, labels=None):
        """Prints out nice representations of the given values."""
        s = self.Stanza(self.indent)
        if func_name == '<module>' and self.in_console:
            func_name = '<console>'
        s.add([func_name + ': '])
        reprs = map(self.safe_repr, values)
        if labels:
            sep = ''
            for label, repr in zip(labels, reprs):
                s.add([label + '=', self.CYAN, repr, self.NORMAL], sep)
                sep = ', '
        else:
            sep = ''
            for repr in reprs:
                s.add([self.CYAN, repr, self.NORMAL], sep)
                sep = ', '
        self.writer.write(s.chunks)

    def trace(self, func):
        """Decorator to print out a function's arguments and return value."""

        def get_func_name(func):
            return getattr(func, "__qualname__", func.__name__)

        def wrapper(*args, **kwargs):
            # Print out the call to the function with its arguments.
            s = self.Stanza(self.indent)
            s.add([self.GREEN, get_func_name(func), self.NORMAL, '('])
            s.indent += 4
            sep = ''
            for arg in args:
                s.add([self.CYAN, self.safe_repr(arg), self.NORMAL], sep)
                sep = ', '
            for name, value in sorted(kwargs.items()):
                s.add([name + '=', self.CYAN, self.safe_repr(value),
                       self.NORMAL], sep)
                sep = ', '
            s.add(')', wrap=False)
            self.writer.write(s.chunks)

            # Call the function.
            self.indent += 2
            start_time = self.time.time()
            try:
                result = func(*args, **kwargs)
            except Exception:
                # Display an exception.
                self.indent -= 2
                etype, evalue, etb = self.sys.exc_info()
                info = self.inspect.getframeinfo(etb.tb_next, context=3)
                s = self.Stanza(self.indent)
                s.add([self.YELLOW,
                       '(+%.1fs) ' % (self.time.time() - start_time),
                       self.NORMAL])
                s.add([self.RED, '!> ', self.safe_repr(evalue), self.NORMAL])
                s.add(['at ', info.filename, ':', info.lineno], ' ')
                lines = self.unindent(info.code_context)
                firstlineno = info.lineno - info.index
                fmt = '%' + str(len(str(firstlineno + len(lines)))) + 'd'
                for i, line in enumerate(lines):
                    s.newline()
                    s.add([
                        i == info.index and self.MAGENTA or '',
                        fmt % (i + firstlineno),
                        i == info.index and '> ' or ': ', line, self.NORMAL])
                self.writer.write(s.chunks)
                raise

            # Display the time taken and return value.
            self.indent -= 2
            s = self.Stanza(self.indent)
            s.add([self.YELLOW, '(+%.1fs) ' % (self.time.time() - start_time),
                   self.NORMAL])
            s.add([self.GREEN, '-> ', self.CYAN, self.safe_repr(result),
                   self.NORMAL])
            self.writer.write(s.chunks)
            return result
        return self.functools.update_wrapper(wrapper, func)

    def __call__(self, *args):
        """If invoked as a decorator on a function, adds tracing output to the
        function; otherwise immediately prints out the arguments."""
        caller_frame = self.sys._getframe(1)
        info = self.inspect.getframeinfo(caller_frame, context=9)

        # info.index is the index of the line containing the end of the call
        # expression, so this gets a few lines up to the end of the expression.
        lines = ['']
        if info.code_context:
            lines = info.code_context[:info.index + 1]

        # If we see "@q" on a single line, behave like a trace decorator.
        for line in lines:
            if line.strip() in ('@q', '@q()') and args:
                return self.trace(args[0])

        # Otherwise, search for the beginning of the call expression; once it
        # parses, use the expressions in the call to label the debugging
        # output.
        for i in range(1, len(lines) + 1):
            labels = self.get_call_exprs(caller_frame,
                                         ''.join(lines[-i:]).replace('\n', ''))
            if labels:
                break
        self.show(info.function, args, labels)
        return args and args[0]

    def __truediv__(self, arg):  # a tight-binding operator
        """Prints out and returns the argument."""
        info = self.inspect.getframeinfo(self.sys._getframe(1))
        self.show(info.function, [arg])
        return arg
    # Compat for Python 2 without from future import __division__ turned on
    __div__ = __truediv__

    __or__ = __div__  # a loose-binding operator
    q = __call__  # backward compatibility with @q.q
    t = trace  # backward compatibility with @q.t
    __name__ = 'Q'  # App Engine's import hook dies if this isn't present

    def d(self, depth=1):
        """Launches an interactive console at the point where it's called."""
        info = self.inspect.getframeinfo(self.sys._getframe(1))
        s = self.Stanza(self.indent)
        s.add([info.function + ': '])
        s.add([self.MAGENTA, 'Interactive console opened', self.NORMAL])
        self.writer.write(s.chunks)

        frame = self.sys._getframe(depth)
        env = frame.f_globals.copy()
        env.update(frame.f_locals)
        self.indent += 2
        self.in_console = True
        self.code.interact(
            'Python console opened by q.d() in ' + info.function, local=env)
        self.in_console = False
        self.indent -= 2

        s = self.Stanza(self.indent)
        s.add([info.function + ': '])
        s.add([self.MAGENTA, 'Interactive console closed', self.NORMAL])
        self.writer.write(s.chunks)


# Install the Q() object in sys.modules so that "import q" gives a callable q.
q = Q()
q.long
sys.modules['q'] = q
