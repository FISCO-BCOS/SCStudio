from collections import Counter
import numpy as np
import just
import gc
import tokenize as tk
from io import BytesIO


def text_tokenize(txt):
    """ specific tokenizer suitable for extracting 'python tokens' """
    toks = []
    try:
        for x in tk.tokenize(BytesIO(txt.encode('utf-8')).readline):
            toks.append(x)
    except Exception:
        pass
    tokkies = []
    old = (0, 0)
    for t in toks:
        if not t.string:
            continue
        if t.start[0] == old[0] and t.start[1] > old[1]:
            tokkies.append(
                " " * (t.start[1] - old[1]))
        tokkies.append(t.string)
        old = t.end
    if txt.endswith(" "):
        tokkies.append(" ")
    toks = tokkies
    return toks[1:]


class EncoderDecoder():
    def __init__(
            self,
            maxlen,
            min_count,
            unknown,
            padding,
            tokenize,
            untokenize,
            reuse,
            totrain,
            usenew):
        self.maxlen = maxlen
        self.min_count = min_count
        self.unknown = unknown
        self.padding = padding
        self.tokenize = tokenize
        self.untokenize = untokenize
        self.questions = []
        self.answers = []
        self.reuse = reuse
        self.totrain = totrain
        self.ex, self.dx = None, None
        self.ey, self.dy = None, None
        self.num_unique_q_tokens = 0
        self.num_unique_a_tokens = 0
        self.num_questions = 0
        self.num_answers = 0
        self.usenew = usenew
        if self.totrain == 1 and self.usenew == 0:
            self.build_data()
            print("SUCCESSFULLY INIT!")
        elif self.usenew == 1:
            self.build_data_new()
        else:
            self.build_data()

    def build_data(self):
        raise NotImplementedError

    def build_data_new(self):
        raise NotImplementedError

    def encode_x(self, x):
        return self.ex.get(x,
                           0)

    def encode_y(self, y):
        return self.ey.get(y, 0)

    def decode_x(self, x):
        return self.dx.get(x, self.unknown)

    def decode_y(self, y):
        return self.dy.get(y, self.unknown)

    def build_coders(self, tokens):
        tokens = [item for sublist in tokens for item in sublist]
        word_to_index = {k: v for k, v in Counter(
            tokens).items() if v >= self.min_count}
        word_to_index = {
            k: i for i, (k, v) in enumerate(
                word_to_index.items(), 1)}
        word_to_index[self.unknown] = 0
        index_to_word = {v: k for k, v in word_to_index.items()}
        index_to_word[0] = self.unknown
        print("BUILT CODERS!")
        return word_to_index, index_to_word

    def build_qa_coders(self):
        self.ex, self.dx = self.build_coders(self.questions)
        print("unique question tokens:", len(self.ex))
        print("Number of QA pairs:", len(self.questions))
        self.ey, self.dy = self.build_coders([self.answers])
        print("unique answer tokens:", len(self.ey))
        print("SUCCESFULLY REBUILT QA CODERS")

    def re_qa_coders(self):
        ed = just.read("models/neural_token.pkl")
        self.ex = ed.ex
        self.dx = ed.dx
        self.ey = ed.ey
        self.dy = ed.dy
        del ed
        # gc.collect()
        print(
            "Reload the original tokens, and unique question tokens:", len(
                self.ex))
        print("and unique answer tokens:", len(self.ey))

    def get_xy(self):
        print("START GETTING XY")
        n = len(self.questions)

        tokenX = np.zeros((n, self.maxlen), dtype=np.int)
        y = np.zeros((n, len(self.ey)), dtype=np.bool)
        print("DELARATION!")
        l = len(self.questions)
        for num_pair, (question, answer) in enumerate(
                zip(self.questions, self.answers)):
            for num_token, q_token in enumerate(question):
                tokenX[num_pair, num_token] = self.encode_x(q_token)

            y[num_pair, self.encode_y(answer)] = 1
        print("COMPELETED FOR LOOP")
        self.num_unique_q_tokens = len(self.ex)
        self.num_unique_a_tokens = len(self.ey)
        self.num_questions = len(self.questions)
        self.num_answers = len(self.answers)

        if self.reuse == 0:
            del self.answers
            del self.questions
            # gc.collect()
            just.write(self, "models/neural_token.pkl")
            # self.saveTxt()
        if self.totrain == 1:
            del self.ex
            del self.ey
            del self.dx
            del self.dy
            # gc.collect()
            if hasattr(self, "questions"):
                del self.questions
            if hasattr(self, "answers"):
                del self.answers
            # gc.collect()
        print("SUCCESSFULLY GOT XY!")
        return tokenX, y

    def pad(self, tokens):
        seqlen = len(tokens)

        return [self.padding] * (self.maxlen - seqlen + 1) + tokens

    def encode_question(self, text):
        X = np.zeros((1, self.maxlen))
        prepped = self.pad(self.tokenize(text)[-self.maxlen:])
        for num, x in enumerate(prepped[1:]):
            X[0, num] = self.encode_x(x)
        return X


