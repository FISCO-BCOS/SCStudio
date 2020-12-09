from collections import Counter
import numpy as np
import just
import gc
import tokenize as tk
from io import BytesIO


# 需要记住的是！tokenize.tokenize()接收两个参数，一个是输出流即readline，所以必须要把原来的txt转成一个输出流再调用readline
def text_tokenize(txt):
    """ specific tokenizer suitable for extracting 'python tokens' """
    toks = []
    try:
        for x in tk.tokenize(BytesIO(txt.encode('utf-8')).readline):  # BytesIO将普通的字符串转成一个IO流！~~
            toks.append(x)
    except Exception:
        pass
    tokkies = []
    old = (0, 0)  # old表示的是上一个token末尾字符所在的（行，列），舒服！
    for t in toks:
        if not t.string:
            continue
        if t.start[0] == old[0] and t.start[1] > old[1]:  # 这里核对的是什么呢？如果这一次token的开始和上一次token的结尾在同一行，但是不同列的话，就执行下面一行！
            tokkies.append(
                " " * (t.start[1] - old[1]))  # 就填充若干长度的空格。为什么要填充呢？因为啊，tokenize会把空格去掉啊！~所以啊，我们就要把空格补回来鸭~那为什么空格这么重要呢？
        tokkies.append(t.string)
        old = t.end
    if txt.endswith(" "):
        tokkies.append(" ")
    toks = tokkies
    return toks[1:]  # 去掉了"utf-8"


class EncoderDecoder():
    # __slots__ = "maxlen","min_count","unknown","padding","tokenize","untokenize","questions","answers","reuse","ex","ey","dx","dy","num_unique_q_tokens","num_unique_a_tokens","totrain","num_questions","num_answers","usenew","X","y"
    def __init__(self, maxlen, min_count, unknown, padding, tokenize, untokenize, reuse, totrain, usenew):
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
                           0)  # 这里的ex.get本质调用的就是dict！！！！！！后面的内容就是default的值！也就是说，如果当前的x没有被编码过的话，就返回0，刚刚好就映射到了UNKNOWN!!!!

    def encode_y(self, y):
        return self.ey.get(y, 0)

    def decode_x(self, x):
        return self.dx.get(x, self.unknown)

    def decode_y(self, y):
        return self.dy.get(y, self.unknown)

    def build_coders(self, tokens):
        # 这是在对word做编码？而不是对
        tokens = [item for sublist in tokens for item in sublist]  # 这里面，每一个sublist就是一次划分 ，然后从每一次划分中提取出单个字符出来！
        word_to_index = {k: v for k, v in Counter(tokens).items() if
                         v >= self.min_count}  # v是各个字符出现的次数！！！而k是字符！如"l":3表示l出现了3次！而v就是一个设定出现次数大于某个阈值的字符才纳入统计的调节数字！其目的就是方便后面人为的忽略一些出现次数太少的字符！
        word_to_index = {k: i for i, (k, v) in enumerate(word_to_index.items(),
                                                         1)}  # enumerate的第二个参数表示一个起始的索引值，即从1开始索引。这条语句提取出了字符，和下标（注意，没提取出次数！！！！）。形成了'h':1,'e':2,'l':3等等这样的结构！
        word_to_index[self.unknown] = 0  # self.unknown就是一个"UNKNOWN"的字符串，把下标为0的那一项给占用掉
        index_to_word = {v: k for k, v in word_to_index.items()}
        index_to_word[0] = self.unknown
        print("BUILT CODERS!")
        return word_to_index, index_to_word

    def build_qa_coders(self):
        self.ex, self.dx = self.build_coders(
            self.questions)  # 这就成功的build出来了！ex就是question的word_to_index的！而dx就是index_to_word的dict！
        print("unique question tokens:", len(self.ex))  # 返回一下总共有多少个不同的字符鸭
        print("Number of QA pairs:", len(self.questions))
        self.ey, self.dy = self.build_coders([self.answers])  # build出来了answers里面word_to_index和index_to_word的对应表！
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
        print("Reload the original tokens, and unique question tokens:", len(self.ex))
        print("and unique answer tokens:", len(self.ey))

    '''
    def saveTxt(self):
        with open("models/QText.txt",'w') as f:
            for k,v in self.ex.items():
                if(k!="\n"):
                    f.write(k+"\n")
                    f.write(str(v)+"\n")
                else:
                    f.write("`"+"\n")
                    f.write(str(v)+"\n")
        with open("models/AText.txt",'w') as f:
            for k,v in self.ey.items():
                if (k != "\n"):
                    f.write(k + "\n")
                    f.write(str(v) + "\n")
                else:
                    f.write("`" + "\n")
                    f.write(str(v) + "\n")
    '''

    def get_xy(self):  # 其目的就是形成数据集，进行one-hot编码！
        print("START GETTING XY")
        n = len(self.questions)
        # X = np.zeros((n, self.maxlen, len(self.ex)), dtype=np.bool) # 形成数据集组数*每个问题的字符长度*字符种类数的matrix
        tokenX = np.zeros((n, self.maxlen), dtype=np.int)
        y = np.zeros((n, len(self.ey)), dtype=np.bool)
        print("DELARATION!")
        l = len(self.questions)
        for num_pair, (question, answer) in enumerate(zip(self.questions,
                                                          self.answers)):  # 将ZIP的两个东西，一项一项配对打包成元组，很好用的东西呢 >_<!!!因此枚举的结果就会是number,question,answer,太棒了！！
            for num_token, q_token in enumerate(question):  # 枚举每一个question的字符，进行标记
                tokenX[num_pair, num_token] = self.encode_x(q_token)
            #print(str(num_pair) + "/" + str(l))
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
        # 这是在补齐这个长度，保证当seqlen本身比maxlen还要小的时候，能够补齐到maxlen的长度
        return [self.padding] * (self.maxlen - seqlen + 1) + tokens

    def encode_question(self, text):
        # X = np.zeros((1, self.maxlen, len(self.ex)), dtype=np.bool) # 1*问题的长度*字符的多样性！这里就体现出UNKNOWN的好处了！如果后面用户输入的预测的引子，有之前没编码过的项的话，就需要一个UNKNOWN来代表他！
        X = np.zeros((1, self.maxlen))
        prepped = self.pad(self.tokenize(text)[-self.maxlen:])
        for num, x in enumerate(prepped[1:]):
            X[0, num] = self.encode_x(x)
        return X


