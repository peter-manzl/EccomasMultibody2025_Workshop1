# inner function checking the quality of the LLM-output
    
def CheckOutputLLM(stringLLM, checkUndesiredKeywords=False, checkHarmfulCommands=False): 

    harmfulCommands = [
        "import os", "import subprocess", "import sys",
        "eval(", "open(", "subprocess.", "os.system", "exec(", "compile(", "input(", 
        "__import__(", 'getattr(obj, "__class__"', "os.popen(", "os.environ", 
        "import socket", "socket.socket", "import requests", "request.get", 
        "import urllib", "urllib.request.urlopen", "import importlib", "import.lib.import_module(", 
        "import shutil", "shutil.rmtree", "shutil.move", "with open(", "f.write", 
        "while True:", 
    ]
    
    # detect harmful commands, which shall not be executed (remove all ...)
    for keyword in harmfulCommands:
        if keyword in stringLLM:
            logger.LogText(f"ERROR: Generated code contains potentially harmful command: '{keyword}'; aborting")
            return None  
    return 