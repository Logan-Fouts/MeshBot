import argparse
import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


DEFAULT_SYSTEM_PROMPT = """
You are MeshBot Ranger Assist, an offline field-support assistant operated by a parks department.

Operating constraints:
- You have no internet and no access to real-time weather, maps, incidents, or closures.
- You cannot dispatch emergency responders or confirm that a message reached staff.
- You run on a low-bandwidth LoRa mesh, so responses must be short, practical, and reliable.

Response rules:
- Prioritize immediate safety, first aid, navigation, shelter, water, wildfire smoke, heat, cold, and wildlife hazards.
- If a user describes a medical emergency, severe injury, wildfire threat, missing person situation, or imminent danger, tell them to seek direct emergency help immediately if any human contact path exists.
- Give step-by-step guidance using short sentences and plain language.
- Never present guesses as facts.
- Keep the response under 5 sentences.
""".strip()


@dataclass
class Settings:
    ai_model: str = "phi3:mini"
    ollama_url: str = "http://localhost:11434/api/generate"
    port: str = "COM3"
    channel_index: int = 1
    chunk_size: int = 180
    send_delay_seconds: float = 1.0
    request_timeout_seconds: int = 30
    max_user_message_length: int = 500
    listen_restart_delay_seconds: float = 2.0
    log_level: str = "INFO"
    disclaimer: str = (
        "Safety notice: This device provides general offline guidance only. "
        "Use official signage, ranger instructions, radios, phones, or emergency beacons first whenever available."
    )
    system_prompt: str = DEFAULT_SYSTEM_PROMPT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MeshBot Ranger Assist for Meshtastic deployments."
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to a JSON configuration file.",
    )
    return parser.parse_args()


def load_settings(config_path: str) -> Settings:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}. Copy config.example.json to config.json and update it."
        )

    with path.open("r", encoding="utf-8") as config_file:
        config_data = json.load(config_file)

    return Settings(**config_data)


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def split_message(message: str, chunk_size: int) -> list[str]:
    chunks = []
    remaining = message.strip()

    while remaining:
        if len(remaining) <= chunk_size:
            chunks.append(remaining)
            break

        split_at = remaining.rfind(" ", 0, chunk_size)
        if split_at <= 0:
            split_at = chunk_size

        chunk = remaining[:split_at].rstrip()
        remaining = remaining[split_at:].lstrip()

        if remaining:
            chunk = f"{chunk} ..."

        chunks.append(chunk)

    return chunks


def run_meshtastic_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    command = ["meshtastic", *arguments]
    logging.debug("Running command: %s", " ".join(command))
    return subprocess.run(command, capture_output=True, text=True, check=False)


def respond(response: str, settings: Settings) -> None:
    full_response = f"{response.strip()}\n\n{settings.disclaimer}".strip()
    logging.info("Sending response with %s characters", len(full_response))

    for chunk in split_message(full_response, settings.chunk_size):
        result = run_meshtastic_command(
            [
                "--port",
                settings.port,
                "--ch-index",
                str(settings.channel_index),
                "--sendtext",
                chunk,
            ]
        )

        if result.returncode != 0:
            logging.error("Meshtastic send failed: %s", result.stderr.strip())
            break

        logging.info("Sent chunk: %s", chunk)
        time.sleep(settings.send_delay_seconds)


def build_prompt(message: str, settings: Settings) -> str:
    sanitized_message = message.strip()[: settings.max_user_message_length]
    return f"{settings.system_prompt}\n\nUser message: {sanitized_message}"


def prompt_ai(question: str, settings: Settings) -> Optional[str]:
    payload = {
        "model": settings.ai_model,
        "prompt": build_prompt(question, settings),
        "stream": False,
    }

    try:
        response = requests.post(
            settings.ollama_url,
            json=payload,
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        logging.error("AI request failed: %s", error)
        return None

    ai_response = response.json().get("response", "").strip()
    if not ai_response:
        logging.warning("AI response was empty")
        return None

    return ai_response


def extract_message(line: str) -> Optional[str]:
    stripped_line = line.strip()
    if not re.match(r"^(payload:|text:)", stripped_line, re.IGNORECASE):
        return None

    return stripped_line.split(":", 1)[1].strip()


def should_ignore_message(message: str) -> bool:
    if not message:
        return True

    if message.startswith(("/", "\\")):
        return True

    return False


def listen(settings: Settings) -> None:
    logging.info(
        "Listening on port %s channel %s", settings.port, settings.channel_index
    )

    while True:
        process = subprocess.Popen(
            [
                "meshtastic",
                "--port",
                settings.port,
                "--ch-index",
                str(settings.channel_index),
                "--listen",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        try:
            assert process.stdout is not None
            for raw_line in process.stdout:
                message = extract_message(raw_line)
                if message is None:
                    continue

                if should_ignore_message(message):
                    logging.info("Ignored command or empty message: %s", message)
                    continue

                logging.info("Received message: %s", message)
                process.terminate()
                process.wait(timeout=5)

                response = prompt_ai(message, settings)
                if response:
                    respond(response, settings)
                break
            else:
                logging.warning("Meshtastic listener exited without data")
        except KeyboardInterrupt:
            logging.info("Stopping listener")
            process.terminate()
            break
        except subprocess.TimeoutExpired:
            process.kill()
            logging.warning("Meshtastic listener did not shut down cleanly")
        except Exception as error:
            logging.exception("Unexpected listener error: %s", error)
            process.terminate()
        finally:
            if process.poll() is None:
                process.terminate()

        time.sleep(settings.listen_restart_delay_seconds)


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)
    configure_logging(settings.log_level)
    listen(settings)


if __name__ == "__main__":
    main()
