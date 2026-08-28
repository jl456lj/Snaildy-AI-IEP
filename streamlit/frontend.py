import streamlit as st
import requests
import json
import os

API_URL = os.getenv("API_URL")

st.set_page_config(
    page_title="AI-IEP, Snaildy",
    page_icon="🤖"
)


st.title("Snaildy AI-IEP program")

st.write(
    "This program generates an IEP for each SEN schoolchildren."
)

with st.form("student", enter_to_submit=False):
    name = st.text_input("Student Name:")
    gradeAge = st.text_input("Age:")
    className = st.text_input("Grade:")
    st.write("SEN category")
    senUnconfirmed = st.text_area("Unconfirmed:")
    senConfirmed = st.text_area("Confirmed:")
    strengthsWeaknesses = st.text_area("Strengths and Weaknesses:")

    if "iep_result" not in st.session_state:    # Initialize state.
        st.session_state["iep_result"] = None

    if "student_name" not in st.session_state:
        st.session_state["student_name"] = ""

    submitted = st.form_submit_button("Submit")
    if submitted:
        student_context = f"""
            【基本資料】
            - 姓名: {name}
            - 年級/年齡: {className} / {gradeAge}

            【特殊教育需要 (SEN) 狀況】
            - 未確定: {senUnconfirmed}
            - 已確定: {senConfirmed}


            【強弱項與性格描述】
            {strengthsWeaknesses}

            """
        try:
            with st.spinner("Generating IEP..."):
                response = requests.post(
                    url=f"http://{API_URL}:8000/chat",
                    json={
                        "context": student_context,
                    },
                    timeout=600
                )

                response.raise_for_status()

                result = response.json()

            st.session_state.iep_result = result
            st.session_state.student_name = name
            st.success("IEP generated successfully!")


        except requests.exceptions.Timeout:

            st.error(
                "The FastAPI server took too long to respond."
            )
        except requests.exceptions.ConnectionError:
            st.error(
                "Unable to connect to FastAPI. "
                "Please make sure FastAPI is running."
            )
        except requests.exceptions.HTTPError as e:
            st.error(
                f"FastAPI returned an error: {e}\n\n"
                f"{response.text}"
            )
        except requests.exceptions.RequestException as e:
            st.error(
                f"Request failed: {e}"
            )
# =========================
# Display Result
# =========================

if st.session_state.iep_result is not None:
    st.subheader("Generated IEP")
    st.json(
        st.session_state.iep_result
    )

    # Convert dictionary → JSON string
    json_data = json.dumps(
        st.session_state.iep_result,
        ensure_ascii=False,
        indent=2
    )

    # This is OUTSIDE the form
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name=f"{st.session_state.student_name}.json",
        mime="application/json"
    )
