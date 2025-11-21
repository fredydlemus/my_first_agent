from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field

llm = init_chat_model("openai:gpt-4o", temperature=1)
file_search_tool = {
    "type": "file_search",
    "vector_store_ids": ["vs_691ba0bbfc0081918552d59f562187eb"],
}
llm = llm.bind_tools([file_search_tool])

class State(MessagesState):
    customer_name: str
    phone: str
    my_age: str

class ContactInfo(BaseModel):
    """Contact information for a person."""
    name: str = Field(description="The name of the person")
    emial: str = Field(description="The email adress of the person")
    phone: str = Field(description="the phone number of the person")
    age: str = Field(description="the age of the person")

llm_with_structured_output = init_chat_model("claude-sonnet-4-20250514", temperature=0)
llm_with_structured_output = llm_with_structured_output.with_structured_output(schema=ContactInfo)

def extractor(state: State):
    history = state["messages"]
    customer_name = state.get("customer_name", None)
    new_state: State = {}
    if customer_name is None or len(history) > 10:
        schema = llm_with_structured_output.invoke(history)
        new_state["customer_name"] = schema.name
        new_state["phone"] = schema.phone
        new_state["my_age"] = schema.age
    return new_state

def conversation(state: State):
    new_state: State = {}
    history = state["messages"]
    last_message = history[-1]
    customer_name = state.get("customer_name", 'John')
    system_message = f"You are a helpful assistant that can answer questions about the customer {customer_name}"
    ai_message = llm.invoke([("system", system_message), ("user", last_message.text)])
    new_state["messages"] = [ai_message]
    return new_state

builder = StateGraph(State)
builder.add_node("conversation", conversation)
builder.add_node("extractor", extractor)

builder.add_edge(START, "extractor")
builder.add_edge("extractor", "conversation")
builder.add_edge("conversation", END)

agent = builder.compile()