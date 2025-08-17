# main.py
import streamlit as st
from modules.auth_module import register, login
from modules.main_page import main_page

def main():
    """
    Control the main application flow.

    - If the user is not logged in (`st.session_state['logged_in']` is False),
      display either the login or registration page depending on 
      `st.session_state['show_register']`.
    - If the user is logged in, render the main page with navigation.

    Session state keys used:
        - 'logged_in' (bool): Whether the user is authenticated.
        - 'show_register' (bool): Whether to show the registration page 
          instead of the login page.

    Returns:
        None: Renders the appropriate UI in the Streamlit app.
    """
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        if 'show_register' not in st.session_state:
            st.session_state['show_register'] = False
        
        if st.session_state['show_register']:
            register()
        else:
            login()
    else:
        main_page()

if __name__ == "__main__":
    main()