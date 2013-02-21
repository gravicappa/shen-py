import shenpy

def cons__question_():
    #dbg_show_step('cons?')
    ret = (type(shenpy.reg[1]) == list) and (len(shenpy.reg[1]) > 0)
    ret = ret and (shenpy.reg[1][0] == shenpy.type_cons)
    shenpy.reg[1] = ret
    return shenpy.reg[0]

shenpy.fns['cons?'] = cons__question_

def tail():
    shenpy.reg[1] = shenpy.reg[1][2]
    return shenpy.reg[0]

shenpy.fns['tail'] = tail

def __plus_():
    shenpy.reg[1] = shenpy.reg[1] + shenpy.reg[2]
    return shenpy.reg[0]

shenpy.fns['+'] = __plus_

def __asterisk_():
    shenpy.reg[1] = shenpy.reg[1] * shenpy.reg[2]
    return shenpy.reg[0]

shenpy.fns['*'] = __asterisk_

