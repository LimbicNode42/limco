from dataclasses import dataclass, field

from utils_state import LangGraphImage

@dataclass
class State:
  """This is the state for the entire graph"""
  name: str = "Dev Team"
  description: str = "A graph for a company to track their goals and progress."
  start_node: str = "__start__"

@dataclass
class Vision:
  """This is goal tracking for the Founder/CEO"""

  goal: str = """
    - Become the industry leader in AI-driven business communication solutions. 
    - Offer an innovative alternative platform that supercedes traditional business communication tools like Slack and Microsoft Teams.
    - The innovative and differentiating sauce is the use of AI to generate summaries in a branching conversation graph instead of the traditional chain format.
  """
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 5 * 360 # days

@dataclass
class TechnologyStrategy:
  """This is goal tracking for the CTO"""

  goal: str = """
    - Develop a graph based communication platform that integrates AI capabilities.
    - Each node is a topic of conversation, allowing for structured and efficient discussions.
    - Rather than a single chat history, each node will have its own history.
    - To avoid cognitive overload each node will contain an AI generated summary of the conversation.
    - Rather than engineers disputing each other the AI node summary will contain the AI's own research and provide options with pros and cons of each engineers proposals.
    - Each node will have a set of AI generated diagrams that can be used to visualize the conversation.
    - Each node will have a timer that will be used to track the time spent on the conversation.
    - Each node will have a timer that will be used to track the staleness of the conversation.
    - Each node will have tags so that engineers can filter conversations by topics of interest to them.
    - Similar to a social media platform nodes will be ranked on their hotness/trendingness.
    - Similar to a social media platform engineers will have a "For You" feed that will show them the most relevant nodes based on their interests and past interactions.
  """
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 360 # days

@dataclass
class TechnologyIteration:
  """This is goal tracking for the Engineering Manager"""

  goal: str = ""
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 30 # days

@dataclass
class TechnologyTask:
  """This is goal tracking for the Senior Engineer"""

  goal: str = ""
  diagrams: list[LangGraphImage] = field(default_factory=list)
  timebox: int = 15 # days
