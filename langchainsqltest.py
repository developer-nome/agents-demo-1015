import os

from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.base import create_sql_agent
#from langchain.agents.agent_types import AgentType
from langchain_community.agent_toolkits import SQLDatabaseToolkit

load_dotenv()  # Load environment variables from .env file

DB_USER = "postgres"
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"

connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def setup_database():
    """Set up sample database talbes and data if they do not exist."""
    db = SQLDatabase.from_uri(connection_string)
    return db


def advanced_sql_agent(db: SQLDatabase):
    """Create a more advanced Langchain SQL agent."""
    llm = ChatOpenAI(
        temperature=0,
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        model=os.getenv("LLM_MODEL"),
    )

    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type='openai-tools',
        handle_parsing_errors=True
    )
    return agent

async def rag_query(user_input):
    db = setup_database()
    agent = advanced_sql_agent(db)
    result = await agent.arun(user_input)
    return result

async def run_sql_query(message: str):
    result = await rag_query(message)
    return result