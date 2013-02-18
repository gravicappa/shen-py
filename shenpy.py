import sys

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

def stack_size(size):
    global stack, sp
    s = len(stack)
    if s + sp <= size:
        stack.extend([None] * size)

def reg_size(size):
    global reg
    if (len(reg) < size + 1):
        reg.extend([None] * (size - len(reg) + 1))

def run():
    global save_pc
    while save_pc:
        try:
            pc = save_pc
            save_pc = None
            while pc:
                #print(pc)
                #dbg_show_step(pc)
                pc = pc()
        except Exception as error:
            print("error: {0}".format(error))
            if call_error_handler(error) == None:
                raise

def err(str):
    raise Exception(str)

def set_error_handler(e):
    global error_handlers, sp, reg, nargs
    error_handlers.append([sp, nargs, e])

def call_error_handler(e):
    global error_handlers, sp, reg, error_obj
    while len(error_handlers) > 0:
        x = error_handlers.pop()
        if x[0] <= sp:
            error_obj = e
            sp = x[0]
            nargs = x[1]
            save_pc = x[2]
            return True
    return None

def cons__question_():
    #dbg_show_step('cons?')
    ret = (type(reg[1]) == list) and (len(reg[1]) > 0)
    ret = ret and (reg[1][0] == type_cons)
    reg[1] = ret
    return reg[0]

fns['cons?'] = cons__question_

def tail():
    reg[1] = reg[1][2]
    return reg[0]

fns['tail'] = tail

def __plus_():
    reg[1] = reg[1] + reg[2]
    return reg[0]

fns['+'] = __plus_

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
