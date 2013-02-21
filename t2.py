import imp
import shenpy
import runtime
import std
import list

imp.reload(shenpy)
imp.reload(runtime)
imp.reload(std)
imp.reload(list)

shenpy.show_step = False

def t(expr, result = None):
    print("")
    func = expr[0]
    args = expr[1:]
    str_args = " ".join(tuple(map(str, args)))
    print("CALLING: ({0} {1})".format(func.__name__, str_args))
    ret = shenpy.call(func, *args)
    print("=> {0}".format(ret))
    if result == None:
        return
    elif result == ret:
        print("OK")
    else:
        print("Error: expected {0}".format(result))

t([shenpy.fns["list-len"], shenpy.dbg_list([1, 2, 3, 4, 5, 6])], 6)
t([shenpy.fns["list-len*"], shenpy.dbg_list([1, 2, 3, 4, 5, 6])], 6)
t([shenpy.fns["use-adder"], 5, 7], 12)
t([shenpy.fns["use-adder"], -5, 7], 2)
t([shenpy.fns["use-freeze"], 11], 21)
#shenpy.show_step = True
t([shenpy.fns["wo-trap-error"], 19], 19 + 19)
t([shenpy.fns["use-trap-error-1"], 19], 19 * 2)
t([shenpy.fns["use-trap-error-2"], 91], -1)
t([shenpy.fns["use-trap-error-3"], 91], -2)
t([shenpy.fns["use-trap-error-4"], 91], 0)
