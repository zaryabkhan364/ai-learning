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

# sentences = [{'ID': 1, 'Answer': 'To, on', 'Explanation': 'Much to somebody’s surprise / embarrassment is an expression used to say that someone feels very surprised, embarrassed  when something happens. Only preposition "to" makes sense in this context. "Insisted on something / on doing something" is a phrasal verb used to express a strong determination or demand. It is generally used with preposition "on". In addition, "insist\' cand be used with a bare infinitive or "should" + bare infintive. I suggest that he should help you / I suggest that he help you.   ', 'Task': '* our surprise he insisted * seeing the documents.', 'Examples': 'But to my surprise, he stopped talking. And much to my surprise, I saw something there I liked. And to my surprise, they listened. I must insist on being paid right now. So we insist that he obey us. Your friends may insist that you be more cooperative and less individualistic.'}, {'ID': 2, 'Answer': 'of, on, out, of', 'Explanation': 'In this context adjective "typical" means showing all the bad characteristics that you expect from somebody or something. To indicate somebody or something, the adjective is usually followed by preposition "of". "On the contrary" is a phrase used to show that you think or feel the opposite of what has just been stated. Only preposition "on" makes sense in this context. If a person’s behavior is out of character, it is very different from the usual way that person behaves. ', 'Task': '“It’s so typical * him to behave like that!”\n“* the contrary, it’s completely * * character for Paul to behave so terribly.”', 'Examples': 'It\'s just typical of Dan to spend all that money on the equipment and then lose interest two months later. It\'s typical of Ramon to waste time when he knows we\'re already late. "I thought you said the film was exciting?" "On the contrary, I nearly fell asleep half way through it!" I\'m not angry with you. On the contrary! It was out of character for Charles not to offer to help. He swore, which was out of character for him.'}, {'ID': 3, 'Answer': 'to, of, for', 'Explanation': 'If you are used to something or someone, you are familiar with something. If you get used to something or someone, you become familiar with something. If you used to do something, you did it in the past but you no longer do it. Phrase "make fun of somebody or something" means making a joke about something or somebody in a way that is not kind. Only preposition "of" is used in this phrase. "The occasion for something" means an opportunity or reason for doing something or for something to happen. ', 'Task': 'I am not used * people making fun * me and I don’t think it is the occasion * laughter.', 'Examples': "I do the dishes every day, so I’m used to it. I can’t get used to the idea that you’re grown up now. Like Neil still makes fun of me. Stop it - I don't make fun of the way you talk, do I? This was the occasion for expressions of friendship by the two presidents. The big occasion for country people was the Agricultural Fair."}, {'ID': 4, 'Answer': 'at, over / in', 'Explanation': 'Phrase "put/set somebody’s mind at rest" means making someone feel less anxious or worried. In this context phrasal verbs "turn over/in" mean going to bed.', 'Task': '“Doctor, what is this lump (шишка) on my head?”\n“Let me set your mind * rest. It’s nothing serious. Just turn * and go to sleep, will you!”', 'Examples': "He's unlikely to know how you feel, and until he does, he can't put your mind at rest. Quite often, all that is required is a friendly chat to put your mind at rest. Please excuse me, Captain but I think I'd better turn in early. He said he'd already eaten and he wanted to turn over and go to sleep early."}, {'ID': 5, 'Answer': 'to, on', 'Explanation': 'If you object to doing something, you feel or say that you oppose or disapprove of something. "On time" means at the correct or agreed time. In time means early enough for something or to do something. Thus, only preposition "on" is appropriate in this context.', 'Task': 'I object * being kept waiting. Why can’t you be * time?', 'Examples': "I have never smoked and I object to being poisoned by other people's indulgence.\r\nWhat I object to is the craze for machinery, not machinery as such. The parade started right on time."}]


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
