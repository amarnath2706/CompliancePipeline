'''
Main execution entry  point for the Complance Pipeline.
'''

import uuid
import json
import logging
from pprint import pprint

from dotenv import load_dotenv
load_dotenv(override=True)

from backend.src.graph.workflow import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("brand-guardian-runner")


def run_cli_simulation():
    '''This function which basically simulated the video complaince audit request'''

    #generate the session id(unique id for every session)
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Audit Session : {session_id} ")

    #define the initial state
    initial_inputs = {
        "video_url": "",
        "video_id": f"vid_{session_id[:8]}",
        "complaine_results" : [],
        "errors" : []
    }

    print("n----Initializing workflow............")
    print(f"Input Payload : {json.dumps(initial_inputs, indent=2)}")

    try:
        final_state = app.invoke(initial_inputs)
        print("\n-----Workflow execution completed successfully!.........")

        print("\n Complaince Audit Report ==")
        print(f"Video ID : {final_state.get('video_id')}")
        print(f"Status : {final_state.get('final_status')}")
        print("\n [VIOALATIONS ARE DETECTED]")
        results = final_state.get("complaine_results",[])

        if results:
            for issue in results:
                print(f" - [{issue.get('severity')}] [{issue.get('category')}] : [{issue.get{'description'}}]")
        else:
            print("No violations detected.")
        print("\n [FINAL SUMMARY]")
        print(final_state.get("final_report"))
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise e
    
if __name__ == "__main__":
    run_cli_simulation()    