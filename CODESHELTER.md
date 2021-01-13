## Note to Code Shelter maintainers

Thank you so much for contributing to the maintenance of this project!
I hope it can continue to be useful to you and to others.

### Involvement

Several people still find `q` useful, but I haven't been available
to keep up with the GitHub issues for some time.  I'm grateful to
Code Shelter maintainers for help fielding these issues.

I would like to continue to be consulted on design decisions.
Because I have not been responsive, though, it is reasonable to
do this in a way that doesn't block progress.
My suggestion would be to notify me with a limited response window:
notify me, let me know when you'd like a response, and let me know
what will happen if I don't respond.
I'd appreciate being notified in this way when a design discussion
is taking place or when a previously discussed plan changes substantially.

### Philosophy

Because I have not been available to do the work, it isn't fair to
expect that all decisions will be made in exactly the way I would
make them.  Nonetheless, I thought it wouldn't hurt to share the
original intentions behind it as a guideline, in case you share my
wish to keep it on that track:

`q` is supposed to be *minimal*, *convenient*, and *predictable*.

Minimal: Its one job is to give you visibility into what's happening
in your program as it runs, and it should focus on doing that job well.

Convenient: The barrier to using `q` should be kept low.  If it's
tedious to use, no one will bother to use it.  Instrumenting a program
with `q` should require a minimum of thinking and typing.

Predictable: The behaviour of `q` must be easy to understand.
Predictability of behaviour is vital for a debugging tool, much
more so than for other programs.  There is room for some fanciness
in how values and data strucures are formatted for display, but
it is imperative that the output be unambiguous.  There should be
very little distance between the output and reality — you don't
want to have to think hard about why `q` is printing some things
and not others or why it is generating output in a particular way.

My greatest fear for the project is that the temptation to satisfy
every feature request will lead to complicated behaviour and a
multiplicity of configuration options.  One of the main strengths
of `q` is its *lack* of configuration options.
If you have to troubleshoot the configuration options to figure out
why it isn't doing what you expect, that defeats the whole point;
a debugging tool is supposed to help you debug your program, not
become another component that you also have to debug.

As a canary test, if `q` one day has a configuration file, in my
opinion, something has gone wrong.  Having to locate such a file,
define its format, and specify its options is far beyond the
level of complexity I'd ideally want.

### Releases

Code Shelter is authorized to maintain this project on PyPI; feel free
to do releases when needed.  Testing is automated with Github Actions.

Thank you!


—Ping