class TextEncoderDecoder(EncoderDecoder):
    def __init__(
            self,
            texts,
            tokenize=str.split,
            untokenize=" ".join,
            window_step=3,
            maxlen=20,
            min_count=1,
            unknown="UNKNOWN",
            padding="PADDING",
            reuse=0,
            totrain=1,
            usepkl=0,
            usenew=0):
        self.texts = texts
        self.window_step = window_step
        self.usepkl = usepkl
        c = super(TextEncoderDecoder, self)
        c.__init__(
            maxlen,
            min_count,
            unknown,
            padding,
            tokenize,
            untokenize,
            reuse,
            totrain,
            usenew)

    def build_data(self):
        self.questions = []
        self.answers = []
        tokencnt = 0
        if len(self.texts) != 0:
            print("Building data without questions.pkl")
            for text in self.texts:
                tokens = self.tokenize(text)
                text = self.pad(tokens)
                tokencnt += len(tokens)
                seqlen = len(text)
                for i in range(0, seqlen - self.maxlen, self.window_step):
                    self.questions.append(text[i: i + self.maxlen])
                    self.answers.append(text[i + self.maxlen])
        else:
            print("Using questions.pkl")
            self.questions = just.read("models/questions.pkl")
            self.answers = just.read("models/answers.pkl")
        del self.texts

        print(tokencnt)
        # gc.collect()
        print("SUCCESSFULLY BUILT DATA!")
        if self.reuse == 0:
            self.build_qa_coders()
        else:
            self.re_qa_coders()
        # print("number of QA pairs:", len(self.questions))
        if self.totrain == 1:
            return self.get_xy()

    '''
    def readTxt(self):
        self.ex=dict()
        self.ey=dict()
        self.dx=dict()
        self.dy=dict()
        with open("models/QText.txt",'r') as f:
            flag=0
            curtoken=""
            for line in f.readlines():
                #line=line.strip()
                line=line[:-1]
                if(flag==0):
                    curtoken=line
                    if(curtoken=="`"):
                        curtoken="\n"
                    flag=1
                else:
                    flag=0
                    self.ex[curtoken]=int(line)
                    self.dx[int(line)]=curtoken
        with open("models/AText.txt",'r') as f:
            flag=0
            curtoken=""
            for line in f.readlines():
                #line=line.strip()
                line=line[:-1]
                if(flag==0):
                    curtoken=line
                    if (curtoken == "`"):
                        curtoken = "\n"
                    flag=1
                else:
                    flag=0
                    self.ey[curtoken]=int(line)
                    self.dy[int(line)]=curtoken

    '''

    def build_data_new(self):
        self.questions = []
        self.answers = []
        self.re_qa_coders()
        # self.readTxt()
        self.num_unique_q_tokens = len(self.ex)
        self.num_unique_a_tokens = len(self.ey)
        print("USING NEW BUILD DATA!!!!!")
        # self.X=[[0 for i in range(self.maxlen)]]
        # self.y=[[0 for i in range(self.num_unique_a_tokens)]]
        self.x = np.zeros((19519500, self.maxlen), dtype=np.int)
        self.y = np.zeros((19519500, 1), dtype=np.int)
        # self.X=np.zeros((1024, self.maxlen),dtype=np.int)
        # self.Y=np.zeros((1024, self.num_unique_a_tokens),dtype=np.bool)
        if self.usepkl == 0:
            cnt = 0
            # cpa=[0 for i in range(self.maxlen)]
            # cpb=[0 for i in range(len(self.ey))]
            for text in self.texts:
                tokens = self.tokenize(text)
                text = self.pad(tokens)
                seqlen = len(text)

                n = int((seqlen - self.maxlen) / self.window_step) + 1
                for i in range(0, seqlen - self.maxlen, self.window_step):
                    curq = text[i:i + self.maxlen]
                    cura = text[i + self.maxlen]
                    for num_token, q_token in enumerate(curq):
                        self.x[cnt, num_token] = self.ex.get(q_token, 0)
                    self.y[cnt, 0] = self.ey.get(cura, 0)

                    cnt += 1
                    # b[0, self.ey.get(cura,0)]=0
                print(str(cnt))
            self.num_questions = cnt
            self.num_answers = cnt
            just.write(self, "models/x_y_new.pkl")
        else:
            t = just.read("models/x_y_new.pkl")
            self.x = t.x
            self.y = t.y
            self.num_questions = t.num_questions
            self.num_answers = t.num_answers
            del t
            gc.collect()
        del self.texts
        gc.collect()
        print("SUCCESSFULLY BUILT DATA!")
        # self.X=np.array(self.X)
        # self.y=np.array(self.y)
        print("TRANSFORMED TO NUMPY ARRAY!")
        print("TOTAL QA PAIRS")
        print(self.num_questions)
        return


class QuestionAnswerEncoderDecoder(EncoderDecoder):
    pass
