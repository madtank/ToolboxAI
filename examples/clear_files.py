import streamlit as st

# Initialize session state keys
if 'uploader_key' not in st.session_state:
    st.session_state['uploader_key'] = 0
if 'last_uploaded_file' not in st.session_state:
    st.session_state['last_uploaded_file'] = None

# Title of the application
st.title("Chatbot with Auto-Clearing File Upload")

# Chat messages container
chat_container = st.container()

# File uploader
uploaded_file = st.file_uploader("Upload a file", key=f"uploader_{st.session_state['uploader_key']}")

# Display the uploaded file name
if uploaded_file is not None:
    st.write("Uploaded file:", uploaded_file.name)
    # Store the uploaded file in session state
    if st.session_state['last_uploaded_file'] != uploaded_file.name:
        st.session_state['last_uploaded_file'] = uploaded_file.name
        st.write("New file uploaded and ready for processing.")
else:
    st.write("No file uploaded.")

# Chat input
if prompt := st.chat_input("Ask me anything!"):
    with chat_container:
        st.write(f"User: {prompt}")
        
        # Process the uploaded file if it exists
        if uploaded_file is not None:
            # Add your file processing logic here
            st.write(f"Processing file: {uploaded_file.name}")
            # Reset the uploader after processing
            st.session_state['uploader_key'] += 1
            st.session_state['last_uploaded_file'] = None
            st.rerun()
        
        # Add your chatbot response logic here
        # st.write("Chatbot: Your response here")