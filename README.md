# Agent-Framework

Agent-Framework is a versatile framework designed for implementing agentic behavior in large language models. It enables developers to build intelligent agents capable of performing tasks and interacting with users in various contexts.

## Prerequisites
- Python version 3.10.12 is required to run this framework.
- Install dependencies using the following command:
  ```bash
  pip install -r requirements.txt
  ```
- Set up your `.env` file with the necessary API keys:
  ```plaintext
  OPENAI_API_KEY=<your_openai_api_key>
  ORGANIZATION_ID=<your_organization_id>
  ```

## Running the Framework
To start the agent server, execute the following command:
```bash
python __main__.py
```
This command sets up the database and configures local storage for saving and retrieving files.

## Endpoints

### 1. Create Task Endpoint
- **URL:** http://127.0.0.1:8000/ap/v1/agent/tasks
- **Request Type:** POST
- **Description:** This endpoint creates a task in the database, gets a plan from AI to solve the task, and returns the task ID.
- **Usage:** 
  ```bash
  curl --location 'http://127.0.0.1:8000/ap/v1/agent/tasks' \
  --header 'Content-Type: application/json' \
  --data '{
      "input": "write a snake game in python.",
      "additional_input": null
    }'
  ```
- **Output:**
  ```json
  {
    "input": "write a snake game in python.",
    "additional_input": {},
    "created_at": "2024-05-12T08:19:33.773229",
    "modified_at": "2024-05-12T08:19:33.773235",
    "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "artifacts": []
  }
  ```

### 2. Execute Task Steps Endpoint
- **URL:** http://127.0.0.1:8000/ap/v1/agent/tasks/<task_id>/steps
- **Request Type:** POST
- **Usage:** 
  ```bash
  curl --location 'http://127.0.0.1:8000/ap/v1/agent/tasks/<task_id>/steps' \
  --header 'Content-Type: application/json' \
  --data '{
      "input": "write a snake game in python."
    }'
  ```
- **Output:**
  ```json
  {
    "name": "write a snake game in python.",
    "input": "write a snake game in python.",
    "additional_input": {},
    "created_at": "2024-05-12T08:30:07.648223",
    "modified_at": "2024-05-12T08:30:07.648230",
    "task_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "step_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "status": "completed",
    "output": "Writing the snake game code to 'snake_game.py' and then concluding the task.",
    "additional_output": {},
    "artifacts": [],
    "is_last": false
  }
  ```
- **Note:** Call this endpoint repeatedly until `"is_last"` is true.

## Feedback
For any issues, suggestions, or feedback regarding the framework, please feel free to open an issue on our GitHub repository or reach out to us directly.

## Contributors
- kartavya singh (@krank41)

## License
