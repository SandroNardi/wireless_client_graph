from pywebio.output import put_markdown, put_html, use_scope, toast, put_buttons
from pywebio.input import input_group, input, DATE, TIME,NUMBER,select
from pyecharts.charts import Line
from pyecharts import options as opts
from datetime import datetime, timedelta, timezone
from meraki_tools.my_logging import get_logger
from project_logic import ProjectLogic
from meraki_tools.meraki_api_utils import MerakiAPIWrapper


logger = get_logger()

class ProjectUI:
    def __init__(self, api_utils: MerakiAPIWrapper,app_scope_name):
        """
        Initializes the ProjectUI class with API_Utils and ProjectLogic instances.
        """
        self._api_utils = api_utils
        self._project_logic = ProjectLogic(api_utils)
        self.logger = get_logger()
        self.app_scope_name=app_scope_name
        self.logger.info("ProjectUI initialized with API_ with API_Utils and ProjectLogic instances.")

    def app_main_menu(self):
        """
        Displays the main navigation menu for the application after an organization is selected.
        Provides options to manage profiles, DNS records, and network associations.
        """
        self.logger.info("Entering app_main_menu function.")

        if self._api_utils is None:
            error_message = "API_Utils instance is not available. Please ensure it was set during ensure it was set during ProjectUI initialization."
            self.logger.error(error_message)
            raise ValueError(error_message)

        try:
            with use_scope(self.app_scope_name, clear=True):
                put_markdown(f"### Organization: {self._api_utils.get_organization_name()} (id: {self._api_utils.get_organization_id()})")
                self.logger.info(f"Displaying main menu for organization: {self._api_utils.get_organization_name()} (id: {self._api_utils.get_organization_id()})")

                put_buttons(
                    [
                        {"label": "Wireless client graph", "value": "wireless_client_graph"},
                    ],
                    onclick=self.handle_main_menu_action,
                )
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred in app_main_menu: {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def handle_main_menu_action(self, action):
        """Handles actions triggered from the main menu buttons."""
        self.logger.info(f"Handling main menu action: {action}")
        try:
            if action == "wireless_client_graph":
                networks = self._api_utils.list_networks(use_cache=True,filter_product_type=["wireless"])
                if isinstance(networks, dict) and "error" in networks:
                    toast(f"Error fetching networks: {networks.get('details')}", color="error")
                    return
                self.ui_collect_and_display(networks)
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred in handle_main_menu_action for action '{action}': {e}")
            toast(f"An unexpected error occurred: {e}", color="error", duration=0)

    def ui_collect_and_display(self, networks_list):
        """
        UI function to request time frame and resolution input, collect data, and display graph.
        Includes validation for Meraki API time and resolution boundaries.
        """
        with use_scope(self.app_scope_name, clear=True):
            now_utc = datetime.now(timezone.utc)
            default_end = now_utc
            default_start = default_end - timedelta(days=7)


            inputs = input_group("Select Time Frame for Wireless Client History", [
                input("Start Date (YYYY-MM-DD)", type=DATE, value=default_start.date().strftime("%Y-%m-%d"), name="start_date"),
                input("Start Time (HH:MM)", type=TIME, value=default_start.strftime("%H:%M"), name="start_time"),
                input("End Date (YYYY-MM-DD)", type=DATE, value=default_end.date().strftime("%Y-%m-%d"), name="end_date"),
                input("End Time (HH:HH)", type=TIME, value=default_end.strftime("%H:%M"), name="end_time"),
            ])

            try:
                # Combine date and time, assuming inputs are intended to be UTC
                t0_dt = datetime.combine(
                    datetime.strptime(inputs['start_date'], "%Y-%m-%d").date(), #type: ignore
                    datetime.strptime(inputs['start_time'], "%H:%M").time(),#type: ignore
                    tzinfo=timezone.utc
                )
                t1_dt = datetime.combine(
                    datetime.strptime(inputs['end_date'], "%Y-%m-%d").date(),#type: ignore
                    datetime.strptime(inputs['end_time'], "%H:%M").time(),#type: ignore
                    tzinfo=timezone.utc
                )
            except ValueError:
                toast("Error: Invalid date or time format. Please use YYYY-MM-DD and HH:MM.", color="error")
                self.logger.error("Invalid date or time format.")
                return

            # --- Meraki API Time Boundary Validations ---

            # 1. End datetime must be strictly after start datetime
            if t1_dt <= t0_dt:
                toast("Error: End datetime must be after start datetime.", color="error")
                self.logger.error("End datetime must be after start datetime.")
                return

            # 2. End datetime cannot be in the future (relative to current UTC time)
            if t1_dt > now_utc:
                toast("Error: End datetime cannot be in the future.", color="error")
                self.logger.error(f"End datetime {t1_dt} is in the future compared to {now_utc}.")
                return

            # 3. Start datetime cannot be older than 31 days from today (current UTC time)
            max_lookback_start = now_utc - timedelta(days=31)
            if t0_dt < max_lookback_start:
                toast("Error: Start datetime cannot be older than 31 days from today.", color="error")
                self.logger.error(f"Start datetime {t0_dt} is older than 31 days from {now_utc}.")
                return

            # 4. The time span (t1 - t0) cannot exceed 31 days
            max_t1_from_t0 = t0_dt + timedelta(days=31)
            if t1_dt > max_t1_from_t0:
                toast("Error: The selected time range cannot exceed 31 days (End datetime is more than 31 days after Start datetime).", color="error")
                self.logger.error(f"End datetime {t1_dt} is more than 31 days after start datetime {t0_dt}.")
                return

            # --- Resolution Input and Validation ---
            # Resolution is now selected from a dropdown, so it's guaranteed to be a valid string representation of minutes
            

            toast(f"Collecting Wireless Client History from {t0_dt.isoformat()} to {t1_dt.isoformat()}", color="info")
            self.logger.info(f"Collecting Wireless Client History from {t0_dt.isoformat()} to {t1_dt.isoformat()}")

            graph_data = self._project_logic.collect_network_data_history(networks_list, t0_dt, t1_dt)

            self.display_graph(graph_data, f"{t0_dt.strftime('%Y-%m-%d %H:%M')} to {t1_dt.strftime('%Y-%m-%d %H:%M')}")

    def display_graph(self, graph_data, title_suffix):
        """
        PyWebIO function to display web-based graphs using pyecharts.
        Displays all networks on a single chart, with a different line for each.
        Also adds a line for the sum of all network clients, and markers for highest and lowest values.
        Adds a 'Back' button to reload the main menu.
        """
        with use_scope('graph_output', clear=True):
            toast("Generating Combined Web-based Client Count Graph...", color="info")
            self.logger.info("Generating Combined Web-based Client Count Graph...")

        if not graph_data:
            with use_scope('graph_output', clear=False):
                toast("No network data collected to display.", color="warning")
                self.logger.warning("No network data collected to display.")
            return

        timestamps = []
        data_length = 0

        first_network_history = None
        for network_id, network_info in graph_data.items():
            if network_info.get('history'):
                first_network_history = network_info['history']
                break

        if first_network_history:
            for entry in first_network_history:
                timestamp_str = entry['startTs'].replace('Z', '+00:00')
                timestamps.append(datetime.fromisoformat(timestamp_str).strftime('%Y-%m-%d %H:%M'))
            data_length = len(first_network_history)
        else:
            with use_scope('graph_output', clear=False):
                toast("No client history data found for any network to display a graph.", color="warning")
                self.logger.warning("No client history data found for any network to display a graph.")
            return

        if not timestamps:
            with use_scope('graph_output', clear=False):
                toast("No client history data found for any network to display a graph.", color="warning")
                self.logger.warning("No client history data found for any network to display a graph.")
            return

        total_client_counts = [0] * data_length

        line_chart = (
            Line(init_opts=opts.InitOpts(width="1400px", height="650px"))
            .add_xaxis(timestamps)
        )

        has_data_to_plot = False
        for network_id, network_info in graph_data.items():
            network_name = network_info.get('name', f"Network ID: {network_id}")
            client_history = network_info.get('history', [])

            if not client_history:
                continue

            client_counts = [entry['clientCount'] if entry.get('clientCount') is not None else 0 for entry in client_history]

            if len(client_counts) != data_length:
                with use_scope('graph_output', clear=False):
                    toast(f"Warning: Data length mismatch for {network_name}. Skipping for total calculation.", color="warning")
                    self.logger.warning(f"Data length mismatch for {network_name}. Skipping for total calculation.")
                continue

            line_chart.add_yaxis(
                network_name,
                client_counts,#type: ignore
                linestyle_opts=opts.LineStyleOpts(width=2),
                label_opts=opts.LabelOpts(is_show=False),
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="Max Value"),
                        opts.MarkPointItem(type_="min", name="Min Value"),
                    ]
                )
            )
            has_data_to_plot = True

            for i, count in enumerate(client_counts):
                total_client_counts[i] += count

        if not has_data_to_plot:
            with use_scope('graph_output', clear=False):
                toast("No valid client history data found across all networks to plot.", color="warning")
                self.logger.warning("No valid client history data found across all networks to plot.")
            return

        line_chart.add_yaxis(
            "Total Clients",
            total_client_counts,#type: ignore
            linestyle_opts=opts.LineStyleOpts(width=4, type_="solid", opacity=0.8),
            itemstyle_opts=opts.ItemStyleOpts(color="#FF0000"),
            label_opts=opts.LabelOpts(is_show=False),
            markpoint_opts=opts.MarkPointOpts(
                data=[
                    opts.MarkPointItem(type_="max", name="Max Total"),
                    opts.MarkPointItem(type_="min", name="Min Total"),
                ]
            )
        )

        line_chart.set_global_opts(
            title_opts=opts.TitleOpts(title=f"Wireless Client Count History for All Networks ({title_suffix})"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(type_="category", boundary_gap=False, axislabel_opts={"rotate": 35}),
            yaxis_opts=opts.AxisOpts(type_="value", name="Clients #"),
            legend_opts=opts.LegendOpts(is_show=True, pos_top="top", pos_left="right"),
        )

        with use_scope('graph_output', clear=False):
            
            def download_csv():
                import io
                import csv
                from pywebio.output import download

                output = io.StringIO()
                writer = csv.writer(output)

                # Write header row
                header = ["Timestamp"] + [
                    network_info.get('name', f"Network ID: {network_id}")
                    for network_id, network_info in graph_data.items()
                ]
                writer.writerow(header)

                # Write data rows
                for i, timestamp in enumerate(timestamps):
                    row = [timestamp]
                    for network_id, network_info in graph_data.items():
                        client_history = network_info.get('history', [])
                        count = (
                            client_history[i]['clientCount']
                            if i < len(client_history) and 'clientCount' in client_history[i]
                            else 0
                        )
                        row.append(count)
                    writer.writerow(row)

                csv_data = output.getvalue().encode('utf-8')  # Encode string to bytes
                output.close()
                download("wireless_client_data.csv", csv_data)

            put_buttons(
                [
                    {"label": "Download Data as CSV", "value": "download_csv"},
                    {"label": "Back", "value": "back"},
                ],
                onclick=lambda btn_val: download_csv() if btn_val == "download_csv" else self.app_main_menu()
            )
        
        put_html(line_chart.render_notebook())
        