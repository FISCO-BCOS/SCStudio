# -*- coding:utf-8 -*-
import sys
import random
import tokenize as tk
from io import BytesIO
from numpy.core.defchararray import isdigit
import numpy as np


class Contract:
    def __init__(self):
        self.name = ''
        self.lineNo = 0


class Variable:
    def __init__(self):
        self.name = ''
        self.type = ''
        self.lineNo = 0


class Function:
    def __init__(self):
        self.name = ''
        self.param = []
        self.returns = []
        self.lineNo = 0


def load_dataset(filename):
    ret = []
    with open(filename, 'r') as f:
        for line in f:
            ret.append(list(line.strip('\n').split(',')))
        f.close()
    return ret


def init():
    contractName = load_dataset('./doc/TopContractNameContent.txt')
    funcName = load_dataset('./doc/TopFunctionNameContent.txt')
    varName = load_dataset('./doc/TopVariableNameContent.txt')

    initList = [
        'var',
        'int',
        'uint',
        'fixed',
        'ufixed',
        'string',
        'byte',
        'bytes',
        'bool',
        'address']
    intTypes = [
        'int%d' % m
        for m in range(8, 257, 8)
    ]
    uintTypes = [
        'uint%d' % m
        for m in range(8, 257, 8)
    ]
    fixedTypes = [
        'fixed%d%dx%d' % (m, n)
        for m in range(0, 249, 8)
        for n in range(8, 257 - m, 8)
    ]
    ufixedTypes = [
        'ufixed%d%dx%d' % (m, n)
        for m in range(0, 249, 8)
        for n in range(8, 257 - m, 8)
    ]
    stringTypes = [
        'string%d' % m
        for m in range(1, 33)
    ]
    bytesTypes = [
        'bytes%d' % m
        for m in range(1, 33)
    ]
    # merge multiple list
    builtInType = sum([intTypes, uintTypes, fixedTypes,
                       ufixedTypes, stringTypes, bytesTypes], initList)

    return contractName, funcName, varName, builtInType


def extractInfo(txt):
    toks = []
    try:
        for x in tk.tokenize(BytesIO(txt.encode('utf-8')).readline):
            toks.append(x)
    except tk.TokenError:
        pass

    tokkies = []
    old = (0, 0)
    skip = False
    for idx, _ in enumerate(toks):
        t = toks[idx]
        if not t.string:
            continue
        if skip:
            skip = False
            continue

        if t.string == '&' and toks[idx - 1].string == '&':
            tokkies[-1] = '&&'
            continue
        elif t.string == '|' and toks[idx - 1].string == '|':
            tokkies[-1] = '||'
            continue
        elif t.string == '+' and toks[idx - 1].string == '+':
            tokkies[-1] = '++'
            continue
        elif t.string == '-' and toks[idx - 1].string == '-':
            tokkies[-1] = '--'
            continue
        elif t.string == ']' and toks[idx - 1].string == '[':
            tokkies[-1] = '[]'
            continue
        elif t.string == '>' and toks[idx - 1].string == '=':
            tokkies[-1] = '=>'
            continue

        if toks[idx - 1].string == '$' and toks[idx + 1].string == '$':
            tokkies[-1] = '$' + t.string + '$'
            skip = True
            continue
        if isdigit(toks[idx - 1].string) and isdigit(toks[idx +
                                                          1].string) and (t.string == '/' or t.string == '.'):  # fraction
            tokkies[-1] = toks[idx - 1].string + \
                t.string + toks[idx + 1].string
            skip = True
            continue

        if t.start[0] == old[0] and t.start[1] > old[1]:
            tokkies.append(" " * (t.start[1] - old[1]))
        tokkies.append(t.string)
        old = t.end
    if txt.endswith(" "):
        tokkies.append(" ")
    toks = tokkies
    l = toks[1:]  # remove "utf-8"

    def not_empty(s):
        return s and s.strip()

    l = list(filter(not_empty, l))
    return l


