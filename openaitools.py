from os import getenv
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Muhit o'zgaruvchilarini yuklab olish
load_dotenv()

# OpenAI asinxron klientini yaratish
client = AsyncOpenAI(
    api_key=getenv("OPENAI_API_KEY"),
)

class OpenAiTools:
    # ChatGPT bilan muloqot qilish uchun metod
    async def get_chatgpt(question: str):
        prompt = question

        try:
            response = await client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="gpt-4-turbo-2024-04-09",  # To'g'ri model nomi
                max_tokens=3000,
                temperature=1,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Xatolik yuz berdi: {str(e)}"  # Xatolik tafsilotlarini qaytarish

    # DALL-E 3 bilan tasvir yaratish uchun metod
    async def get_dalle(prompt: str):
        try:
            response = await client.images.generate(
                model="dall-e-3",  # To'g'ri model nomi
                prompt=prompt,
                size="1024x1024",
                quality="standard",  # Sifat parametri
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            return f"Xatolik yuz berdi: {str(e)}"  # Xatolik tafsilotlarini qaytarish

