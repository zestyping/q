q
=

### Po's change log:

1. made it to work on *Windows*
2. on Windows, the output will be in the **current working folder**
3. the file name will be `loq`
4. added some print statements to give exception information
5. if on *Linux / Mac / others*, it works in the original way

------------

Quick and dirty debugging output for tired programmers.

Install q with "easy\_install -U q" or "pip install -U q".

All output goes to /tmp/q, which you can watch with this shell command:

    tail -f /tmp/q

on Windows:

    tail -f ./loq

or just  

    tail -f loq

To print the value of foo, insert this into your program:

    import q; q(foo)

Use "q/" to print the value of something in the middle of an expression
while leaving the result unaffected.  In this example, you can print the
value of f(y) without needing to put f(y) in a temporary variable:

    x = q/f(y) + z

To trace a function's arguments and return value, insert this above the def:

    import q
    @q
