dump_file = open('state.py', 'w')

def eval_code_x():
    global dump_file
    if dump_file:
        dump_file.write(reg[sp])
    return eval_code()

defun_x("shenpy.eval", 1, eval_code_x)

call = call_x

def finish_dump():
    global dump_file
    import pprint
    if dump_file:
        del globvars['*stoutput*']
        del globvars['*stinput*']
        dump_file.write('globvars.update(load(')
        dump_file.write(pprint.pformat(dump(globvars)))
        dump_file.write('))\n')
        dump_file.write('call = call_x\n')
        dump_file.close()
        dump_file = None
