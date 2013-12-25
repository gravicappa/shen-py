import sys
import io
import os
import traceback
import time
import inspect
import cPickle as pickle
from cStringIO import StringIO 

class Tag:
    all = {}
    def __init__(self, name='???'):
        self.name = name
        Tag.all[name] = self
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
globvars = {}

sp = 0
reg_top = 0
reg = [None]
nargs = 0
next = None

start = None

dbg_step = False
dbg_output = sys.stdout
show_step = False
show_step_frame = True
dump_error = True

# Compatibility with python3
try:
    xrange
except Exception:
    xrange = range

def reg_size(size):
    global reg, sp, reg_top
    s = len(reg)
    top = sp + size
    if reg_top < top:
        reg_top = top
    if top > s:
        reg.extend([None] * (top - s))
    return reg

def wipe_stack(begin):
    global reg, sp, reg_top
    for i in xrange(sp + begin, reg_top):
        reg[i] = None
    reg_top = sp + begin

def run():
    global start, error_obj, fns, show_step, nargs, next, sp, reg
    while start:
        try:
            pc = start
            start = None
            while pc:
                #print(pc)
                if show_step: dbg_show_step(pc, frame_only = show_step_frame)
                pc = pc()
                #print('=> pc: {}'.format(pc))
        except Exception as error:
            #with_dbg_output(lambda f: f.write("**ERROR: {0}\n".format(error)))
            #traceback.print_exc()
            if len(error_handlers) == 0:
                if dump_error:
                    dbg_show_step("UNCAUGHT ERROR")
                raise
            #dbg_show_step("ERROR HANDLER")
            error_obj = error
            call_error_handler(error_obj)
            #dbg_print('start: {}'.format(start))

def paranoid_check_sp(prev):
    if sp != prev:
        error("call left sp {0} != {1}".format(sp, prev))

def paranoid_check_reg(sp):
    for i in reg[sp:]:
      if i != None:
        dbg_print('nonempty reg: {}'.format(i))
        dbg_print('nonempty sp: {}'.format(sp))
        dbg_print('nonempty reg_top: {}'.format(reg_top))
        dbg_print('nonempty regs: {}'.format(reg))
        error("call left nonempty reg")

def call_function(proc, *args):
    global reg, nargs, sp
    i = sp
    nargs = len(args)
    if isclosure(proc):
        nargs += len(proc[3])
    reg_size(nargs + 1)
    for x in reversed(args):
        reg[i] = x
        i += 1
    if isclosure(proc):
        fn = proc[1]
        for x in reversed(proc[3]):
            reg[i] = x
            i += 1
    elif callable(proc):
        fn = proc
    else:
        error("{} is not a function".format(proc))
    return fn

def call_x(proc, *args):
    global reg, nargs, start, sp
    prevsp = sp
    start = call_function(proc, *args)
    run()
    paranoid_check_sp(prevsp)
    ret = reg[sp]
    reg[sp] = None
    paranoid_check_reg(sp)
    return ret

def error(str):
    raise Exception(str)
    return fail_obj

def error_to_string(e):
    #traceback.print_exc()
    return str(e)

def push_error_handler(e):
    global error_handlers, sp, reg, nargs
    #dbg_show_step("SET ERROR HANDLER")
    error_handlers.append((sp, reg_top, nargs, next, e))
    #with_dbg_output(lambda out: out.write('cont: {}\n'.format(error_handlers)))

def pop_error_handler():
    global error_handlers
    error_handlers.pop()

def default_error_handler():
    global error_obj
    raise error_obj

def error_unwind_get_handler():
    global error_handlers, sp, reg_top, nargs, next
    sp, reg_top, nargs, next, e = error_handlers.pop()
    return e

def call_error_handler(*args):
    global error_handlers, sp, reg_top, nargs, next, start
    sp, _, nargs, next, e = error_handlers.pop()
    #dbg_print("reg_top: {} e: {}".format(reg_top, e))
    wipe_stack(0)
    start = call_function(e, *args)
    #dbg_print("start: {}".format(start))

def dbg_print(x, output=None):
    with_dbg_output(lambda out: out.write(x + '\n'), output)

def with_dbg_output(func, output = None):
    if not output:
        output = dbg_output
    if not hasattr(output, 'write'):
        with_dbg_output(func, sys.stdout)
        with open(output, 'a') as f:
            with_dbg_output(func, f)
    else:
        func(output)

