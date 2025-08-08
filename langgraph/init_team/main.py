from dotenv import load_dotenv
import os, json
from langchain.chat_models import init_chat_model

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage

from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt

from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

@tool
def human_assistance(name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> str:
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday,
        },
    )
    # If the information is correct, update the state as-is.
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "Correct"
    # Otherwise, receive information from the human reviewer.
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Made a correction: {human_response}"

    # This time we explicitly update the state with a ToolMessage inside
    # the tool.
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    # We return a Command object in the tool to update our state.
    return Command(update=state_update)

tool = TavilySearch(max_results=2)
tools = [tool, human_assistance]

llm = init_chat_model("google_genai:gemini-2.0-flash")
llm_with_tools = llm.bind_tools(tools)

memory = InMemorySaver()

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    name: str
    birthday: str

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Because we will be interrupting during tool execution,
    # we disable parallel tool calling to avoid repeating any
    # tool invocations when we resume.
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

graph = graph_builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "1"}}

def stream_graph_updates(user_input: str):
    """Stream graph updates for regular user input"""
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()

def check_for_interrupts():
    """Check if the graph is interrupted and waiting for human input"""
    snapshot = graph.get_state(config)
    return snapshot.next == ('tools',) and snapshot.tasks

def resume_with_human_input(human_response: dict):
    """Resume execution with human input"""
    human_command = Command(resume=human_response)
    events = graph.stream(human_command, config, stream_mode="values")
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()

def show_state_replay():
    """Show state history and allow user to select a checkpoint to replay from"""
    print("\n📜 State History:")
    print("=" * 80)
    
    states = list(graph.get_state_history(config))
    to_replay = None
    
    for i, state in enumerate(states):
        print(f"[{i}] Num Messages: {len(state.values.get('messages', []))}, Next: {state.next}")
        print(f"    Checkpoint ID: {state.config['configurable']['checkpoint_id']}")
        if state.values.get('name') or state.values.get('birthday'):
            print(f"    State: name='{state.values.get('name', 'N/A')}', birthday='{state.values.get('birthday', 'N/A')}'")
        print("-" * 80)
        
        # Select a specific state based on the tutorial criteria (6 messages)
        if len(state.values.get("messages", [])) == 6:
            to_replay = state
    
    if to_replay:
        print(f"\n🎯 Found target state with 6 messages")
        print(f"Next node to execute: {to_replay.next}")
        print(f"Checkpoint ID: {to_replay.config['configurable']['checkpoint_id']}")
        
        print("\nWould you like to resume from this checkpoint? (y/n)")
        choice = input("Choice: ")
        
        if choice.lower().startswith('y'):
            print("\n🔄 Resuming from checkpoint...")
            # This is step 4: Load a state from a moment-in-time
            # Using the checkpoint_id to resume from that exact moment
            events = graph.stream(None, to_replay.config, stream_mode="values")
            for event in events:
                if "messages" in event:
                    event["messages"][-1].pretty_print()
        else:
            print("❌ Replay cancelled")
    else:
        print("⚠️ No suitable state found with 6 messages to replay from")

def replay_from_checkpoint(checkpoint_id: str):
    """Load and resume from a specific checkpoint ID"""
    # Create config with specific checkpoint
    replay_config = {
        "configurable": {
            "thread_id": config["configurable"]["thread_id"],
            "checkpoint_id": checkpoint_id
        }
    }
    
    print(f"🔄 Resuming from checkpoint: {checkpoint_id}")
    events = graph.stream(None, replay_config, stream_mode="values")
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()

while True:
    try:
        # Check if we're in an interrupted state
        if check_for_interrupts():
            print("\n🤖 Assistant is waiting for human input...")
            print("   Type 'y' if correct, or provide corrections")
            print("   Format: correct=y  OR  name=NewName,birthday=NewDate")
            human_input = input("Human: ")
            
            if human_input.lower() in ["skip", "cancel"]:
                print("❌ Skipping human assistance...")
                continue
            else:
                print("🔄 Resuming with your input...")
                # Parse human input into proper format
                if human_input.lower().startswith('y'):
                    human_response = {"correct": "yes"}
                elif '=' in human_input:
                    # Parse key=value pairs
                    human_response = {}
                    pairs = human_input.split(',')
                    for pair in pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            human_response[key.strip()] = value.strip()
                else:
                    # Default to correction format
                    human_response = {"correct": "no", "feedback": human_input}
                
                resume_with_human_input(human_response)
                continue
        
        # Normal interaction
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Assistant: Goodbye!")
            break
        elif user_input.lower() in ["replay", "history"]:
            show_state_replay()
        elif user_input.lower().startswith("replay "):
            # Allow replay from specific checkpoint ID
            parts = user_input.split(" ", 1)
            if len(parts) > 1:
                checkpoint_id = parts[1]
                replay_from_checkpoint(checkpoint_id)
            else:
                print("❌ Please provide a checkpoint ID: replay <checkpoint_id>")
        elif user_input.lower() in ["help"]:
            print("\n🔧 Available commands:")
            print("  help - Show this help")
            print("  replay/history - Show state history and replay options")
            print("  replay <checkpoint_id> - Replay from specific checkpoint")
            print("  quit/exit/q - Exit the program")
            continue
        
        stream_graph_updates(user_input)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break