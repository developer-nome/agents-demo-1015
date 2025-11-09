import asyncpg
import os
from openai import AsyncOpenAI

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
load_dotenv()

class SQLQuery(BaseModel):
    sql_query: str
    explanation: str

client = AsyncOpenAI(
    api_key = os.getenv("API_KEY"),
    base_url = os.getenv("BASE_URL")
)
model_name = os.getenv("LLM_MODEL")
model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))
agent = Agent(
    model=model,
    system_prompt="""
        You are an assistant that generates SQL queries based on user input
        Database schema:
        CREATE TABLE IF NOT EXISTS airports
        (
            airport_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            airport_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
            location character varying(100) COLLATE pg_catalog."default"
        );
        CREATE TABLE IF NOT EXISTS pilots
        (
            pilot_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            first_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
            last_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
            email character varying(100) COLLATE pg_catalog."default" NOT NULL,
            phone_number character varying(15) COLLATE pg_catalog."default",
            hire_date date NOT NULL
        );
        CREATE TABLE IF NOT EXISTS flight_delays
        (
            flight_delay_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            delay_date date NOT NULL,
            airport_id INTEGER NOT NULL,
            pilot_id INTEGER NOT NULL,
            flight_delay_minutes INTEGER NOT NULL,
            flight_delay_reason character varying(255) COLLATE pg_catalog."default"
        );
        Examples:
        - Input: "List the database tables"
          Output: SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema = 'public';
        - Input: "List all the columns in the airports table"
          Output: SELECT column_name FROM information_schema.columns WHERE table_name = 'airports';
        - Input: "Show me airport locations"
          Output: SELECT airport_name, location FROM airports;
        - Input: "Show me flight delays."
          Output: SELECT delay_date, flight_delay_reason FROM flight_delays;
    """,
    output_type=SQLQuery
)

async def validate_and_execute(sql_query: str):
    DB_USER = "postgres"
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "postgres"
    
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    conn = await asyncpg.connect(connection_string)
    try:
        # First, validate the query
        await conn.execute(f"EXPLAIN {sql_query}")
        print("SQL Query is valid.")

        # Check if it's an UPDATE or DELETE operation
        query_type = sql_query.strip().upper()
        if query_type.startswith(('UPDATE', 'DELETE', 'INSERT')):
            # Execute the modification query
            result = await conn.execute(sql_query)
            return {"modification": True, "result": result}
        else:
            # Execute the SELECT query and fetch results
            results = await conn.fetch(sql_query)
            return {"modification": False, "result": results}
    except Exception as e:
        print(f"SQL Query validation/execution failed: {e}")
        return None
    finally:
        await conn.close()

async def run_sql_query_copilot(message: str):
    # Get SQL query from AI agent
    result = await agent.run(message)
    print("AI Generated SQL Query:")

    # Access the SQLQuery object attributes
    sql_result = result.output
    print(f"SQL Query: {sql_result.sql_query}")
    print(f"Explanation: {sql_result.explanation}")

    # Execute the SQL query and get results
    print("Executing SQL Query...")
    db_results = await validate_and_execute(sql_result.sql_query)

    if db_results:
        # Check if it was a modification operation
        if db_results["modification"]:
            success_message = f"SQL modification executed successfully: {db_results['result']}"
            print(success_message)
            return success_message
        else:
            # Handle SELECT query results
            query_results = db_results["result"]
            if query_results:
                print("Query Results:")

                # Extract clean data and store as strings
                result_strings = []
                for row in query_results:
                    # Get all column values and join with dash separator
                    row_values = [str(value) for value in row.values()]
                    result_strings.append(" - ".join(row_values))

                # Optionally store as a single string with newlines
                clean_output = "\n".join(result_strings)
                print(clean_output)
                return clean_output
            else:
                no_data_message = "Query executed successfully but returned no data."
                print(no_data_message)
                return no_data_message
    else:
        error_message = "Failed to execute SQL query."
        print(error_message)
        return error_message