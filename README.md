Updating the README to include both the client and server setup provides a comprehensive guide for users on how to run your chat application. Below is an enhanced README version that includes instructions for both the server and client components:

---

# Simple Chat Application

This repository contains a simple chat application written in Python. It includes both the server and client scripts, allowing users to set up their own chat server, connect as clients, choose nicknames, and send/receive messages in a multi-threaded environment.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/dadams-AU/simple-chat-client.git
   ```

2. Navigate to the cloned directory:
   ```bash
   cd simple-chat-client
   ```

## Server Setup

1. Locate your local IP address and open port 65432 (or any port you prefer).

2. Make sure you have Python 3 installed on your system.

3. To make the server script executable and set it to auto-start (optional), refer to the detailed steps provided in the documentation/comments within the repository.

4. Start the chat server by running:
   ```bash
   python3 server.py
   ```
   Ensure the server is running and listening for incoming connections on the indicated port before starting any clients.

## Client Setup

1. Ensure the chat server is running and accessible from the client machine.

2. If necessary, adjust your PATH environment variable to include the chat application directory (optional):
   ```bash
   export PATH=$PATH:/path/to/simple-chat-client
   ```

3. Run the chat client script on each client computer:
   ```bash
   python3 chat.py
   ```

4. When prompted, enter your desired nickname.

5. You're now ready to start chatting!

## Usage

- **Server**: The server needs to be started before any clients can connect. It listens for incoming connections and handles messages between clients.
- **Client**: After starting the client script, enter a nickname when prompted. Once connected, you can start sending messages to the chat, which will be broadcasted to all connected clients.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Feel free to contribute to both the server and client code or any documentation improvements.

## License

This project is licensed under the [MIT License](https://github.com/dadams-AU/simple-chat-client/blob/main/LICENSE).

---

This README provides a clear, structured guide for setting up and using both the server and client parts of your chat application. Feel free to adjust the instructions based on the actual paths, requirements, or any additional steps specific to your project.
