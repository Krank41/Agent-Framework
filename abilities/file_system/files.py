from typing import List
from ..registry import ability
from typing import Dict
import subprocess
import json

@ability(
    name="run_python_file",
    description="run a python file",
    parameters=[
        {
            "name": "file_name",
            "description": "Name of the file",
            "type": "string",
            "required": True
        }
    ],
    output_type="dict"
)

async def run_python_file(agent, task_id: str, file_name: str) -> Dict:


    get_cwd = agent.workspace.get_cwd_path(task_id)

    return_dict = {
        "return_code": -1,
        "stdout": "",
        "stderr": ""
    }

    command = f"python {file_name}"

    try:
        req = subprocess.run(command,
            shell=True,
            capture_output=True,
            cwd=get_cwd
        )

        return_dict["return_code"] = req.returncode
        return_dict["stdout"] = req.stdout.decode()
        return_dict["stderr"] = req.stderr.decode()
    except Exception as err:
        print("subprocess call failed:",err)
        raise err
    
    try:
        return_json = json.dumps(return_dict)
    except json.JSONDecodeError as err:
        print("JSON dumps failed:",err)
        raise err
    
    return return_json


@ability(
    name="list_files",
    description="List files in a directory",
    parameters=[
        {
            "name": "path",
            "description": "Path to the directory",
            "type": "string",
            "required": True,
        }
    ],
    output_type="list[str]",
)
async def list_files(agent, task_id: str, path: str) -> List[str]:

    return agent.workspace.list(task_id=task_id, path=path)


@ability(
    name="write_file",
    description="Write data to a file",
    parameters=[
        {
            "name": "file_name",
            "description": "Name of the file",
            "type": "string",
            "required": True,
        },
        {
            "name": "data",
            "description": "Data to write to the file",
            "type": "bytes",
            "required": True,
        },
    ],
    output_type="File has been succesfully written",
)
async def write_file(agent, task_id: str, file_name: str, data: bytes) -> None:

    try:
        if isinstance(data, bytes):
            data = data.decode()
        
        data = data.replace('\\\\', '\\')
        data = data.replace('\\n', '\n')

        data = str.encode(data)

        agent.workspace.write(task_id=task_id, path=file_name, data=data)
    
        await agent.db.create_artifact(
            task_id=task_id,
            file_name=file_name.split("/")[-1],
            relative_path=file_name,
            agent_created=True,
        )
    except Exception as err:
        logger.error(f"write_file failed: {err}")
        raise err


@ability(
    name="read_file",
    description="Read data from a file",
    parameters=[
        {
            "name": "file_path",
            "description": "Path to the file",
            "type": "string",
            "required": True,
        },
    ],
    output_type="bytes",
)
async def read_file(agent, task_id: str, file_path: str) -> bytes:

    return agent.workspace.read(task_id=task_id, path=file_path)
