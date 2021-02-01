# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from signal import signal, SIGPIPE, SIG_DFL
import os
import sys
import json
import subprocess
import time
import datetime
import threading
import logging
import re
import tempfile
import functools
from multiprocessing import Process
from _vulnerabilities import VUL_MAPPING_TABLES, get_vul_info


class VulsRecorder:
    def __init__(self):
        self._vuls = {}

    def __iter__(self):
        return iter(self._vuls.items())

    def record(self, vul_id, line_no):
        if vul_id not in self._vuls:
            self._vuls[vul_id] = []

        if line_no not in self._vuls[vul_id]:
            self._vuls[vul_id].append(line_no)


def execute_command(contract_dir, cmd, timeout, output=None):
    cwd = os.getcwd()
    os.chdir(contract_dir)
    if output is not None:
        output = open(output, "w")
    else:
        output = open("/dev/null", "w")

    try:
        subprocess.run(cmd, timeout=timeout, check=True,
                       stdout=output, shell=True)
    except subprocess.TimeoutExpired as e:
        logging.warning(
            f"[execute_command]timeout occurs when running `{cmd}`, timeout: {timeout}s")
    except Exception as e:
        logging.warning(
            f"[execute_command]error occurs when running `{cmd}`, output: {e}")
    finally:
        output.close()
        os.chdir(cwd)


__SMART_CHECK_REPORT_FILE = "smart_check_report.txt"
__MYTH_REPORT_FILE = "myth_report.txt"


def run_smart_check(contract_dir, contract, timeout):
    cmd = f"smartcheck -p {contract}"
    execute_command(contract_dir, cmd, timeout, __SMART_CHECK_REPORT_FILE)


def run_oyente(contract_dir, contract, timeout):
    cmd = f"docker run -v $(pwd):/project qspprotocol/oyente-0.4.25 -s /project/{contract} -j"
    execute_command(contract_dir, cmd, timeout)


def run_myth(contract_dir, contract, timeout):
    # Mythrill uses latest solc to compile contract, but when the version
    # of latest solc is not match with compiler version which is indicated
    # by `pragma solidity` statement in contract, Mythrill will refuse to
    # check contract. To avoid being got stuck in above situation, we need
    # to find the compiler version requirement in contract, and pass it to
    # Mythrill via `--solv` option.

    # First, we use a specified regex expression to search first occurrence
    # of `pragma solidity` statement, and extract the version info inside it.
    # This method can cover most cases.
    # TODO: Process cases such as `pragma solididy <0.4.26;`.
    content = open(os.path.join(contract_dir, contract)).read()
    version = re.search(
        r"pragma\s+solidity.*?(\d+.\d+.\d+)\s*;", content, re.DOTALL)
    if version is None:
        logging.warning(
            "[run_myth]the contract has no `pragma solidity` stmt")
        return
    version = version.group(1)

    cmd_prefix = f"docker run -v $(pwd):/tmp mythril/myth analyze /tmp/{contract} -t 3"
    execute_command(
        contract_dir,
        f"{cmd_prefix} --solv {version}",
        timeout,
        __MYTH_REPORT_FILE)

    # But unfortunately, in first try sometimes we may get a incorrect match,
    # for example, a `pragma solidity` statement written in comments. In this
    # case, we need to check whether the output of Mythrill still contains hint
    # about mismatch of compiler version requirement. If it's true, we will
    # extract actually version requirement from error info, and then try again.
    report_path = os.path.join(contract_dir, __MYTH_REPORT_FILE)
    if not validate_report(report_path):
        return
    content = open(report_path).read()
    if content.find("Source file requires different compiler version") != -1:
        # Sometimes the error info is incomplete due to that the statement is
        # written in multi-line, such as: `pragma \n solidity \n 0.5.7;`, which
        # is permitted by solidity syntax. So we need find out the start line
        # number first, and then search from that line.
        print(content)
        line_no = int(re.search(r"(\d+) \|", content).group(1))
        contract_path = os.path.join(contract_dir, contract)
        lines = open(contract_path).readlines()
        remain = "\n".join(lines[line_no - 1:])
        version = re.search(
            r"pragma\s+solidity.*?(\d+.\d+.\d+)\s*;",
            remain,
            re.DOTALL).group(1)
        cmd = f"{cmd_prefix} --solv {version}"
        execute_command(contract_dir, cmd, timeout, __MYTH_REPORT_FILE)


