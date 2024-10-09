# Community Members Processor

## Overview

**Community Members Processor** is a Python-based Command-Line Interface (CLI) application designed to process community member data efficiently. It accepts either a ZIP file containing a CSV of members or a CSV file directly as input. The application filters members based on their join dates, tracks the most recent join date using a local cache, and outputs a refined CSV containing essential member information.

## Features

- **Flexible Input Handling:** Supports both ZIP archives containing a CSV file and standalone CSV files as input.
- **Date-Based Filtering:** Filters members based on a reference join date, ensuring only recent members are processed.
- **Local Caching:** Maintains a cache of the last processed join date to streamline subsequent runs.
- **Customizable Output:** Allows users to specify the output file name or defaults to a timestamped filename.
- **Sorted Output:** Outputs the processed members sorted by join date in descending order.
- **Robust Date Parsing:** Handles multiple date formats, including ISO 8601, to ensure compatibility with various CSV data.

## Requirements

- **Python Version:** Python 3.7 or higher
- **Dependencies:** Utilizes only Python's standard library; no external packages are required.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/redrhino-online/tlr-circle-community-member-audit.git
   cd tlr-circle-community-member-audit
   ```

## Usage

The application can be executed via the command line, accepting various arguments to customize its behavior.

### Command Structure

```bash
python process.py [--timestamp "<reference_timestamp>"] [--output <output_file>] <input_file>
```

### Arguments

- `--input` or `-i`: **(Required)**  
  Path to the input file, which can be either a ZIP archive containing a CSV file or a standalone CSV file.

- `--output` or `-o`: **(Optional)**  
  Desired name for the output CSV file. If not provided, the application defaults to `output_<YYYYMMDD_HHMMSS>.csv`.

- `--timestamp` or `-r`: **(Optional)**  
  Reference timestamp to filter members. Acceptable formats:
  - `YYYY-MM-DD HH:MM:SS` (e.g., `2024-09-30 16:56:42`)
  - ISO 8601 (e.g., `2024-09-30T16:56:42Z`)

### Example Command

```bash
python process.py --input community_conscious_love_community_121102_1728496028_member_list.csv --output today.csv --timestamp "2024-09-30T16:56:42.000Z"
```

**Note:** Replace `process.py` with the actual script name if different.

### Behavior Based on Arguments

- **With Reference Timestamp (`--timestamp`):**
  
  The application uses the provided timestamp to filter members, ignoring any cached reference dates. This is ideal for automated runs where user interaction is minimized.

- **Without Reference Timestamp:**
  
  - **If a Cache Exists:**  
    The application uses the cached last join date to filter members automatically.
  
  - **If No Cache Exists:**  
    The application prompts the user to either provide a reference timestamp or include all members.

### Default Output File Name

If the `--output` argument is not provided, the application generates a default file name based on the current date and time:

```
output_YYYYMMDD_HHMMSS.csv
```

*Example:* `output_20241009_153045.csv`

## Output

The application generates a CSV file containing the following fields:

- **First Name**
- **Last Name**
- **Email**
- **Join Date** (in ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`)
- **Profile URL**

The output is sorted by `Join Date` in descending order, ensuring the most recently joined members appear first.

### Sample Output

```csv
First Name,Last Name,Email,Join Date,Profile URL
Kristin,,example@example.com,2024-10-03T03:10:11Z,https://conscious-love.circle.so/u/xxxxxxx
```

## Caching Mechanism

The application maintains a local cache (`last_join_date.pkl`) to store the most recent join date processed. This cache ensures that subsequent runs only process new members who joined after the last recorded date.

- **Cache Location:**  
  The cache file is stored in the same directory as the script.

- **Cache Handling:**
  - **Loading:**  
    On startup, the application checks for the existence of the cache file to determine the reference date.
  
  - **Saving:**  
    After processing, the application updates the cache with the latest join date from the processed members.

- **Handling Corrupted Cache:**
  If the cache file is corrupted or unreadable, the application warns the user and proceeds without it, prompting for a reference timestamp or including all members.

## Error Handling

The application includes robust error handling to manage various scenarios:

- **Invalid Input File Type:**
  
  If the input file is neither a ZIP archive nor a CSV file, the application notifies the user and exits.

  ```bash
  An error occurred: Input file must be a ZIP or CSV file.
  ```

- **Invalid Date Format:**
  
  If a member's `Join Date` is in an unrecognized format, the application raises a `ValueError` with the problematic row's data.

  ```bash
  An error occurred: Invalid date format in row: {'User ID': '13844083', 'First Name': 'Kristin', ...}
  ```

- **Corrupted Cache File:**
  
  If the cache file is corrupted, the application warns the user and proceeds without using the cache.

  ```bash
  Warning: Cache file is corrupted. It will be ignored.
  No cached timestamp found. Do you want to (1) Provide a timestamp or (2) Include all members? [1/2]:
  ```

- **File Read/Write Errors:**
  
  The application handles I/O errors gracefully, informing the user of issues like inability to read the input file or write the output file.

  ```bash
  Failed to write output file: [Error Details]
  ```
