# model for given exercises
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
from requests.exceptions import ConnectTimeout


# Set up API credentials
api_key = 'api_key'
Token = 'Token'
supabase_url = 'supabase_url'
supabase_key = 'supa_key'

from supabase import create_client, Client
supabase: Client = create_client(supabase_url, supabase_key)

sentences = supabase.table('prepositions').select("*").execute()
# print(sentences)
sentences = sentences.data


def start(update, context):
    update.message.reply_text("Welcome to the Fill-in-the-Blank Test.\n\nI will ask you questions with a blank space, and you need to fill in the blank with the correct preposition or phrase.\n\ntype 'end' to exit the test.")
    context.user_data['correct_answer'] = None  # Initialize user_data for the current user
    ask_question(update, context)  # Ask the first question

def end_test(update, context):
    # Send a message to the user indicating the end of the test.
    update.message.reply_text("Test ended. Thank you for participating!")

    # Clear user_data to reset the test for the next session
    context.user_data.clear()


#ask user question
def ask_question(update, context):
    context.user_data['correct_answer'] = None 
    sentences = context.user_data.get('sentences')
    if not sentences:
        context.user_data['sentences'] = supabase.table('prepositions').select("*").execute().data
        sentences = context.user_data['sentences']

    sentence = random.choice(sentences)
    task = sentence['Task'].replace("*", "_")
    correct_answer = sentence['Answer']
    context.user_data['correct_answer'] = correct_answer  # Store the correct answer for comparison
    update.message.reply_text(f"Fill in the blank:\n\nType 'next' for another fill in the blank\n\n{task}\n")


#check answer
def check_answer(update, context):
    user_answer = update.message.text.strip().lower()
    correct_answer = context.user_data.get('correct_answer')
    sentences = context.user_data.get('sentences')
    print(user_answer, correct_answer)

    if user_answer in correct_answer.split(', ') or user_answer in correct_answer.split('/ ') or user_answer in correct_answer.lower():
        print(user_answer, correct_answer)
        sentence = next((x for x in sentences if x['Answer'] == correct_answer), None)
        explanation = sentence['Explanation']
        examples = sentence['Examples']
        update.message.reply_text(f"Correct!\nThe answer is: {correct_answer}\n")
        if explanation or examples:
            update.message.reply_text(f"Explanation: {explanation}\n\nExamples: {examples}")
            ask_question(update, context)
        else:
            prompt = f"Please explain the usage of the preposition comprehensively (with solved examples in points) in the following sentence:\n\n{sentence['Task'].replace('*', '_')}\n\nExplanation:"
            try:
                response = requests.post(
                    'https://api.openai.com/v1/engines/text-davinci-003/completions',
                    headers={'Authorization': f'Bearer {api_key}'},
                    json={'prompt': prompt, 'max_tokens': 4000, 'temperature': 0.7}
                )
                response.raise_for_status()
                explanation_chatgpt = response.json()['choices'][0]['text'].strip()
                update.message.reply_text(f"Explanation: {explanation_chatgpt}")
                ask_question(update, context)
            except ConnectTimeout as e:
                # Retry the API request in case of a timeout error
                update.message.reply_text("Timeout error occurred. Retrying...")
                check_answer(update, context)
            except requests.exceptions.RequestException as e:
                update.message.reply_text("An error occurred while fetching the explanation.")

    elif correct_answer is None:
        update.message.reply_text("Please start the test by typing /start")
        return

    elif user_answer == "next":
        ask_question(update, context)  # Ask the next question
        return

    elif user_answer == "end":
        end_test(update, context)  # Call the end_test function to end the test
        return
      
    else:
        update.message.reply_text("Incorrect answer. Please try again.")


def main():
    updater = Updater(Token, use_context=True)
    dp = updater.dispatcher

    sentences = supabase.table('prepositions').select("*").execute().data

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_answer, pass_user_data=True))

    dp.add_handler(CommandHandler("end", end_test))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
