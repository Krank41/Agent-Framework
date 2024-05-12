import json
import pprint
import os
from agent import Agent 
from db import AgentDB
from schema import Step
from schema import StepRequestBody
from workspace import Workspace
from schema import Task
from schema import TaskRequestBody
from prompting import PromptEngine
from llm import chat_completion_request
from ai_profile import ProfileGenerator
from ai_planning import AIPlanning
from datetime import datetime
from weaviate_memstore import WeaviateMemstore
from agent_log import AgentLogger
LOG = AgentLogger(__name__)

class ForgeAgent(Agent):

    def __init__(self, database: AgentDB, workspace: Workspace):
        super().__init__(database, workspace)
        self.chat_history = {}
        self.expert_profile = None
        self.prompt_engine = PromptEngine(os.getenv("OPENAI_MODEL"))
        self.ai_plan = None
        self.instruction_msgs = {}
        self.task_steps_amount = {}
        # memstore
        self.memstore_db = os.getenv("VECTOR_DB")
        self.memstore = None

    def add_chat_memory(self, task_id: str, chat_msg: dict) -> None:
        LOG.info(f"Adding chat memory for task {task_id}")
        try:
            data_class = "chat"
            WeaviateMemstore.add_data_obj(self.memstore,data_class,chat_msg )
        except Exception as err:
            LOG.error(f"add_chat_memory failed: {err}")

    def add_chat(self, 
        task_id: str, 
        role: str, 
        content: str,
        is_function: bool = False,
        function_name: str = None):
        
        if is_function:
            chat_struct = {
                "role": role,
                "name": function_name,
                "content": content
            }
        else:
            chat_struct = {
                "role": role, 
                "content": content
            }
        
        try:
            if chat_struct not in self.chat_history[task_id]:
                self.chat_history[task_id].append(chat_struct)
            else:
                chat_struct["role"] = "user"
                timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
                chat_struct["content"] = f"[{timestamp}] You have gone off course and repeating the same step. Remember the instructions you are supposed to be working through and move on\n\n{self.instruction_msgs[-1]}"
                self.chat_history[task_id].append(chat_struct)

        except KeyError:
            self.chat_history[task_id] = [chat_struct]

         # add chat memory
        if not is_function and chat_struct not in self.chat_history[task_id]:
            try:
                self.add_chat_memory(task_id, chat_struct)
            except Exception as err:
                LOG.error(f"Adding chat memory failed: {err}")



    async def create_task(self, task_request: TaskRequestBody) -> Task:
        self.instruct_amt = 0
        # create task
        try:
            task = await self.db.create_task(
                input=task_request.input,
                additional_input=task_request.additional_input
            )     
            LOG.info(f"Task created: {task.task_id} input: {task.input[:40]}{'...' if len(task.input) > 40 else ''}")

        except Exception as err:
            LOG.error(f"create_task failed: {err}")
        
        try:
            if self.memstore_db == "weaviate":
                self.memstore = WeaviateMemstore(use_embedded=True)
        except Exception as err:
            LOG.error(f"memstore creation failed: {err}")

        directory_path = self.workspace.get_cwd_path(task.task_id)

        if not os.path.exists(directory_path):
           os.makedirs(directory_path)
           LOG.info(f"Directory '{directory_path}' created successfully.")
        else:
           LOG.info(f"Directory '{directory_path}' already exists.")

        profile_gen = ProfileGenerator(
            task,
            "gpt-3.5-turbo"
        )

        LOG.info("Generating expert profile...")

        while self.expert_profile is None:
            role_reply = await profile_gen.role_find()
            try:        
                self.expert_profile = json.loads(role_reply)
            except Exception as err:
                LOG.error(f"role_reply failed\n{err}")

        LOG.info("Profile generated!")
        self.instruction_msgs[task.task_id] = []
        await self.set_instruction_messages(task.task_id, task.input)
        self.task_steps_amount[task.task_id] = 0
        return task


    async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:
        # have AI determine last step
        step = await self.db.create_step(
            task_id=task_id,
            input=step_request,
            additional_input=step_request.additional_input,
            is_last=False
        )

        step.status = "created"
        self.task_steps_amount[task_id] += 1
        LOG.info(f"Step {self.task_steps_amount[task_id]}")
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

        try:
            LOG.info(f"chat history {self.chat_history[task_id]}")
            chat_completion_parms = {
                "messages": self.chat_history[task_id],
                "model": os.getenv("OPENAI_MODEL"),
                "temperature": 0.1
            }

            chat_response = await chat_completion_request(**chat_completion_parms)

        except Exception as err:
            LOG.error(f"API token error. Cut down messages {err}")
            step.status = "error"
        
        LOG.info(f"chat_response\n{chat_response}")

        try:
            answer = json.loads(chat_response)
            output = None     
            # make sure about reply format
            #ability
            #abilities
            #check one ability or more abilities
            correct_spelling = ""
            if "ability" in answer:
                correct_spelling = "ability"
            elif "abilities" in answer:
                correct_spelling = "abilities"


            if (correct_spelling not in answer or "thoughts" not in answer):
                system_prompt = self.prompt_engine.load_prompt("system-reformat")
                LOG.info("your rply was not in given json format ...")
                self.add_chat(task_id,"system",f"Your reply was not in the given JSON format.\n{system_prompt}")
                LOG.error("chat[-1]: {self.chat_history[task_id][-1]}")
                LOG.error(f"chat_response\n{chat_response}")
            else:
                # Set the step output and is_last from AI
                if "speak" in answer["thoughts"]:
                    step.output = answer["thoughts"]["speak"]
                else:
                    step.output = "Nothing to say..."
                LOG.info(f"{step.output}")
                LOG.info(f"step status {step.status} is_last? {step.is_last}")


                if "abilities" in answer:
                    ability = answer["abilities"]
                    for n in range(len(ability)):
                        if ability and (ability[n]["name"] != "" and ability[n]["name"] != None and ability[n]["name"] != "None"):
                            ability_name = ability[n]["name"]
                            LOG.info(f"Running Ability:{ability_name}")
                            try:
                                if "args" in ability[n]:
                                    output = await self.abilities.run_ability(task_id,ability[n]["name"],**ability[n]["args"])
                                else:
                                    output = await self.abilities.run_ability(task_id,ability[n]["name"])   
                            except Exception as err:
                                LOG.error(f"Ability run failed: {err}")
                                output = err
                                self.add_chat(task_id=task_id,role="system",content=f"[{timestamp}] Ability {ability[n]['name']} failed to run: {err}")
                            else:
                                if output == None:
                                    output = ""
                                LOG.info(f"Ability Output\n{output}")
                                if isinstance(output, bytes):
                                    output = output.decode()
                                if "args" in ability[n]:
                                    ccontent = f"[Arguments {ability[n]['args']}]: {output} "
                                else:
                                    ccontent = output
                                self.add_chat(task_id=task_id,role="function",content=ccontent,is_function=True,function_name=ability[n]["name"])
                                step.status = "completed"
                                if ability[n]["name"] == "finish":
                                    step.is_last = True

                elif "ability" in answer:
                    ability = answer["ability"]
                    try:
                        if "args" in ability.keys():
                            output = await self.abilities.run_ability(task_id,ability["name"],**ability["args"])
                        else:
                            output = await self.abilities.run_ability(task_id,ability["name"])   
                    except Exception as err:
                        LOG.error(f"Ability run failed: {err}")
                        output = err
                        self.add_chat(task_id=task_id,role="system",content=f"[{timestamp}] Ability {ability['name']} failed to run: {err}")
                    LOG.info(f"Ability Output\n{output}")
                    if output == None or output = "":
                        output = "Ability Executed successfully.Task completed"
                        
                    if isinstance(output, bytes):
                        output = output.decode()
                    if "args" in ability.keys():
                        ccontent = f"[Arguments {ability['args']}]: {output} "
                    else:
                        ccontent = output
                    self.add_chat(task_id=task_id,role="function",content=ccontent,is_function=True,function_name=ability["name"])
                    step.status = "completed"
                    if ability["name"] == "finish":
                        step.is_last = True


        except Exception as e:
            # Handle other exceptions
            LOG.error(f"execute_step error: {e}")
            LOG.error(f"chat_response: {chat_response}")
            step.status = "completed"
            step.is_last = False
            self.add_chat(task_id,"system",f"Something went wrong with processing on our end. Please reformat your reply and try again.\n{e}")
    # dump whole chat log at last step
        if step.is_last and task_id in self.chat_history:
            LOG.info("dump whole chat log at last step >>")
            LOG.info(f"{pprint.pformat(self.chat_history[task_id])}")
        # Return the completed step
        return step

    async def set_instruction_messages(self, task_id: str, task_input: str):

        system_prompt = self.prompt_engine.load_prompt("system-reformat")
        LOG.info(f"{system_prompt}")
        self.instruction_msgs[task_id].append(("system", system_prompt))
        self.add_chat(task_id, "system", system_prompt)
        # add abilities prompt
        abilities_prompt = self.prompt_engine.load_prompt(
            "abilities-list",
            **{"abilities": self.abilities.list_abilities_for_prompt()}
        )
        LOG.info(f"{abilities_prompt}")
        self.instruction_msgs[task_id].append(("system", abilities_prompt))
        self.add_chat(task_id, "system", abilities_prompt)
        # add role system prompt
        try:
            role_prompt_params = {
                "name": self.expert_profile["name"],
                "expertise": self.expert_profile["expertise"]
            }
        except Exception as err:
            LOG.error(f"""
                Error generating role, using default\n
                Name: Joe Anybody\n
                Expertise: Project Manager\n
                err: {err}""")

            role_prompt_params = {
                "name": "Joe Anybody",
                "expertise": "Project Manager"
            }
            
        role_prompt = self.prompt_engine.load_prompt(
            "role-statement",
            **role_prompt_params
        )
        LOG.info(f"{role_prompt}")
        self.instruction_msgs[task_id].append(("system", role_prompt))
        self.add_chat(task_id, "system", role_prompt)
        self.ai_plan = AIPlanning(
            task_input,
            task_id,
            self.abilities.list_abilities_for_prompt(),
            self.workspace,
            "gpt-4"
        )
        try:
            plan_steps = await self.ai_plan.create_steps()
        except Exception as err:
            LOG.error(f"plan_steps_prompt failed\n{err}")
        
        ctoa_prompt_params = {
            "plan": plan_steps,
            "task": task_input
        }

        task_prompt = self.prompt_engine.load_prompt(
            "step-work",
            **ctoa_prompt_params
        )
        LOG.info(f"{task_prompt}")
        self.instruction_msgs[task_id].append(("user", task_prompt))
        self.add_chat(task_id, "user", task_prompt)
