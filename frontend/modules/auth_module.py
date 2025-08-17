import streamlit as st
import requests
from settings import AUTH_BASE_URL


def login():
    """
    Render the login UI and authenticate the user.

    Displays username and password inputs. When submitted, it sends a POST
    request to `{AUTH_BASE_URL}/login/`. On success (HTTP 200), the function:
      - Stores the token in `st.session_state['token']`
      - Sets `st.session_state['logged_in'] = True`
      - Calls `st.rerun()` to refresh the page state
    On failure, an error message is shown.

    UI controls:
        - "Login" button: Attempts authentication.
        - "Create account" button: Sets `st.session_state['show_register'] = True`
          to switch to the registration view.
    """
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        data = {"username": username, "password": password}
        response = requests.post(f"{AUTH_BASE_URL}/login/", json=data)

        if response.status_code == 200:
            token = response.json().get("token")
            st.success("Login successful!")
            st.session_state['token'] = token
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Login failed. Check your credentials.")

    if st.button("Create account"):
        st.session_state['show_register'] = True


def register():
    """
    Render the registration UI and create a new account.

    Displays fields for username, email, and password. When submitted, it sends a
    POST request to `{AUTH_BASE_URL}/register/`. On success (HTTP 201), a success
    message is shown and the view toggles back to login by setting
    `st.session_state['show_register'] = False`. On failure, an error message is shown.

    UI controls:
        - "Register" button: Attempts to create the account.
        - "Back to Login" button: Returns to the login view by setting
          `st.session_state['show_register'] = False`.
    """
    st.title("Create Account")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        data = {
            "username": username,
            "email": email,
            "password": password
        }
        response = requests.post(f"{AUTH_BASE_URL}/register/", json=data)
        if response.status_code == 201:
            st.success("Account created! You can now login.")
            st.session_state['show_register'] = False
        else:
            st.error("Registration failed. Try again.")

    if st.button("Back to Login"):
        st.session_state['show_register'] = False
