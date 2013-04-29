import pprint
import sys

varcnt = 0

def newvar():
    global varcnt
    varcnt += 1
    return "tmp.v" + str(varcnt)

def delvar(var):
    return "del {}\n".format(var)

#from runtime import *

dump_file = open('state.py', 'w')

def eval_code_x():
    global dump_file
    if dump_file:
        dump_file.write(reg[1])
    return eval_code()

defun_x("shenpy.eval", 1, eval_code_x)

call = call_x

def str_from_obj(x):
    if x == []:
        return "[]"
    elif x == fail_obj:
        return "fail_obj"
    elif x == sys.stdin:
        return "sys.stdin"
    elif x == sys.stdout:
        return "sys.stdout"
    elif isinstance(x, bool):
        return str(x)
    elif isinstance(x, int) or isinstance(x, float):
        return str(x)
    elif isinstance(x, str):
        return pprint.pformat(x)
    elif issymbol(x):
        return "[type_symbol, " + pprint.pformat(x[1]) + "]"
    elif iscons(x):
        return "[type_cons, " + str_from_obj(x[1]) + ", " \
                 + str_from_obj(x[2]) + "]"
    elif isclosure(x) and x[4] != None:
        return "fns[' + pprint.pformat(x[4]) + ']'"
    elif isabsvector(x):
        sep = ""
        ret = "["
        for y in x:
            ret += sep + str_from_obj(y)
            sep = ", "
        return ret + "]"
    else:
        raise Exception('Unknown object {}'.format(x))

def dump_long_vector(x, var):
    ret = "{} = [fail_obj] * {}\n".format(var, x[0] + 1)
    for i in xrange(0, len(x)):
        if x[i] != fail_obj:
            if iscons(x[i]):
                var1 = newvar()
                ret += dump_long_list(x[i], var1)
                ret += "{}[{}] = {}\n".format(var, i, var1)
                ret += "del {}\n".format(var1)
            else:
                ret += "{}[{}] = {}\n".format(var, i, str_from_obj(x[i]))
    return ret

def dump_long_list(x, var):
    lst = []
    while iscons(x):
        lst.append(x[1])
        x = x[2]
    ret = "{} = []\n".format(var)
    for y in reversed(lst):
        if iscons(y):
            var1 = newvar()
            ret += dump_long_list(y, var1)
            ret += "{1} = [type_cons, {0}, {1}]\n".format(var1, var)
            ret += "del {}\n".format(var1)
        else:
            z = str_from_obj(y)
            ret += "{1} = [type_cons, {0}, {1}]\n".format(z, var)
    return ret

def test():
    x = [3, dbg_list([[type_symbol, "one"],
                      dbg_list([1, 2, 3]),
                      dbg_list([4, 5, dbg_list([6, 7])])]),
                     dbg_list([8, 9, [type_symbol, "ten"]]),
                     dbg_list([3])]
    s = dump_long_vector(x, "xxx")
    print(s)
    return s

def dump_var(f, key, val):
    f.write('vars[{}] = {}\n'.format(pprint.pformat(key), val))

def dump_vars(f):
    f.write("tmp = Tag('tmp')\n")
    for v in vars:
        if v == "shen.*history*":
            dump_var(f, v, "[]")
        elif v == "*property-vector*":
            var = newvar()
            f.write(dump_long_vector(vars[v], var))
            dump_var(f, v, var)
            f.write(delvar(var))
        elif v == "shen.*signedfuncs*":
            var = newvar()
            f.write(dump_long_list(vars[v], var))
            dump_var(f, v, var)
            f.write(delvar(var))
        else:
            dump_var(f, v, str_from_obj(vars[v]))
    f.write('del tmp\n')

def finish_dump():
    global dump_file
    if dump_file:
        dump_vars(dump_file)
        dump_file.write('call = call_x\n')
        dump_file.close()
        dump_file = None
