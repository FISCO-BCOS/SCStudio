import os
import just
from encoder_decoder import TextEncoderDecoder, text_tokenize
from model import LSTMBase
from flask import Flask, jsonify, request
from tensorflow.keras.backend import clear_session
import tensorflow as tf
import json

from mainLSTM import *
from selectWord import *

app = Flask(__name__)

def get_model(model_name):
    return LSTMBase(model_name)


def read_models(base_path="models/"):
    return set([x.split(".")[0] for x in os.listdir(base_path)])


from tensorflow.python.keras.backend import set_session
sess = tf.Session()
graph = tf.get_default_graph()

set_session(sess)
models = {x: get_model(x) for x in read_models()}


def preprocess(deal):
    deal.replace("\\n","\n")
    deal.replace("\\\"","\"")
    return deal


def fillAWord(symbol, sentence, curLine, context, fillNums, 
              contractName, funcName, varName, contract_user, func_user, var_user):
    ret = []
    choice = setChoice(sentence)
    print("Choice:", choice)
    
    if symbol == 'CONTRACT' :
        if sentence.find('is') == -1 :
            length = len(contractName)
            times = min(length, fillNums)
            idxList = np.random.choice(length, times, replace=False)
            for idx in idxList :
                ret.append(contractName[idx-1][0])
        else :  # use user defined
            length = len(contract_user)
            times = min(length, fillNums)
            contract_user_name = list(item.name for item in contract_user)
            dis = list(float(1.0 / (abs(item.lineNo - curLine) + 1)) for item in contract_user)
            prop = normalize(dis)
            ret = random_pick(contract_user_name, prop, times)
        # print("Contract:", ret)

    if symbol == 'VARIABLE' or symbol == 'UNKNOWN' :
        if choice == 1 and sentence.find('=') == -1 :
            length = len(varName)
            times = min(length, fillNums)
            idxList = np.random.choice(length, times, replace=False)
            for idx in idxList :
                ret.append(varName[idx-1][0])
        else :  # use user defined
            length = len(var_user)
            times = min(length, fillNums)
            variable_user_name = list(item.name for item in var_user)
            # variable_user_line = list(item.lineNo for item in var_user)
            # variable_user_line_abs = list(abs(item.lineNo - curLine + 1) for item in var_user)
            print("V:", variable_user_name)
            # print(variable_user_line, variable_user_line_abs)
            dis = list(float(1.0 / (abs(item.lineNo - curLine) + 1)) for item in var_user)
            prop = normalize(dis)
            ret = random_pick(variable_user_name, prop, times)
        # print("Variable:", ret)
    
    if symbol == 'FUNCTION' :
        if choice == 1 :
            length = len(funcName)
            times = min(length, fillNums)
            idxList = np.random.choice(length, times, replace=False)
            for idx in idxList :
                ret.append(funcName[idx-1][0])
        else :  # use user defined
            length = len(func_user)
            times = min(length, fillNums)
            function_user_name = list(item.name for item in func_user)
            dis = list(float(1.0 / (abs(item.lineNo - curLine) + 1)) for item in func_user)
            prop = normalize(dis)
            totalFunc = len(func_user)
            funcIdx = list([x for x in range(0, totalFunc)])
            selectPosList = random_pick(funcIdx, prop, times)

            for selectPos in selectPosList :
                new_str = func_user[selectPos].name + '('
                for p in range(len(func_user[selectPos].param)) :
                    # new_str += func_user[selectPos].param[p].type
                    # new_str += ' '
                    new_str += func_user[selectPos].param[p].name
                    if p != len(func_user[selectPos].param) - 1 :
                        new_str += ', '
                new_str += ')'
                ret.append(new_str)
        # print("Function:", ret)

    else : 
        pass

    return ret


@app.route("/tokenPredict", methods=["POST", "GET"])
def tokenPredict():
    if request.method == "POST":
        data = request.get_data(as_text=True)
        print("POST:", data)
        total = json.loads(data)
        context = preprocess(total["context"])
        sentence = total["sentence"]
        curLine = total["curLine"]
        print(context, "<:>", sentence, "<:>", curLine)

        model_name = "neural_token"

        global sess
        global graph

        with graph.as_default():
            set_session(sess)
            # if context[:-1] != '\n' :
            #     context += '\n'
            context = context.rstrip()
            context += ' '
            # param temp
            str_initList = callOneLSTM(context, models)
            print(str(str_initList))

            contractName, funcName, varName, contract_user, func_user, var_user = select_word_init(context)
            # variable_user_name = list(item.name for item in var_user)
            # print("variable_user_name:", variable_user_name)
            # function_user_name = list(item.name for item in func_user)
            # print("function_user_name:", function_user_name)
            # contract_user_name = list(item.name for item in contract_user)
            # print("contract_user_name:", contract_user_name)

            symbols = ['CONTRACT', 'FUNCTION', 'VARIABLE', 'UNKNOWN']
            candidateList = []
            fillNums = 5
            for str_init in str_initList :
                if str_init in symbols :
                    str_fill_list = fillAWord(str_init, sentence, curLine, context, fillNums, 
                                              contractName, funcName, varName, contract_user, func_user, var_user)
                    for str_fill in str_fill_list :
                        candidateList.append(str_fill)
                else :
                    candidateList.append(str_init)
            print("====== CandidateList: ======")
            print(candidateList)

            return jsonify({"data": {"results": [x.strip() for x in candidateList]}})

    if request.method == "GET":
        return "use post!"



# @app.route("/predict", methods=["POST","GET"])
# def predict():

#     if request.method == "POST":
#         # d = request.form
#         # print("*d", d, type(d))
#         # data = request.form.get("data")
#         data = request.get_data(as_text=True)
#         print("POST:", data)
#         total = json.loads(data)
#         sentence = total["sentence"]
#         print(sentence)
#         curLine = total["curLine"]
#         print(curLine)
#         context = preprocess(total["context"])
#         print(context)
        
#         model_name = "neural_token"
        
#         global sess
#         global graph
           
#         with graph.as_default():
#             set_session(sess)
#             if(sentence[:-1]!='\n'):
#                 sentence+="\n"
#             # param temp
#             str_initList = callLSTM(sentence, models) 

#             #curLine = 21
#             #conTextFileName = './myContract.sol'
#             #context = getContext(conTextFileName)
#             candidateList = callMain(str_initList, curLine, context)
#             return jsonify({"data": {"results": [x.strip() for x in candidateList]}})
#     if request.method == "GET":
#         return "use post!"


def main(host="0.0.0.0", port=9065):
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()


