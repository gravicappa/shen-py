import sys
import io
import os
import traceback
import time

class Tag:
    def __init__(self, name='?'):
        self.name = name
    def __repr__(self):
        return "#<shenpy.Tag {0}>".format(self.name)

type_function = Tag('func')
type_symbol = Tag('sym')
type_cons = Tag('cons')
type_substring = Tag('substr')
type_subvector = Tag('subvec')
type_bool = Tag('bool')
fail_obj = Tag('fail')

error_handlers = []
error_obj = None
fns = {}
vars = {}
sp = -1
stack = []
reg = [None]
save_pc = None
nargs = 0

show_step = False
dump_error_file = "error.txt"

try:
    xrange
except Exception:
    xrange = range

def stack_size(size):
    global stack, sp
    s = len(stack)
    if sp + size + 1 > s:
        stack.extend([None] * (sp + size - s + 1))
    else:
        for i in xrange(sp + 1, s):
            stack[i] = None
    return stack

def reg_size(size):
    global reg
    if len(reg) < size + 1:
        reg.extend([None] * (size - len(reg) + 1))
    else:
        for i in xrange(size + 1, len(reg)):
            reg[i] = None
    return reg

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
                if dump_error_file != None:
                    with open(dump_error_file, "w") as errfile:
                        dbg_show_step("UNCAUGHT ERROR", errfile)
                raise
            #dbg_show_step("ERROR HANDLER")
            error_obj = error
            nargs = 0
            save_pc = fns["klvm-call-error-handler"][1]()

def error(str):
    raise Exception(str)
    return fail_obj

def error_to_string(e):
    traceback.print_exc()
    return str(e)

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

def dbg_show_step(name='', file=sys.stdout):
    file.write("## SHOW {0}\n".format(name))
    file.write("  nargs: {0}\n".format(nargs))
    file.write("  sp: {0}\n".format(sp))
    i = 0
    for x in reg:
        file.write("    Reg[{0}]: {1}\n".format(i, x))
        i += 1
    i = 0
    for x in stack:
        file.write("    Stack[{0}]: {1}\n".format(i, x))
        i += 1
    file.write("\n")
    if dbg_step:
        print("--<Press return to continue>--")
        sys.stdin.readline()

def call_x(proc, *args):
    global reg, nargs, save_pc
    nargs = len(args)
    i = 1
    if isclosure(proc):
        save_pc = proc[1]
        nargs += proc[2]
        for x in proc[3]:
            reg[i] = x
    else:
        save_pc = proc
    reg_size(nargs + 1)
    reg[0] = None
    for x in args:
        reg[i] = x
        i += 1
    run()
    if sp >= 0:
        return error("call left sp {0} >= 0".format(sp))
    return reg[1]

def call(proc, *args):
    pass

def issymbol(x):
    return isinstance(x, list) and (len(x) == 2) and (x[0] == type_symbol)

def iscons(x):
    return isinstance(x, list) and (len(x) == 3) and (x[0] == type_cons)

def isvector(x):
    return (isinstance(x, list) and (len(x) > 1) and isinstance(x[0], int)
            and (x[0] > 0))

def isabsvector(x):
    return (isinstance(x, list) and (len(x) > 0) \
            and (not isinstance(x[0], Tag)))

def isclosure(x):
    return (isinstance(x, list) and (len(x) == 5) and x[0] == type_function)

def isequal_list(x, y):
    n = len(x)
    if n != len(y):
        return False
    i = 0
    for a in x:
        if not isequal(a, y[i]):
            return False
    return True

def isequal(x, y):
    return (isinstance(x, bool) and isinstance(y, bool) and x == y) \
           or (isinstance(x, list) and isinstance(y, list) \
               and isequal_list(x, y)) \
           or x == y \
           or (issymbol(x) and isclosure(y) and x[1] == y[4]) \
           or (issymbol(y) and isclosure(x) and y[1] == x[4])

def setval(key, x):
    if not issymbol(key):
        return error("The value {0} is not a symbol".format(key))
    vars[key[1]] = x
    return x

