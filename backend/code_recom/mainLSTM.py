from syntaxCheck import *
import time
import os
import sys
from threading import Thread, BoundedSemaphore
from time import sleep
import random

import just
from encoder_decoder import TextEncoderDecoder, text_tokenize
from model import LSTMBase


def neural_complete(model, text, diversities, subsequent, decay):
    predictions = [
        model.predict(
            text,
            diversity=diversities[index],
            subsequent=subsequent[index],
            decay=decay,
            max_prediction_steps=80,
            break_at_token="\n") for index in range(
            len(diversities))]
    # returning the latest sentence, + prediction
    suggestions = [text.split("\n")[-1] + x.rstrip("\n") for x in predictions]
    return suggestions


def read_models(base_path="models/"):
    return set([x.split(".")[0] for x in os.listdir(base_path)])


def get_model(model_name):
    return LSTMBase(model_name)


def load_models():
    models = {x: get_model(x) for x in read_models()}
    return models


def callLSTM(sentence, models):

    model_name = "neural_token"
    # model, sentence, temperature
    first_temp = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.5, 1.6,
                  1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6]
    subsequent_temp = [
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1,
        0.1]
    # suggestions = neural_complete(models[model_name], sentence, [0.1, 0.3, 0.5, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0])
    suggestions = neural_complete(
        models[model_name],
        sentence,
        first_temp,
        subsequent_temp,
        0)

    return suggestions


def callOneLSTM(sentence, models):
    model_name = "neural_token"
    predictions = models[model_name].oneTokenPredict(sentence)
    return predictions


class Context:
    def __init__(self, type, startLine, endLine):
        self.type = type
        self.startLine = startLine
        self.endLine = endLine


def getContext(filename):
    file = open(filename, 'r')
    context = file.readlines()
    file.close()
    return context


def getLocation(curLine, context):
    # father: "Function" or "Contract" or "None"
    father = "None"
    cList = []
    cList.append(Context("None", 1, len(context)))

    lineNum = 0
    while lineNum != len(context):
        if 'contract ' in context[lineNum]:
            cntBracker = 0
            for j in range(lineNum, len(context)):
                cntBracker += context[j].count('{')
                cntBracker -= context[j].count('}')

                if cntBracker == 0:
                    cList.append(Context("Contract", lineNum + 1, j + 1))
                    lineNum = j
                    break
        else:
            lineNum += 1

    lineNum = 0
    while lineNum != len(context):
        if 'function ' in context[lineNum] or 'modifier ' in context[lineNum]:
            cntBracker = 0
            for j in range(lineNum, len(context)):
                cntBracker += context[j].count('{')
                cntBracker -= context[j].count('}')

                if cntBracker == 0:
                    cList.append(Context("Function", lineNum + 1, j + 1))
                    lineNum = j
                    break
        else:
            lineNum += 1

    for i in range(len(cList)):
        # print(cList[i].type, cList[i].startLine, cList[i].endLine)
        if curLine >= cList[i].startLine and curLine <= cList[i].endLine:
            father = cList[i].type
    # print(father)
    return father


class FixedStatement:
    def __init__(self, name, desc):
        self.name = name
        self.desc = desc


def init_fixed_statement():
    globalFuncList = []

    globalFuncList.append(FixedStatement('for-loop', 'control structure'))
    globalFuncList.append(FixedStatement('while-loop', 'control structure'))
    globalFuncList.append(FixedStatement('if-else', 'control structure'))
    globalFuncList.append(FixedStatement('do-loop', 'control structure'))

    # globalFuncList.append(FixedStatement('blockhash(uint)', 'global function'))
    # globalFuncList.append(FixedStatement('block.coinbase(address)', 'global function'))
    # globalFuncList.append(FixedStatement('block.difficulty(uint)', 'global function'))
    # globalFuncList.append(FixedStatement('block.gaslimit(uint)', 'global function'))
    # globalFuncList.append(FixedStatement('block.number(uint)', 'global function'))

    # globalFuncList.append(FixedStatement('gasleft()', 'global function'))
    # globalFuncList.append(FixedStatement('msg.data(bytes)', 'global function'))
    # globalFuncList.append(FixedStatement('msg.sender(address)', 'global function'))
    # globalFuncList.append(FixedStatement('msg.value(uint)', 'global function'))
    # globalFuncList.append(FixedStatement('msg.sig(bytes4)', 'global function'))

    # globalFuncList.append(FixedStatement('assert(bool condition)', 'global function'))
    # globalFuncList.append(FixedStatement('require(bool condition)', 'global function'))
    globalFuncList.append(FixedStatement('revert();', 'global function'))
    # globalFuncList.append(FixedStatement('selfdestruct(address)', 'global function'))
    # globalFuncList.append(FixedStatement('keccak256(args)', 'global function'))

    return globalFuncList


def choose_fix_statement(setLen1, globalFuncList):
    fixList = []
    while setLen1:
        idx = random.randint(0, len(globalFuncList) - 1)
        if globalFuncList[idx] not in fixList:
            fixList.append(globalFuncList[idx])
            setLen1 -= 1
    return fixList


# def deal_with_single_sen(str_init, curLine, context, father) :
#     sentence = ''
#     result = 0