def build_user_dataset(context, builtInType):
    contract_user, func_user, var_user = [], [], []

    fileLines = context.split('\n')
    del fileLines[-1]  # delete current line
    # print(len(fileLines), fileLines[0])

    # traverse every line in editor page
    for i, line in enumerate(fileLines):
        idx = i + 1
        _list = extractInfo(line)
        # print("_list:", _list)

        if 'contract ' in line:
            c = Contract()
            c.name = _list[_list.index('contract') + 1]
            c.lineNo = idx
            contract_user.append(c)
            # print(c.name, c.lineNo)
        elif 'function ' in line:
            f = Function()
            f.name = _list[_list.index('function') + 1]

            param_begin_pos = _list.index('(') + 1
            for pos in range(param_begin_pos, len(_list)):
                if _list[pos] == ',' or _list[pos + 1] == ',':
                    continue
                if _list[pos] == ')' or _list[pos + 1] == ')':
                    break
                else:
                    vp = Variable()
                    vp.name = _list[pos + 1]
                    vp.type = _list[pos]
                    vp.lineNo = idx
                    f.param.append(vp)
                    # print("receive:", vp.type, vp.name)
                    var_user.append(vp)

            if 'returns' in _list:
                return_begin_pos = _list.index('returns') + 2
                for pos in range(return_begin_pos, len(_list)):
                    if _list[pos] == ',' or _list[pos + 1] == ',':
                        continue
                    if _list[pos] == ')' or _list[pos + 1] == ')':
                        break
                    else:
                        vp2 = Variable()
                        vp2.name = _list[pos + 1]
                        vp2.type = _list[pos]
                        vp2.lineNo = idx
                        f.returns.append(vp2)
                        # print("return:", vp2.type, vp2.name)

            f.lineNo = idx
            func_user.append(f)
            # print(f.name, f.lineNo)

        elif 'mapping' in line:
            modifiers = [
                'public',
                'private',
                'internal',
                'external',
                'pure',
                'view',
                'const']
            for modifier in modifiers:
                if modifier in _list:
                    _list.remove(modifier)

            v = Variable()
            v.type = 'mapping'
            v.name = _list[_list.index(')') + 1]
            v.lineNo = idx
            var_user.append(v)

        else:
            modifiers = [
                'public',
                'private',
                'internal',
                'external',
                'pure',
                'view',
                'const']
            for modifier in modifiers:
                if modifier in _list:
                    _list.remove(modifier)

            for j in builtInType:
                if len(_list) and _list[0] == j:
                    v = Variable()
                    v.type = j
                    v.name = _list[_list.index(j) + 1]
                    v.lineNo = idx
                    var_user.append(v)
                    # print(v.name, v.type)

    return contract_user, func_user, var_user


def setChoice(sentence, builtInType):
    if sentence.find('contract ') != -1 or \
            sentence.find('library ') != -1 or \
            sentence.find('function ') != -1 or \
            sentence.find('modifier ') != -1 or \
            sentence.find('event ') != -1 or \
            sentence.find('struct ') != -1 or \
            sentence.find('enum ') != -1:
        return 1

    # remove heading spaces
    sentence = sentence.lstrip()
    for i in builtInType:
        if sentence.startswith(i):
            return 1
    return 2


# def random_pick(sortlist, probabilities, n=1) :
#     ret = []
#     x = random.uniform(0, 1)
#     tmpList = sortlist

#     while n :
#         cumulative_probability = 0.0
#         for item, item_probability in zip(tmpList, probabilities) :
#             cumulative_probability += item_probability
#             if x < cumulative_probability :
#                 break
#         if item not in ret :
#             ret.append(item)
#             if item in tmpList :
#                 tmpList.remove(item)
#             n -= 1
#         else :
#             continue
#     return ret


def random_pick(sortlist, probabilities, n=1):
    ret = []
    idxList = np.random.choice(len(sortlist), n, replace=False)
    for idx in idxList:
        ret.append(sortlist[idx])
    return ret


def normalize(data):
    sum_ = sum(data)
    ret = list((float(item) / sum_) for item in data)
    return ret


