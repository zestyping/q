q
=

[![Build Status](https://travis-ci.org/zestyping/q.svg)](https://travis-ci.org/zestyping/q)

Quick and dirty debugging output for tired programmers.

Install q with "easy\_install -U q" or "pip install -U q".

All output goes to /tmp/q, which you can watch with this shell command::

    tail -f /tmp/q

If TMPDIR is set, the output goes to $TMPDIR/q.

To print the value of foo, insert this into your program::

    import q; q(foo)

To print the value of something in the middle of an expression, insert
"q()", "q/", or "q|".  For example, given this statement::

    file.write(prefix + (sep or '').join(items))

...you can print out various values without using any temporary variables::

    file.write(prefix + q(sep or '').join(items))  # prints (sep or '')
    file.write(q/prefix + (sep or '').join(items))  # prints prefix
    file.write(q|prefix + (sep or '').join(items))  # prints the arg to write

To trace a function's arguments and return value, insert this above the def::

    import q
    @q

To start an interactive console at any point in your code, call q.d()::

    import q; q.d()

The following
[Lightning Talk](http://pyvideo.org/video/1858/sunday-evening-lightning-talks#t=25m15s)
shows how powerful using q can be.
