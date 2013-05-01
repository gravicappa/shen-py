Introduction
------------
This is Python version of a [Shen language](http://shenlanguage.org). In
current state it is only a showcase and side-effect of my [klvm
translator](https://github.com/gravicappa/klvm) and unbearably slow. Also keep
in mind that I haven't written Python before.

Running
-------
Go to directory where `shen.py` is and type

    python -m shen

If you imported shen from Python repl you can start Shen repl via

    shen.repl()

Python integration
------------------
To define a Shen function from Python use shen.defun construct:

    shen.defun("plus", 2, lambda: shen.reg[1] + shen.reg[2])

where first argument is the function's name, second is the number of
arguments, and third is a function that takes zero arguments. In that function
passed arguments are accessed via shen.reg array.

To load Python file from Shen use `shenpy.load` function.
