import os, shutil, re, sys
import csv
import time
import subprocess
import functools

rootPath = '/home/ubuntu/smartIDE/'
# rootPath = './'
backdoorPath = rootPath + 'backdoorDetector/'
ori_contractPath = rootPath + 'contract/'
tmpPath = backdoorPath + 'tmp/'


def dl_clean() :
    os.chdir(backdoorPath)
    subprocess.call("rm -rf " + tmpPath + "*", shell=True)


def dl_init() :
    # tmp path
    if os.path.exists(tmpPath) :
        pass
    else :
        os.mkdir(tmpPath)


def cmp(x, y) :
    if int(x, 16) < int(y, 16):
        return -1
    if x == y:
        return 0
    else:
        return 1


def isLegal(ch) :
    if ch >= '0' and ch <= '9' : return True
    elif ch >= 'a' and ch <= 'z' : return True
    elif ch >= 'A' and ch <= 'Z' : return True
    elif ch == '[' or ch == ']' or ch == '.' : return True
    else : return False


def getLocation(contractPath, fileName) :
    ret = {}
    with open(contractPath + fileName + '/' + fileName + '.sol', 'r') as f :
        lines = f.readlines()
        for idx, line in enumerate(lines) :
            if 'function ' in line :
                pos1 = line.find('function ') + 9
                pos2 = line.find('(')
                func = line[pos1:pos2]
                funcName = ''.join(func.split())
                ret[funcName] = idx + 1
        f.close()
    return ret


from signal import signal, SIGPIPE, SIG_DFL

signal(SIGPIPE, SIG_DFL)
   
def execute_command(toolName, cmd, timeout):
    devnull = open(os.devnull, 'w')
    p = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=devnull, shell=True) 
    t_beginning = time.time() 
    seconds_passed = 0 
    while True: 
        if p.poll() is not None: 
            break 
        seconds_passed = time.time() - t_beginning 
        # print("*", seconds_passed)
        if timeout and seconds_passed > timeout: 
            p.terminate() 
            print(toolName + " running out time.")
            # raise TimeoutError(cmd, timeout) 
            return 0, seconds_passed
        time.sleep(0.1) 
    return 1, seconds_passed


def dl_run(contractPath, fileName, timeout) :

    os.chdir(tmpPath)

    if not os.path.exists(tmpPath + fileName) :
        os.system("mkdir " + fileName)

    curPath = tmpPath + fileName + '/'
    os.chdir(curPath)  # current path is './tmp/filename/

    # get function signature
    cmd_sig = 'solc --hashes ' + contractPath + fileName + '/' + fileName + \
            '.sol > ' + fileName + '.sig'
    subprocess.call(cmd_sig, shell=True)

    cmd_bin = 'solc --bin-runtime ' + contractPath + fileName + '/' + fileName + \
            '.sol | tail -n 1 > ' + fileName + '.hex'
    print(cmd_bin)
    subprocess.call(cmd_bin, shell=True)

    mapList = {}
    with open(curPath + fileName + '.sig', 'r') as f1 :
        lines = f1.readlines()
        for line in lines :
            pos1 = line.find(':')
            if pos1 == 8 :
                pos2 = line.find('(')
                f_sig = line[0:pos1]
                f_name = line[pos1+2:pos2]
                mapList[f_sig] = f_name
            else :
                pass
        f1.close()
    sigList = list(mapList.keys())
    sigList = sorted(sigList, key=functools.cmp_to_key(cmp))
    # print(sigList)

    funcDict = getLocation(contractPath, fileName)
    print(funcDict)

    # # run datalog
    # cmd_dl = backdoorPath + 'MadMax/bin/analyze.sh ' + fileName + '.hex ' + \
    #         backdoorPath + 'MadMax/tools/bulk_analyser/mySpec.dl'
    # subprocess.call(cmd_dl, shell=True)

    # # get suspect function name
    # csvList = ['Vulnerability_UnboundedMassOp', 
    #         'Vulnerability_WalletGriefing', 
    #         'Vulnerability_OverflowLoopIterator']

    # run datalog
    cmd_dl = backdoorPath + 'MadMax/bin/analyze.sh ' + curPath + fileName + '.hex ' + \
            backdoorPath + 'backdoor.dl'

    execute_command("Backdoor", cmd_dl, timeout)

    # get suspect function name
    csvList = ['ArbitraryTransfer', 
               'GenerateToken', 
               'DestroyToken',
               'FrozeAccount',
               'DisableTransfer']

    lineList, backdoorList = [], []
    for i in range(len(csvList)) :
        csvFile = csvList[i] + '.csv'
        if not os.path.exists(curPath + csvFile) :
            continue
        if os.path.getsize(curPath + csvFile) == 0 :
            continue
        
        with open(curPath + csvFile, 'r') as f :
            lines = f.readlines()
            for line in lines :
                idx = int(line)
                sig = sigList[idx]
                funcName = mapList[sig]
                lineNo = funcDict[funcName]

                lineList.append(lineNo)
                backdoorList.append(csvList[i])
                print("**", fileName, funcName, lineNo, csvList[i])

            f.close()
    
    return lineList, backdoorList


def detect_backdoor(contractPath, fileName, timeout):
    
    dl_init()
    dl_clean()

    lineList, backdoorList = dl_run(contractPath, fileName, timeout)
    print("Detect backdoor done.")
    return lineList, backdoorList


if __name__ == "__main__":
    # fileName = 'MarketPlace1587637952000'
    fileName = sys.argv[1]
    timeout = 60

    lineList, backdoorList = detect_backdoor(ori_contractPath, fileName, timeout)
    # shutil.rmtree(tmpPath)
