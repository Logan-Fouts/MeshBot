#!/bin/bash

# Meshtastic AI Bot Script
# Listens for messages and responds using AI

# Configuration
AI_MODEL="llama3.2"
CHANNEL_INDEX=2
MAC_ADDRESS="10:51:DB:51:03:E1"
OLLAMA_URL="http://localhost:11434/api/generate"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to send message via Meshtastic
send_message() {
    local response="$1"
    echo -e "${BLUE}📤 Sending response...${NC}"
    meshtastic --ble "$MAC_ADDRESS" --ch-index "$CHANNEL_INDEX" --sendtext "$response"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Message sent successfully${NC}"
    else
        echo -e "${RED}❌ Failed to send message${NC}"
    fi
}

# Function to get AI response
get_ai_response() {
    local question="$1"
    local prompt="You are a survival bot working in a mesh offgrid network to provide potentially life saving information to people. Answer the following question in under 220 characters.: $question"
    
    echo -e "${YELLOW}🤔 Consulting AI...${NC}"
    
    # Make API request to Ollama
    response=$(curl -s -X POST "$OLLAMA_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$AI_MODEL\",
            \"prompt\": \"$prompt\",
            \"stream\": false
        }")
    
    # Check if curl was successful
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Error connecting to Ollama${NC}"
        return 1
    fi
    
    # Extract response using different methods
    local ai_response=""
    
    # Try to extract response field
    if command -v jq >/dev/null 2>&1; then
        ai_response=$(echo "$response" | jq -r '.response // . // empty' 2>/dev/null)
    else
        # Fallback: use grep/sed if jq is not available
        ai_response=$(echo "$response" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"//')
        if [ -z "$ai_response" ]; then
            ai_response=$(echo "$response" | head -1)
        fi
    fi
    
    if [ -z "$ai_response" ]; then
        echo -e "${RED}❌ No response from AI${NC}"
        echo "Raw response: $response"
        return 1
    fi
    
    # Trim to 220 characters for Meshtastic
    ai_response=$(echo "$ai_response" | cut -c1-220)
    echo "$ai_response"
}

# Function to listen for messages
listen_for_messages() {
    echo -e "${GREEN}📡 Starting Meshtastic AI Bot${NC}"
    echo -e "Device: $MAC_ADDRESS"
    echo -e "Channel: $CHANNEL_INDEX"
    echo -e "AI Model: $AI_MODEL"
    echo -e "Press Ctrl+C to stop\n"
    
    # Counter for received messages
    local message_count=0
    
    while true; do
        echo -e "${YELLOW}👂 Listening for messages...${NC}"
        
        # Listen for messages and filter for text content
        meshtastic --ble "$MAC_ADDRESS" --ch-index "$CHANNEL_INDEX" --listen 2>&1 | \
        while IFS= read -r line; do
            # Check if line contains a text message
            if echo "$line" | grep -q -E "text.:|payload.:"; then
                message_count=$((message_count + 1))
                echo -e "\n${GREEN}=== Message #$message_count ===${NC}"
                echo -e "Raw: $line"
                
                # Extract the actual message text
                local message_text=""
                if echo "$line" | grep -q "text.:"; then
                    message_text=$(echo "$line" | grep -o "text.: '[^']*'" | sed "s/text.: '//;s/'//")
                elif echo "$line" | grep -q "payload.:"; then
                    message_text=$(echo "$line" | grep -o "payload.: '[^']*'" | sed "s/payload.: '//;s/'//")
                fi
                
                if [ -n "$message_text" ]; then
                    echo -e "${BLUE}💬 Received: $message_text${NC}"
                    
                    # Get AI response
                    ai_response=$(get_ai_response "$message_text")
                    
                    if [ $? -eq 0 ] && [ -n "$ai_response" ]; then
                        echo -e "${YELLOW}🤖 AI Response: $ai_response${NC}"
                        
                        # Send response
                        send_message "$ai_response"
                    else
                        echo -e "${RED}❌ Could not get AI response${NC}"
                    fi
                fi
                echo -e "${GREEN}=====================${NC}\n"
            fi
        done
        
        # If we get here, the listen command ended
        echo -e "${YELLOW}🔄 Listen session ended, restarting in 5 seconds...${NC}"
        sleep 5
    done
}

# Function to test the setup
test_setup() {
    echo -e "${BLUE}🧪 Testing setup...${NC}"
    
    # Test Meshtastic connection
    echo -e "Testing Meshtastic connection..."
    if meshtastic --ble "$MAC_ADDRESS" --info >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Meshtastic connection OK${NC}"
    else
        echo -e "${RED}❌ Meshtastic connection failed${NC}"
        return 1
    fi
    
    # Test Ollama connection
    echo -e "Testing Ollama connection..."
    if curl -s "$OLLAMA_URL" -X POST -H "Content-Type: application/json" -d '{"model":"'"$AI_MODEL"'","prompt":"test","stream":false}' >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama connection OK${NC}"
    else
        echo -e "${RED}❌ Ollama connection failed${NC}"
        echo -e "Make sure Ollama is running: ollama serve"
        return 1
    fi
    
    # Test AI response
    echo -e "Testing AI response..."
    test_response=$(get_ai_response "Hello")
    if [ $? -eq 0 ] && [ -n "$test_response" ]; then
        echo -e "${GREEN}✅ AI response test OK${NC}"
        echo -e "Test response: $test_response"
    else
        echo -e "${RED}❌ AI response test failed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    return 0
}

# Function to show usage
show_usage() {
    echo "Meshtastic AI Bot"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  listen    - Start listening and responding to messages (default)"
    echo "  test      - Test the setup"
    echo "  send      - Send a test message"
    echo "  help      - Show this help"
    echo ""
    echo "Configuration:"
    echo "  Edit the script to change MAC_ADDRESS, CHANNEL_INDEX, or AI_MODEL"
}

# Function to send a test message
send_test_message() {
    local test_msg="AI Bot is online! Send me a question."
    echo -e "${BLUE}📤 Sending test message...${NC}"
    send_message "$test_msg"
}

# Main execution
case "${1:-listen}" in
    "listen")
        # Check if jq is available (optional but helpful)
        if ! command -v jq >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  jq not found. Install jq for better JSON parsing.${NC}"
            echo -e "Ubuntu/Debian: sudo apt install jq"
            echo -e "macOS: brew install jq"
        fi
        
        listen_for_messages
        ;;
    "test")
        test_setup
        ;;
    "send")
        send_test_message
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac
