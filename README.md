# Cat20-Fractal-Telegram-Bot

## Overview
This bot enables users to retrieve CAT-20 token details, including minting progress and holder count, through Telegram.

## Features
- Retrieve CAT-20 token information via a designated API.
- Provide detailed minting progress and holder statistics in an organized message format.
- Facilitate minting, transferring, and deploying CAT-20 tokens.

## Setup

### Prerequisites
- Python 3.10.13 or higher
- Telegram bot token acquired from [BotFather](https://core.telegram.org/bots#botfather)
- API endpoint for CAT-20 token details

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/cat20-fractal-telegram-bot.git
   cd cat20-telegram
   ```
2. Create a `.env` file containing your Telegram bot token and API URL:
    ```python
    TELEGRAM_KITTYBOT_TOKEN="YOUR_TELEGRAM_KITTYBOT_TOKEN"
    TELEGRAM_KITTYMINTBOT_TOKEN="YOUR_TELEGRAM_KITTYMINTBOT_TOKEN"
    CAT20_API="http://127.0.0.1:3000/api"
    NODE_CLIENT_DIR="/home/therealkomrad/Documents/fractal1/cat-token-box/packages/cli"
    FRACTAL_MEMPOOL_API="https://mempool.fractalbitcoin.io/api"
    FEERANGE_INDEX=0  # Ranges from 0 (slowest) to 5 (fastest)
    ENCRYPTION_KEY_PATH="bot_config/key.key"

    MIN_HOTMINT=20 
    MAX_HOTMINT=99
    PREMINE_HOTMINT=0
    INTERVAL_HOTMINT=3600
    ```

3. Install dependencies:
    ```python
    pip install -r requirements.txt
    ```

4. Encryption

Generate an encryption key with:
```python
python3 cat20_telegram/KittyMintBot/generate_key.py
```

Set appropriate permissions:
```bash
chmod 600 cat20_telegram/KittyMintBot/bot_config/key.key
```

(Optional) Automate key rotation using a cron job:
```bash
crontab -e
0 0 1 * * /usr/bin/python3 /path/to/the/cat20_telegram/KittyMintBot/rotate_keys.py >> /path/to/the/cat20_telegram/KittyMintBot/key_rotation.log 2>&1
```

5. Launch the bot:
```python
python3 KittyBot.py
python3 KittyMintBot.py
```

## Usage
After initiating the bot, you can send the following commands:

### KittyBot Commands

To retrieve mempool fees:
```
/fees
```

To obtain token information:
```
/token <token_id>
```

To check wallet balance:
```
/balance <address>
```

To initiate background hot mint alerts (occurring every <interval> seconds):
```
/hotmint <interval>
```

To halt background hot mint alerts:
```
/stophotmint <interval>
```

### KittyMintBot Commands

To initiate minting:
```
/mint
```

To cease minting:
```
/stop_minting
```

To verify balances:
```
/check_balances
```

## Environment Setup

To establish the necessary environment for this project:

1. Ensure Conda is installed on your system.

2. Create a script named `setup_env.sh` in your project directory:
   ```bash
   #!/bin/bash
   
   PYTHON_VERSION=$(cat .python_version)
   conda create -n kittybot python=$PYTHON_VERSION -y
   conda activate kittybot
   pip install -r requirements.txt
   ```

3. Make the script executable:
   ```bash
   chmod +x setup_env.sh
   ```

4. Execute the script:
   ```bash
   ./setup_env.sh
   ```

5. After the script completes, activate the environment manually:
   ```bash
   conda activate kittybot
   ```
This will create a Conda environment named "kittybot" with the specified Python version and install all dependencies from `requirements.txt`.

### Customizing CAT-20 Bot with Ollama

This project leverages the [Ollama](https://ollama.com/) Llama 3.2 model for dynamic responses. Here's how to configure and customize it:

#### Step 1: Install Ollama
Refer to the installation guide on the [Ollama website](https://ollama.com/) for instructions.

#### Step 2: Create a Custom `Modelfile`
Establish a `Modelfile` that articulates the desired bot behavior and tone. Create a file named `Modelfile` in your project directory with the following specifications:

```modelfile
# Utilize the Llama 3.2 model as a foundational base
FROM llama3.2

# Set response creativity to be playful and engaging
PARAMETER temperature 0.9
# Enable a larger context window for enhanced conversational coherence
PARAMETER num_ctx 4096

# Define the system message to establish the bot's tone and role
SYSTEM """
You are a Telegram bot for a memecoin called KittyCash. You are friendly, fun, and filled with cat puns, responding with humor and enthusiasm for crypto topics, particularly those related to KittyCash. Keep responses concise, engaging, and informative while occasionally making playful remarks about KittyCash’s value, popularity, or benefits.
"""

# Set a template to delineate user and assistant messages
TEMPLATE """
{{ if .System }}<|start_header_id|>system<|end_header_id|>
{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>
{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>
{{ .Response }}<|eot_id|>
"""
```

#### Step 3: Create or Overwrite the Model in Ollama

Execute the following command to create or update the model with your custom settings:
```bash
ollama create kittybot-model -f ./Modelfile
```

#### Step 4: Verify the Model (Optional)

To confirm the model's functionality, test it by running:
```bash
ollama run kittybot-model
```

With this setup, your customized model will deliver tailored responses to Telegram bot commands, enhancing the overall experience for the CAT-20 memecoin community.

### Uploading Default Logo

To set a default logo for the bot, use the `upload_default_media.py` script to retrieve the `file_id` for `logo/default_cover.mp4`:

1. Execute the script:
   ```bash
   python3 upload_default_media.py
   ```

2. Update the `DEFAULT_COVER_FILE_ID` in your `.env` file with the acquired `file_id`.

# FastAPI API

To run the FastAPI API, execute the following command from the root directory:
```bash
python app/main.py
```
