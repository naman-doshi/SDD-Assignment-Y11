from flask import Flask, jsonify, request, render_template
import json
import random
from bardapi import Bard
from dotenv import load_dotenv
import os
load_dotenv()

# Function to get parsed Bard questions
def askBard(string):
    
    # Setting up variables for API key shuffling in case rate limits are reached 
    numberOfAPI = 4
    apiNumber = numberOfAPI

    # Initialising Bard instance
    token = os.getenv("BARD_0")
    bard = Bard(token=token)

    # Repeatedly trying to get a response until it is successful
    ans = None
    while ans == None:
        try:
            ans = bard.get_answer(string)['content']
        except:
            # If the rate limit is reached, the API key is changed in a cyclical manner
            apiNumber += 1
            if apiNumber == numberOfAPI:
                apiNumber = 0
            token = os.getenv("BARD_" + str(apiNumber))
            bard = Bard(token=token)

    # Splitting the response into lines
    ans = ans.splitlines()

    # Deleting the first line (always useless) since it may trigger false positives in question detection
    del ans[0]

    questions = []

    for line in ans:
        # Checking if the line actually contains something of use (i.e. not blank)
        if len(line) > 5:
            # Checking if the line is a question
            if line[0].isnumeric():
                if len(questions) != 0:
                    if len(questions[-1]) != 6:
                        return []
                questions.append([line[3:]])
            # Checking if it's an answer option
            elif line[0] == '(':
                questions[-1].append(line[4:])
            # Checking if it's a correct answer in the format "The answer is (A)" just in case
            elif '(' in line and ')' in line and len(questions[0]) > 3:
                questions[-1].append(line[line.index('(')+1:line.index(')')])
            # Checking if it's a correct answer in the format "Answer: A"
            elif "answer:" in line.lower():
                questions[-1].append(line[line.index(':')+2])

    return questions

string = '''Please provide 10 moderately difficult multiple choice questions, 4 answer options 
(formatted as (A), (B), (C), (D)), and the correct answer (a new line formatted exactly like Answer: D) 
for the New South Wales Software Design and Development syllabus. Please respond with no formatting, 
and give me a variety of questions covering different aspects of the syllabus.'''

allQuestions = []

while len(allQuestions) < 100:
    print(len(allQuestions))
    allQuestions += askBard(string)

print(len(allQuestions))
for line in allQuestions:
    print(len(line))
    print(line)
