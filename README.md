# q

[![Code Shelter](https://www.codeshelter.co/static/badges/badge-flat.svg)](https://www.codeshelter.co/) [![Build Status](https://travis-ci.org/zestyping/q.svg)](https://travis-ci.org/zestyping/q)

Quick and dirty debugging output for tired programmers.

For a short demo, watch the [Lightning Talk](http://pyvideo.org/video/1858/sunday-evening-lightning-talks#t=25m15s) from PyCon 2013.

Install q with `pip install -U q`.

All output goes to `/tmp/q` (or on Windows, to `$HOME/tmp/q`).  You can
watch the output with this shell command while your program is running:

    tail -f /tmp/q

To print the value of foo, insert this into your program:

    import q; q(foo)

To print the value of something in the middle of an expression, you can
wrap it with `q()`.  You can also insert `q/` or `q|` into the expression;
`q/` binds tightly whereas `q|` binds loosely.  For example, given this
statement:

    file.write(prefix + (sep or '').join(items))

you can print out various values without using any temporary variables:

    file.write(prefix + q(sep or '').join(items))  # prints (sep or '')
    file.write(q/prefix + (sep or '').join(items))  # prints prefix
    file.write(q|prefix + (sep or '').join(items))  # prints the arg to write

To trace a function (showing its arguments, return value, and running time),
insert this above the def:

    import q
    @q

To start an interactive console at any point in your code, call q.d():

    import q; q.d()

# Other projects inspired by this one

* [`q` for golang](https://github.com/y0ssar1an/q) 
* [`qq` for elixir](https://github.com/mandarvaze/q)
* [`ic` for Python](https://github.com/gruns/icecream) - Similar library for Python, inspired by `q`.
