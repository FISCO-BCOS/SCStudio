import os, shutil, re
import csv
import subprocess
import functools

rootPath = '/home/renardbebe/Desktop/SmartIDE/SCCC/backdoorDetector/'

contractPath = rootPath + 'test2/'
tmpPath = rootPath + 'tmp/'


def dl_clean() :
    os.chdir(rootPath)
    subprocess.call("rm -rf " + tmpPath + "/*", shell=True)


def dl_init() :
    # tmp path
    if os.path.exists(tmpPath) :
        pass
    else :
        os.mkdir(tmpPath)


def dl_load_data() :
    ret = []
    # for each contract bytecode in contractPath/
    AllFile = os.listdir(contractPath)
    # AllFile.sort(key=lambda x:int(x[:-4], 16))
    for file in AllFile:
        fileName = ''
        file_path = os.path.join(contractPath, file) 
        if os.path.splitext(file_path)[1] == '.sol':
            fileName = os.path.splitext(file_path)[0].split('/')[-1]
            ret.append(fileName)
        else :
            pass
    return ret


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


def getLocation(fileName) :
    ret = {}
    with open(contractPath + fileName + '.sol', 'r') as f :
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


def dl_run() :
    fileList = dl_load_data()

    for fileName in fileList :
        os.chdir(tmpPath)

        if not os.path.exists(tmpPath + fileName) :
            os.system("mkdir " + fileName)
        curPath = tmpPath + fileName + '/'
        os.chdir(curPath)  # current path is './tmp/filename/

        # get function signature
        cmd_sig = rootPath + 'lib/solc4.26 --hashes ' + contractPath + fileName + \
                '.sol > ' + fileName + '.sig'
        subprocess.call(cmd_sig, shell=True)

        cmd_bin = rootPath + 'lib/solc4.26 --bin-runtime ' + contractPath + fileName + \
                '.sol | tail -n 1 > ' + fileName + '.hex'
        subprocess.call(cmd_bin, shell=True)

        mapList = {}
        with open(fileName + '.sig', 'r') as f1 :
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

        funcDict = getLocation(fileName)
        print(funcDict)

        # run datalog
        cmd_dl = rootPath + 'MadMax/bin/analyze.sh ' + fileName + '.hex ' + \
                rootPath + 'MadMax/tools/bulk_analyser/mySpec.dl'
        subprocess.call(cmd_dl, shell=True)

        # get suspect function name
        csvList = ['Vulnerability_UnboundedMassOp.csv', 
                'Vulnerability_WalletGriefing.csv', 
                'Vulnerability_OverflowLoopIterator.csv']

        # copy target contract to output/
        # shutil.copy(contractPath + fileName + '.sol', outputPath + fileName + '.sol')
        for i in range(len(csvList)) :
            if os.path.getsize(csvList[i]) == 0 :
                continue
            with open(csvList[i], 'r') as f :
                lines = f.readlines()
                for line in lines :
                    idx = int(line)
                    sig = sigList[idx]
                    funcName = mapList[sig]
                    lineNo = funcDict[funcName]
                    print(fileName, funcName, lineNo, csvList[i])

                    # dl_modify(fileName, funcName, i)

                f.close()


def detect_backdoor():
    dl_init()
    # dl_clean()

    dl_run()


if __name__ == "__main__":
    detect_backdoor()
    # shutil.rmtree(tmpPath)
