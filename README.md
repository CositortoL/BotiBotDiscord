# Discord Bot for Promotions Management

![Discord Bot](https://example.com/discord-bot-image.png)

This Discord bot is designed to manage promotions in a server. It allows users to add, edit, delete, and view promotions. It also checks for expired promotions and sends notifications to the server. The bot uses Google Sheets as a database to store the promotions and MongoDB for replica and backup.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repository:
    ```
    git clone https://github.com/yourusername/discord-bot.git
    ```
2. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```
3. Create a `.env` file in the root directory of the project and add the following environment variables:
    ```
    DISCORD_TOKEN=your-discord-token
    GOOGLE_SHEETS_API_KEY=your-google-sheets-api-key
    MONGODB_CONNECTION_STRING=your-mongodb-connection-string
    ```
4. Run the bot:
    ```
    python bot.py
    ```

## Usage

The bot supports the following commands:

- `/promocion`: Starts a dialogue with the user to add a new promotion. The user must have the ability to receive direct messages from server members.

- `/ver_promociones`: Displays all the current promotions in the server.

- `/eliminar_promocion <UUID>`: Deletes a promotion with the specified UUID. This command can only be used by users with the 'ADMIN'roles.

- `/ver_logs`: Displays all the log records. This command can only be used by users with the 'ADMIN' roles.

- `/editar_registro <UUID>`: Starts a dialogue with the user to edit a promotion with the specified UUID. This command can only be used by users with the 'ADMIN' roles.

- `/replica`: Checks for differences between the Google Sheets database and the MongoDB database and updates the MongoDB database accordingly. This command can only be used by users with the 'ADMIN' role.

The bot also performs a task every 7 days to check for expired promotions and sends notifications to the server.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
