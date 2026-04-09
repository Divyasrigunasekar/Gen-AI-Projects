require('dotenv').config();
const express = require('express');
const { OpenAI } = require('openai');
const path = require('path');

const app = express();
const port = 3000;

app.use(express.static('public'));
app.use(express.json());

const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

app.post('/api/extract', async (req, res) => {
    try {
        const userInput = req.body.text;
        if (!userInput) {
            return res.status(400).json({ error: 'Text is required' });
        }

        const response = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [
                {
                    role: "system",
                    content: "You are a keyword extractor.\n\nInstructions:\n- Output all relevant keywords\n- Separate with commas\n- No explanation\n- No extra text"
                },
                {
                    role: "user",
                    content: `Text: "${userInput}"`
                }
            ],
            temperature: 0.3,
        });

        const keywords = response.choices[0].message.content.trim();
        res.json({ keywords });
    } catch (error) {
        console.error('Error explicitly extracting keywords:', error);
        res.status(500).json({ error: 'Failed to extract keywords' });
    }
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});
