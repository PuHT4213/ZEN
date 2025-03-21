# 文件：pmi_ngram.py
# 来源：https://github.com/shizhediao/T-DNA/blob/main/TDNA/pmi_ngram.py

import argparse
from collections import defaultdict
import re
import math
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import split_text, is_chinese_char, replace_punctuation

class FindNgrams:
    def __init__(self, min_count=0, min_pmi=0, language='en'):
        self.min_count = min_count
        self.min_pmi = min_pmi
        self.words = defaultdict(int)
        self.ngrams, self.pairs = defaultdict(int), defaultdict(int)
        self.total = 0.
        self.language = language

    # def text_filter(self, sentence):
    #     cleaned_text = []
    #     index = 0
    #     for i, w in enumerate(sentence):
    #         if re.match(u'[^\u0600-\u06FF\u0750-\u077F\u4e00-\u9fa50-9a-zA-Z]+', w):
    #             if i > index:
    #                 cleaned_text.append([w.lower() for w in sentence[index:i]])
    #             index = 1 + i
    #     if index < len(sentence):
    #         cleaned_text.append([w.lower() for w in sentence[index:]])
    #     return cleaned_text

    # def count_ngram(self, texts, n):
    #     self.ngrams = defaultdict(int)
    #     for sentence in texts:
    #         # sub_sentence = sentence.split()
    #         sub_sentence = split_text(sentence)
    #         for i in range(n):
    #             n_len = i + 1
    #             for j in range(len(sub_sentence) - i):
    #                 ngram = tuple([w for w in sub_sentence[j: j+n_len]])
    #                 self.ngrams[ngram] += 1
    #     self.ngrams = {i:j for i, j in self.ngrams.items() if j > self.min_count}

    def find_ngrams_pmi(self, texts, n, freq_threshold):
        for sentence in texts:
            # sub_sentence = sentence.split()
            # split the sentence into words, customizing the split_text function for chinese characters
            sub_sentence = split_text(sentence)
            # count the frequency of each word
            self.words[sub_sentence[0]] += 1
            for i in range(len(sub_sentence)-1):
                self.words[sub_sentence[i + 1]] += 1
                self.pairs[(sub_sentence[i], sub_sentence[i+1])] += 1
                # total means the total number of words
                self.total += 1
        self.words = {i: j for i, j in self.words.items() if j > self.min_count}
        self.pairs = {i: j for i, j in self.pairs.items() if j > self.min_count}

        # calculate the pointwise mutual information
        min_mi = math.inf
        max_mi = -math.inf

        self.strong_segments = set()
        for pair, pair_count in self.pairs.items():
            if pair[0] in self.words and pair[1] in self.words:
                # calculate the pointwise mutual information: log(p(x,y)/(p(x)*p(y)))
                mi = math.log(self.total * pair_count / (self.words[pair[0]] * self.words[pair[1]]))
                if mi > max_mi:
                    max_mi = mi
                if mi < min_mi:
                    min_mi = mi
                # if the pointwise mutual information is greater than the threshold, add the pair to the strong_segments
                if mi >= self.min_pmi:
                    self.strong_segments.add(pair)


        self.ngrams = defaultdict(int)
        for sentence in texts:
            # sub_sentence = sentence.split()
            sub_sentence = split_text(sentence)
            # cut the sentence into n-grams
            candidate_ngram = [sub_sentence[0]]
            for i in range(len(sub_sentence)-1):
                if (sub_sentence[i], sub_sentence[i+1]) in self.strong_segments:
                    candidate_ngram.append(sub_sentence[i+1])
                else:
                    self.ngrams[tuple(candidate_ngram)] += 1
                    candidate_ngram = [sub_sentence[i+1]]
        self.ngrams = {i:j for i, j in self.ngrams.items() if j > self.min_count and len(i) <= n}

        self.renew_ngram_by_freq(texts, freq_threshold, n)


    def renew_ngram_by_freq(self, all_sentences, min_feq, ngram_len=10):
        new_ngram2count = {}
        new_all_sentences = []

        for sentence in all_sentences:
            # sentence = sentence.split()
            sentence = split_text(sentence)
            sen = sentence
            # iterate through the sentence, 
            for i in range(len(sen)):
                for n in range(1, ngram_len + 1):
                    if i + n > len(sentence):
                        break
                    n_gram = tuple(sentence[i: i + n])
                    if n_gram not in self.ngrams:
                        continue
                    if n_gram not in new_ngram2count:
                        new_ngram2count[n_gram] = 1
                    else:
                        new_ngram2count[n_gram] += 1
        self.ngrams = {gram: c for gram, c in new_ngram2count.items() if c > min_feq}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, required=True, help="the name of dataset")
    parser.add_argument('--output_dir', type=str, required=True, help="the output path")
    parser.add_argument('--ngram', type=int, default=5, help="n")
    parser.add_argument('--min_count', type=int, default=5, help="min_count")
    parser.add_argument('--min_pmi', type=int, default=1, help="min_pmi")
    parser.add_argument('--ngram_freq_threshold', type=int, default=5, help="ngram_freq_threshold")
    parser.add_argument('--delete_special_symbol', action='store_false', help="Whether to remove special symbols")
    config = parser.parse_args()

    ngram_list = []
    dataset = config.dataset
    ngram = config.ngram
    min_count = config.min_count
    min_pmi = config.min_pmi
    ngram_freq_threshold = config.ngram_freq_threshold

    print('dataset: ', dataset)
    f_read = open(config.dataset, 'r')
    f_write = open(config.output_dir, 'w')

    sentence_list = []
    for line in f_read:
        # check if the line is empty
        if len(line.strip()) == 0:
            continue
        # replace all punctuations with space
        line = replace_punctuation(line)
        # check if the line is empty
        if len(line.strip()) == 0:
            continue
        sentence_list.append(line)

    ngram_finder = FindNgrams(min_count=min_count, min_pmi=min_pmi)
    ngram_finder.find_ngrams_pmi(sentence_list, ngram, ngram_freq_threshold)

    ngram_type_count = [0 for _ in range(ngram)]
    ngram_finder.ngrams = dict(sorted(ngram_finder.ngrams.items(), key = lambda kv:(kv[1], kv[0]), reverse=True))  #sort


    count = 0
    for w, freq in ngram_finder.ngrams.items():
        # print("w,c", w, c)
        count += 1
        s = ""
        for word_index in range(len(w)):
            word = w[word_index]
            # check if the word is a Chinese character
            if is_chinese_char(word):
                s += word
            else:
                s += w[word_index]+" "
        # reject the ngram that contains only one word
        if len(s) == 1:
            continue
        
        s += ","+str(freq)
        s = s.strip()
        i = len(s)
        if config.delete_special_symbol:
            while i>0:
                if s[i-1].isalnum():
                    break
                i -= 1
        s = s[0:i]
        if s not in ngram_list and len(s)>0:
            if s not in ngram_list:
                ngram_list.append(s)

    ngram_count = 0
    for ngram_phrase in ngram_list:
        ngram_count += 1
        f_write.write(ngram_phrase+'\n')
        # ngram_type_count[len(list(ngram_phrase.split())) - 1] += 1

    print(str(ngram_type_count))
    f_read.close()
    f_write.close()

if __name__ == '__main__':
    main()