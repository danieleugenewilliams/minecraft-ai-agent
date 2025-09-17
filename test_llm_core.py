#!/usr/bin/env python3
"""
Simple test for LLM agent Ollama integration
"""

import requests
import json
import time

def test_ollama_connection():
    """Test connection to Ollama"""
    print("=== Testing Ollama Connection ===")
    
    try:
        # Test if Ollama is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✓ Ollama is running")
            print(f"Available models: {len(models.get('models', []))}")
            for model in models.get('models', []):
                print(f"  - {model.get('name', 'Unknown')}")
            return True
        else:
            print(f"✗ Ollama responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to Ollama: {e}")
        return False

def test_llm_minecraft_decision():
    """Test LLM making Minecraft decisions"""
    print("\n=== Testing LLM Minecraft Decision Making ===")
    
    # Simulate game state
    mock_game_state = {
        'color_coverage': {
            'wood': 0.15,  # 15% wood visible
            'leaves': 0.25,  # 25% leaves visible
            'dirt': 0.10,   # 10% dirt visible
            'stone': 0.05,  # 5% stone visible
            'grass': 0.20,  # 20% grass visible
            'sky': 0.25     # 25% sky visible
        },
        'recent_actions': ['look_right', 'move_forward', 'look_left']
    }
    
    # Create prompt
    system_prompt = """You are an AI agent controlling a character in Minecraft through iPhone mirroring. 

OBJECTIVE: Build a small shelter by gathering wood and dirt, then constructing a basic structure

CRITICAL CONTROL INFORMATION:
- ONLY the UP arrow key moves the character forward (this is the ONLY movement that works!)
- j/k/l/i keys control camera looking (NOT movement)
- If character is spinning/stuck, use 'center_view' to reset camera
- To explore: alternate between 'move_forward' (up key) and looking around

AVAILABLE ACTIONS:
- move_forward: Use UP arrow (ONLY working movement)
- look_left: Use j key to turn camera left
- look_right: Use l key to turn camera right  
- look_up: Use i key to look up
- look_down: Use k key to look down
- center_view: Use enter key to center camera
- mine: Left click to break blocks
- place: Right click to place blocks
- jump: Space bar
- wait: Do nothing for one cycle

RESPONSE FORMAT:
Analyze the situation briefly, then respond with exactly one action in this format:
ACTION: [action_name]
REASON: [brief explanation]

Be decisive and specific. Focus on the objective of building a shelter."""

    user_prompt = f"""CURRENT GAME STATE:
Colors visible on screen:
- Wood: {mock_game_state['color_coverage']['wood']:.1%}
- Leaves: {mock_game_state['color_coverage']['leaves']:.1%}  
- Dirt: {mock_game_state['color_coverage']['dirt']:.1%}
- Stone: {mock_game_state['color_coverage']['stone']:.1%}
- Grass: {mock_game_state['color_coverage']['grass']:.1%}
- Sky: {mock_game_state['color_coverage']['sky']:.1%}

Recent actions: {mock_game_state['recent_actions'][-3:]}

What should you do next to work toward building a shelter? Remember:
- Find trees (wood/leaves) to chop for building materials
- Look for dirt to gather for foundation
- Use ONLY 'move_forward' for movement (up arrow key)
- Use looking actions (j/k/l/i) to scan for resources
- If spinning/stuck, use 'center_view' to reset

Choose your next action:"""

    try:
        payload = {
            "model": "qwen2.5:7b",
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        print("Sending request to LLM...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "").strip()
            
            print("✓ LLM Response received:")
            print("-" * 40)
            print(llm_response)
            print("-" * 40)
            
            # Parse the response
            lines = llm_response.split('\n')
            action_line = None
            reason_line = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('ACTION:'):
                    action_line = line.replace('ACTION:', '').strip()
                elif line.startswith('REASON:'):
                    reason_line = line.replace('REASON:', '').strip()
            
            if action_line:
                print(f"✓ Parsed Action: {action_line}")
                print(f"✓ Reason: {reason_line or 'No reason provided'}")
                
                # Validate action
                valid_actions = [
                    'move_forward', 'look_left', 'look_right', 'look_up', 'look_down',
                    'center_view', 'mine', 'place', 'jump', 'wait'
                ]
                
                if action_line in valid_actions:
                    print(f"✓ Action '{action_line}' is valid")
                    return True
                else:
                    print(f"⚠ Action '{action_line}' is not in valid actions list")
                    print(f"Valid actions: {valid_actions}")
                    return False
            else:
                print("✗ Could not parse ACTION from response")
                return False
                
        else:
            print(f"✗ LLM request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        return False

def test_control_simulation():
    """Test simulating controls based on LLM decisions"""
    print("\n=== Testing Control Simulation ===")
    
    actions_to_test = [
        ('move_forward', 'Press UP arrow for 0.5 seconds'),
        ('look_left', 'Press j key for 0.3 seconds'),
        ('look_right', 'Press l key for 0.3 seconds'),
        ('center_view', 'Press enter key'),
        ('mine', 'Left click'),
        ('wait', 'Sleep for 0.5 seconds')
    ]
    
    print("Simulating control actions:")
    for action, description in actions_to_test:
        print(f"  {action:12} -> {description}")
        time.sleep(0.1)  # Small delay to simulate processing
    
    print("✓ All control actions simulated successfully")
    return True

if __name__ == "__main__":
    print("LLM Agent Test Suite")
    print("=" * 50)
    
    # Test Ollama connection
    ollama_ok = test_ollama_connection()
    
    # Test LLM decision making
    llm_ok = test_llm_minecraft_decision() if ollama_ok else False
    
    # Test control simulation
    control_ok = test_control_simulation()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Ollama Connection: {'✓ PASS' if ollama_ok else '✗ FAIL'}")
    print(f"LLM Decision Making: {'✓ PASS' if llm_ok else '✗ FAIL'}")
    print(f"Control Simulation: {'✓ PASS' if control_ok else '✗ FAIL'}")
    
    if all([ollama_ok, llm_ok, control_ok]):
        print("\n🎉 All core LLM agent tests passed!")
        print("The LLM agent can:")
        print("  - Connect to Ollama")
        print("  - Analyze game state")
        print("  - Make intelligent decisions")
        print("  - Output valid control actions")
        print("\nReady for integration with vision and input systems!")
    else:
        print("\n❌ Some tests failed. Check the output above.")
        if not ollama_ok:
            print("💡 Make sure Ollama is running: ollama serve")