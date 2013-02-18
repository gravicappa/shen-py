import imp
import shenpy
import runtime
import list

imp.reload(shenpy)
imp.reload(runtime)
imp.reload(list)

def t(func, *args):
    print("")
    str_args = " ".join(tuple(map(str, args)))
    print("CALLING: ({0} {1})".format(func.__name__, str_args))
    ret = shenpy.call(func, *args)
    print("=> {0}".format(ret))

t(shenpy.fns["list-len"], shenpy.dbg_list([1, 2, 3, 4, 5, 6]))
t(shenpy.fns["list-len*"], shenpy.dbg_list([1, 2, 3, 4, 5, 6]))
t(shenpy.fns["use-adder"], 5, 7)
t(shenpy.fns["use-freeze"], 11)
t(shenpy.fns["wo-trap-error"], 19)
t(shenpy.fns["use-trap-error-1"], 19)
t(shenpy.fns["use-trap-error-2"], 91)