class TextEncoderDecoder(EncoderDecoder):
    # __slots__ = "maxlen", "min_count", "unknown", "padding", "tokenize", "untokenize", "questions", "answers", "reuse", "ex", "ey", "dx", "dy", "num_unique_q_tokens", "num_unique_a_tokens", "totrain", "num_questions", "num_answers", "usenew", "X", "y","texts","window_step"
    def __init__(self, texts, tokenize=str.split, untokenize=" ".join,
                 window_step=3, maxlen=20, min_count=1,
                 unknown="UNKNOWN", padding="PADDING", reuse=0, totrain=1, usepkl=0, usenew=0):
        self.texts = texts
        self.window_step = window_step
        self.usepkl=usepkl
        c = super(TextEncoderDecoder, self)
        # 即找到TextEncoderDecoder的父类EncoderDecoder，然后再将其
        # 转换为EncoderDecoder对象，此时，c即为一个EncoderDecoder对象
        c.__init__(maxlen, min_count, unknown, padding, tokenize, untokenize, reuse, totrain, usenew)

    def build_data(self):
        self.questions = []
        self.answers = []
        tokencnt=0
        if len(self.texts) != 0:
            print("Building data without questions.pkl")
            for text in self.texts:
                # 这里的tokenize就是引用的str.split。这里的作用就是把text分成字符的list!!!如text="hello",self.tokenize之后就是
                # tokens=['h','e','l',...]
                # 但是token为标准训练的时候，tokenize指的是text_tokenize函数
                tokens = self.tokenize(text)
                # 这里面返回的tokens就是拆分后的token
                text = self.pad(tokens)
                tokencnt+=len(tokens)
                seqlen = len(text)  # 现在这里面的text，就是一个一个的token咯~
                for i in range(0, seqlen - self.maxlen, self.window_step):  # 只不过，就是把char换成token而已呀
                    # 即准备训练集！
                    self.questions.append(text[i: i + self.maxlen])
                    self.answers.append(text[i + self.maxlen])
        else:
            print("Using questions.pkl")
            self.questions = just.read("models/questions.pkl")
            self.answers = just.read("models/answers.pkl")
        del self.texts
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("total tokencnt!!")
        print(tokencnt)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # gc.collect()
        print("SUCCESSFULLY BUILT DATA!")
        if self.reuse == 0:
            self.build_qa_coders()  # 重点改造这里！想办法把这里换成基于已有的编码进行训练！
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
                # 这里的tokenize就是引用的str.split。这里的作用就是把text分成字符的list!!!如text="hello",self.tokenize之后就是
                # tokens=['h','e','l',...]
                # 但是token为标准训练的时候，tokenize指的是text_tokenize函数
                tokens = self.tokenize(text)
                # 这里面返回的tokens就是拆分后的token
                text = self.pad(tokens)
                seqlen = len(text)  # 现在这里面的text，就是一个一个的token咯~

                n = int((seqlen - self.maxlen) / self.window_step) + 1
                # self.X=np.zeros((n,self.maxlen),dtype=np.int)
                # self.y=np.zeros((n,len(self.ey)),dtype=np.bool)
                # a=np.zeros((1,self.maxlen),dtype=np.int)
                # b=np.zeros((1,self.num_unique_a_tokens),dtype=np.bool)
                # b=cpb
                for i in range(0, seqlen - self.maxlen, self.window_step):  # 只不过，就是把char换成token而已呀
                    # 即准备训练集！
                    curq = text[i:i + self.maxlen]
                    cura = text[i + self.maxlen]
                    # 给curq 和 cura一个编码
                    for num_token, q_token in enumerate(curq):
                        # a [num_token]=self.ex.get(q_token,0)
                        # a[0, num_token]=self.ex.get(q_token, 0)
                        self.x[cnt, num_token] = self.ex.get(q_token, 0)
                    # b[self.ey.get(cura,0)]=1
                    # b[0, self.ey.get(cura,0)]=1
                    self.y[cnt, 0] = self.ey.get(cura, 0)
                    # self.X=np.concatenate((self.X, a))
                    # self.y=np.concatenate((self.y, b))
                    # self.X.append(a)
                    # self.y.append(b)

                    cnt += 1
                    # b[0, self.ey.get(cura,0)]=0
                print(str(cnt))
            self.num_questions=cnt
            self.num_answers=cnt
            just.write(self,"models/x_y_new.pkl")
        else:
            t=just.read("models/x_y_new.pkl")
            self.x=t.x
            self.y=t.y
            self.num_questions=t.num_questions
            self.num_answers=t.num_answers
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
        # TODO: Numpy Array比list更有效率！所以要还换成Numpy Array!但开大数组，访问到5337109的时候被kill
        return


class QuestionAnswerEncoderDecoder(EncoderDecoder):
    pass
