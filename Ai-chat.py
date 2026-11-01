from openai import OpenAI
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

print("Welcome to BMW AI Chatbot!")

user_question = input("Ask me anything about BMW: ")
print("Sending question to Ollama...")
response = client.chat.completions.create(
    model="qwen3:4b",
   messages=[
    {
        "role": "system",
        "content": (
            "You are a professional automotive AI assistant. "
            "You specialize in BMW vehicles, engines, performance, and comparisons. "
            "Give accurate, clear, and helpful answers. "
            "Never invent horsepower, torque, engine specifications, or model years. "
            "Distinguish between different model years, generations, and trims. "
            "If you are uncertain about a fact, clearly say so instead of guessing. "
            "Explain technical information in simple language. "
            "Keep answers organized, professional, and easy to read."
        )
    },
    {"role": "user", "content": user_question}
]
)
print(response.choices[0].message.content)