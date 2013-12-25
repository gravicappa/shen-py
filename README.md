Introduction
------------
This is Python version of a [Shen language](http://shenlanguage.org). In
current state it is only a showcase and side-effect of my [klvm
translator](https://github.com/gravicappa/klvm) and unbearably slow. Also keep
in mind that I haven't written Python before.

Running
-------
Go to directory where `shen.py` is and type

    python -m runshen

If you imported shen from Python repl you can start Shen repl via

    shen.repl()

or call a Shen function via

    shen.call("function-name", *args)

Python integration
------------------
To define a Shen function from Python use shen.proc decorator.

    # Theese code samples define `poly1` and `poly2` shen functions
    
    @shen.proc
    def poly1(x, a, b):
      return a * x + b
    
    @shen.proc('poly2')
    def shenpy_poly2(x, a, b, c):
      return a * x * x + b * x + c

To load Python file from Shen use `shenpy.load` function.
