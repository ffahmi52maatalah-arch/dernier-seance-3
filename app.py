import os

import gradio as gr
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/agent/invoke")


def chat_with_agent(user_input: str) -> str:
    if not user_input.strip():
        return "Please enter a question."
    try:
        response = requests.post(
            API_URL, json={"input": {"input": user_input}}, timeout=120
        )
        response.raise_for_status()
        # LangServe wraps the result: {"output": {"output": "..."}}
        return response.json()["output"]["output"]
    except requests.RequestException as e:
        return f"Error contacting agent: {e}"
    except (KeyError, ValueError):
        return "Error: unexpected response from the agent server."


demo = gr.Interface(
    fn=chat_with_agent,
    inputs=gr.Textbox(lines=2, placeholder="Ask me anything..."),
    outputs="text",
    title="LangChain Agent with Gradio",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
