# README

`bht_automation_test.py` is the main script. At the bottom of the script, under "MAIN", there are two functions being called:

1. `record_gpt_choicest` - This asks ChatGPT for choicest pieces for each commentary based on a "choicest prompt".
2. `record_gpt_bht` - This asks ChatGPT for a final bht based on all the choicest pieces from each commentary based on a "bht prompt"

# STEPS
## 1. Make sure you have a "commentary" folder. 
The structure of this folder is:

commentary -> [commentator] -> [book] -> [chapter] -> [verse.txt]

For example,
`commentary/Albert Barnes/2 Peter/Chater 1/Verse 19.txt` would contain the Barnes commentary on 2 Peter 1:19. You 

## 2. Make sure you have a "gpt prompts" folder.
The structure of this folder is:

gpt prompts -> bht -> bht prompt.txt
gpt prompts -> choicest -> choicest prompt.txt

This is where the ChatGPT prompts will are used to ask ChatGPT to perform the task.

## 3. Run the `bht_automation_test.py` script.
You may need to sign up at openAI and get an API Key for the global `OPENAI_API_KEY` variable. You'll be asked to add your credit card. Each script run costs some fraction of a cent. In developing this script I've run it many times and I currently owe around 10 cents. 

You may also need to set up python and install the `openai` library. 