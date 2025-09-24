# type: ignore
# project_logic.py
import os
import meraki
import json
import requests
from meraki_tools.my_logging import get_logger
from meraki_tools.meraki_api_utils import MerakiAPIWrapper


logger = get_logger()

class ProjectLogic:
    def __init__(self, api_utils:MerakiAPIWrapper):
        """
        Initializes the ProjectLogic class with an API_Utils instance.
        This instance will be used for all API interactions within this class.
        """
        self._api_utils = api_utils
        self.logger = get_logger()
        self.logger.info("ProjectLogic initialized with API_Utils instance.")
    

    def collect_network_data_history(self, networks_list, t0_dt, t1_dt):
        """
        Collects wireless client count history for a given list of networks
        within a specified time range and resolution.
        """
        collected_data = {}

        t0_str = t0_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')
        t1_str = t1_dt.isoformat(timespec='seconds').replace('+00:00', 'Z')

        dashboard = self._api_utils.get_dashboard()
        if dashboard is None:
            self.logger.error("Dashboard API client is not initialized.")
            return collected_data

        for network in networks_list:
            network_id = network['id']
            network_name = network.get('name', f"Unnamed Network ({network_id})")
            try:
                history = dashboard.wireless.getNetworkWirelessClientCountHistory(
                    network_id,
                    t0=t0_str,
                    t1=t1_str,
                    autoResolution=True
                )
                collected_data[network_id] = {
                    "name": network_name,
                    "history": history
                }
            except meraki.APIError as e:
                self.logger.error(f"Meraki API Error for {network_name}: {e}")
                collected_data[network_id] = {
                    "name": network_name,
                    "history": []
                }
            except Exception as e:
                self.logger.error(f"Unexpected error for {network_name}: {e}")
                collected_data[network_id] = {
                    "name": network_name,
                    "history": []
                }
        return collected_data