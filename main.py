from dotenv import load_dotenv
import os
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import (
    mood_logger_tool, 
    query_history_tool, 
    generate_insight_tool,
    recommend_support_tool,
    search_content_tool,
    crisis_mode_tool
)
from database import init_database

# Load environment variables
load_dotenv()

class WellnessResponse(BaseModel):
    mood_detected: str
    support_provided: str
    tools_used: list[str]
    crisis_alert: bool = False
    recommendations: list[str] = []

# Initialize the database
init_database()

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

parser = PydanticOutputParser(pydantic_object=WellnessResponse)

# System prompt for MindWeaver
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are MindWeaver, an intelligent AI mental wellness guide. Your role is to:
        
        1. Engage in empathetic, purposeful conversations about emotions and mental health
        2. Help users reflect on their feelings and identify patterns
        3. Provide personalized coping strategies and recommendations
        4. Maintain a conversation-based log of emotional entries
        5. Proactively analyze past interactions to offer insights
        6. CRITICAL: Immediately activate crisis intervention if you detect severe distress, self-harm, or suicidal ideation
        
        Your approach should be:
        - Warm, non-judgmental, and supportive
        - Ask thoughtful, probing questions to help users articulate their feelings
        - Use past conversation data to provide personalized insights
        - Always prioritize user safety and well-being
        
        Available tools:
        - mood_logger_tool: Log user's mood and reasons
        - query_history_tool: Retrieve past mood entries for analysis
        - generate_insight_tool: Create personalized insights from historical data
        - recommend_support_tool: Provide mood-specific coping strategies
        - search_content_tool: Find relevant external resources
        - crisis_mode_tool: IMMEDIATE activation for crisis situations
        
        Crisis keywords to watch for: suicide, kill myself, end it all, no point living, 
        want to die, hurt myself, self-harm, overdose, etc.
        
        Wrap your response in the specified format: {format_instructions}
        """,
    ),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
]).partial(format_instructions=parser.get_format_instructions())

# Create tools list
tools = [
    mood_logger_tool,
    query_history_tool, 
    generate_insight_tool,
    recommend_support_tool,
    search_content_tool,
    crisis_mode_tool
]

# Create agent
agent = create_tool_calling_agent(
    llm=llm,
    prompt=prompt,
    tools=tools
)

# Create agent executor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True,
    handle_parsing_errors=True
)

def start_conversation():
    """Start the MindWeaver conversation loop"""
    print("\n🌟 Welcome to MindWeaver - Your Personal Mental Wellness Guide 🌟")
    print("I'm here to support you through conversations about your emotions and well-being.")
    print("Type 'quit' or 'exit' to end our session.\n")
    
    chat_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\nMindWeaver: Take care of yourself! Remember, I'm always here when you need support. 💙")
                break
            
            if not user_input:
                continue
                
            # Process user input through agent
            response = agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            # Parse structured response
            try:
                structured_response = parser.parse(response.get("output", ""))
                
                # Display response
                print(f"\nMindWeaver: {structured_response.support_provided}")
                
                # Show recommendations if any
                if structured_response.recommendations:
                    print("\n💡 Recommendations:")
                    for rec in structured_response.recommendations:
                        print(f"   • {rec}")
                
                # Crisis alert handling
                if structured_response.crisis_alert:
                    print("\n🚨 CRISIS SUPPORT ACTIVATED 🚨")
                    print("Please reach out for immediate help if you're in crisis.")
                
                # Update chat history
                chat_history.append(("human", user_input))
                chat_history.append(("assistant", structured_response.support_provided))
                
            except Exception as parse_error:
                # Fallback for parsing errors
                raw_output = response.get("output", "I apologize, but I'm having trouble processing that right now. Can you tell me how you're feeling today?")
                print(f"\nMindWeaver: {raw_output}")
                chat_history.append(("human", user_input))
                chat_history.append(("assistant", raw_output))
                
        except KeyboardInterrupt:
            print("\n\nMindWeaver: Session interrupted. Take care! 💙")
            break
        except Exception as e:
            print(f"\nMindWeaver: I apologize, but I encountered an error. Let's try again. How are you feeling right now?")
            print(f"Error details: {str(e)}")

def proactive_check_in():
    """Proactive weekly check-in based on historical data"""
    try:
        # Query recent history for insights
        insight_response = agent_executor.invoke({
            "input": "Generate insights from my past week of mood entries and provide a proactive check-in message",
            "chat_history": []
        })
        
        print("\n🔄 Weekly Check-in from MindWeaver:")
        print(insight_response.get("output", "How have you been feeling this week?"))
        
    except Exception as e:
        print(f"Error during proactive check-in: {str(e)}")

if __name__ == "__main__":
    # Check if API key is configured
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please create a .env file with your Google API key:")
        print("GOOGLE_API_KEY=your-api-key-here")
        exit(1)
    
    # Start the conversation
    start_conversation()