def dbg_show_step_x(name, output, frame_only):
    output.write("## SHOW {0}\n".format(name))
    output.write("  nargs: {0}\n".format(nargs))
    output.write("  next: {0}\n".format(next))
    output.write("  sp: {0}\n".format(sp))
    output.write("  reg_top: {0}\n".format(reg_top))
    if frame_only:
        i = sp
    else:
        i = 0
    end = len(reg)
    for x in reversed(reg):
        if x != None:
            break
        end -= 1
    for x in reg[i:end]:
        output.write("    Reg[{0}]: {1}\n".format(i, tostring_x(x)))
        i += 1
    if end < len(reg):
        output.write("    Reg[{0}-{1}]: None\n".format(end, len(reg) - 1))
    i = 0
    output.write("\n")
    if dbg_step and output == sys.stdout:
        print("--<Press return to continue>--")
        sys.stdin.readline()

def dbg_show_step(name='', frame_only=False, output=None):
    with_dbg_output(lambda output: dbg_show_step_x(name, output, frame_only),
                    output)

def call(proc, *args):
    pass

def intern(x):
    if x == "true":
        return True
    elif x == "false":
        return False
    elif isinstance(x, str):
        return (type_symbol, x)
    else:
        error("intern: argument '{}' is not a string".format(x))

def issymbol(x):
    return isinstance(x, tuple) and (len(x) == 2) and (x[0] == type_symbol)

def iscons(x):
    return isinstance(x, tuple) and (len(x) == 3) and (x[0] == type_cons)

def isvector(x):
    return (isinstance(x, list) and (len(x) > 1)
            and (isinstance(x[0], int) or isinstance(x[0], long))
            and (x[0] > 0))

def isabsvector(x):
    return (isinstance(x, list) and (len(x) > 0) \
            and (not isinstance(x[0], Tag)))

def isclosure(x):
    return (isinstance(x, tuple) and (len(x) == 5) and x[0] == type_function \
            and callable(x[1]))

def isequal_list(x, y):
    n = len(x)
    if n != len(y):
        return False
    i = 0
    for a in x:
        if not isequal(a, y[i]):
            return False
        i += 1
    return True

def isequal(x, y):
    return (isinstance(x, bool) and isinstance(y, bool) and x == y) \
           or (((isinstance(x, tuple) and isinstance(y, tuple)) \
                or (isinstance(x, list) and isinstance(y, list))) \
               and isequal_list(x, y)) \
           or x == y \
           or (issymbol(x) and isclosure(y) and x[1] == y[4]) \
           or (issymbol(y) and isclosure(x) and y[1] == x[4])

def setval(key, x):
    if not issymbol(key):
        return error("The value {0} is not a symbol".format(key))
    globvars[key[1]] = x
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
    elif isinstance(x, int) or isinstance(x, float) or isinstance(x, long):
        return repr(x)
    elif issymbol(x):
        return x[1]
    elif isclosure(x):
        if x[4] == None:
            if x[1].__name__:
                return "#<closure " + x[1].__name__ + "#" + str(id(x)) + ">"
            else:
                return "#<closure #" + str(id(x)) + ">"
        elif len(x[3]) == 0:
            return x[4]
        else:
            return "#<closure " + x[4] + "#" + str(id(x)) + ">"
    elif x == fail_obj:
        return "..."
    else:
        return error("str cannot convert {0} to a string." .format(x))

def filter_pred(line):
    return not (line.startswith("global ") or line.startswith("del "))

def eval_code():
    global ret
    ret = next
    x = reg[sp]

    # Avoid leaking of defined one-shot functions
    y = "global toplevel_func\n"
    y += "def toplevel_func():\n"
    y += "  global ret, nargs, reg\n"
    y += "\n".join(map(lambda line: "  " + line,
                   filter(filter_pred, x.split("\n"))))
    #print('eval_code y:\n{0}\n'.format(y))
    exec(compile(y, "<string>", "exec"))
    global toplevel_func
    toplevel_func()
    del toplevel_func
    #print('eval_code ret: {0}'.format(ret))
    return ret

def proc(x = ""):
    def mk(fn, name):
        if name == '':
            name = fn.__name__
        args = inspect.getargspec(fn).args
        x_nargs = len(args)
        def x():
            r = fn_entry(x, x_nargs, name)
            if r != fail_obj: return r
            r = fn(*reversed(reg[sp:sp + x_nargs]))
            return fn_return(r, next)
        reg_size(1)
        reg[sp] = fns[name] = (type_function, x, x_nargs, [], name)
        return fn
    if callable(x):
        return mk(x, x.__name__)
    return lambda f: mk(f, x)

