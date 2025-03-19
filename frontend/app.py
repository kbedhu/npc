import streamlit as st
import requests
from typing import List, Dict, Any
import json  # Import the json module
import re

st.title("NPC Soul App")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ("NPC Creation", "NPC Interaction", "List NPCs"))

# Fetch NPC list from backend for editing
response = requests.get("http://localhost:8000/npc/list")
npcs: list[dict[str, any]] = (
    response.json().get("npcs", []) if response.status_code == 200 else []
)
npc_names = [npc.get("name", "Unknown") for npc in npcs]
npc_ids = [npc.get("id", -1) for npc in npcs]

# Track the previously selected NPC
if "previous_npc" not in st.session_state:
    st.session_state["previous_npc"] = None

# NPC Creation and Editing Screen
if page == "NPC Creation":
    st.header("Create or Edit an NPC")

    # Dropdown to select an NPC to edit
    selected_npc_name = st.selectbox("Select NPC to Edit", ["Create New"] + npc_names)
    selected_npc = next((npc for npc in npcs if npc["name"] == selected_npc_name), None)
    print("selected_npc", selected_npc)
    print("selected_npc_name", st.session_state.get("name", selected_npc_name))

    # Check if the selected NPC has changed
    if st.session_state["previous_npc"] != selected_npc_name:
        # Clear form fields
        st.session_state["name"] = ""
        st.session_state["background"] = ""
        st.session_state["appearance"] = ""
        # Update the previous NPC
        st.session_state["previous_npc"] = selected_npc_name

    with st.form("npc_creation_form"):
        # Use tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Overview", "Personality", "Cognition", "Dialogue"]
        )

        with tab1:
            name = st.text_input(
                "Name",
                # value=st.session_state.get(
                #     "name", selected_npc["name"] if selected_npc else ""
                # ),
                value=selected_npc["name"] if selected_npc else "",
                help="Enter the NPC's name",
            )
            background = st.text_area(
                "Background",
                # value=st.session_state.get(
                #     "background", selected_npc["background"] if selected_npc else ""
                # ),
                value=selected_npc["background"] if selected_npc else "",
                help="Enter the NPC's background",
            )
            appearance = st.text_area(
                "Appearance",
                # value=st.session_state.get(
                #     "appearance", selected_npc["appearance"] if selected_npc else ""
                # ),
                value=selected_npc["appearance"] if selected_npc else "",
                help="Describe the NPC's appearance",
            )

        with tab2:
            emotional_traits = st.text_area(
                "Emotional Traits",
                value=(
                    selected_npc["personality"].split(", ")[0] if selected_npc else ""
                ),
                help="Describe emotional traits",
            )
            behavioral_traits = st.text_area(
                "Behavioral Traits",
                value=(
                    selected_npc["personality"].split(", ")[1] if selected_npc else ""
                ),
                help="Describe behavioral traits",
            )
            current_state = st.text_input(
                "Current State", help="Enter the current state of the NPC"
            )

        with tab3:
            goals = st.text_area(
                "Goals",
                value=selected_npc["goals"] if selected_npc else "",
                help="Enter the NPC's goals",
            )
            knowledge = st.text_area("Knowledge", help="Enter the NPC's knowledge")
            assets = st.text_area(
                "Assets",
                value=selected_npc["assets"] if selected_npc else "",
                help="Enter the NPC's assets",
            )
            memory = st.text_area(
                "Memory",
                value=selected_npc["memory"] if selected_npc else "",
                help="Enter the NPC's memory",
            )

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
        submitted = st.form_submit_button("Save NPC")
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
            if selected_npc:
                # Update existing NPC
                response = requests.put(
                    f"http://localhost:8000/npc/update/{selected_npc['id']}",
                    json=npc_data,
                )
                if response.status_code == 200:
                    st.success("NPC updated successfully!")
                else:
                    st.error("Failed to update NPC.")
            else:
                # Create new NPC
                response = requests.post(
                    "http://localhost:8000/npc/create", json=npc_data
                )
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

        # print("npc_details", npcs[npc_id])
        # Initialize chat history
        # print("coming here 1", st.session_state)
        if "chat_history" not in st.session_state:
            # print("coming here 2")
            st.session_state["chat_history"] = []

        # Ensure chat history is scrollable and latest messages are visible
        chat_container = st.container()
        # print("coming here 3", st.session_state)
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

        # Fetch latest interactions with the selected NPC
        interactions_response = requests.get(
            f"http://localhost:8000/npc/interactions/{npc_id}"
        )
        if interactions_response.status_code == 200:
            interactions = interactions_response.json().get("interactions", [])
            print("interactions LENGTH************:", len(interactions))
            # Format last 10 interactions for the prompt
            interaction_history = "\n".join(
                f"You: {interaction['player_input']}\nNPC: {interaction['npc_response']}"
                for interaction in interactions[-10:]
            )
        else:
            interaction_history = ""

        print("interaction_history", interaction_history)

        # Define a callback function to clear the input field
        def clear_input():
            player_input = st.session_state["player_input"]

            if player_input:
                st.session_state["chat_history"].append(f"**You**: {player_input}")
                chat_history.markdown(
                    "<br>".join(st.session_state["chat_history"]),
                    unsafe_allow_html=True,
                )
                # Include interaction history in the prompt
                prompt = f"{interaction_history}\n"
                # Add player details like name, background, appearance, personality, goals, and assets to the prompt
                prompt += f"The details of the character{npc_selection} are formatted like a JSON \n"
                prompt += f"The JSON is: {npcs[npc_names.index(npc_selection)]}"
                prompt += f"Respond with the short, sweet response to the player's input in context of the character and interaction history"
                prompt += f"You are {npc_selection}. Answer as if you were speaking directly, without narrating any actions or emotions."
                # prompt += f"Respond with a JSON object with the following keys: 'npc_screenplay', 'npc_response'"
                # prompt += f"The 'npc_screenplay' key should contain how NPC reacts to the player's input"
                # prompt += f"The 'npc_response' key should contain the NPC's verbose response to the player's input"
                player_input = f"\n The player's input is: {player_input}"
                # print("prompt", prompt)
                # print prompt length
                # print("prompt length", len(prompt))
                response = requests.post(
                    f"http://localhost:8000/npc/interact/{npc_id}",
                    json={"player_input": player_input, "prompt_context": prompt},
                )
                print("response", response.text)
                if response.status_code == 200:
                    # Extract the JSON string from the response
                    response_text = response.text.strip()
                    # print("response_text", response_text)
                    response_json = json.loads(response_text)
                    # print("response_json hear me\n\n", response_json["npc_response"])
                    response_json = response_json["npc_response"]
                    # print("response_json\n\n", response_json)
                    # start = response_json.find("{")
                    # end = response_json.rfind("}")
                    # print("start", start)
                    # print("end", end)
                    # # Extract the content
                    # if start != -1 and end != -1:
                    #     json_str = response_json[start : end + 1]
                    #     json_str = json_str.replace("\n", "")
                    #     # print(json_str)
                    # print("json_str", json_str)
                    # if json_str:

                    try:
                        # response_json = json.loads(json_str)  # Parse the JSON string
                        # check if the response_json is a dictionary

                        # if isinstance(response_json, dict):
                        #     npc_response = response_json["npc_response"]
                        #     # print("npc_response is dict", response_json)

                        print("Final response:::\n", response_json)
                        st.session_state["chat_history"].append(
                            # f"**{npc_selection}**: {response_json}<br>"
                            f"{response_json}<br>"
                        )
                        chat_history.markdown(
                            "<br><br>".join(st.session_state["chat_history"]),
                            unsafe_allow_html=True,
                        )
                    except json.JSONDecodeError:
                        st.error("Failed to parse NPC response.")
                    # else:
                    #     st.error("Unexpected response format.")
                else:
                    st.error(f"Failed to get NPC response. {response}")
            st.session_state["player_input"] = ""

        # Create a container at the bottom for input
        with st.container():
            # Input for player message
            player_input = st.text_input(
                "Your Input", key="player_input", on_change=clear_input
            )

# Add a new page for listing NPCs
if page == "List NPCs":
    st.title("List of Created NPCs")
    response = requests.get("http://localhost:8000/npc/list")
    if response.status_code == 200:
        npcs = response.json().get("npcs", [])
        # Filter out NPCs with null or empty personality
        npcs = [npc for npc in npcs if npc.get("personality")]
        if npcs:
            for npc in npcs:
                st.subheader(npc.get("name", "Unknown"))
                st.write(f"Background: {npc.get('background', 'N/A')}")
                st.write(f"Appearance: {npc.get('appearance', 'N/A')}")
                st.write(f"Personality: {npc.get('personality', 'N/A')}")
                st.write(f"Goals: {npc.get('goals', 'N/A')}")
                st.write(f"Assets: {npc.get('assets', 'N/A')}")
                st.write(f"Memory: {npc.get('memory', 'N/A')}")
                st.write("---")
        else:
            st.write("No NPCs found.")
    else:
        st.error("Failed to retrieve NPCs.")
