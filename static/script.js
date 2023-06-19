// Creating a canvas for the confetti
const canvas = document.getElementById("confettiBox");
const jsConfetti = new JSConfetti({ canvas });

// Adding an event listener to trigget the logData function when the form is submitted
let form = document.getElementById("game-settings");
form.addEventListener("submit", logData);

// Function to update the text of each question
function updateQuestion(list) {
  // Create a variable for each element in the question
  let question = document.getElementById("questionText");
  let optA = document.getElementById("optionAChoice");
  let optB = document.getElementById("optionBChoice");
  let optC = document.getElementById("optionCChoice");
  let optD = document.getElementById("optionDChoice");

  // Update the text of each element
  question.innerHTML = list[0];
  optA.innerHTML = list[1];
  optB.innerHTML = list[2];
  optC.innerHTML = list[3];
  optD.innerHTML = list[4];
}

// Function to double the score when the user answers a question correctly
function doubleScore() {
  let score = document.getElementById("score");
  score.innerHTML = parseInt(score.innerHTML) * 2;
}

// Function to reset the score to 1 when the user gets a question wrong
function resetScore() {
  let score = document.getElementById("score");
  score.innerHTML = 1;
}

// Function to estimate the waiting time for the user
function estimateWaitingTime(numQuestions, LFQ) {
  let time = 0;
  let timeBlock = document.getElementById("wait-time");

  // From general testing, each question takes about 0.9 seconds to be generated.
  if (LFQ) {
    // Of course, we need to subtract the time taken to generate the pre-written questions.
    // This works every time except when numQuestions = 10
    // But in this case, the actual loading time will be 0 seconds and thus this page will not be shown to the user.
    time = 0.9 * Math.abs(numQuestions - 20);
    // console.log(time)
  } else {
    time = 0.9 * numQuestions;
  }

  timeBlock.innerHTML = time;
}

// Function to make the intro page disappear and the loading page appear
function showLoadingPage(numQuestions, LFQ) {
  let f = document.getElementById("question-box");
  f.classList.add("hidden");
  f.classList.remove("shown");

  let elem = document.getElementById("loading");
  elem.classList.add("shown");
  elem.classList.remove("hidden");

  estimateWaitingTime(numQuestions, LFQ);
}

// Function to log the data from the form to the backend and start the game
function logData(event) {
  // Prevent the page from automatically reloading on form submission
  event.preventDefault();

  // Hiding the intro page
  let f = document.getElementById("question-box");
  f.classList.add("hidden");
  f.classList.remove("shown");

  // Creating the request
  let req = new XMLHttpRequest();
  let formData = new FormData();

  // Creating the parameters to be passed
  let params = {
    numQuestions: [numQuestions.value],
    LFQ: [includePreWrittenQuestions.checked],
  };

  // console.log(params);

  // Appending the parameters to the form data
  formData.append("params", JSON.stringify(params));

  // Showing the loading page
  showLoadingPage(numQuestions.value, includePreWrittenQuestions.checked);

  // responseReceived = false;

  // Setting a function to be called when the request is complete
  req.onreadystatechange = function () {
    if (req.readyState == XMLHttpRequest.DONE) {
      // Get the questions from the backend, and start the game with these questions
      var allQuestions = req.responseText;
      // console.log(allQuestions);
      startGame(JSON.parse(allQuestions));
      // responseReceived = true;
    }
  };

  // Sending the request to the endpoint /getQuestions
  req.open("POST", "/getQuestions");
  req.send(formData);

  // console.log(responseReceived);
}

// Tedious function to show the ending page
function showEndingPage(correctAnswers, totalQuestions) {
  // Showing the ending page and updating all variables in it
  let finalScore = document.getElementById("score").innerHTML;

  let eachQuestion = document.getElementById("eachQuestion");
  eachQuestion.classList.add("hidden");
  eachQuestion.classList.remove("shown");

  let endingPage = document.getElementById("endingPage");
  endingPage.classList.add("shown");
  endingPage.classList.remove("hidden");

  let score = document.getElementById("finalScore");
  score.innerHTML = finalScore;

  let correct = document.getElementById("correctAnswers");
  correct.innerHTML = correctAnswers;

  let total = document.getElementById("totalQuestions");
  total.innerHTML = totalQuestions;

  // Sending the quiz stats to the backend to be logged in a text file
  let req = new XMLHttpRequest();
  let formData = new FormData();

  let params = {
    playerScore: [finalScore],
    correctAnswers: [correctAnswers],
    questionsAsked: [totalQuestions],
  };

  // console.log(params);

  formData.append("params", JSON.stringify(params));
  req.open("POST", "/conclude");
  req.send(formData);
}

// Main gameplay function
function startGame(list) {
  // Getting a list of all option elements, and initialising variables
  const options = document.querySelectorAll(".answerOption");
  let index = 0;
  let correctAnswers = 0;

  // Showing the question  page
  let loading = document.getElementById("loading");
  loading.classList.add("hidden");
  loading.classList.remove("shown");

  let elem = document.getElementById("eachQuestion");
  elem.classList.add("shown");
  elem.classList.remove("hidden");

  // Showing the very first question
  updateQuestion(list[index]);

  // Adding an event listener to each option
  options.forEach((option) => {
    // It is a click listener
    option.addEventListener("click", () => {
      // console.log(index);

      if (option.innerHTML === list[index][5]) {
        // If the user gets the question right, add confetti, double the score, and add 1 to the correct answers
        jsConfetti.addConfetti({
          confettiRadius: 3,
        });
        correctAnswers++;
        doubleScore();
      } else {
        // If the user gets the question wrong, reset the score — no visual feedback for now
        resetScore();
      }

      // Increment index to move onto the next question
      index++;
      if (index === list.length) {
        // If the user has answered all questions, show the ending page
        showEndingPage(correctAnswers, list.length);
        // Returning 0 to exit this function
        return 0;
      }

      // Otherwise, update the question and continue
      // An else statement is not needed as the function will exit if the condition is met
      // Thus, if the condition is not met, the function will continue
      updateQuestion(list[index]);
    });
  });
}