def defun_x(name, nargs, func):
    reg_size(1)
    reg[sp] = fns[name] = (type_function, func, nargs, [], name)
    return next

def dbg_list(items):
    ret = ()
    for x in reversed(items):
        ret = (type_cons, x, ret)
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
    elif x == ():
        return '[]'
    elif isinstance(x, str):
        return '"' + x + '"'
    elif isvector(x):
        return '<' + ', '.join(map(tostring_x, x)) + '>'
    elif isabsvector(x):
        return '<<' + ', '.join(map(tostring_x, x)) + '>>'
    else:
        try:
            x = tostring(x)
            if x == fail_obj:
                return '...'
            else:
                return x
        except:
            return str(x)

def read_byte(stream):
    s = stream.read(1)
    if len(s) == 0:
        return -1
    return ord(s)

def write_byte(byte, stream):
    stream.write(chr(byte))
    return byte

def write_string(str, out):
    out.write(str)
    return str

@proc('open')
def open_file(name, dir):
    modes = {"in" : "r", "out" : "w"}
    mode = None
    if issymbol(dir):
        mode = modes.get(dir[1])
    if mode:
        path = os.path.expanduser(globvars["*home-directory*"] + name)
        return open(path, mode)
    else:
        return error("open: '{0}' unknown direction".format(tostring_x(dir)))

@proc('shenpy.print')
def shenpy_print(x):
    print(x)
    return True

@proc('shenpy.exec')
def shenpy_exec(x):
    exec(compile(x, "<string>", "exec"))
    return True

@proc('shenpy.eval')
def shenpy_eval(x):
    return eval(x)

def shenpy_load():
    with open(reg[sp], 'r') as f:
        reg[sp] = f.read()
    return eval_code()

def repl():
    call(fns["shen.shen"])

globvars["*macros*"] = ()
globvars["*stoutput*"] = sys.stdout
globvars["*stinput*"] = sys.stdin
globvars["*language*"] = "python"
globvars["*implementation*"] = "all"
globvars["*port*"] = "0.1.0"
globvars["*porters*"] = "Ramil Farkhshatov"

def nop():
    wipe_stack(0)
    return next

defun_x("shen.process-datatype", 2, nop)
defun_x("compile", 3, nop)
defun_x("declare", 2, nop)
defun_x("adjoin", 2, nop)
defun_x("shenpy.eval", 1, eval_code)
defun_x("shenpy.load", 1, shenpy_load)
defun_x("shenpy.quit", 0, quit)

@proc('get-time')
def get_time(x):
    return time.time()

def mk_closure():
    global reg, sp, nargs, next
    fn = reg[sp + nargs - 1]
    v = reg[sp:sp + nargs - 1]
    wipe_stack(1)
    reg[sp] = (type_function, fn, nargs, v, None)
    return next

defun_x("klvm-mk-closure", 1, mk_closure)

def test_regs():
    global reg, sp
    reg_size(10)
    for i in xrange(11): reg[i] = i
    print("regs: {}\n".format(reg))
    wipe_stack(5)
    print("regs: {}\n".format(reg))

def dbg_log(fn):
    def x(*args):
        dbg_print("({} {})".format(fn, args))
        ret = fn(*args)
        dbg_print("({} {}) => {}".format(fn, args, ret))
        return ret
    x.__name__ = fn.__name__
    return x

def pickle_id(obj):
    if isinstance(obj, Tag):
        return obj.name
    else:
        return None

def pickle_load(id):
    return Tag.all[id]

def dump(obj):
    out = StringIO()
    p = pickle.Pickler(out, -1)
    p.persistent_id = pickle_id
    p.dump(obj)
    return out.getvalue()

def load(data):
    stream = StringIO(data)
    up = pickle.Unpickler(stream)
    up.persistent_load = pickle_load
    return up.load()

def test_dump():
    import pprint
    x = [2, fail_obj, dbg_list(["one", 'tw"o', "thr'e", 4])]
    s = dump(x)
    pp = pprint.PrettyPrinter()
    with open("toystate.py", "wt") as f:
        f.write("data = ")
        f.write(pp.pformat(s))
        f.write("\n")
