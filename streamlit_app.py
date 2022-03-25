# -*- coding: utf-8 -*-
import os
import time
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


def login():
    logged_in = False
    if not st.session_state['authentication_status']:
        load_dotenv(f'{Path(__file__).parent}/.env')
        login_form = st.empty()
        with login_form:
            with st.form("Login Form"):
                username = st.text_input("Email")
                passwd = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                if submitted:
                    try:
                        assert username == os.environ['FLASK_USERNAME']
                        assert passwd == os.environ['FLASK_PASSWORD']
                        logged_in = True
                    except AssertionError:
                        st.error('Incorrect credentials!')

        if logged_in:
            login_form.success('Logged in successfully!')
            time.sleep(1)
            login_form.empty()
            return True


if __name__ == '__main__':
    st.set_page_config(page_title='Files server',
                       page_icon='🐦',
                       layout='wide',
                       initial_sidebar_state='expanded')

    st.markdown("""<style> footer {visibility: hidden;} 
    footer::before { content:'NC State University & 
    NC Museum of Natural Sciences | Maintained by Mohammad Alyetama'; 
    visibility: visible; position: fixed; left: 1; right: 1; bottom: 0; 
    text-align: center; } </style>""",
                unsafe_allow_html=True)

    st.markdown("""<style>
    #MainMenu {visibility: hidden;}
    </style>""",
                unsafe_allow_html=True)

    load_dotenv()

    login_container = st.empty()

    with login_container:
        if 'authentication_status' not in st.session_state:
            st.session_state['authentication_status'] = False

        if login():
            st.session_state['authentication_status'] = True
            login_container.empty()

    if st.session_state['authentication_status']:
        uploaded_file = st.file_uploader(label='Choose a file', accept_multiple_files=True)
        if uploaded_file:
            for file in uploaded_file:
                file_id = str(uuid.uuid4()).split('-')[0]
                suffix = Path(file.name).suffix
                with open(f'files/{file_id}{suffix}', 'wb') as f:
                    f.write(file.getvalue())
                url = f'https://d.aibird.me/{file_id}{suffix}'
                st.markdown(f'{file.name} [{url}]({url})')
