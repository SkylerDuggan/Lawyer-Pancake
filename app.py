import json
import tkinter as tk
from tkinter import messagebox

#Main ChatGPT script from Nov 2024. Can use for future revisions.

# Load LSAT questions from JSON file
def load_questions(filename="questions.json"):
    with open(filename, "r") as file:
        return json.load(file)

class LSATApp:
    def __init__(self, root, questions):
        self.root = root
        self.questions = questions
        self.current_question = 0
        self.correct_answers = 0

        # Set up the window
        self.root.title("LSAT Practice Tool")

        # Text area for passage (only for reading comprehension questions)
        self.passage_label = tk.Label(root, wraplength=400, text="", font=("Arial", 12), fg="blue")
        self.passage_label.pack(pady=10)

        self.question_label = tk.Label(root, wraplength=400, text="", font=("Arial", 14))
        self.question_label.pack(pady=20)

        self.radio_var = tk.StringVar()

        # Multiple choice options
        self.option_a = tk.Radiobutton(root, text="", variable=self.radio_var, value="A", font=("Arial", 12))
        self.option_a.pack(anchor="w")
        self.option_b = tk.Radiobutton(root, text="", variable=self.radio_var, value="B", font=("Arial", 12))
        self.option_b.pack(anchor="w")
        self.option_c = tk.Radiobutton(root, text="", variable=self.radio_var, value="C", font=("Arial", 12))
        self.option_c.pack(anchor="w")
        self.option_d = tk.Radiobutton(root, text="", variable=self.radio_var, value="D", font=("Arial", 12))
        self.option_d.pack(anchor="w")
        self.option_e = tk.Radiobutton(root, text="", variable=self.radio_var, value="E", font=("Arial", 12))
        self.option_e.pack(anchor="w")

        # Submit button
        self.submit_button = tk.Button(root, text="Submit", command=self.check_answer)
        self.submit_button.pack(pady=20)

        self.load_next_question()

    def load_next_question(self):
        """Load the next question and its answer choices."""
        if self.current_question < len(self.questions):
            question_data = self.questions[self.current_question]

            # Show passage if it's a reading comprehension question
            if question_data["type"] == "reading_comprehension":
                self.passage_label.config(text=question_data.get("passage", ""))
                self.passage_label.pack(pady=10)
            else:
                self.passage_label.pack_forget()

            self.question_label.config(text=question_data["question"])
            self.option_a.config(text="A. " + question_data["choices"]["A"])
            self.option_b.config(text="B. " + question_data["choices"]["B"])
            self.option_c.config(text="C. " + question_data["choices"]["C"])
            self.option_d.config(text="D. " + question_data["choices"]["D"])
            self.option_e.config(text="E. " + question_data["choices"]["E"])
            self.radio_var.set(None)  # Clear the selection
        else:
            self.end_quiz()

    def check_answer(self):
        """Check the answer and provide feedback."""
        selected = self.radio_var.get()
        if selected == self.questions[self.current_question]["correct"]:
            self.correct_answers += 1
            messagebox.showinfo("Correct!", "Your answer is correct.")
        else:
            correct_answer = self.questions[self.current_question]["correct"]
            messagebox.showerror("Incorrect", f"Wrong answer! The correct answer is {correct_answer}.")
        self.current_question += 1
        self.load_next_question()

    def end_quiz(self):
        """Show final results."""
        messagebox.showinfo("Quiz Completed", f"Your score: {self.correct_answers}/{len(self.questions)}")
        self.root.quit()

def load_next_question(self):
    """Load the next question and its answer choices."""
    if self.current_question < len(self.questions):
        question_data = self.questions[self.current_question]

        # Display the passage if it's a reading comprehension question
        if question_data["type"] == "reading_comprehension":
            self.passage_label.config(text=question_data.get("passage", ""))
            self.passage_label.pack(pady=10)
        else:
            self.passage_label.pack_forget()

        # Display question along with its Preptest, section, and question number
        self.question_label.config(
            text=f"PrepTest {question_data['preptest']} - Section {question_data['section']} - Question {question_data['question_number']}\n\n{question_data['question']}"
        )
        self.option_a.config(text="A. " + question_data["choices"]["A"])
        self.option_b.config(text="B. " + question_data["choices"]["B"])
        self.option_c.config(text="C. " + question_data["choices"]["C"])
        self.option_d.config(text="D. " + question_data["choices"]["D"])
        self.option_e.config(text="E. " + question_data["choices"]["E"])
        self.radio_var.set(None)  # Clear the selection
    else:
        self.end_quiz()


# Load the questions
questions = load_questions()

# Initialize the GUI application
root = tk.Tk()
app = LSATApp(root, questions)
root.mainloop()
