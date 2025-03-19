import streamlit as st
import requests

st.title("NPC Soul App")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ("NPC Creation", "NPC Interaction", "List NPCs"))

# NPC Creation Screen
if page == "NPC Creation":
    st.header("Create a New NPC")
    with st.form("npc_creation_form"):
        # Use tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Overview", "Personality", "Cognition", "Dialogue"]
        )

        with tab1:
            name = st.text_input("Name", help="Enter the NPC's name")
            background = st.text_area("Background", help="Enter the NPC's background")
            appearance = st.text_area(
                "Appearance", help="Describe the NPC's appearance"
            )

        with tab2:
            emotional_traits = st.text_area(
                "Emotional Traits", help="Describe emotional traits"
            )
            behavioral_traits = st.text_area(
                "Behavioral Traits", help="Describe behavioral traits"
            )
            current_state = st.text_input(
                "Current State", help="Enter the current state of the NPC"
            )

        with tab3:
            goals = st.text_area("Goals", help="Enter the NPC's goals")
            knowledge = st.text_area("Knowledge", help="Enter the NPC's knowledge")
            assets = st.text_area("Assets", help="Enter the NPC's assets")
            memory = st.text_area("Memory", help="Enter the NPC's memory")

        with tab4:
            text_attributes = st.text_area(
                "Text Attributes", help="Enter text attributes"
            )
            audio_attributes = st.text_area(
                "Audio Attributes", help="Enter audio attributes"
            )

        # Ensure mandatory fields are filled
        if not name or not background or not emotional_traits or not behavioral_traits:
            st.warning("Please fill in all mandatory fields.")
        submitted = st.form_submit_button("Create NPC")
        if submitted:
            # Send data to backend
            npc_data = {
                "name": name,
                "personality": emotional_traits + ", " + behavioral_traits,
                "background": background,
                "appearance": appearance,
                "goals": goals,
                "assets": assets,
                "memory": memory,
            }
            response = requests.post("http://localhost:8000/npc/create", json=npc_data)
            if response.status_code == 200:
                st.success("NPC created successfully!")
            else:
                st.error("Failed to create NPC.")

# NPC Interaction Screen
elif page == "NPC Interaction":
    st.header("Interact with NPCs")
    # Fetch NPC list from backend
    response = requests.get("http://localhost:8000/npc/list")
    if response.status_code == 200:
        npcs = response.json().get("npcs", [])
        npc_names = [npc["name"] for npc in npcs]
        npc_ids = [npc["id"] for npc in npcs]
        npc_selection = st.selectbox("Select NPC", options=npc_names)
        npc_id = npc_ids[npc_names.index(npc_selection)]

        # Initialize chat history
        print("coming here 1", st.session_state)
        if "chat_history" not in st.session_state:
            print("coming here 2")
            st.session_state["chat_history"] = []

        # Ensure chat history is scrollable and latest messages are visible
        chat_container = st.container()
        print("coming here 3", st.session_state)
        # with chat_container:
        #     # Apply the CSS class to the container
        #     st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        #     chat_history = st.empty()
        #     # Use HTML line breaks for new lines
        #     chat_history.markdown(
        #         "<br>".join(st.session_state["chat_history"]), unsafe_allow_html=True
        #     )
        #     st.markdown("</div>", unsafe_allow_html=True)
        #     print("coming here 4", "Chat history added")
        with chat_container:
            # Apply the CSS class to the container
            chat_history = st.empty()
            # Format chat history with extra newline after NPC responses
            formatted_chat = "<br>".join(
                f"{msg}<br>" if msg.startswith("**NPC**:") else msg
                for msg in st.session_state.get("chat_history", [])
            )
            chat_history.markdown(formatted_chat, unsafe_allow_html=True)

            # chat_history.markdown(
            #     "<br>".join(st.session_state.get("chat_history", [])),
            #     unsafe_allow_html=True,
            # )

        # Define a callback function to clear the input field
        def clear_input():
            player_input = st.session_state["player_input"]

            if player_input:
                st.session_state["chat_history"].append(f"**You**: {player_input}")
                chat_history.markdown(
                    "<br>".join(st.session_state["chat_history"]),
                    unsafe_allow_html=True,
                )
                response = requests.post(
                    f"http://localhost:8000/npc/interact/{npc_id}",
                    json={"player_input": player_input},
                )
                if response.status_code == 200:
                    npc_response = response.json().get("npc_response", "")
                    st.session_state["chat_history"].append(
                        f"**{npc_selection}**: {npc_response}<br>"
                    )
                    chat_history.markdown(
                        "<br><br>".join(st.session_state["chat_history"]),
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(f"Failed to get NPC response. {response}")
            st.session_state["player_input"] = ""

        # Create a container at the bottom for input
        with st.container():
            # Input for player message
            player_input = st.text_input(
                "Your Input", key="player_input", on_change=clear_input
            )

        # Button to send the message
        # submit_button = st.button("Send")

        # if submit_button and player_input:
        # if player_input:
        # Display the player's message immediately
        # st.session_state["chat_history"].append(f"**You**: {player_input}")
        # chat_history.markdown(
        #     "<br>".join(st.session_state["chat_history"]), unsafe_allow_html=True
        # )

        # Send player input to backend
        # response = requests.post(
        #     f"http://localhost:8000/npc/interact/{npc_id}",
        #     json={"player_input": player_input},
        # )
        # clear the input field using the clear_input function
        # clear_input()
        # if response.status_code == 200:
        #     npc_response = response.json().get("npc_response", "")
        #     # Update chat history with NPC response
        #     st.session_state["chat_history"].append(
        #         f"**{npc_selection}**: {npc_response}"
        #     )
        #     chat_history.markdown(
        #         "<br>".join(st.session_state["chat_history"]),
        #         unsafe_allow_html=True,
        #     )
        #     # Clear the input field after successful submission
        #     # clear_input()
        # else:
        #     st.error(f"Failed to get NPC response. {response}")

    # # Load interactions with the selected character only
    # st.session_state["chat_history"] = [
    #     chat
    #     for chat in st.session_state["chat_history"]
    #     if f"**NPC**: {npc_selection}" in chat
    # ]

# Add a new page for listing NPCs
if page == "List NPCs":
    st.title("List of Created NPCs")
    response = requests.get("http://localhost:8000/npc/list")
    # print(response.json())
    if response.status_code == 200:
        npcs = response.json().get("npcs", [])
        # Filter out NPCs with null or empty personality
        npcs = [npc for npc in npcs if npc["personality"]]
        if npcs:
            for npc in npcs:
                st.subheader(npc["name"])
                st.write(f"Personality: {npc['personality']}")
                st.write(f"Goals: {npc['goals']}")
                st.write(f"Assets: {npc['assets']}")
                st.write(f"Memory: {npc['memory']}")
                st.write("---")
        else:
            st.write("No NPCs found.")
    else:
        st.error("Failed to retrieve NPCs.")
