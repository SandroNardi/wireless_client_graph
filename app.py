# type: ignore
# app.py
from pywebio.output import toast
from pywebio import start_server, config
from meraki_tools.my_logging import setup_logger  # Setup logger and log storage
from pywebio.session import register_thread
import threading
import meraki_tools.meraki_ui as meraki_ui
import os
import about

# Import the new class-based modules
from project_logic import ProjectLogic
from project_ui import ProjectUI


# Initialize logger with console output enabled for debugging and monitoring.
logger = setup_logger(enable_logging=True, console_logging=True, file_logging=True)
required_app_setup_param = {"api_key": True, "organization_id": True, "network_id": False}

# Application setup parameters, potentially from environment variables or defaults.
app_setup_param = {"api_key": os.getenv("MK_CSM_KEY"), "organization_id": os.getenv("MK_MAIN_ORG")}

app_scope_name = "app"
UI=meraki_ui.PyWebIOApp(app_scope_name,about.APP_INFO)

def app():
    """
    The main PyWebIO application function.
    Initializes the UI, sets up background tasks, and orchestrates the application flow.
    """
    logger.info("Starting PyWebIO application.")
    try:
        # Create and register a background thread to update the log display in the UI.
       
        t = threading.Thread(target=UI.update_log_display)
        register_thread(t)

        UI.render_header() # Assuming APP_INFO is now handled within meraki_ui or passed differently
        t.start()  # Start the log update thread.

        # Call app_setup and get the API_Utils object
        api_utils = UI.app_setup(required_app_setup_param, app_setup_param=app_setup_param)

        if api_utils is None:
            # Handle setup failure (e.g., API key missing, organization not found)
            logger.error("Application setup failed. Exiting.")
            toast("Application setup failed. Please check configurations.", color="error", duration=0)
            return # Use return instead of exit(1) in PyWebIO app context

        # --- New: Instantiate ProjectLogic and ProjectUI ---
        # 1. Instantiate the ProjectLogic class, injecting the api_utils instance
        project_logic_instance = ProjectLogic(api_utils)

        # 2. Instantiate the ProjectUI class, injecting both api_utils and the project_logic_instance
        project_ui_instance = ProjectUI(api_utils, project_logic_instance,app_scope_name)

        # 3. Start the application by calling the main menu method on the ProjectUI instance
        project_ui_instance.app_main_menu()
        # --- End New ---

    except Exception as e:
        # Log and show error toast if any unexpected error occurs during application startup.
        logger.exception(f"An unexpected error occurred during application startup: {e}")
        toast(f"An unexpected error occurred during startup: {e}", color="error", duration=0)

if __name__ == "__main__":
    """
    Entry point of the script.
    Configures PyWebIO and starts the server.
    """
    logger.info("Application script started.")
    # Apply custom CSS styles from the wrapper module for UI customization.
    config(css_style=UI.get_css_style())
    # Start PyWebIO server on port 8080 with debug enabled for development.
    start_server(app, port=8080, debug=True)