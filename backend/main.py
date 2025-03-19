from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from urllib.parse import urlparse

app = FastAPI()

# Load environment variables from .env
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("POSTGRESQL_EXTERNAL_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Warning: Neither POSTGRESQL_EXTERNAL_URL nor DATABASE_URL is set")

if DATABASE_URL:
    # Parse the DATABASE_URL
    result = urlparse(DATABASE_URL)
    db_config = {
        "dbname": result.path[1:],
        "user": result.username,
        "password": result.password,
        "host": result.hostname,
        "port": result.port or 5432,
    }
else:
    # Fallback to individual environment variables
    db_config = {
        "dbname": os.getenv("POSTGRES_DATABASE"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

print(
    f"Attempting to connect to database at {db_config['host']}:{db_config['port']}/{db_config['dbname']}"
)

# Create a connection pool
try:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **db_config)
    print("Connection pool created successfully")
except Exception as e:
    print(f"Error creating connection pool: {e}")
    connection_pool = None


@contextmanager
def get_db_connection():
    """Get a database connection from the pool."""
    connection = None
    try:
        connection = connection_pool.getconn()
        yield connection
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    finally:
        if connection:
            connection_pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
    """Get a database cursor using a connection from the pool."""
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            yield cursor
            if commit:
                connection.commit()
        finally:
            cursor.close()


# Set your OpenAI API key here
load_dotenv()  # Load environment variables from .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


class NPC(BaseModel):
    name: str
    personality: str
    goals: str
    assets: str
    memory: str
    background: str
    appearance: str


@app.get("/")
@app.head("/")
async def root():
    return {"message": "Welcome to the NPC Soul App!"}


@app.post("/npc/create")
async def create_npc(npc: NPC):
    try:
        with get_db_connection() as connection:
            # Insert NPC into the database
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO npcs (name, personality, goals, assets, memory, background, appearance)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    npc.name,
                    npc.personality,
                    npc.goals,
                    npc.assets,
                    npc.memory,
                    npc.background,
                    npc.appearance,
                ),
            )
            connection.commit()
        return {"message": "NPC created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating NPC: {str(e)}")


@app.post("/npc/interact/{npc_id}")
async def interact_with_npc(
    npc_id: int,
    player_input: str = Body(..., embed=True),
    prompt_context: str = Body(..., embed=True),
):
    try:
        with get_db_connection() as connection:
            # Fetch NPC from the database
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM npcs WHERE id = %s", (npc_id,))
            npc = cursor.fetchone()
            if not npc:
                raise HTTPException(status_code=404, detail="NPC not found")

            # Use the prompt_context to construct the prompt
            messages = [
                {
                    "role": "system",
                    "content": prompt_context,
                },
                {"role": "user", "content": player_input},
            ]
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
            )
            npc_response = (
                response.choices[0].message.content.strip()
                if response.choices[0].message.content
                else ""
            )

            # Insert interaction into the database
            cursor.execute(
                """
                INSERT INTO interactions (npc_id, player_input, npc_response)
                VALUES (%s, %s, %s)
                """,
                (npc_id, player_input, npc_response),
            )
            connection.commit()
        return {"npc_response": npc_response}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during interaction: {str(e)}"
        )


@app.get("/npc/list")
async def list_npcs():
    try:
        with get_db_connection() as connection:
            # Fetch all NPCs from the database
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM npcs")
            npcs = cursor.fetchall()

        # Convert tuples to dictionaries
        npc_list = [
            {
                "id": npc[0],
                "name": npc[1],
                "background": npc[2],
                "appearance": npc[3],
                "personality": npc[4],
                "goals": npc[5],
                "assets": npc[6],
                "memory": npc[7],
            }
            for npc in npcs
        ]
        return {"npcs": npc_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching NPCs: {str(e)}")


@app.delete("/npc/remove_empty_personality")
async def remove_empty_personality_npcs():
    try:
        with get_db_connection() as connection:
            # Delete NPCs with empty personality from the database
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM npcs WHERE personality IS NULL OR personality = ''"
            )
            connection.commit()
        return {"message": "NPCs with empty personality removed successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing NPCs: {str(e)}")


@app.put("/npc/update/{npc_id}")
async def update_npc(npc_id: int, npc: NPC):
    try:
        with get_db_connection() as connection:
            # Update NPC in the database
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE npcs SET name = %s, personality = %s, goals = %s, assets = %s, memory = %s, background = %s, appearance = %s
                WHERE id = %s
                """,
                (
                    npc.name,
                    npc.personality,
                    npc.goals,
                    npc.assets,
                    npc.memory,
                    npc.background,
                    npc.appearance,
                    npc_id,
                ),
            )
            connection.commit()
        return {"message": "NPC updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating NPC: {str(e)}")


@app.get("/npc/interactions/{npc_id}")
async def get_latest_interactions(npc_id: int, limit: int = 5):
    try:
        with get_db_connection() as connection:
            # Fetch latest interactions from the database
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT player_input, npc_response FROM interactions
                WHERE npc_id = %s
                ORDER BY id DESC
                LIMIT %s
                """,
                (npc_id, limit),
            )
            interactions = cursor.fetchall()

        # Convert tuples to dictionaries
        interaction_list = [
            {"player_input": interaction[0], "npc_response": interaction[1]}
            for interaction in interactions
        ]
        return {"interactions": interaction_list}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching interactions: {str(e)}"
        )


# Add this at the end of the file
if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", "8000"))
    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=port)
