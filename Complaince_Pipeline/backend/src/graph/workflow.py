'''This modeule defines the nodes for the workflow and defines the DAG : Directed Acyclic Graph.
That orchestrate the video complaince audit process
It basically connects the nodes which are using the state graph from langgraph

logic:
START -> index_video_node -> audio_content_node -> report_generation_node -> END 
'''