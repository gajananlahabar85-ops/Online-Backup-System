import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime


# ---------------- DATABASE ----------------

conn = sqlite3.connect(
    "backup_system.db",
    check_same_thread=False
)

cursor = conn.cursor()


# User Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
)
""")


# Files Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    filename TEXT,
    upload_time TEXT
)
""")


conn.commit()


# Default User
cursor.execute("SELECT * FROM users")

if cursor.fetchone() is None:
    cursor.execute(
        "INSERT INTO users(username,password) VALUES (?,?)",
        ("admin","admin123")
    )
    conn.commit()


# Create Upload Folder
if not os.path.exists("uploads"):
    os.makedirs("uploads")


# ---------------- LOGIN ----------------


if "login" not in st.session_state:
    st.session_state.login = False


def check_login(username,password):

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    )

    return cursor.fetchone()



if not st.session_state.login:

    st.title("🔐 Online Backup System Login")


    username = st.text_input("Username")

    password = st.text_input(
        "Password",
        type="password"
    )


    if st.button("Login"):

        if check_login(username,password):

            st.session_state.login = True
            st.session_state.username = username

            st.success("Login Successful")

            st.rerun()

        else:

            st.error("Invalid Username or Password")



# ---------------- MAIN SYSTEM ----------------


else:


    st.sidebar.title("Online Backup System")


    menu = st.sidebar.radio(
        "Select Option",
        [
            "Dashboard",
            "Upload File",
            "My Backup Files"
        ]
    )


    if st.sidebar.button("Logout"):

        st.session_state.login = False

        st.rerun()



# Dashboard

    if menu == "Dashboard":


        st.title("☁️ Backup Dashboard")


        total = cursor.execute(
            "SELECT COUNT(*) FROM files WHERE username=?",
            (st.session_state.username,)
        ).fetchone()[0]


        st.metric(
            "Total Backup Files",
            total
        )


        st.write(
            "Welcome:",
            st.session_state.username
        )



# Upload File


    elif menu == "Upload File":


        st.title("📤 Upload File")


        uploaded_file = st.file_uploader(
            "Choose File"
        )


        if uploaded_file:


            file_path = os.path.join(
                "uploads",
                uploaded_file.name
            )


            with open(file_path,"wb") as f:

                f.write(
                    uploaded_file.getbuffer()
                )


            cursor.execute(
                """
                INSERT INTO files
                (username,filename,upload_time)
                VALUES(?,?,?)
                """,
                (
                    st.session_state.username,
                    uploaded_file.name,
                    str(datetime.now())
                )
            )


            conn.commit()


            st.success(
                "File Backup Completed"
            )



# View Backup Files


    elif menu == "My Backup Files":


        st.title("📂 My Backup Files")


        data = pd.read_sql_query(

            """
            SELECT * FROM files
            WHERE username=?
            """,

            conn,

            params=(
                st.session_state.username,
            )

        )


        if not data.empty:


            st.dataframe(data)


            filename = st.selectbox(
                "Select File",
                data["filename"]
            )


            path = os.path.join(
                "uploads",
                filename
            )


            if os.path.exists(path):


                with open(path,"rb") as file:


                    st.download_button(
                        "Download File",
                        file,
                        filename
                    )


            if st.button("Delete File"):


                if os.path.exists(path):

                    os.remove(path)


                cursor.execute(
                    "DELETE FROM files WHERE filename=?",
                    (filename,)
                )


                conn.commit()


                st.success(
                    "File Deleted"
                )

                st.rerun()


        else:

            st.info(
                "No Backup Files Found"
            )
