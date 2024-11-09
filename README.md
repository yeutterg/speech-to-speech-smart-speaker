# Speech-to-Speech Smart Speaker

This is the Python code for a smart speaker (like the Amazon Echo or Google Home) that is built atop [OpenAI's Realtime API](https://platform.openai.com/docs/guides/realtime). This speech-to-speech API is more conversational and lower latency than traditional voice assistants, such as Alexa.

Follow the [build log on YouTube](https://www.youtube.com/playlist?list=PLboszRf3aO5aD2V_da5jIyB33Sp1MpEe3).

This is an open-source project, and all improvements are welcome! Please submit pull requests. Let's build the future of ambient intelligence together.

## Setup

1. Clone this repository
2. Go to [platform.openai.com](https://platform.openai.com/), create an account and add $5-$10 credit (if you haven't already), then [create a new API secret key](https://platform.openai.com/api-keys) and copy it
3. Make a copy of .env.sample and rename it to .env.local
4. Paste your new API key into .env.local under OPENAI_API_KEY=""