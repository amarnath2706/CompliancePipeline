'''This modeule defines the nodes for the workflow and defines the DAG : Directed Acyclic Graph.
That orchestrate the video complaince audit process
It basically connects the nodes which are using the state graph from langgraph

logic:
START -> index_video_node -> audio_content_node -> report_generation_node -> END 
'''

from langgraph.graph import StateGraph, END
from backend.src.graph.state import VideoAuditState
from backend.src.graph.nodes import index_video_node, audit_content_node

def create_graph():
    '''It constructs and compiles the langgraph workflow
    Returns : It retuens the compile graph which is nothing but the runnable graph object for execution'''

    #initialize the graph with the state schema
    workflow = StateGraph(VideoAuditState)

    #add the nodes to the graph
    workflow.add_node("indexer", index_video_node)
    workflow.add_node("auditor", audit_content_node)

    #define the entry point node as the indexer node
    workflow.set_entry_point("indexer") 

    #define the edges
    workflow.add_edge("indexer", "auditor")
    #once the audit is done then the workflow will end
    workflow.add_edge("auditor", END)

    #compile the graph
    app = workflow.compile()
    return app

#expose this app
app = create_graph()