# Run backdoor detector
def run_bdd(contract_dir, contract, timeout):
    # Get bin of contract
    bin_file = contract + ".hex"
    cmd = f"solc --bin-runtime {contract} | tail -n 1"
    execute_command(contract_dir, cmd, timeout, bin_file)

    backdoor_detector_root = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "backdoor_detector")
    analyze_entry = os.path.sep.join(
        [backdoor_detector_root, "MadMax", "bin", "analyze.sh"])
    backdoor_datalog = os.path.join(backdoor_detector_root, "backdoor.dl")
    cmd = " ".join([analyze_entry, bin_file, backdoor_datalog])
    execute_command(contract_dir, cmd, timeout)


def run_analysis_tools(contract_dir, contract, timeout):
    processes = []
    args = (contract_dir, contract, timeout)
    processes.append(Process(target=run_smart_check, args=args))
    processes.append(Process(target=run_oyente, args=args))
    processes.append(Process(target=run_myth, args=args))
    processes.append(Process(target=run_bdd, args=args))

    for process in processes:
        process.start()
    for process in processes:
        process.join()


def validate_report(report_path):
    if not os.path.exists(report_path):
        return False
    if not os.path.isfile(report_path):
        return False
    if os.path.getsize(report_path) == 0:
        return False
    return True


def processing_myth_report(contract_dir, vuls_recorder):
    report_path = os.path.join(contract_dir, __MYTH_REPORT_FILE)
    if not validate_report(report_path):
        return

    vul_mapping_table = VUL_MAPPING_TABLES["myth"]
    with open(report_path) as f:
        lines = f.readlines()
        lines_num = len(lines)

        i = 0
        while i < lines_num:
            if '====' in lines[i]:
                vul_type = None
                line_no = None
                for j in range(i + 1, lines_num):
                    if 'SWC ID:' in lines[j]:
                        # Example: "SWC ID: 111"
                        vul_type = lines[j][lines[j].rfind(':') + 1:].strip()
                    if 'In file:' in lines[j]:
                        # Example: "In file: /tmp/tx_origin.sol:20"
                        line_no = int(lines[j][lines[j].rfind(':') + 1:-1])
                    if ('====' in lines[j]) or (j == (lines_num - 1)):
                        i = j
                        break
                if vul_type in vul_mapping_table:
                    vul_id = vul_mapping_table[vul_type]
                    vuls_recorder.record(vul_id, line_no)
            else:
                i += 1


