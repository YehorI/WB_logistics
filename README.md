# Launching the Bot

This guide provides instructions for launching the bot using either Poetry directly or Docker.

## Prerequisites

- Python 3.12 or later
- Poetry (for running without Docker)
- Docker (for running with Docker)

## Option 1: Running with Poetry

1. Clone the repository:
   ```
   git clone https://github.com/YehorI/wb_logi_bot.git
   cd wb_logi_bot
   ```

2. Install dependencies:
   ```
   poetry install
   ```

3. Run the bot:
   ```
   poetry run python -m app.main
   ```

## Option 2: Running with Docker

1. Clone the repository:
   ```
   git clone https://github.com/YehorI/WB_logistics.git
   cd wb_logi_bot
   ```

2. Build the Docker image:
   ```
   docker build -t wb_logi_bot .
   ```

3. Run the bot in a Docker container:
   ```
   docker run wb_logi_bot
   ```

## Configuration

Before running the bot, make sure to set up any necessary configuration:

1. Copy the example configuration file:
   ```
   cp .env.example .env
   ```

## Troubleshooting

If you encounter any issues:

1. Ensure all prerequisites are installed and up to date.
2. Check that all configuration settings in `config.yml` are correct.
3. If using Docker, make sure Docker is running on your system.

For more detailed information or if you encounter persistent issues, please refer to the full documentation or open an issue on the GitHub repository.