def choose(
        sentence,
        symbol,
        choice,
        contractName,
        funcName,
        varName,
        contract_user,
        func_user,
        var_user,
        curLine,
        times):

    returnSen = sentence
    word = []

    if symbol == '$CONTRACT$':
        if sentence.find('is') == - \
                1 or sentence.find(symbol) < sentence.find('is'):
            length = len(contractName)
            if length < times:
                return returnSen
            idxList = np.random.choice(length, times, replace=False)
            for idx in idxList:
                word.append(contractName[idx - 1][0])
        else:  # use user defined
            length = len(contract_user)
            if length < times:
                return returnSen
            contract_user_name = list(item.name for item in contract_user)
            dis = list(float(1.0 / abs(item.lineNo - curLine))
                       for item in contract_user)
            prop = normalize(dis)
            word = random_pick(contract_user_name, prop, times)
        for w in word:
            returnSen = returnSen.replace(symbol, w, 1)

    elif symbol == '$FUNCTION$':
        if choice == 1:
            length = len(funcName)
            if length < times:
                return returnSen
            idxList = np.random.choice(length, times, replace=False)
            for idx in idxList:
                word.append(funcName[idx - 1][0])
            for w in word:
                returnSen = returnSen.replace(symbol, w, 1)
        else:  # use user defined
            length = len(func_user)
            if length < times:
                return returnSen
            function_user_name = list(item.name for item in func_user)
            dis = list(float(1.0 / abs(item.lineNo - curLine))
                       for item in func_user)
            prop = normalize(dis)
            totalFunc = len(func_user)
            funcIdx = list([x for x in range(0, totalFunc)])
            selectPosList = random_pick(funcIdx, prop, times)

            for selectPos in selectPosList:
                # select whole function part
                pos1 = returnSen.find(symbol)
                pos2 = -1
                cntMatch = 0
                flag = False
                for k in range(pos1, len(returnSen)):
                    if (returnSen[k] == '('):
                        cntMatch += 1
                    elif (returnSen[k] == ')'):
                        cntMatch -= 1
                        flag = True
                    if cntMatch == 0 and flag:
                        pos2 = k
                        break
                old_str = returnSen[pos1:pos2 + 1]

                new_str = func_user[selectPos].name + '('
                for p in range(len(func_user[selectPos].param)):
                    # new_str += func_user[selectPos].param[p].type
                    # new_str += ' '
                    new_str += func_user[selectPos].param[p].name
                    if p != len(func_user[selectPos].param) - 1:
                        new_str += ', '
                new_str += ')'
                # print(old_str, new_str)

                returnSen = returnSen.replace(old_str, new_str, 1)

    elif symbol == '$VARIABLE$' or symbol == 'UNKNOWN':
        if choice == 1:
            length = len(varName)
            if length < times:
                return returnSen
            idxList = np.random.choice(length, times, replace=False)
            for idx in idxList:
                word.append(varName[idx - 1][0])
        else:  # use user defined
            length = len(var_user)
            if length < times:
                return returnSen
            variable_user_name = list(item.name for item in var_user)
            dis = list(float(1.0 / abs(item.lineNo - curLine))
                       for item in var_user)
            prop = normalize(dis)
            word = random_pick(variable_user_name, prop, times)
        for w in word:
            returnSen = returnSen.replace(symbol, w, 1)

    else:
        pass
    return returnSen


def select_word_init(context):

    contractName, funcName, varName, builtInType = init()
    contract_user, func_user, var_user = build_user_dataset(
        context, builtInType)
    # print("length:", len(contract_user), len(func_user), len(var_user))
    return contractName, funcName, varName, contract_user, func_user, var_user


def fillWords(
        sentence,
        curLine,
        context,
        contractName,
        funcName,
        varName,
        contract_user,
        func_user,
        var_user):

    ret = sentence
    finish = True
    symbol_list = ['$CONTRACT$', '$FUNCTION$', '$VARIABLE$', 'UNKNOWN']
    choice = setChoice(sentence, builtInType)

    for i in range(len(symbol_list)):
        # print(i, ret)
        times = ret.count(symbol_list[i])
        ret = choose(
            ret,
            symbol_list[i],
            choice,
            contractName,
            funcName,
            varName,
            contract_user,
            func_user,
            var_user,
            curLine,
            times)
    for it in symbol_list:
        if it in ret:
            finish = False  # not finish symbol replacing
            break
    return ret, finish


if __name__ == "__main__":
    # test
    # sentence = "contract $CONTRACT$"
    sentence = "a = mul(b.fn1(x, y).UNKNOWN);"
    # sentence = "uint $VARIABLE$ = $VARIABLE$ + 3;"
    # sentence = "function $FUNCTION$(uint $VARIABLE$, uint $VARIABLE$) public returns (uint $VARIABLE$) "
    # sentence = "function $FUNCTION$() public returns(uint $VARIABLE$, uint $VARIABLE$, uint $VARIABLE$)"

    # sentence = "contract $CONTRACT$, $CONTRACT$ is $CONTRACT$, $CONTRACT$"
    # sentence = "$VARIABLE$ = $VARIABLE$ * 2;"
    # sentence = "$VARIABLE$.$FUNCTION$($VARIABLE$);"
    # sentence = "$VARIABLE$.$FUNCTION$($VARIABLE$, $VARIABLE$).$FUNCTION$($VARIABLE$);"

    curLine = 21
    fillWords(sentence, curLine)
