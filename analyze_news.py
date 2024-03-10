import requests
from bs4 import BeautifulSoup
import nltk
from nltk import pos_tag
from nltk.tokenize import sent_tokenize, word_tokenize
from textblob import TextBlob

def Analyze_news(url):
    """It sends request and fetches the data from the web"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        headline = soup.find("h1", class_="native_story_title").text
        main_content = soup.find("div",id ="pcl-full-content")
        paragraphs = main_content.find_all('p')
        paragraph_texts = [p.get_text() for p in paragraphs]



        cleaned_text = ""
        adder=0
        for sentence in paragraph_texts:
            for char in sentence:
              if char=='.':
                adder+=1
            cleaned_sentence = ''.join(sentence.split('.'))
            cleaned_sentence = ''.join(cleaned_sentence.split(','))
            cleaned_text += cleaned_sentence

        # Perform analysis
        sentences = nltk.sent_tokenize(cleaned_text)
        num_sentences = adder
        words = nltk.word_tokenize(cleaned_text)
        num_words = len(words)
        pos_tags = pos_tag(words, tagset='universal')


        pos_tag_counts = {}
        for word, tag in pos_tags:
            if tag != '.':
                if tag in pos_tag_counts:
                    pos_tag_counts[tag] += 1
                else:
                    pos_tag_counts[tag] = 1

        #calculating sentiment
        sentiment = TextBlob(cleaned_text).sentiment
        

        if sentiment.polarity > 0:
            sentiment_label = 'Positive'
        elif sentiment.polarity < 0:
            sentiment_label = 'Negative'
        else:
            sentiment_label = 'Neutral'


        return {
          "url": url,
          "text": cleaned_text,
          "num_sentences": num_sentences,
          "num_words": num_words,
          "pos_tags": len(pos_tags),
          "pos_tag_counts": pos_tag_counts,
          "sentiment_labels": sentiment_label,
          "headlines" : headline
        }
    except Exception as e:
        print(f"Error: {e}")
        return None