#     if str_init == '' :
#         return sentence, result

#     print("Before filling words :", str_init)

#     result0 = location_check(str_init, father)
#     print("* Context location check:", result0)
#     if result0 == 'Fail!' :
#         return sentence, result

#     result1 = syntax_check_r1(str_init)
#     print("* Syntax check -r1:", result1)
#     if result1 == 'Fail!' :
#         return sentence, result

#     errCnt = 0
#     choice, contractName, funcName, varName, contract_user, func_user, var_user = select_word_init(str_init, context)

#     while True :
#         if errCnt > 2:
#             break
#         # fill in words
#         str_fill = fillWords(str_init, curLine, context,
#                                 choice, contractName, funcName, varName, contract_user, func_user, var_user)
#         print("After filling words  :", str_fill)

#         result2 = syntax_check_r2(str_fill)
#         print("* Syntax check -r2:", result2)

#         if result2 == 'Pass!' :
#             result = 1
#             return str_fill, result
#         else :
#             errCnt += 1

#     return sentence, result


def run_child(
        str_initList,
        curLine,
        context,
        father,
        threads,
        ret,
        contractName,
        funcName,
        varName,
        contract_user,
        func_user,
        var_user):
    def deal_with_single_sen(str_init, curLine, context, father):
        sentence = ''

        if str_init == '':
            return

        print("Before filling words :", str_init)

        result0 = location_check(str_init, father)
        print("* Context location check:", result0)
        if result0 == 'Fail!':
            return

        result1 = syntax_check_r1(str_init)
        print("* Syntax check -r1:", result1)
        if result1 == 'Fail!':
            return

        errCnt = 0
        cnt = 0
        while True:
            # print("errCnt:", errCnt)
            if errCnt >= 2 or cnt >= 2:
                return
            # fill in words
            str_fill, finish = fillWords(
                str_init, curLine, context, contractName, funcName, varName, contract_user, func_user, var_user)
            print("After filling words  :", str_fill)
            if not finish:
                return

            result2 = syntax_check_r2(str_fill)
            print("* Syntax check -r2:", result2)

            if result2 == 'Pass!':
                ret.append(str_fill)
                # return
                cnt += 1
            else:
                errCnt += 1

    maxjobs = BoundedSemaphore(20)

    def wrapper(str_init, curLine, context, father):
        deal_with_single_sen(str_init, curLine, context, father)
        maxjobs.release()

    for str_init in str_initList:
        # print("xxINIT:", str_init)
        maxjobs.acquire()
        thread = Thread(
            target=wrapper,
            args=(
                str_init,
                curLine,
                context,
                father))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def callMain(str_initList, curLine, context):
    print("**", str_initList)
    str_initList = list(set(str_initList))
    t1 = time.time()

    father = getLocation(curLine, context)
    totalLen = 10  # number of showing sentences

    contractName, funcName, varName, contract_user, func_user, var_user = select_word_init(
        context)
    globalFuncList = init_fixed_statement()

    t2 = time.time()
    print("$ Time cost Initial:", (t2 - t1))

    # call LSTM model
    print("Initial:", str_initList)

    t3 = time.time()
    print("$ Time cost Call LSTM:", (t3 - t2))

    print("*", str_initList, len(str_initList))
    recomList = []
    threads = []
    # while len(recomList) < setLen2:
    #     run_child(str_initList, curLine, context, father, threads, recomList,
    #               contractName, funcName, varName, contract_user, func_user, var_user)
    #     recomList = list(set(recomList))
    # print(len(recomList))
    run_child(
        str_initList,
        curLine,
        context,
        father,
        threads,
        recomList,
        contractName,
        funcName,
        varName,
        contract_user,
        func_user,
        var_user)
    recomList = list(set(recomList))
    recomList = sorted(recomList, key=lambda i: i[0])
    print("RecomList complete.")

    # using union prop for selecting
    needLen = totalLen - len(recomList)
    setLen1 = min(needLen, len(globalFuncList))
    fixListName, fixListDesc = [], []
    if setLen1 > 0:
        fixList = choose_fix_statement(setLen1, globalFuncList)
        fixListName = list([item.name for item in fixList])
        fixListDesc = list([item.desc for item in fixList])
        fixListName = sorted(fixListName, key=lambda i: i[0])
    print("FixList complete.")

    candidateList = recomList + fixListName

    print("====== CandidateList: ======")
    for cand in candidateList:
        if 'UNKNOWN' not in cand:
            print(cand)

    print("$ Time cost Fill Words:", (time.time() - t3))
    print("$ Time cost Total:", (time.time() - t1))

    return candidateList


if __name__ == "__main__":

    input_sentence = "uint a;"  # last sentence

    # call LSTM model
    # models = load_models()
    # str_initList = callLSTM(input_sentence, models)
    str_initList = [
        'uint $VARIABLE$ = $VARIABLE$;',
        '$VARIABLE$ = 1;',
        'modifier UNKOWN']

    curLine = 21  # starts with 1
    conTextFileName = './myContract.sol'
    context = getContext(conTextFileName)

    candidateList = callMain(str_initList, curLine, context)
