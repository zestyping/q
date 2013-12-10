##Install
`python setup.py install`

##Uninstall
`pip uninstall q`

##Usage
If `TMPDIR` or `TEMP` is set, the output file is `$TMPDIR/log.q` or `$TEMP/log.q`,
or you can config (just need once) it with:

    q = q.config('/path/to/record_file')

You can add `q` to `__builtin__`, then you can use `q` just like `print`

    import __builtin__
    import q
    __builtin__.__dict__['q'] = q

To print the value of something in the middle of an expression, insert
`q()` `q<` `q>` or `q<>`.
For example:
`foo(('1' + '2').join('3'))`

    import q

    @q
    def foo(arg):
        pass

    foo((q>'1' + '2').join('3'))
    foo((q<'1' + '2').join('3'))
    foo((q<>'1' + '2').join('3'))
    foo(1)

To trace a function's arguments and return value, insert this above the def:

    import q
    @q

To start an interactive console at any point in your code, call `q.d()`:

    import q; q.d()
