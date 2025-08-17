import io
import pandas as pd
import requests
import streamlit as st
from settings import API_BASE_URL


def api_request(method, endpoint, token, json_data=None):
    """
    General helper for making authenticated API requests with error handling.

    Sends an HTTP request to the backend API, attaching the provided token 
    in the `Authorization` header. Handles authentication errors (401), 
    validation errors (400), and other HTTP/connection errors gracefully.

    Args:
        method (str): The HTTP method (e.g., "GET", "POST", "PATCH", "DELETE").
        endpoint (str): The relative API endpoint (appended to API_BASE_URL).
        token (str): Authentication token for the current user session.
        json_data (dict, optional): JSON body to include in the request.

    Returns:
        dict | list | bool | None:
            - Parsed JSON response for successful requests.
            - `True` if the response is HTTP 204 No Content.
            - `None` if an error occurs (e.g., network error, 401 unauthorized).
    """
    headers = {'Authorization': f'Token {token}'}
    try:
        url = f"{API_BASE_URL}/{endpoint}"
        response = requests.request(method, url, headers=headers, json=json_data)
        if response.status_code == 401:
            st.error("Session invalid or expired. Please log in again.")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
            return None
        if response.status_code == 400:
            return response.json()
        response.raise_for_status()
        return response.json() if response.status_code != 204 else True
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API communication error: {e}")
        return None


def parse_hours_string(hours_decimal):
    """
    Convert a decimal number of hours into a human-readable string format.

    Args:
        hours_decimal (float | Decimal | None): The number of hours as a decimal.
            Example: 1.5 -> "1h 30min".

    Returns:
        str: A formatted string in the format "Xh Ymin".
             Returns "0h 0min" if input is None.
    """
    if hours_decimal is None:
        return "0h 0min"
    total_minutes = int(float(hours_decimal) * 60)
    h, m = divmod(total_minutes, 60)
    return f"{h}h {m}min"


def export_to_excel(token, start_date, end_date):
    """
    Export project summary data to an Excel file and provide a Streamlit download button.

    Retrieves project summary data (optionally filtered by date range) from the API, 
    formats it into an Excel sheet, calculates the total hours, and allows the user 
    to download the file directly from the Streamlit UI.

    Args:
        token (str): Authentication token for the API request.
        start_date (datetime.date | None): Start date for filtering project time entries.
        end_date (datetime.date | None): End date for filtering project time entries.

    Returns:
        None: Displays a download button in the Streamlit app if data is available.
    """
    endpoint = 'projects/summary/'
    if start_date and end_date:
        endpoint += f'?start_date={start_date}&end_date={end_date}'

    data = api_request('get', endpoint, token)
    if not data:
        st.warning("No data to export for the selected period.")
        return

    df = pd.DataFrame(data)
    df['total_hours'] = pd.to_numeric(df['total_hours'])

    if start_date and end_date:
        sheet_name = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}"
    else:
        sheet_name = "All Time"

    total_sum = df['total_hours'].sum()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_export = df[['name', 'total_hours']].copy()
        df_to_export.columns = ['Project', 'Total Hours']
        df_to_export.to_excel(writer, index=False, sheet_name=sheet_name)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        total_row = len(df_to_export) + 1
        worksheet.write(total_row, 0, "Total")
        worksheet.write(total_row, 1, total_sum)

        money_format = workbook.add_format({'num_format': '0.00'})
        worksheet.set_column(1, 1, 12, money_format)

    output.seek(0)
    filename = "track_time_records.xlsx"

    st.download_button(
        label="Download Excel",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
