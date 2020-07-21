import os, shutil, re

CONTRACT_PATH = './test/'
# CONTRACT_PATH = './largeDataset/'
OUTPUT_PATH = './output/'
OUTPUTAST_PATH = OUTPUT_PATH + 'AST/'
OUTPUTCONTRACT_PATH = OUTPUT_PATH + 'Contract/'

def create_folder(filePath):
    if os.path.exists(filePath):
        pass
    else :
        os.mkdir(filePath)

def init():
    create_folder(CONTRACT_PATH)
    # empty output folder
    shutil.rmtree(OUTPUTAST_PATH)
    create_folder(OUTPUTAST_PATH)
    shutil.rmtree(OUTPUTCONTRACT_PATH)
    create_folder(OUTPUTCONTRACT_PATH)


def comment_remover(text): 
    def replacer(match): 
        s = match.group(0) 
        if s.startswith('/') : 
            return " " # note: a space and not an empty string 
        else : 
            return s 
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"', 
        re.DOTALL | re.MULTILINE 
    ) 
    return re.sub(pattern, replacer, text) 


def DelCommentLine(lines):
    """
        Delete comment in one line
    """
    content = []
    for line in lines :
        l = comment_remover(line)
        content.append(l)
    return content


def DelCommnetLines(lines):
    """
        Delete comment cross lines
    """
    commentStart = 0
    content = []
    for line in lines :
        if commentStart == 0 :
            if line.strip().startswith("/*") :
                commentStart = 1
                continue
            else:
                content.append(line)
        else:
            if line.strip().startswith("*/") :
                commentStart = 0
    return content


def DelSpaceLines(lines):
    """
        Delete (continuous) space or empty lines
    """
    content = []
    for idx, line in enumerate(lines):
        # if (idx + 1 < len(lines)) and (len(lines[idx].split()) == 0) and (len(lines[idx+1].split()) == 0) :
        #     continue
        if len(lines[idx].split()) == 0 :
            continue
        else :
            content.append(line)
    return content


def remove_comment(text) :
    """
        - line starts with //
        - line contains //
        - line contains /* and */
        - line/lines between /* and */
    """
    l1 = DelCommentLine(text)
    l2 = DelCommnetLines(l1)
    # delete extra space lines
    l3 = DelSpaceLines(l2)
    return l3


def preprocess():
    filelist = os.listdir(CONTRACT_PATH)

    for file in filelist :
        if file.endswith('.sol') :
            content = []
            with open(CONTRACT_PATH + file, 'r') as f1 :
                lines = f1.readlines()
                content = remove_comment(lines)
                f1.close()
            with open(OUTPUT_PATH + file, 'w') as f2 :
                f2.writelines(content)
                f2.close()


if __name__ == "__main__":
    # init()

    preprocess()
    print("preprocess done!")
