import pandas as pd, sys, math
from collections import defaultdict # just so that creating new dict entries is just a little bit easier
def unique_word_set(content):
    return set(content.split(' ')) - {''}
class Classifier:    
    def __init__(self, train_set):
        self.train_set = train_set


        # format: tag     content
        #         [label] [message body]


        self.words_to_count = defaultdict(int)
        self.label_to_count = defaultdict(int)
        self.label_word_to_count = defaultdict(int)
        self.N = 0
        for idx, row in train_set.iterrows():
            content = row["content"]
            label = row["tag"]
            
            self.N+=1
            self.label_to_count[label]+=1
            # assume every email has been lowercased and non-alphanumeric chars stripped, so can split by spaces
            unique_words = unique_word_set(content)
            for word in unique_words:
                self.words_to_count[word]+=1
                self.label_word_to_count[(label, word)]+=1       

    def predict(self, content):
        most_probable = 0.0
        most_probable_label = ""
        for label in self.label_to_count:
            log_prob = math.log(self.label_to_count[label]/self.N)
            for word in unique_word_set(content):
                if self.words_to_count[word]:
                    p = (label, word)
                    if self.label_word_to_count[p]:
                        log_prob += math.log(self.label_word_to_count[p] / self.label_to_count[label])
                    else: 
                        log_prob += math.log(self.words_to_count[word] / self.N)
                else:
                    log_prob += math.log(1/self.N)
            if (log_prob > most_probable or most_probable_label == ""):
                most_probable = log_prob
                most_probable_label = label
        return most_probable_label, most_probable

    def predict_all(self, test_set):
        tested = 0
        correct = 0
        for idx, row in test_set.iterrows():
            tested+=1
            actual = row["tag"]
            content = (row["content"])
            predicted = self.predict(content)
            # print(f"  correct = {actual}, predicted = {predicted[0]}, log-probability score = {predicted[1]}\n  content = {content}\n")
            if actual==predicted[0]:
                correct+=1
        # print(f"performance: {correct} / {tested} posts predicted correctly")

    def print_classifier(self, filename):
        with open(filename,'w') as f:
            s = ""

            s+="classes:\n"
            for label_row in sorted(self.label_to_count):
                s+=(f"  {label_row}, {self.label_to_count[label_row]} examples, log-prior = {math.log(self.label_to_count[label_row] / self.N)}") + "\n"
            s+=("classifier parameters:") + "\n"
            for label_word in sorted(self.label_word_to_count):
                s+=(f"  {label_word[0]}:{label_word[1]}, count = {self.label_word_to_count[label_word]}, log-likelihood = {math.log(self.label_word_to_count[label_word] / self.label_to_count[label_word[0]])}") + "\n"
            f.write(s)