import streamlit as st
import pandas as pd
import numpy as np

# Set the page title shown in the browser tab
st.set_page_config(page_title="My Streamlit App", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = None    
    
display_user = st.empty()
    
col1, col2 = st.columns(2)

if not st.session_state.authenticated:
    with col1:
        st.write("Log in")
        user = st.text_input("Username")
        password = st.text_input("Password",type="password")

        if user == "admin" and password == "lucc":
            st.session_state.authenticated = True
            st.rerun()



    
if st.session_state.authenticated:
    display_user.write("logged in as: joe")
    with col1:
        with st.container(border=True):
            
            if st.button("View all paddlers"):
                st.session_state.menu_selection = "paddlers"
                
            if st.button("Create group"):
                st.session_state.menu_selection = "create"
                
            if st.button("Saved groups"):
                st.session_state.menu_selection = "saved"
                
            if st.button("Trip log"):
                st.session_state.menu_selection = "log"
                
        if st.button("Log out"):
            st.session_state.authenticated = False
            st.rerun()

    
    with col2:
        
        if st.session_state.menu_selection == "paddlers":
            st.write("Here they are!")
            
        elif st.session_state.menu_selection == "create":
            st.write("Creating group...")
            
        elif st.session_state.menu_selection == "saved":
            st.write("Here are your saved groups")
            
        elif st.session_state.menu_selection == "log":
            st.write("Recent trips:")
            
        elif st.session_state.menu_selection == None:
            st.write("")

    
