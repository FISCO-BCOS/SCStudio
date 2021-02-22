import os
import subprocess
import logging
import json
import uuid

from flask import Flask, request


app = Flask(__name__)
cur_dir = os.path.dirname(__file__)

# Uses absolute path to mount volume in Docker
contracts_dir = "/tmp/contracts"
secure_check_dir = os.path.join(cur_dir, "secure_check")


@app.route("/contract_analysis", methods=["POST"])
def contract_analysis():
    if not os.path.exists(contracts_dir):
        os.mkdir(contracts_dir)

    timeout = request.json["timeout"]
    content = request.json["content"]
    contract_id = str(uuid.uuid4()).replace("-", "")

    contract_dir = os.path.join(contracts_dir, contract_id)
    os.mkdir(contract_dir)
    with open(os.path.join(contract_dir, contract_id + ".sol"), "w", encoding="utf-8") as f:
        f.write(content)

    try:
        subprocess.run(
            f"python3 {os.path.join(secure_check_dir, 'main.py')} {contract_dir} {timeout}",
            check=True, shell=True)
    except Exception as e:
        logging.warning(
            f"[execute_command]error occurs, message: {e}")
        return {
            "status": -1,
            "msg": str(e),
            "vulnerabilities": []
        }

    result_file = os.path.join(contract_dir, "final_report.json")
    if not os.path.exists(result_file):
        return {
            "status": -1,
            "msg": "Failed to generate report, maybe you need to try again",
            "vulnerabilities": []
        }

    result = open(result_file).read()
    return {
        "status": 0,
        "msg": "",
        "vulnerabilities": json.loads(result)
    }


logging.basicConfig(
    format='[%(levelname)s][%(asctime)s]%(message)s', level=logging.DEBUG)
