## Wireless Client Count Graph

Create an interactive, web-based graph of Cisco Meraki wireless client counts across all networks in a selected organization over a specified time range. The app is built with PyWebIO for the UI, uses the official Meraki Dashboard API for data, and renders charts with pyecharts. You can also export the graphed data to CSV.

### Features
- **Organization-aware:** Uses your Meraki organization to enumerate wireless networks.
- **Time range selection:** Choose a start and end in UTC with validation against Meraki API limits.
- **Auto resolution:** Let Meraki auto-select the best resolution for the requested range.
- **Combined chart:** Plots one line per network plus a bold line for the total.
- **Max/Min markers:** Highlights extremes for each series.
- **CSV export:** Download the displayed time series as a CSV file.
- **Logging:** Writes to `app.log` and the in-app log pane.

### Time range rules (Meraki API)
- End must be after start.
- End cannot be in the future.
- Start cannot be older than 31 days from now.
- Duration cannot exceed 31 days.

---

### Prerequisites
- Python 3.9+
- A Cisco Meraki Dashboard API key with access to the target organization

Recommended Python packages (install via pip):

```bash
pip install pywebio meraki pyecharts
```

If you use a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows PowerShell
pip install pywebio meraki pyecharts
```

---

### Configuration
Set the following environment variables so the app can authenticate and preselect the organization:

- `MK_CSM_KEY` — Your Meraki Dashboard API key
- `MK_MAIN_ORG` — Organization ID to use by default

On Windows PowerShell:

```powershell
$env:MK_CSM_KEY = "<your_api_key_here>"
$env:MK_MAIN_ORG = "<your_organization_id_here>"
```

These are read at startup in `app.py`. The app will validate that it has what it needs before proceeding.

---

### Run the app
From the project root:

```bash
python app.py
```

By default, PyWebIO starts a local server on port 8080. Open `http://127.0.0.1:8080` in your browser.

---

### Using the app
1. The main screen shows the selected organization.
2. Click "Wireless client graph".
3. Pick the start and end date/time (UTC). The app enforces Meraki’s limits listed above.
![Date Pick](screenshot/datepick.png "Pick date")
4. The chart renders one series per wireless network, plus a red "Total Clients" line.
![Graph output](screenshot/graph.png "Graph ouptut")
5. Use the buttons to download the displayed data as CSV or go back to the main menu.

CSV includes a header row with `Timestamp` followed by each network name; subsequent rows contain counts aligned by timestamp.

---

### Project structure
```
wireless_client_graph/
  app.py                 # Entry point; starts PyWebIO server and UI
  project_ui.py          # UI flows (menu, inputs, chart rendering, CSV export)
  project_logic.py       # Data collection via Meraki Dashboard API
  meraki_tools/
    meraki_api_utils.py  # Meraki API wrapper, organization/network listing
    my_logging.py        # Logging setup and helpers
    meraki_ui.py         # App shell (scopes, header, setup, log pane, CSS)
    style.css            # Optional custom styles for PyWebIO
  about.py               # App metadata (name, description, links, license text)
  app.log                # Runtime logs
  README.MD              # This file
  LICENSE                # MIT License
```

---

### Logging
- Runtime activity is logged to `app.log` and surfaced in the UI log panel.
- Logging is configured in `meraki_tools.my_logging` and enabled in `app.py`.

---

### Troubleshooting
- **401/403 errors:** Verify `MK_CSM_KEY` is set and has required permissions.
- **Organization not found:** Ensure `MK_MAIN_ORG` is a valid organization ID accessible by your key.
- **Empty chart:** No wireless networks found, or no history available for the selected window.
- **Time validation errors:** Adjust inputs to respect the 31-day window and non-future end time.

If issues persist, check `app.log` for stack traces and API messages.

---

### Development notes
- The UI is built with PyWebIO scopes and buttons, rendering charts with pyecharts.
- Data is fetched using the official `meraki` Python SDK (`DashboardAPI`).
- Network filtering in `meraki_api_utils.list_networks` supports `filter_product_type=["wireless"]`.

---

### License
This project is licensed under the MIT License. See `LICENSE` for details.

