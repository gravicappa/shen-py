import os, sys, traceback, unittest, test_def, imp, test1
import runtime as shen

pr = shen.dbg_print
cases = ()

def reset_runtime():
    shen.sp = 0
    shen.reg_top = 0
    shen.reg = []
    shen.next = None

def init_runtime():
    @shen.proc('+')
    def plus(x, y):
        return x + y

    @shen.proc('-')
    def minus(x, y):
        return x - y

    @shen.proc
    def minus(x, y):
        return x - y

    gensym_counter = 0
    @shen.proc
    def gensym(s):
        global gensym_counter
        gensym_counter += 1
        return (shen.type_symbol, s[1] + str(gensym_counter))

    @shen.proc('vector->')
    def vector_set(v, i, x):
        v[i] = x
        return v

    @shen.proc('<-vector')
    def vector_ref(v, i):
        return v[i]

    @shen.proc('or')
    def shen_or(a, b):
        return a or b

    @shen.proc('and')
    def shen_and(a, b):
        return a and b

def strcall(x):
    args = " ".join(map(shen.tostring_x, x[1:]))
    sep = ""
    if args != "":
        sep = " "
    return "({}{}{})".format(x[0], sep, args)

def reload_shen(stream):
    import imp
    for x in (shen, test1, test_def):
        imp.reload(x)
    shen.dbg_output = stream
    shen.show_step = False
    shen.show_step_frame = False
    shen.dump_error = True
    init_runtime()
    reset_runtime()
    global cases
    cases = test_def.mkcases(shen)

class Test_eq(unittest.TestCase):
    def runTest(self):
        eq = [
            [True, True],
            [False, False],
            [True, shen.intern('true')],
            [False, shen.intern('false')],
            [[1, 2, 3], [1, 2, 3]],
            [[1, 2, True], [1, 2, shen.intern('true')]],
            [(shen.type_symbol, 'and'), shen.intern('and')]
        ]
        neq = [
            [True, 1],
            [False, 0]
        ]
        for a, b in eq:
            msg = '{} != {}'.format(a, b)
            self.assertTrue(shen.isequal(a, b), msg = msg)
        for a, b in neq:
            msg = '{} == {}'.format(a, b)
            #self.assertFalse(shen.isequal(a, b), msg = msg)

def assert_msg(ret, expected):
    str = '{} != {}'.format(shen.tostring_x(ret), shen.tostring_x(expected))
    return str

def mktest(t):
    expr, expected = t
    def fn():
        reset_runtime()
        pr('\n{}\n'.format("".join(["="] * 60)))
        pr('Calling {}'.format(strcall(expr)))
        try:
            ret = shen.call_x(shen.fns[expr[0]], *expr[1:])
        except Exception as error:
            assert True, "Exception: {}".format(error)
            ret = "ERROR"
        pr('\n# {} => {}\n'.format(strcall(expr), shen.tostring_x(ret)))
        assert shen.isequal(ret, expected), assert_msg(ret, expected)
    desc = '{} => {}'.format(strcall(expr), shen.tostring_x(expected))
    return unittest.FunctionTestCase(fn, description=desc)

def mksuite():
    global cases
    cases = test_def.mkcases(shen)
    suite = unittest.TestSuite()
    suite.addTest(Test_eq())
    suite.addTests(map(mktest, cases))
    return suite

def run(reload = True, output = sys.stderr):
    if isinstance(output, str):
        try: os.remove(output)
        except OSError: pass
        with open(output, 'a') as s:
            run(reload, s)
    else:
        if reload:
            reload_shen(output)
        else:
            init_runtime()
        unittest.TextTestRunner(stream=output).run(mksuite())

if __name__ == '__main__':
    run(reload = False)
