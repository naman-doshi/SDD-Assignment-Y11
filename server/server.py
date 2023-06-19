# Importing dependencies
from flask import Flask, jsonify, request, render_template
import json
import random
from bardapi import Bard
from dotenv import load_dotenv
import os
import webbrowser
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

    # print(ans)

    # Deleting the first line (always useless) since it may trigger false positives in question detection
    del ans[0]

    questions = []

    # questionFound = False

    for line in ans:
        # Checking if the line actually contains something of use (i.e. not blank)
        if len(line) > 5:
            # Checking if the line is a question
            if line[0].isnumeric():
                if len(questions) != 0:
                    if len(questions[-1]) != 6:
                        return []
                # questionFound = True
                questions.append([line[3:]])
            # Checking if it's an answer option
            elif line[0] == '(':
                if len(line) < 5 or len(questions) == 0:
                    return []
                questions[-1].append(line[4:])
            # Checking if it's a correct answer in the format "The answer is (A)" just in case
            elif '(' in line and ')' in line:
                if len(questions) != 0:
                    if len(questions[-1]) > 4:
                        questions[-1].append(line[line.index('(')+1:line.index(')')])
            # Checking if it's a correct answer in the format "Answer: A"
            elif "answer:" in line.lower():
                if len(questions) != 0:
                    questions[-1].append(line[line.index(':')+2])

            # print(line, questionFound)


    return questions

def loadFileQuestions(numQuestions):

    # Initialising an integer that counts how many lines have been loaded so far
    numLinesLoaded = 0

    # Initialising an integer that stores the current question number (0-indexed)
    currentQuestion = 0

    # Initialising an array that will store all of the questions and will ultimately be returned
    allQuestions = []

    # Opening the questions file and iterating over each line
    # Since the "with" method is used, the file is automatically closed
    with open('server/questions.txt', 'r') as questionFile:
        # Reads the first line of the file, and strips it of any newline characters or spaces
        currentLine = questionFile.readline().strip()

        # Pre-test loop — checks if the current line is not blank
        while currentLine and numLinesLoaded < numQuestions * 6:

            # If the number of lines loaded is divisible by 6, a new question must have started
            # This is because each question has 6 lines
            if numLinesLoaded % 6 == 0:
                # Incrementing the current question number and appending a new empty array to the list of questions
                # This signifies the start of a new question
                currentQuestion = int(numLinesLoaded / 6)
                allQuestions.append([])
            
            # Appending another line of the text file to the current question
            allQuestions[currentQuestion].append(currentLine.strip())

            # Incrementing the number of lines loaded
            numLinesLoaded += 1

            # Reading the next line
            currentLine = questionFile.readline().strip()

    # Randomising the order of the questions
    random.shuffle(allQuestions)
    doublyRandomisedQuestions = []
    letterToIndex = {'A': 1, 'B': 2, 'C':3, 'D':4}
    i = 0
    
    # Randomising the order of the answer options and appending the correct answer's text to the end of the question
    # Also accounts for the edge case where the user requests 10 questions
    while i < min(20, numQuestions):
        currentQuestion = allQuestions[i]
        question = currentQuestion[0]
        correctAnswerText = currentQuestion[letterToIndex[currentQuestion[5]]]
        options = currentQuestion[1:5]
        random.shuffle(options)
        doublyRandomisedQuestions.append([question] + options + [correctAnswerText])
        i += 1
    
    # If the user requests more than 20 questions, the Bard API is used to generate the rest
    if numQuestions > 20:
        # print(numQuestions - 20)
        doublyRandomisedQuestions += loadBardQuestions(numQuestions - 20)

    return doublyRandomisedQuestions

def loadBardQuestions(numQuestions):
    # Asking questions 10 at a time — the maximum that Bard can reliably provide in one answer
    questions = []
    while len(questions) < numQuestions:
        questions += askBard("Please provide 10 moderately difficult multiple choice questions, 4 answer options (formatted as (A), (B), (C), (D)), and the correct answer (a new line formatted exactly like Answer: D) for the New South Wales Software Design and Development syllabus. Please respond with no formatting, and give me a variety of questions covering different aspects of the syllabus. The format of your response should be: 1 line for the question, 4 lines for all the answer options, 1 line for the correct answer, and then a blank newline. Then you can move on to the next question.")
    # Randomising the order of the answer options and appending the correct answer's text to the end of the question
    letterToIndex = {'A': 1, 'B': 2, 'C':3, 'D':4}
    newQuestions = []

    for item in questions:
        question = item[0]
        correctAnswerText = item[letterToIndex[item[5]]]
        options = item[1:5]
        random.shuffle(options)
        newQuestions.append([question] + options + [correctAnswerText])
        
    return newQuestions


# Initialising Flask app with directories
app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Flask route to render index.html at all times when a user is viewing it (via a GET request).
@app.route('/', methods = ['GET'])
def index():
    return render_template(("index.html"))

# Method to return questions to the front end
@app.route('/getQuestions', methods=['POST', 'GET'])
def getQuestions():
    if request.method == 'POST':
        # Processing the data from the frontend
        file = request.form
        params = file['params']
        params = json.loads(params)

        # Getting the variables numQuestions and loadFileQuestions (LFQ)
        numQuestions = int(params['numQuestions'][0])
        LFQ = params['LFQ'][0]
        
        # Acquiring the questions
        if LFQ == True:
            allQuestions = loadFileQuestions(numQuestions)
        else:
            allQuestions = loadBardQuestions(numQuestions)
        
        # Returning the questions in JSON format
        return jsonify(allQuestions)

# Method to log the user's score and other metrics       
@app.route('/conclude', methods=['POST', 'GET'])
def conclude():
    if request.method == 'POST':
        # Processing the data from the frontend
        file = request.form
        params = file['params']
        params = json.loads(params)
        playerScore = int(params['playerScore'][0])
        correctAnswers = int(params['correctAnswers'][0])
        questionsAsked = int(params['questionsAsked'][0])

        # Same as Version 7 — Writing the game's statistics to the report
        with open("server/report.txt", 'a') as userReport:
            # Appending text to indicate the start of a new report
            userReport.write("————— Commence New Report —————\n")

            # Appending the normal metrics displayed to the user as well
            userReport.write("GAME OVER!\n")
            userReport.write(f"Thank you for playing Who Wants to Be a University Student!\n")
            userReport.write(f"Your final score was {playerScore} points.\n")
            userReport.write(f"You answered {correctAnswers} out of {questionsAsked} questions correctly.\n")

            # Returning '0' only because it is required; it has no real purpose
            return '0'


if __name__ == '__main__':

    # Opening the game in the user's default browser
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://127.0.0.1:8080/')

    app.run(host='127.0.0.1', port=8080)

