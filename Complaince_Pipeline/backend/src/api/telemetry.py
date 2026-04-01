'''
azure opentelemetry integration 
'''

import os 
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

#create a dedicated logger for telemetry
logger = logging.getLogger("brand-guardian-telemetry")

def setup_telemetry():
    ''''It initializes the Azure Monitor OpenTelemetry.
    It is the industry standard observability framework
    It Tracks:
    HTTP requests, database queries, errors, performance metrics

    This function will send the data to azure monitor (kind of flight data recorder for our application)

    It auto captures the every api request

    No need to manually log each endpoint
    '''

    #retrieve the connection string from environment variable
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    #check if the connection string is configured or not
    if not connection_string:
        logger.warning("No instrumentation key found for Azure Monitor. Telemetry is disabled.")
        return
    #configure the azure monitor
    try:
        configure_azure_monitor(
        connection_string=connection_string,
        logger_name = "brand-guardian-tracer"
        )
        logger.info("Azure Monitor OpenTelemetry configured successfully and Enabled")
    except Exception as e:
        logger.error(f"Failed to configure Azure Monitor OpenTelemetry: {str(e)}")
        raise Exception("Telemetry setup failed. Please check your Azure Monitor configuration and try again.")
    
    '''Why do we use telemetry
    
    don't have telemetry : API is slow -> no idea which part is causing the slowness -> user experience is bad -> lose customers
    how many users today? No visibility

    With Telemetry : API is slow -> check telemetry data -> identify the bottleneck -> optimize that part -> improved user experience -> retain customers

    if i have the endpoint called as "/audit"  averages 4.5 seconds and indexer takes 3.8 seconds these kind of insights will tracked by the telemetry.

    Error logs show : 12% of audits fail due to youtube download errors

    It also shows the Metrics : 450 API calls per day, 95% success rate, 200ms average response time
    
    
    '''