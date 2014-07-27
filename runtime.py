import sys, io, os, traceback, time, inspect
import cPickle as pickle
from cStringIO import StringIO 

class Tag:
    __slots__ = ['name']
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
reg = []
nargs = 0
next = None
ret = None

start = None

dbg_step = False
dbg_output = sys.stdout
show_step = False
show_step_frame = False
dump_error = False

# Compatibility with python3
try:
    xrange
except Exception:
    xrange = range

def reg_size(n):
    global reg, sp, reg_top
    size = sp + n
    s = len(reg)
    if size > s:
        reg.extend([None] * (size - s))
    return reg

def wipe_stack(off):
    global sp, reg_top
    return
    local_reg = reg
    for i in xrange(sp + off, reg_top):
        local_reg[i] = None
    reg_top = sp

def run():
    global error_obj, fns, show_step, nargs, sp, reg, start
    while start:
        try:
            pc = start
            start = None
            while pc:
                if show_step: dbg_show_step(pc, frame_only = show_step_frame)
                pc = pc()
                #print('=> pc: {}'.format(pc))
        except Exception as error:
            #with_dbg_output(lambda f: f.write("**ERROR: {0}\n".format(error)))
            #traceback.print_exc()
            if len(error_handlers) == 0:
                if dump_error:
                    with_dbg_output(lambda f:
                                    f.write("**ERROR: {0}\n".format(error)))
                    traceback.print_exc()
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
    n = len(args)
    if isclosure(proc):
        n2 = len(proc[4])
    else:
        n2 = 0
    reg_size(n + n2 + 1)
    reg[sp:sp + n] = reversed(args)
    i = sp + n
    if isclosure(proc):
        fn = proc[2]
        reg[i:i + n2] = proc[4]
    elif callable(proc):
        fn = proc
    else:
        error("{} is not a function".format(proc))
    nargs = n + n2
    return fn

def call_x(proc, *args):
    global reg, nargs, start, sp, ret
    prevsp = sp
    start = call_function(proc, *args)
    run()
    paranoid_check_sp(prevsp)
    r = ret
    ret = None
    #paranoid_check_reg(sp)
    return r

def error(str):
    raise Exception(str)
    return fail_obj

def error_to_string(e):
    #traceback.print_exc()
    return str(e)

def push_error_handler(e):
    global error_handlers, sp, reg, nargs
    #dbg_show_step("SET ERROR HANDLER")
    error_handlers.append((sp, next, e))
    #with_dbg_output(lambda out: out.write('cont: {}\n'.format(error_handlers)))

def pop_error_handler():
    global error_handlers
    error_handlers.pop()

def default_error_handler():
    global error_obj
    raise error_obj

def error_unwind_get_handler():
    global error_handlers, sp, reg_top, nargs, next
    sp, next, e = error_handlers.pop()
    return e

def call_error_handler(*args):
    global error_handlers, sp, reg_top, nargs, next, start
    sp, next, e = error_handlers.pop()
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
    output.write("  ret: {0}\n".format(ret))
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
    global fns
    if x == "true":
        return True
    elif x == "false":
        return False
    elif x in fns:
        return fns[x]
    elif isinstance(x, str):
        return (type_symbol, x)
    else:
        error("intern: argument '{}' is not a string".format(x))

def issymbol(x):
    return isinstance(x, tuple) \
           and (((len(x) == 2) and (x[0] == type_symbol)) \
                or isclosure(x))

def iscons(x):
    return isinstance(x, tuple) and (len(x) == 3) and (x[0] == type_cons)

def isvector(x):
    return (isinstance(x, list) and (len(x) > 1)
            and isinstance(x[0], (int, long))
            and (x[0] > 0))

def isabsvector(x):
    return (isinstance(x, list) and (len(x) > 0) \
            and (not isinstance(x[0], Tag)))

def isclosure(x):
    return (isinstance(x, tuple) and (len(x) == 5) and x[0] == type_function \
            and callable(x[2]))

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
           or (x == y) \
           or (issymbol(x) and isclosure(y) and x[1] == y[1]) \
           or (issymbol(y) and isclosure(x) and y[1] == x[1])

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
    elif isinstance(x, (int, float, long)):
        return repr(x)
    elif issymbol(x):
        return x[1]
    elif isclosure(x):
        if x[1] == None:
            if x[2].__name__:
                return "#<closure " + x[2].__name__ + "#" + str(id(x)) + ">"
            else:
                return "#<closure #" + str(id(x)) + ">"
        elif len(x[4]) == 0:
            return x[1]
        else:
            return "#<closure " + x[1] + "#" + str(id(x)) + ">"
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
        global ret
        if name == '':
            name = fn.__name__
        args = inspect.getargspec(fn).args
        x_nargs = len(args)
        def x():
            r = fn_entry(x, x_nargs, name)
            if r != fail_obj: return r
            r = fn(*reversed(reg[sp:sp + x_nargs]))
            return fn_return(r, next)
        x.__name__ = fn.__name__
        ret = fns[name] = (type_function, name, x, x_nargs, [])
        return fn
    if callable(x):
        return mk(x, x.__name__)
    return lambda f: mk(f, x)

def defun_x(name, nargs, func):
    global ret
    ret = fns[name] = (type_function, name, func, nargs, [])
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
    global ret
    with open(reg[sp], 'r') as f:
        ret = f.read()
    return eval_code()

def repl():
    call(fns["shen.shen"])

globvars["*macros*"] = ()
globvars["*stoutput*"] = sys.stdout
globvars["*stinput*"] = sys.stdin
globvars["*language*"] = "python"
globvars["*implementation*"] = "all"
globvars["*port*"] = "0.2.0"
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
    global reg, sp, nargs, next, ret, sp_top
    fn = reg[sp + nargs - 1][2]
    v = reg[sp:sp + nargs - 1]
    ret = (type_function, None, fn, nargs - 1, v)
    sp_top = sp + nargs
    wipe_stack(0)
    return next

defun_x("klvm.mk-closure", 1, mk_closure)

def test_regs():
    global reg, sp
    reg_size(10)
    for i in xrange(11): reg[i] = i
    print("regs: {}\n".format(reg))
    wipe_stack()
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
