from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

print("Welcome to BMW AI Chatbot!")

user_question = input("Ask me anything about BMW: ")
print("Sending question to Ollama...")
response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {"role": "user", "content": user_question}
    ]
)
print(response.choices[0].message.content)