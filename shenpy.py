import sys
import traceback

type_function = object()
type_symbol = object()
type_cons = object()
type_substring = object()
type_subvector = object()

error_handlers = []
error_obj = None
fns = {}
sp = -1
stack = []
reg = [None]
save_pc = None
nargs = 0

show_step = False

def stack_size(size):
    global stack, sp
    s = len(stack)
    if sp + size + 1 > s:
        stack.extend([None] * (sp + size - s + 1))

def reg_size(size):
    global reg
    if (len(reg) < size + 1):
        reg.extend([None] * (size - len(reg) + 1))

def run():
    global save_pc, error_obj, fns, show_step, nargs, sp, stack, reg
    while save_pc:
        try:
            pc = save_pc
            save_pc = None
            while pc:
                #print(pc)
                if show_step:
                    dbg_show_step(pc)
                pc = pc()
        except Exception as error:
            #print("**ERROR: {0}".format(error))
            #traceback.print_exc()
            if len(error_handlers) == 0:
                raise
            #dbg_show_step("ERROR HANDLER")
            error_obj = error
            nargs = 0
            save_pc = fns["klvm-call-error-handler"]()

def err(str):
    raise Exception(str)

def push_error_handler(e):
    global error_handlers, sp, reg, nargs
    #dbg_show_step("SET ERROR HANDLER")
    error_handlers.append([sp, nargs, reg[0], e])

def pop_error_handler():
    global error_handlers
    error_handlers.pop()

def default_error_handler():
    global error_obj
    raise error_obj

def error_unwind_get_handler():
    global error_handlers, sp, reg, error_obj
    x = error_handlers.pop()
    sp = x[0]
    nargs = x[1]
    reg[0] = x[2]
    return x[3]

dbg_step = False

def dbg_show_step(name=''):
    print("## SHOW {0}".format(name))
    print("  nargs: {0}".format(nargs))
    print("  sp: {0}".format(sp))
    i = 0
    for x in reg:
        print("    Reg[{0}]: {1}".format(i, x))
        i += 1
    i = 0
    for x in stack:
        print("    Stack[{0}]: {1}".format(i, x))
        i += 1
    print("")
    if dbg_step:
        print("--<Press return to continue>--")
        sys.stdin.readline()

def dbg_list(items):
    ret = []
    for x in reversed(items):
        ret = [type_cons, x, ret]
    return ret

def call(proc, *args):
    global reg, nargs, save_pc
    nargs = len(args)
    reg_size(nargs + 1)
    reg[0] = None
    i = 1
    for x in args:
        reg[i] = x
        i += 1
    save_pc = proc
    run()
    return reg[1]
