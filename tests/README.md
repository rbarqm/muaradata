# 📡 Database & Tunnel Connectivity Test Utility

A lightweight command-line utility written in **Python** to validate
database connectivity and SSH tunnel availability.\
This tool is designed to simplify connection testing for environments
where multiple database endpoints and tunnels are configured through encrypted CSV
credential files.

It provides an interactive CLI menu to:

-   Test SSH tunnel availability
-   Test database connectivity
-   Display configured connection targets in a readable table format

------------------------------------------------------------------------

## Features

-   🔌 **Database Connection Test**
    -   Executes a simple SQL query to validate connectivity to a target
        database.
-   🌐 **SSH Tunnel Availability Test**
    -   Verifies if a tunnel host and port are reachable.
-   📊 **Readable CLI Output**
    -   Uses `tabulate` to display connection information in a
        structured table.
-   🧩 **CSV-based Configuration**
    -   Connection metadata stored in CSV files for easy maintenance.

------------------------------------------------------------------------

## Requirements

-   Python **3.7+**
-   Required Python packages:

```{=html}
<!-- -->
```
    pandas
    tabulate

Additionally, the project expects a custom library:

    iriis_connection_library

This library must expose the following functions:

-   `run_query(sql, aim)`
-   `run_exec(...)`
-   `insert_data(...)`

------------------------------------------------------------------------

## Installation

Clone the repository:

``` bash
git clone https://github.com/yourusername/db-tunnel-test.git
cd db-tunnel-test
```

Install dependencies:

``` bash
pip install pandas tabulate
```

Ensure the internal connection library is available in your environment.

------------------------------------------------------------------------

## Project Structure

    project-root/
    │
    ├── unit_test.py
    ├── credentials/
    │   ├── credentials.csv
    │   └── tunnels.csv
    │
    └── README.md

### Credentials File

`credentials/credentials.csv`

Example:

    id;name;host
    1;prod_db;10.10.10.10
    2;dev_db;10.10.20.20

### Tunnel Configuration

`tunnels.csv`

Example:

    id;name;host_tunnel
    1;jump_server;127.0.0.1
    2;analytics_tunnel;127.0.0.2

------------------------------------------------------------------------

## Usage

Run the script:

``` bash
python unit_test.py
```

You will see an interactive menu:

    HOW TO RESET:
    1. TEST TUNNEL
    2. TEST DB CONNECTION
    0. EXIT
    Answer :

### 1️⃣ Test Tunnel

-   Displays a list of available tunnel endpoints.
-   Enter the **Conn ID**.
-   The script attempts to open a socket connection to verify the
    tunnel.

Example result:

    Success: Tunnel on 127.0.0.1:22 active.

or

    Failed: No connection to 127.0.0.1:22.

------------------------------------------------------------------------

### 2️⃣ Test Database Connection

-   Displays configured database connections.
-   Enter the **Conn ID**.
-   A simple SQL query is executed:

```{=html}
<!-- -->
```
    SELECT 'Connected to <connection_name>' as response

Example output:

    Connected to prod_db

------------------------------------------------------------------------

## How It Works

### Database Test

1.  Loads connection metadata from `credentials.csv`
2.  Displays connection list using `tabulate`
3.  User selects a connection ID
4.  Executes query via:

```{=html}
<!-- -->
```
    run_query(sql, aim=<connection_name>)

------------------------------------------------------------------------

### Tunnel Test

1.  Loads tunnel metadata from `tunnels.csv`
2.  User selects a tunnel ID
3.  Attempts socket connection:

```{=html}
<!-- -->
```
    socket.create_connection((host, port), timeout=3)

Default port:

    22 (SSH)

------------------------------------------------------------------------

## Error Handling

Basic error handling includes:

-   Invalid connection ID
-   Empty user input
-   Socket connection failure
-   Connection timeout

------------------------------------------------------------------------

## Security Notes

-   Do **not commit real credentials** into the repository.
-   Store sensitive connection data securely.
-   Consider using environment variables or secret managers.

------------------------------------------------------------------------

## Possible Improvements

-   Add logging support
-   Add configuration validation
-   Support multiple ports for tunnel testing
-   Add automated unit tests
-   Convert CLI to `argparse` or `typer`
-   Support `.env` configuration

------------------------------------------------------------------------


## 🧾 Lisensi & Informasi

**Author:** Redian Barqy Muhammad  
**Email:** redian.muhammad@sigma.co.id  
**Copyright:** © 2025 IRIIS Project  


MIT License