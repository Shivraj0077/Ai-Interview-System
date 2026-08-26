# AI Interview System

[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/Shivraj0077/Ai-Interview-System.git)

This project is an adaptive AI-powered technical interview system designed to simulate a real-world software engineering interview. It dynamically selects questions, evaluates candidate responses, and adjusts the difficulty level based on performance. The system is built around a robust knowledge base of technical concepts and uses large language models for generating questions and providing nuanced evaluations.

## Core Components

The system is composed of two main parts: a rich knowledge base and the interview engine that orchestrates the interview flow.

### 1. Knowledge Base

Located in `backend/data/`, the knowledge base is a collection of JSON files and Python scripts that prepare technical concepts for the interview engine.

-   **`Rag-db.json`**: The source of truth. This file contains a comprehensive list of technical concepts, each with a detailed explanation, core signals (key points a good answer should include), advanced signals (bonus points), and common misconceptions.
-   **`add-levels.py`**: This script processes `Rag-db.json` to create `final-chunks.json`. It categorizes each concept into a specific domain (e.g., `database`, `security`) and subdomain, and assigns a difficulty level (L1, L2, L3).
-   **`chunks-to-db.py`**: This script takes the processed `final-chunks.json` and upserts the data into a Supabase `rag_concepts` table, making it available for retrieval.
-   **`embed.py`**: This script uses Google's `text-embedding-004` model to generate vector embeddings for each technical concept. These embeddings are then uploaded to the Supabase database to enable semantic search.

### 2. Interview Engine

The core logic resides in `backend/interview/question.py`. It manages the entire interview session from question selection to final evaluation.

-   **Adaptive Question Generation**: Instead of random selection, the system uses semantic search via `pgvector` in Supabase. It embeds the candidate's recent answers and retrieves the most topically relevant concepts for the next question, creating a natural and grounded conversational flow.
-   **Dynamic Difficulty Adjustment**: The `update_difficulty` function assesses the candidate's score on the previous question. A high score (>=8) increases the difficulty for the next question, while a low score (<=4) decreases it, ensuring the interview is challenging but fair.
-   **Hallucination-Reduced Evaluation**: The `evaluate_answer` function is designed for accuracy. It uses Groq's Llama 3.1 model but constrains it to evaluate answers *strictly* based on the signals and misconceptions defined in the knowledge base. A `_verify_grounding` post-processing step ensures the AI's evaluation does not cite "hallucinated" signals that were not in the source material, enhancing the reliability of the feedback.

## How It Works

A typical interview session follows these automated steps:

1.  **Initialization**: The interview starts at a default difficulty level (L1).
2.  **Concept Retrieval**: `fetch_concept` retrieves a set of relevant technical concepts from Supabase using semantic search, based on the ongoing conversation history. A random concept is chosen from this relevant set to maintain variety.
3.  **Question Generation**: The `generate_question` function prompts the Groq API to formulate a natural, conversational question grounded strictly in the text of the chosen concept.
4.  **Candidate Response**: The candidate provides their answer via the command line.
5.  **Evaluation**: `evaluate_answer` assesses the response against the concept's predefined signals and misconceptions. It generates a score, a verdict (weak, average, strong), and a list of covered and missed points.
6.  **Grounding Verification**: The system internally verifies that the AI's evaluation is based only on the provided signals, removing any hallucinated feedback.
7.  **Difficulty Update**: The candidate's score is used to determine the difficulty level for the next question.
8.  **Loop**: The process repeats for the configured number of questions.

## Technology Stack

-   **AI & Language Models**:
    -   **Groq (Llama 3.1)**: For fast question generation and answer evaluation.
    -   **Google Gemini (text-embedding-004)**: For creating vector embeddings for semantic search.
-   **Backend**: Python
-   **Database**: Supabase with the `pgvector` extension for storing concepts and performing semantic search.
-   **Configuration**: `dotenv` for managing environment variables.

## Setup and Usage

### Prerequisites

-   Python 3.x
-   An account with Supabase, Groq, and Google AI Studio to obtain API keys.

### Configuration

1.  Clone the repository.
2.  Create a `.env` file in the root directory.
3.  Add your API keys and Supabase credentials to the `.env` file:
    ```
    SUPABASE_URL="YOUR_SUPABASE_URL"
    SUPABASE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
    GROQ_API_KEY="YOUR_GROQ_API_KEY"
    GEMINI_API_KEY="YOUR_GOOGLE_AI_API_KEY"
    ```

### Data Pipeline

To populate your Supabase database with the interview concepts:

1.  **Create the Table**: Set up a table named `rag_concepts` in your Supabase project. Ensure it has columns for `id`, `text`, `domain`, `subdomain`, `difficulty`, and a `vector` column for embeddings. You will also need columns for `core_signals`, `advanced_signals`, and `misconceptions` as text arrays.
2.  **Process Data**: Run the `add-levels.py` script to classify and structure the initial data.
    ```sh
    python backend/data/add-levels.py
    ```
3.  **Upload to Database**: Run the `chunks-to-db.py` script to upload the structured text data to Supabase.
    ```sh
    python backend/data/chunks-to-db.py
    ```
4.  **Generate Embeddings**: Run the `embed.py` script to create and upload vector embeddings for each concept. *Note: This script will perform inserts, ensure your table is configured accordingly or modify the script to perform updates if you've already run `chunks-to-db.py`.*
    ```sh
    python backend/data/embed.py
    ```

### Running the Interview

To start the interactive interview simulation, run the `question.py` script:

```sh
python backend/interview/question.py
```

The script will guide you through the interview, prompting for answers and providing evaluations in real-time.
