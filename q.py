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

__author__ = 'Ka-Ping Yee <ping@zesty.ca>'

# WARNING: q's behaviour changes depending on the text of the
# source code near its call site.  Don't ever do this in real code!


import ast, code, inspect, os, pydoc, sys, random, re, time, copy

_stdout = sys.stdout
_text_repr = pydoc.TextRepr()
_default_output_path = os.path.join(os.environ.get('TMPDIR') or os.environ.get('TEMP') or '/tmp', 'log.q')
_escape_sequences = ['\x1b[0m'] + ['\x1b[3%dm' % i for i in range(1, 7)]
_normal, _red, _green, _yellow, _blue, _magenta, _cyan = _escape_sequences
if sys.version_info >= (3,):
    _basestring_types = (str, bytes)
    _text_types = (str,)
else:
    _basestring_types = (basestring,)
    _text_types = (unicode,)


class Q(object):
    """Quick and dirty debugging output for tired programmers.

    If TMPDIR or TEMP is set, the output file is $TMPDIR/log.q or $TEMP/log.q,
    or you can config it with (just need once):

        q = q.config('/path/to/record_file')

    You can add `q` to `__builtin__`, then you can use `q` just like `print`

        import __builtin__
        import q
        __builtin__.__dict__['q'] = q

    To print the value of something in the middle of an expression, insert
    `q()`, `q<`, `q>` or `q<>`.  For example:

        foo(('1' + '2').join('3'))

    >>> import q
    >>> foo = lambda x: None
    >>> # print to stdout
    >>> foo((q>'1' + '2').join('3'))

     0.0s 1    <doctest __main__.Q[2]> '12'

    foo((q>'1' + '2').join('3'))

    >>> # print to file
    >>> foo((q<'1' + '2').join('3'))
    >>> # print to file and stdout
    >>> foo((q<>'1' + '2').join('3'))

     0.0s 1    <doctest __main__.Q[4]> '12'

    foo((q<>'1' + '2').join('3'))


    >>> @q
    ... def foo(arg):
    ...     pass
    ...
    ...
    >>> foo(1)

    To trace a function's arguments and return value, insert this above the def:

        import q
        @q

    To start an interactive console at any point in your code, call q.d():

        import q; q.d()
    """

    class FileWriter(object):
        """An object that appends to or overwrites a single file."""
        def __init__(self, path, to_stdout=False):
            self.path = path
            self.open = open
            self.to_stdout = to_stdout
            # App Engine's dev_appserver patches 'open' to simulate security
            # restrictions in production; we circumvent this to write output.
            if open.__name__ == 'FakeFile':  # dev_appserver's patched 'file'
                self.open = open.__bases__[0]  # the original built-in 'file'

        def write(self, mode, content):
            if 'b' not in mode:
                mode = '%sb' % mode
            if isinstance(content, _basestring_types) and isinstance(content, _text_types):
                content = content.encode('utf-8')
            try:
                if self.to_stdout:
                    f = _stdout
                    f.write(content)
                else:
                    f = self.open(self.path, mode)
                    f.write(content)
                    f.close()
            except IOError:
                pass


    class Writer:
        """Abstract away the output pipe, timestamping, and color support."""
        def __init__(self, file_writer):
            self.color = True
            self.file_writer = file_writer
            self.gap_seconds = 2
            self.start_time = time.time()
            self.last_write = 0

        def write(self, chunks):
            content = ''.join(chunks)

            now = time.time()
            prefix = '%4.1fs ' % ((now - self.start_time) % 100)
            indent = ' ' * len(prefix)
            if self.color:
                prefix = _yellow + prefix + _normal
            if now - self.last_write >= self.gap_seconds:
                prefix = '\n' + prefix
            self.last_write = now

            output = prefix + content
            self.file_writer.write('a', output + '\n')


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
            """Adds a list of strings that are to be printed on one line."""
            items = list(map(str, items))
            size = sum([len(x) for x in items if not x.startswith('\x1b')])
            if (wrap and self.column > self.indent and
                self.column + len(sep) + size > self.width):
                self.chunks.append(sep.rstrip() + '\n' + ' '*self.indent)
                self.column = self.indent
            else:
                self.chunks.append(sep)
                self.column += len(sep)
            self.chunks.extend(items)
            self.column += size


    def __init__(self, output_path=None):
        self.output_path = output_path or _default_output_path
        self.writer_file = self.Writer(self.FileWriter(self.output_path))
        self.writer_stdout = self.Writer(self.FileWriter(self.output_path, to_stdout=True))
        self.writer = self.writer_file or self.writer_stdout
        self.indent = 0
        # in_console tracks whether we're in an interactive console.
        # We use it to display the caller as "<console>" instead of "<module>".
        self.in_console = False

    def unindent(self, lines):
        """Removes any indentation that is common to all of the given lines."""
        indent = min(len(self.re.match(r'^ *', line).group()) for line in lines)
        return [line[indent:].rstrip() for line in lines]

    def safe_repr(self, value):
        # TODO: Use colour to distinguish '...' elision from actual '...' chars.
        # TODO: Show a nicer repr for SRE.Match objects.
        # TODO: Show a nicer repr for big multiline strings.
        result = _text_repr.repr(value)
        if isinstance(value, _basestring_types) and len(value) > 80:
            # If the string is big, save it to a file for later examination.
            if isinstance(value,  _text_types):
                value = value.encode('utf-8')
            path = self.output_path + '%08d.txt' % random.randrange(1e8)
            self.FileWriter(path).write('w', value)
            result += ' (file://' + path + ')'
        return result

    def get_call_exprs(self, line):
        """Gets the argument expressions from the source of a function call."""
        line = line.lstrip()
        try:
            tree = self.ast.parse(line)
        except SyntaxError:
            return None
        for node in self.ast.walk(tree):
            if isinstance(node, self.ast.Call):
                offsets = [arg.col_offset for arg in node.args]
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

    def _log(self, writer, traceback, values, labels=None):
        """Prints out nice representations of the given values."""
        s = self.Stanza(self.indent)
        t = traceback
        s.add([_green,'%-4s ' % t.lineno, _normal])
        s.add([_green, t.filename + ' ', _normal])
        reprs = map(self.safe_repr, values)
        if labels:
            sep = ''
            for label, repr in zip(labels, reprs):
                s.add([label + '=', _cyan, repr, _normal], sep)
                sep = ', '
        else:
            sep = ''
            for repr in reprs:
                s.add([_cyan, repr, _normal], sep)
                sep = ', '
        s.add(['\n', ''.join(t.code_context)])
        writer.write(s.chunks)

    def log_to_file(self, *args, **kwargs):
        self._log(self.writer_file, *args, **kwargs)

    def log_to_stdout(self, *args, **kwargs):
        self._log(self.writer_stdout, *args, **kwargs)

    def trace(self, func):
        """Decorator to print out a function's arguments and return value."""

        def wrapper(*args, **kwargs):
            # Print out the call to the function with its arguments.
            s = self.Stanza(self.indent)
            s.add([_green, func.__name__, _normal, '('])
            s.indent += 4
            sep = ''
            for arg in args:
                s.add([_cyan, self.safe_repr(arg), _normal], sep)
                sep = ', '
            for name, value in sorted(kwargs.items()):
                s.add([name + '=', _cyan, self.safe_repr(value),
                       _normal], sep)
                sep = ', '
            s.add(')', wrap=False)
            self.writer.write(s.chunks)

            # Call the function.
            self.indent += 2
            try:
                result = func(*args, **kwargs)
            except:
                # Display an exception.
                self.indent -= 2
                etype, evalue, etb = sys.exc_info()
                info = self.inspect.getframeinfo(etb.tb_next, context=3)
                s = self.Stanza(self.indent)
                s.add([_red, '!> ', self.safe_repr(evalue), _normal])
                s.add(['at ', info.filename, ':', info.lineno], ' ')
                lines = self.unindent(info.code_context)
                firstlineno = info.lineno - info.index
                fmt = '%' + str(len(str(firstlineno + len(lines)))) + 'd'
                for i, line in enumerate(lines):
                    s.newline()
                    s.add([i == info.index and _magenta or '',
                           fmt % (i + firstlineno),
                           i == info.index and '> ' or ': ', line, _normal])
                self.writer.write(s.chunks)
                raise

            # Display the return value.
            self.indent -= 2
            s = self.Stanza(self.indent)
            s.add([_green, '-> ', _cyan, self.safe_repr(result), _normal])
            self.writer.write(s.chunks)
            return result
        return wrapper

    def __call__(self, *args):
        """If invoked as a decorator on a function, adds tracing output to the
        function; otherwise immediately prints out the arguments."""
        info = inspect.getframeinfo(sys._getframe(1), context=9)

        # info.index is the index of the line containing the end of the call
        # expression, so this gets a few lines up to the end of the expression.
        lines = ['']
        if info.code_context:
            lines = info.code_context[:info.index + 1]

        # If we see "@q" on a single line, behave like a trace decorator.
        if lines[-1].strip().startswith('@') and args:
            return self.trace(args[0])

        # Otherwise, search for the beginning of the call expression; once it
        # parses, use the expressions in the call to label the debugging output.
        for i in range(1, len(lines) + 1):
            labels = self.get_call_exprs(''.join(lines[-i:]).replace('\n', ''))
            if labels:
                break
        self.log_to_file(info, args, labels)
        return args and args[0]

    # <
    def __lt__(self, arg):
        info = inspect.getframeinfo(sys._getframe(1))
        self.log_to_file(info, [arg])
        return arg

    # >
    def __gt__(self, arg):
        info = inspect.getframeinfo(sys._getframe(1))
        self.log_to_stdout(info, [arg])
        return arg

    # <>
    def __ne__(self, arg):
        info = inspect.getframeinfo(sys._getframe(1))
        self.log_to_file(info, [arg])
        self.log_to_stdout(info, [arg])
        return arg

    # backward compatibility with @q.q
    q = __call__
    # backward compatibility with @q.t
    t = trace
    # App Engine's import hook dies if this isn't present
    __name__ = 'Q'

    def d(self, depth=1):
        """Launches an interactive console at the point where it's called."""
        info = inspect.getframeinfo(sys._getframe(1))
        s = self.Stanza(self.indent)
        s.add([info.function + ': '])
        s.add([_magenta, 'Interactive console opened', _normal])
        self.writer.write(s.chunks)

        frame = sys._getframe(depth)
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
        s.add([_magenta, 'Interactive console closed', _normal])
        self.writer.write(s.chunks)

    @classmethod
    def config(cls, filename=None):
        """config the output path"""
        q = Q(filename)
        # When we insert Q() into sys.modules, all the globals become None
        # so we have to copy everything
        _globals = copy.copy(globals())
        sys.modules['q'] = q
        globals().update(_globals)
        return q


Q.config()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
