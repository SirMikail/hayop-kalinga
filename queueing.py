import streamlit as st
import pandas as pd
import time
import json
from streamlit_autorefresh import st_autorefresh

# Function to persist state
def load_queues():
    try:
        with open('queues.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "waiting_queue": [],
            "now_serving": None,
            "wellness": [],
            "checkup": [],
            "emergency": [],
            "surgery": []
        }

def save_queues(queues):
    with open('queues.json', 'w') as f:
        json.dump(queues, f)

# Load persisted queues
queues = load_queues()


def render_card(client, owner, time="", bg_color="white", text_color="black", width="300px", height="100px"):
    card_style = f"""
        <div style='
            background-color: {bg_color};
            border-radius: 15px;
            padding: 10px;
            width: {width};
            height: {height};
            text-align: center;
            color: {text_color};
            display: flex;
            justify-content: center;
            align-items: center;
            border: 4px solid #45B08C;
            animation: blink 1s infinite; /* Blinking effect */
        '>
            {client} </br>
            {owner} </br>
            {time}
        </div>

        <style>
        @keyframes blink {{
            0%, 100% {{
                border-color: #45B08C;
            }}
            50% {{
                border-color: transparent; /* Change to transparent to create blinking effect */
            }}
        }}
        </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)


def render_aesthetic_tile(position, pet_name, pet_type="cat"):
    # Choose image based on pet type
    if pet_type.lower() == "dog":
        image_url = "https://www.kevinandkaia.com/uploads/1/2/6/1/126191832/s922489433528641189_p21_i36_w600.png"  # Dog image URL
    elif pet_type.lower() == "cat":
        image_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRbD2RPvrugMQqts43agdSLYp1s9dPhup-U1SHuI4ZmiaIdcUGzw3Q_2YopAOqCGayuFdw&usqp=CAU"  # Cat image URL
    else:
        image_url = "https://example.com/default_animated.gif"  # Default image

    tile_style = f"""
        <div style='
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 5px;  /* Added padding for better spacing */
        '>
            <img src='{image_url}' alt='{pet_type}' style='width: 100px; height: 100px; object-fit: cover; border-radius: 10px;'/>
            <h2 style='font-size: 18px; color: #3A3A3A;'>#{position}</h2><p style='font-size: 18px; color: #3A3A3A;'>{pet_name}</p>
        </div>
    """
    return tile_style



# Admin View
def admin_view():
    st.title("Admin View")
    with st.form("add_client_form"):
        pet_name = st.text_input("Pet Name")
        guardian_name = st.text_input("Guardian Name")
        animal_type = st.text_input("Animal Type")
        add_client_btn = st.form_submit_button("Add Client to Waiting Queue")

    if add_client_btn and pet_name and guardian_name:
        queues["waiting_queue"].append({
            "pet_name": pet_name,
            "guardian_name": guardian_name,
            "animal_type": animal_type,
            "time_added": time.time()
        })
        save_queues(queues)
        st.success(f"{pet_name} added to waiting queue")

    # Display all clients in the waiting queue
    if queues["waiting_queue"]:
        st.header("Waiting Queue")
        for i, client in enumerate(queues["waiting_queue"]):
            elapsed_time = int(time.time() - client["time_added"])
            # edit this for admin view
            render_card(client=client['pet_name'].upper(),
                        owner=client['guardian_name'].upper(),
                        time=f"Waited: {elapsed_time} seconds",
                        bg_color="#90EE90",  # Light green
                        text_color="black",
                        width="350px",
                        height="100px")
    
    if queues["now_serving"]:
        st.header("Now Serving")
        render_card(client=queues['now_serving']['pet_name'].upper(),
                    owner=queues['now_serving']['guardian_name'].upper(),
                    time="",
                    bg_color="#90EE90",  # Light green
                    text_color="black",
                    width="350px",
                    height="100px")
    
    # Remove Client from Waiting Queue
    if queues["waiting_queue"]:
        st.header("Remove Client from Waiting Queue")
        client_names = [f"{client['pet_name']} ({client['guardian_name']})" for client in queues["waiting_queue"]]
        client_to_remove = st.selectbox("Select Client to Remove", client_names)
        if st.button("Remove Client"):
            queues["waiting_queue"] = [client for client in queues["waiting_queue"] if f"{client['pet_name']} ({client['guardian_name']})" != client_to_remove]
            save_queues(queues)
            st.success(f"{client_to_remove} has been removed from the waiting queue.")

    if queues["waiting_queue"]:
        if st.button("Serve Next Client"):
            queues["now_serving"] = queues["waiting_queue"].pop(0)
            save_queues(queues)

    # Assign client from "Now Serving" to an assignment queue
    if queues["now_serving"]:
        assign_queue = st.selectbox("Assign to Queue", ["Wellness", "Checkup", "Emergency", "Surgery"])
        if st.button("Assign to Queue"):
            queues[assign_queue.lower()].append({
                "pet_name": queues["now_serving"]["pet_name"],
                "guardian_name": queues["now_serving"]["guardian_name"],
                "time_assigned": time.time()
            })
            queues["now_serving"] = None
            save_queues(queues)

    # Remove client from any assignment queue
    st.header("Remove Client from Assignment Queues")
    for queue_name in ["Wellness", "Checkup", "Emergency", "Surgery"]:
        if queues[queue_name.lower()]:
            client_names = [f"{client['pet_name']} ({client['guardian_name']})" for client in queues[queue_name.lower()]]
            client_to_remove = st.selectbox(f"Remove from {queue_name} Queue", client_names, key=f"remove_{queue_name}")
            if st.button(f"Remove from {queue_name}", key=f"remove_{queue_name}_btn"):
                queues[queue_name.lower()] = [client for client in queues[queue_name.lower()] if f"{client['pet_name']} ({client['guardian_name']})" != client_to_remove]
                save_queues(queues)


# Client View
def client_view():
    # Waiting Queue
    st.markdown("<h3 style='text-align: center;'>Waiting Queue</h3>", unsafe_allow_html=True)
    with st.container():
        if queues["waiting_queue"]:
            num_columns = 4
            columns = st.columns(num_columns)

            # Generate the tiles for each column
            for i, client in enumerate(queues["waiting_queue"]):
                position = i + 1
                tile = render_aesthetic_tile(position=position, pet_name=client['pet_name'].upper())
                
                # Place the tile in the appropriate column
                col_index = i % num_columns
                columns[col_index].markdown(tile, unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align: center;'>No clients in waiting queue</p>", unsafe_allow_html=True)

    # Now Serving
    st.markdown("<h3 style='text-align: center;'>Now Serving</h3>", unsafe_allow_html=True)
    if queues["now_serving"]:
        render_card(client=queues['now_serving']['pet_name'].upper(),
                    owner=queues['now_serving']['guardian_name'].upper(),
                    time="",
                    text_color="black",
                    width="350px",
                    height="100px")
    else:
        st.markdown("<p style='text-align: center;'>No clients can be served at the moment</p>", unsafe_allow_html=True)

    # Create a 2x2 grid of columns
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # Wellness Queue (top-left quadrant)
    with col1:
        st.markdown("<h3 style='text-align: center;'>Wellness</h3>", unsafe_allow_html=True)
        if queues["wellness"]:
            for client in queues["wellness"]:
                elapsed_time = int(time.time() - client["time_assigned"])
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = ""
                if hours > 0:
                    formatted_time += f"{hours}H "
                if minutes > 0:
                    formatted_time += f"{minutes}M "
                if seconds > 0:
                    formatted_time += f"{seconds}S "
                render_card(client=client['pet_name'].upper(),
                            owner=client['guardian_name'].upper(),
                            time=formatted_time,
                            bg_color="#90EE90",  # Light green
                            text_color="black",
                            width="350px",
                            height="100px")
        else:
            st.write("<p style='text-align: center;'>No clients in the wellness queue</p>", unsafe_allow_html=True)

    # Checkup Queue (top-right quadrant)
    with col2:
        st.markdown("<h3 style='text-align: center;'>Checkup</h3>", unsafe_allow_html=True)
        if queues["checkup"]:
            for client in queues["checkup"]:
                elapsed_time = int(time.time() - client["time_assigned"])
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = ""
                if hours > 0:
                    formatted_time += f"{hours}H "
                if minutes > 0:
                    formatted_time += f"{minutes}M "
                if seconds > 0:
                    formatted_time += f"{seconds}S "
                render_card(client=client['pet_name'].upper(),
                            owner=client['guardian_name'].upper(),
                            time=formatted_time,
                            bg_color="#90EE90",  # Light green
                            text_color="black",
                            width="350px",
                            height="100px")
        else:
            st.write("<p style='text-align: center;'>No clients in the checkup queue</p>", unsafe_allow_html=True)

    # Emergency Queue (bottom-left quadrant)
    with col3:
        st.markdown("<h3 style='text-align: center;'>Emergency</h3>", unsafe_allow_html=True)
        if queues["emergency"]:
            for client in queues["emergency"]:
                elapsed_time = int(time.time() - client["time_assigned"])
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = ""
                if hours > 0:
                    formatted_time += f"{hours}H "
                if minutes > 0:
                    formatted_time += f"{minutes}M "
                if seconds > 0:
                    formatted_time += f"{seconds}S "
                render_card(client=client['pet_name'].upper(),
                            owner=client['guardian_name'].upper(),
                            time=formatted_time,
                            bg_color="#90EE90",  # Light green
                            text_color="black",
                            width="350px",
                            height="100px")
        else:
            st.write("<p style='text-align: center;'>No clients in the emergency queue</p>", unsafe_allow_html=True)
    # Surgery Queue (bottom-right quadrant)
    with col4:
        st.markdown("<h3 style='text-align: center;'>Surgery</h3>", unsafe_allow_html=True)
        if queues["surgery"]:
            for client in queues["surgery"]:
                elapsed_time = int(time.time() - client["time_assigned"])
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = ""
                if hours > 0:
                    formatted_time += f"{hours}H "
                if minutes > 0:
                    formatted_time += f"{minutes}M "
                if seconds > 0:
                    formatted_time += f"{seconds}S "
                render_card(client=client['pet_name'].upper(),
                            owner=client['guardian_name'].upper(),
                            time=formatted_time,
                            bg_color="#90EE90",  # Light green
                            text_color="black",
                            width="350px",
                            height="100px")
        else:
            st.write("<p style='text-align: center;'>No clients in the surgery queue</p>", unsafe_allow_html=True)


# Choose view
view = st.sidebar.selectbox("Select View", ["Admin", "Client"])

if view == "Admin":
    admin_view()
else:
    client_view()

# Autorefresh
st_autorefresh(interval=1000, key="queue_refresh")
