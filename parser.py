import os
import json
import csv
from openai import OpenAI

#OpenAI API
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

def create_prompt_for_questions(batch_number):
    prompt = [
        {
            "role": "system",
            "content": (
                "You are an assistant tasked with reading LSAT PrepTest PDFs and extracting all questions, passages, and answers."
                " Please extract each question in the format provided below and do so chronologically."
            )
        },
        {
            "role": "user",
            "content": (
                "Read the attached LSAT PrepTest PDF and extract the questions one by one, ensuring that you capture the section number, "
                "question number, passage, question text, and answer choices in a structured format. The output should be structured as a CSV "
                "with the following headers: Section, Question Number, Passage, Question, Answer Choices."
            )
        }
    ]
    return prompt

def send_to_openai(prompt):
    chat_completion = client.chat.completions.create(
        model="gpt-4o", #explore other models
        messages=prompt,
    )
    return chat_completion.choices[0].message.content

def save_csv_output(output, output_file):
    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Question Number", "Passage", "Question", "Choices"])
        lines = output.splitlines()
        for line in lines:
            #Example
            writer.writerow([line])

def process_pdf_for_questions_in_batches(pdf_file, output_file):
    batch_number = 1
    while True:
        prompt = create_prompt_for_questions(batch_number)
        output = send_to_openai(prompt)
        if not output or "I have completed the extraction" in output:
            break
        save_csv_output(output, output_file)
        batch_number += 1

#Example
if __name__ == "__main__":
    pdf_file = "LSAT_PT_90.pdf"
    output_file = "AI_pt90_questions.csv"
    process_pdf_for_questions_in_batches(pdf_file, output_file)
