import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda

# Load API key from .env file
load_dotenv()


def clean_sql_query(query_response):
    """Cleans the raw LLM output to be a pure SQL query."""
    # Remove markdown formatting
    if "```" in query_response:
        query_response = query_response.split("```")[1]
        if query_response.lower().startswith("sql"):
             query_response = query_response[3:] # remove 'sql'
    # Remove potential "SQLQuery:" prefix
    if ":" in query_response:
        query_response = query_response.split(":", 1)[-1]
    return query_response.strip()

# --- App Configuration ---
DATABASE_FILE = "ecommerce_data.db"
st.set_page_config(page_title="AI E-commerce Agent", page_icon="🤖", layout="centered")
st.title("🤖 AI Agent for E-commerce Data")
st.write("Ask me anything about your product sales, advertising, or eligibility data!")

# --- Database & LLM Setup ---
# Check if the database exists before continuing
if not os.path.exists(DATABASE_FILE):
    st.error(f"Database file '{DATABASE_FILE}' not found. Please run `setup_database.py` first.")
    st.stop()

# Connect to the database and initialize the LLM
db = SQLDatabase.from_uri(f"sqlite:///{DATABASE_FILE}")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key="API_KEY", temperature=0)

# --- Core Logic (Text-to-SQL) ---
# Create the chain that converts a question into a SQL query
write_query_chain = create_sql_query_chain(llm, db)

# Create the tool that executes the SQL query
execute_query_tool = QuerySQLDataBaseTool(db=db)

# The prompt for the final answer
answer_prompt = PromptTemplate.from_template(
    """
    Given the user's question, the corresponding SQL query, and the SQL result, answer the user's question in a clear, human-readable format.

    Question: {question}
    SQL Query: {query}
    SQL Result: {result}
    Answer:
    """
)

# The full chain that puts it all together
rephrase_answer_chain = answer_prompt | llm | StrOutputParser()

chain = (
    RunnablePassthrough.assign(query=write_query_chain).assign(
       result=itemgetter("query") | RunnableLambda(clean_sql_query) | execute_query_tool
    )
    | rephrase_answer_chain
)

# --- Rectified User Interface Section ---

# 1. Initialize session state safely at the top
if "question" not in st.session_state:
    st.session_state.question = ""

# 2. Create the sidebar with example questions
st.sidebar.title("Example Questions")
example_questions = [
    "What is my total sales?",
    "What is the total ad spend?",
    "Calculate the RoAS (Return on Ad Spend)",
    "Which product had the highest CPC (Cost Per Click)?",
    "How many unique products are there in the ad sales data?"
]
for q in example_questions:
    # When a button is clicked, it updates the session state
    if st.sidebar.button(q, key=f"btn_{q}"):
        st.session_state.question = q

# 3. Create the main text input, using the session state value
question_input = st.text_input("Your Question:", value=st.session_state.question, placeholder="e.g., What is my total sales?")

# 4. Handle the "Get Answer" button click
if st.button("Get Answer", key="get_answer"):
    # Use the value from the text input field
    if question_input:
        with st.spinner("Thinking..."):
            try:
                response = chain.invoke({"question": question_input})
                st.markdown(response)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a question.")