import os
import db
from dotenv import load_dotenv
from workspace import LocalWorkspace
from agent_log import AgentLogger
import agents

load_dotenv()
LOG = AgentLogger(__name__)

database_name = os.getenv("DATABASE_STRING")

if __name__ == "__main__":
    """Runs the agent server"""
    database_name = database_name
    workspace = LocalWorkspace(os.getenv("AGENT_WORKSPACE"))
    port = os.getenv("PORT")
    database = db.AgentDB(database_name, debug_enabled=False)
    agent = agents.ForgeAgent(database=database, workspace=workspace)
    agent.start(port=port)
    LOG.info(f"Agent server starting")