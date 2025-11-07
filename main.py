import requests
import subprocess
import sys
import re
import time

def respond(response, port, channel_index=0, chunk_size=200):
    print(f"Responding with message: {response}")

    disclaimer = "\n\n## Disclaimer\n*Please exercise extreme caution when utilizing this device, as it is not perfect and relies on a limited offline communication system - think twice before relying solely on this last-ditch option, and always prioritize other means of safety.*"
    response += disclaimer
    if len(response) <= chunk_size:
        result = subprocess.run(["meshtastic", "--port", port, "--ch-index", str(channel_index), "--sendtext", response], 
                               capture_output=True, text=True)
        return

    while len(response) > 0: 
        if len(response) <= chunk_size:
            chunk = response
        else:
            chunk = response[:chunk_size] + " *...*"
        response = response[chunk_size:]
        result = subprocess.run(["meshtastic", "--port", port, "--ch-index", str(channel_index), "--sendtext", chunk], 
                               capture_output=True, text=True)
        print("Sending:", chunk)
        time.sleep(1)

def prompt_ai(question, ai_model="llama3.2"):
    url = "http://localhost:11434/api/generate"
    prompt = f"""
    You are MeshRanger AI, an offline emergency guide for remote areas using a lora mesh to communicate over long distances using low power radio.
    The goal is for national parks and others to purchase these devices that they can deploy in high locations in remote areas to provide a saftey net of information to hikers and such.
    The whole device will be a heltec v3 meshtastic device connected to a raspberry pi 5 most likely which will run a ollama model prompt engineered to be a kind of guide.

    Rules:

        You have no internet. Never claim to know real-time weather, maps, or news. State this limitation clearly when relevant.

        Focus on actionable survival info: first aid, navigation, shelter, water, and hazard identification.

        You cannot contact any emergency services.

        Prioritize life-threatening issues first. Give clear, step-by-step commands.

        Be calm and definitive.

        When in doubt, advise on general principles and the urgency of seeking help.

        Keep responses concise and to the point, max of 5 sentences.

    """
    question = prompt + "\nUser message: " + question
    data = {
        "model": ai_model,
        "prompt": question,
        "stream": False
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json().get('response', 'No response field found')
    else:
        print("Error:", response.status_code, response.text)

def listen(port, channel_index=0):
    print(f"Listening for messages...")
    
    while True:
        process = subprocess.Popen([
            "meshtastic", "--port", port, "--ch-index", str(channel_index), 
            "--listen"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        try:
            while True:
                line = process.stdout.readline()
                    
                line = line.strip()
                if "text:" in line.lower() or "payload:" in line.lower():
                    if re.match(r"^(payload:|text:)", line, re.IGNORECASE):
                        message = line.split(":", 1)[1].strip()

                        if len(message) > 1 and message[1] in ['\\', '/']:
                            print(f"🚫 Ignored command message: {message}")
                            continue

                        print(f"Received message: {message}")
                        
                        process.terminate()
                        process.wait()
                        
                        response = prompt_ai(message)
                        if response and len(response.strip()) > 0:
                            respond(response, port, channel_index)
                        
                        break
                    
        except KeyboardInterrupt:
            print("\nStopping...")
            process.terminate()
            break
        except Exception as e:
            print(f"Error in listening: {e}")
            process.terminate()

def main():
    # Should move this to a settings file that is loaded  in
    ai_model = "llama3.2"
    channel_index = 2
    port = "/dev/ttyUSB0"
    listen(port, channel_index)

if __name__ == "__main__":
    main()