def processing_bdd_report(contract_dir, contract, vuls_recorder):
    ast_file = contract + ".ast"
    cmd = f"solc --ast-compact-json {contract}"
    execute_command(contract_dir, cmd, timeout, ast_file)

    selector2name, fn2loc = {}, {}
    with open(os.path.join(contract_dir, ast_file)) as f:
        lines = f.readlines()
        start = -1
        for i, line in enumerate(lines):
            print(line.strip())
            if line.strip() == f"======= {contract} =======":
                start = i
                break
        if start == -1:
            return

        ast = json.loads("".join(lines[start + 1:]))
        contracts = [node for node in ast["nodes"] if node["nodeType"]
                     == "ContractDefinition" and node["abstract"] == False]
        for contract in contracts:
            fns = [node for node in contract["nodes"] if node["nodeType"]
                   == "FunctionDefinition" and node["kind"] == "function"]
            for fn in fns:
                name = fn["name"]
                selector = fn["functionSelector"]
                selector2name[selector] = name
                start_pos = fn["src"].split(":")[0]
                fn2loc[name] = start_pos
    selectors = sorted(selector2name.keys(), key=lambda x: int(x, 16))

    # Get suspect function name from ".csv" reports
    reports = ['ArbitraryTransfer',
               'GenerateToken',
               'DestroyToken',
               'FrozeAccount',
               'DisableTransfer']

    for report in reports:
        report_path = os.path.join(contract_dir, report + ".csv")
        if not validate_report(report_path):
            continue

        with open(report_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                idx = int(line)
                selector = selectors[idx]
                fn_name = selector2name[selector]
                line_no = fn2loc[fn_name]
                vuls_recorder.record(report, line_no)


def processing_oyente_report(contract_dir, vuls_recorder):
    report_path = contract_dir
    for f in os.listdir(report_path):
        path, ext = os.path.splitext(f)
        if ext == ".json" and path.find(".sol:") != -1:
            report_path = os.path.join(report_path, f)
    if not validate_report(report_path):
        return

    vul_mapping_table = VUL_MAPPING_TABLES["oynete"]
    with open(report_path) as f:
        data = json.load(f)
        line_no = -1

        for vul_type, info_list in data["vulnerabilities"].items():
            for info in info_list:
                start_flag = ".sol:"
                start = info.find(start_flag) + len(start_flag)
                end = info[start:].find(':')
                line_no = int(info[start: start + end])

                vul_id = vul_mapping_table[vul_type]
                vuls_recorder.record(vul_id, line_no)


def processing_smart_check_report(contract_dir, vuls_recorder):
    report_path = os.path.join(contract_dir, __SMART_CHECK_REPORT_FILE)
    if not validate_report(report_path):
        return

    vul_mapping_table = VUL_MAPPING_TABLES['smart_check']
    with open(report_path) as f:
        lines = f.readlines()
        lines_num = len(lines)

        i = 0
        while i < lines_num:
            if 'ruleId:' in lines[i]:
                vul_type = None
                line_no = None
                for j in range(i, lines_num):
                    if 'ruleId:' in lines[j]:
                        # Example: "ruleId: SOLIDITY_TX_ORIGIN"
                        vul_type = lines[j][lines[j].rfind(':') + 2:-1]
                    if 'line:' in lines[j]:
                        # Example: "line: 10"
                        line_no = int(lines[j][lines[j].rfind(':') + 2:-1])
                    if ('content:' in lines[j]) or (j == (lines_num - 1)):
                        i = j
                        break
                if vul_type in vul_mapping_table:
                    vul_id = vul_mapping_table[vul_type]
                    vuls_recorder.record(vul_id, line_no)
            else:
                i += 1


def processing_reports(contract_dir, contract):
    vuls_recorder = VulsRecorder()
    processing_smart_check_report(contract_dir, vuls_recorder)
    processing_oyente_report(contract_dir, vuls_recorder)
    processing_myth_report(contract_dir, vuls_recorder)
    processing_bdd_report(contract_dir, contract, vuls_recorder)
    return vuls_recorder


def infer_contract_name(contract_dir):
    return os.path.split(contract_dir)[1] + ".sol"


if __name__ == '__main__':
    def abort(msg):
        print(msg)
        exit(-1)

    argc = len(sys.argv)
    if argc < 2 or argc > 3:
        abort(
            f"usage: python3 {sys.argv[0]} <contract_dir> [timeout]")

    contract_dir = sys.argv[1]
    if not os.path.exists(contract_dir):
        abort(f"the path is not exist: {contract_dir}")

    timeout = 60
    if argc == 3:
        arg = sys.argv[2]
        error = f"invalid timeout `{arg}`, which is expected to be a positive number"
        try:
            timeout = int(arg)
            if not timeout > 0:
                abort(error)
        except Exception as _:
            abort(error)

    signal(SIGPIPE, SIG_DFL)
    logging.basicConfig(
        format='[%(levelname)s][%(asctime)s]%(message)s', level=logging.DEBUG)

    contract = infer_contract_name(contract_dir)
    run_analysis_tools(contract_dir, contract, timeout)
    vuls_recorder = processing_reports(contract_dir, contract)
    out_json = {
        "contractname": contract,
        "vulnerabilities": {}
    }
    for vul_id, lines in vuls_recorder:
        vul_info = get_vul_info(vul_id)
        if vul_info.level != "ignore":
            out_json["vulnerabilities"][vul_id] = {}
            vul = out_json["vulnerabilities"][vul_id]
            vul["name"] = vul_info.name
            vul["description"] = vul_info.desc
            vul["swcId"] = vul_info.swc
            vul["lineNo"] = lines
            vul["advice"] = vul_info.advice
            vul["level"] = vul_info.level
    js = json.dumps(out_json, sort_keys=True, indent=4, separators=(',', ':'))
    print(js)

    with open(os.path.join(contract_dir, "final_report.json"), "w") as f:
        json.dump(out_json, f, indent=1)
