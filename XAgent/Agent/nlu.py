import pandas as pd
import os
import sys
import  logging
# sys.path.append('/homes/bach/XAGENT/XAgent/Agent')
# silence command-line output temporarily
# sys.stdout, sys.stderr = os.devnull, os.devnull
from importlib_resources import files
from simcse import SimCSE

from XAgent.Agent.constraints import select_msg, l_support_questions_ids, request_number_msg, request_more_msg
from XAgent.Agent.utils import print_log

# unsilence command-line output

enabled = True
topk = 400
class NLU:
    def __init__(self):
        self.model = SimCSE("princeton-nlp/sup-simcse-roberta-large")
        self.df = pd.read_csv(files("XAgent").joinpath('Agent/Median_4.csv'), index_col=0).drop_duplicates()
        self.model.build_index(list(self.df['Question']))

    def get_list_questions(self, match_results):
        labels = []
        questions = []
        # print(l_support_questions_ids)
        # print(l_support_questions_ids)
        df_original_questions = pd.read_csv(files("XAgent").joinpath('Agent/original_question.csv'))
        for idx, (question,_) in enumerate(match_results):
            label = self.df.query('Question == @question')['Label'].iloc[0]
            if len(questions) < 5:
                question = df_original_questions.query("Label == @label").iloc[0]['Question']
            if label not in labels and label in l_support_questions_ids:
                questions.append(question)
                labels.append(label)
        # print(questions)
        return questions

    def replace_information(self, question, features, prediction, current_instance, labels):
        if "{X}" in question:
            question = question.replace("{X}", f"{{{features[0]},{features[1]}, ...}}")
        if "{P}" in question:
            question = question.replace("{P}", str(prediction))
        if "{Q}" in question:
            question = question.replace("{Q}", str([label for label in labels if str(label) != str(prediction)]))
        return question
    def match(self, question, features, prediction, current_instance, labels):
        threshold = 0.6
        match_results = self.model.search(question, threshold=threshold)
        logging.log(26, f"question = {question}")
        logging.log(26, f"result = {match_results}")
        if len(match_results) > 0:
            match_question, score = match_results[0]
            # print("hallo" + match_question)
            return match_question
        else:
            match_results = self.model.search(question, threshold=0, top_k=topk)
            questions = self.get_list_questions(match_results)
            # print(match_results)
            # ans = "I am not sure what you mean. Can you please choose one of the following questions if there is a match, otherwise, choose 6 to get more questions\n"
            ans = select_msg
            # print_log("xagent", ans)
            for idx, question in enumerate(questions[:5]):
                question = self.replace_information(question, features, prediction, current_instance, labels)
                msg = f"{idx+1}. {question}"
                # print(msg)
                ans += f"{msg}\n"
            msg = "6. See more questions"
            # print(msg)
            ans += f"{msg}"
            # msg = "Please choose the number of the corresponding question"
            # print(msg)
            # ans += f"{msg}\n"
            # logging.log(25, f"Xagent: {ans}")
            print_log("xagent", ans)
            choice = print_log("user")
            while(True):
                if choice.isnumeric():
                    if int(choice) <= topk+1:
                        break
                msg = request_number_msg
                print_log("xagent", msg)
                choice = print_log("user")
            ans = request_more_msg
            if int(choice) == 0:
                return "unknown"
            if int(choice) == 6:
                for idx, question in enumerate(questions[5:15], start=5):
                    question = self.replace_information(question, features, prediction, current_instance, labels)
                    msg = f"{idx+1}. {question}"
                    ans+=f"{msg}\n"
                print_log("xagent", ans)
                choice = print_log("user")
                if int(choice) == 0:
                    return "unknown"
                while (True):
                    if choice.isnumeric():
                        if int(choice) < 15:
                            break
                    msg = request_number_msg
                    print_log("xagent", msg)
                    choice = print_log("user")
            return questions[int(choice) - 1]
        return "unknown"
