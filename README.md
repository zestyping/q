q
=

Quick and dirty debugging output for tired programmers.

Install q with "easy\_install q" or "pip install q".

To print the value of foo, insert this into your program:

    import q; q.q(foo)

To trace a function's arguments and return value, insert this above the def:

    import q
    @q.t

The output will appear in /tmp/q, which you can watch with this shell command:

    tail -f /tmp/q

Disable the tracing temporarily by calling disable after importing the module,
which turns the q.q() and q.t calls into no-ops:
    import q
    q.disable()