def absvector_set(v, i, x):
    v[i] = x
    return v

def tostring(x):
    if isinstance(x, bool):
        if x:
            return "true"
        else:
            return "false"
    elif isinstance(x, int) or isinstance(x, float):
        return repr(x)
    elif issymbol(x):
        return x[1]
    elif isclosure(x):
        if x[4] != None:
            return x[4]
        else:
            return "#<closure>"
    elif x == fail_obj:
        return "..."
    else:
        return error("str cannot convert {0} to a string." .format(x))

def eval_code():
    global ret
    x = reg[1]

    # Avoid leaking of defined one-shot functions
    def filter_pred(line):
        return not (line.startswith("global ") or line.startswith("del "))
    y = "global toplevel_func\n"
    y += "def toplevel_func():\n"
    y += "  global ret, nargs, reg\n"
    y += "\n".join(map(lambda line: "  " + line,
                   filter(filter_pred, x.split("\n"))))

    #print('eval_code y:\n{0}\n'.format(y))
    ret = reg[0]
    exec(compile(y, "<string>", "exec"))
    global toplevel_func
    toplevel_func()
    del toplevel_func
    #print('eval_code ret: {0}'.format(ret))
    return ret

def defun_x(name, nargs, func):
    reg_size(1)
    reg[1] = fns[name] = [type_function, func, nargs, [], name]
    return reg[0]

def defun(name, nargs, func):
    def fn(): return mkfun(fn, nargs, func)
    return defun_x(name, nargs, fn)

def dbg_list(items):
    ret = []
    for x in reversed(items):
        ret = [type_cons, x, ret]
    return ret

def dbg_pylist(x):
    ret = []
    while iscons(x):
        ret.append(x[1])
        x = x[2]
    return ret

def tostring_list(x):
    s = "["
    sep = ""
    while iscons(x):
        s = s + sep + tostring_x(x[1])
        sep = " "
        x = x[2]
    return s + "]"

def tostring_x(x):
    if iscons(x):
        return tostring_list(x)
    elif x == []:
        return '[]'
    else:
        x = tostring(x)
        if x == fail_obj:
            return '...'
        else:
            return x

def read_byte(stream):
    s = stream.read(1)
    if len(s) == 0:
        return -1
    return ord(s)

def write_byte(stream, byte):
    stream.write(chr(byte))
    return []

def write_string(str, out):
    out.write(str)
    return []

def open_file(name, dir):
    modes = {"in" : "r", "out" : "w"}
    mode = None
    if issymbol(dir):
        mode = modes.get(dir[1])
    if mode:
        path = os.path.expanduser(vars["*home-directory*"] + name)
        return open(path, mode)
    else:
        return error("open: '{0}' unknown direction".format(tostring_x(dir)))

def open_stream(type, name, dir):
    openers = {"file" : open_file}
    opener = None
    if issymbol(type):
        opener = openers.get(type[1])
    if opener:
        return opener(name, dir)
    return error("open: {0} unknown type".format(type))

def shenpy_load():
    with open(reg[1], 'r') as f:
        reg[1] = f.read()
    return eval_code()

def repl():
    call(fns["shen.shen"])

vars["*macros*"] = []
vars["*stoutput*"] = sys.stdout
vars["*stinput*"] = sys.stdin
vars["*language*"] = "python"
vars["*implementation*"] = "all"
vars["*port*"] = "0.0.2"
vars["*porters*"] = "Ramil Farkhshatov"

defun_x("shen.process-datatype", 2, lambda: reg[0])
defun_x("compile", 3, lambda: reg[0])
defun_x("declare", 2, lambda: reg[0])
defun_x("adjoin", 2, lambda: reg[0])
defun_x("shenpy.eval", 1, eval_code)
defun_x("shenpy.load", 1, shenpy_load)
defun_x("shenpy.quit", 0, quit)

defun("get-time", 1, lambda: time.time())
defun("open", 3, lambda: open_stream(reg[1], reg[2], reg[3]))
