import os
import just
import numpy as np
from tensorflow.keras.layers import Activation, Dense, LSTM, Bidirectional
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import RMSprop,Adam
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.backend import clear_session, set_session
import tensorflow as tf





class LSTMBase(object):

    def __init__(self, model_name, encoder_decoder=None, hidden_units=128, base_path="models/"):
        self.model_name = model_name
        self.h5_path = base_path + model_name + ".h5"
        self.pkl_path = base_path + model_name + ".pkl"

        self.model = None
        self.hidden_units = hidden_units
        if encoder_decoder is None:
            if os.path.isfile(self.pkl_path):
                self.encoder_decoder = just.read(self.pkl_path)
            else:
                self.encoder_decoder=encoder_decoder
        else:
            self.encoder_decoder = encoder_decoder

    def sample(self, preds, temperature=1.0):
        # helper function to sample an index from a probability array
        # 较少的熵使生成的序列更加可预测，较多的熵更具有创造性
        preds = np.asarray(preds).astype('float64')
        preds = np.log(preds) / temperature
        exp_preds = np.exp(preds)
        preds = exp_preds / np.sum(exp_preds)
        probas = np.random.multinomial(1, preds, 1)
        return np.argmax(probas)

    def build_model(self):
        if os.path.isfile(self.h5_path):
            print("++++++++++++++++SUCCESSFUL_LOAD++++++++++++++++++++++++++++++")
            model = self.load()
        return model



    def predict(self, text, diversity, subsequent, decay, max_prediction_steps, break_at_token=None): # diversity表示第一个token的多样性，subsequent代表后续字符的多样性，decay表示随着预测step的增加temp会依次减小多少
        if self.model is None:
            self.model = self.build_model()
            a=np.ones((1,1,2172))
            self.model.predict(a)
        outputs = []
        for i in range(max_prediction_steps):
            X = self.encoder_decoder.encode_question(text)
            preds = self.model.predict(X, verbose=0)[0]
            if i==0: # 预测第一个token
                diversity = diversity
            else:
                diversity = subsequent
                diversity -= decay
            answer_token = self.sample(preds, diversity)
            new_text_token = self.encoder_decoder.decode_y(answer_token)
            outputs.append(new_text_token)
            text += new_text_token # 把上一步预测的结果拼接在字符串后面，继续作为模型的输入，来进行预测
            if break_at_token is not None and break_at_token == new_text_token:
                break
        return self.encoder_decoder.untokenize(outputs)

    def tenSample(self, preds):
        reslist=[]

        for i in range(10):
            curtop=(np.argmax(preds))
            reslist.append(curtop)
            preds[curtop]=0

        return reslist

    def oneTokenPredict(self, text):
        if self.model is None:
            self.model = self.build_model()
        outputs = []

        X = self.encoder_decoder.encode_question(text) # 在这里面已经做了截取！
        try:
            preds = self.model.predict(X, verbose=0)[0]
        except Exception as e:
            print(e)
            clear_session()
            preds = self.model.predict(X, verbose=0)[0]

        answer_tokens = self.tenSample(preds)

        res = []

        for answer_token in answer_tokens:
            new_text_token = self.encoder_decoder.decode_y(answer_token)
            if 'UNKNOWN' not in new_text_token :
                res.append(new_text_token)

        return res


    def load(self):
        return load_model(self.h5_path)
        

