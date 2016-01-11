# coding=utf-8
# Andrew Estis
# January 2016

import os
import json
import jieba
from datetime import *

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


class weiboPost():
    # Standardized class to contain relevant information from Weibo posts. Extracted from JSON fields.
    def __init__(self, postID, userID, postType):
        self.postID = postID
        self.userID = userID
        self.postType = postType

        self.text = ""
        self.hasKors = False
        self.korsTerm = ""
        self.hasSpade = False
        self.spadeTerm = ""

        self.location = []
        self.gender = ""


def mainEvaluator():
# Main
    weiboPostList = [] #List of weiboPost objects.

    # terms & variations for each brand name below.
    chineseTermsForMK = ["米高歌斯", "迈克尔科尔斯", "迈克", "科尔斯", "Michael Kors", "MichaelKors", "Kors"]
    chineseTermsForKS = ["凯特丝蓓", "凯特", "丝蓓", "Kate Spade", "KateSpade", "Spade"]
    chineseFashionTerms = chineseTermsForMK + chineseTermsForKS

    for dirGroup in os.walk("weibo_dataset/weibo"): # Walk through the 'weibo' directory...
        for subDir in dirGroup[2]: # subDir would point to an individual file within the date directory.
            if subDir[0] == '.':
                continue  # Skip .DS_STORE
            postDir = dirGroup[0]+"/"+subDir  # Entire directory of post.

            with open(postDir, "r") as currJsonFile:
                currData = json.load(currJsonFile)  # Load json

                for postType in ["comment", "repost", "status"]:
                    if postType in postDir:  # look to the directory of the file to find which dir it is in.=
                        currPostType = postType

                currPost = weiboPost(currData["id"], currData["user"]["id"], currPostType) #Instantiate weiboPost object
                currPost.location = currData["user"]["location"].split()  #include location information in list form
                currPost.gender = currData["user"]["gender"] # Include poster's gender

                currPost.timestamp = (datetime.strptime(currData["created_at"], "%a %b %d %H:%M:%S +0800 %Y"))
                # Noted that the timezone is always +0800 (China); did not include timezone-aware logic here in
                # the interest of time (no pun intended).

                if currPostType == "repost":  # Repost text is stored in a different location than other post types.
                    currPost.text = currData["retweeted_status"]["text"]
                else:
                    currPost.text = currData["text"]

                currPost.hasKors, currPost.korsTerm = findBrand(currPost, chineseTermsForMK)  # Find MK Mentions
                currPost.hasSpade, currPost.spadeTerm = findBrand(currPost, chineseTermsForKS)  # Find KS Mentions
                weiboPostList.append(currPost)  # Add to weiboPostList. All functions iterate through this list of objs.

    question1(weiboPostList)
    question2(weiboPostList)
    question3(weiboPostList, chineseFashionTerms)

    genderBias(weiboPostList)


def findBrand(currPost, termsForBrand):
    # Find brand-related terms in post
    hasBrand = False
    brandTerm = "" # keyword indicating post is related to a brand

    for term in termsForBrand:
        if term in currPost.text: #If any of the keywords are found, mark hasBrand as TRUE and kick out / return.
            hasBrand = True
            brandTerm = term
            break

    return hasBrand, brandTerm


def question1(weiboPostList):
    # Output function with answers to questions 1(a) and 1(b).
    provinceDict = {}
    overseasDict = {"其他": 0, "海外": 0}

    MK_Count, KS_Count = 0, 0 
    for post in weiboPostList:
        if post.hasKors:
            MK_Count += 1
        if post.hasSpade:
            KS_Count += 1
        if post.location[0] == "其他":
            continue
        elif post.location[0] == "海外":  # Add 1 to international locations in int'l dictionary.
            if post.location == ["海外"]:
                overseasDict["海外"] += 1
            elif post.location[1] in overseasDict:
                overseasDict[post.location[1]] += 1
            else:
                overseasDict[post.location[1]] = 1
        elif post.location[0] in provinceDict:  # Add 1 to provincial locations in Province dictionary.
            provinceDict[post.location[0]] += 1
        else:
            provinceDict[post.location[0]] = 1

    print "Total posts:", len(weiboPostList)
    print "MK:", MK_Count
    print "KS:", KS_Count

    print "\nTop 10 posting locations within China:"
    for data in sorted(provinceDict.iteritems(), key=lambda tup: tup[1], reverse=True)[:10]:
        print data[0], data[1]

    print "\nTop 10 posting locations globally:"
    for data in sorted(overseasDict.iteritems(), key=lambda tup: tup[1], reverse=True)[:12]:
        # Increased to 12 to quickly exclude values "其他" and "海外"
        print data[0], data[1]



def question2(weiboPostList):
    # Find highest posts about each brand within a given hour and day.
    dateDict = {}
    hourDict = {}

    for date in set(post.timestamp.date() for post in weiboPostList):  # Add all distinct dates to the dictionary.
        dateDict[date] = 0
    for hour in range(0, 24): # Add hours 0-24 to dictionary.
        hourDict[hour] = 0

    for brand in ("Michael Kors", "Kate Spade"): #For both brand names...
        if brand == "Michael Kors":
            brandSubList = filter(lambda x: x.hasKors, weiboPostList) # Create a sublist of only posts mentioning brand
        else:
            brandSubList = filter(lambda x: x.hasSpade, weiboPostList)

        for post in brandSubList:  # Add to the date and hour keys in dict for each post that satisfies those criteria.
            dateDict[post.timestamp.date()] += 1
            hourDict[post.timestamp.hour] += 1

        if brand == "Michael Kors":
            korsDate = max(dateDict.iterkeys(), key=(lambda key: dateDict[key])) # Find key with max value for each dict
            korsHour = max(hourDict.iterkeys(), key=(lambda key: hourDict[key]))
            print "Most frequent posts for "+brand+" on date: "+korsDate.strftime("%a %b %d %Y")
            print "("+str(dateDict[korsDate]), "posts)"  # print key with highest value.
            print "Most frequent posts for "+brand+" between: "+str(korsHour)+":00 and "+str(korsHour+1)+":00"
            print "("+str(hourDict[korsHour]), "posts)"
        else:
            spadeDate = max(dateDict.iterkeys(), key=(lambda key: dateDict[key]))
            spadeHour = max(hourDict.iterkeys(), key=(lambda key: hourDict[key]))
            print "Most frequent posts for "+brand+" on date: "+spadeDate.strftime("%a %b %d %Y")
            print "("+str(dateDict[spadeDate]), "posts)"
            print "Most frequent posts for "+brand+" between: "+str(spadeHour)+":00 and "+str(spadeHour+1)+":00"
            print "("+str(hourDict[spadeHour]), "posts)"


def question3(weiboPostList, chineseFashionTerms):
    # Tokenize and count terms included in posts about each brand.

    ignoreMoreTerms = True # Set to 'true' to exclude more common chinese terms.

    # Dump commonly-occurring tokens and symbols.
    ignoreTerms = chineseFashionTerms + [" ", "#", "@", ".", "。", "&", "spade", "回复", "【", "的", "，", "/", "]",
                                         "[", "!", ":", "：", "�", "~", "～", "`", "、", "】", "a", "t", "c", "h",
                                         "！", "cn", "http", ",", "哦", "了", "”", "“", ">", "$"]
    if ignoreMoreTerms:
        # Exclude these common Chinese pronouns, particles, and verbs. (and, is, he, she, no, also, etc.)
        ignoreTerms.extend(["你", "我", "他", "她", "它", "都", "有", "是", "和", "在", "没", "不", "也", "日", "就",
                            "你们", "2015", "会", "为"])

    # Exclude other variations on the brand names.
    for term in ["Michael", "Kate", "Kors", "MK"]:
        ignoreTerms.append(term)
        ignoreTerms.append(term.upper())
        ignoreTerms.append(term.lower())

    for brand in ["Michael Kors", "Kate Spade"]:
        tokenFrequencies = {}  # Create a new dict to store the amount of occurrences of each token.
        if brand == "Michael Kors":
            currPostList = filter(lambda x: x.hasKors, weiboPostList)
        else:
            currPostList = filter(lambda x: x.hasSpade, weiboPostList)

        for post in currPostList:
            postText = unicode(post.text)  # encode to unicode (so as to be parseable by jieba)
            postTokens = jieba.tokenize(postText)  # collect tokenization results for that post in postTokens.
            for token in postTokens:
                if token[0] in ignoreTerms:
                    continue  # Drop ignored terms.
                if token[0] in tokenFrequencies: # If it already exists in dict, +1
                    tokenFrequencies[token[0]] += 1
                else: # Else, create an entry
                    tokenFrequencies[token[0]] = 1
        print
        print "Token frequency data for", brand+":"
        for data in sorted(tokenFrequencies.iteritems(), key=lambda tup: tup[1], reverse=True)[:12]:
            # Printed top 12 here to quickly exclude values like "<?>" ("can't display UTF" character)
            print "Word:", data[0], "\t", "Frequency:", data[1]


def genderBias(weiboPostList):
    # Detect % participation of males / females in the mentions of either brand.
    MK_Count, korsMale, KS_Count, spadeMale = 0, 0, 0, 0    # Counters for overall mentions and mentions by males.
                                                            # Back into female mentions.
    MK_List = filter(lambda x: x.hasKors and x.gender in ["m", "f"], weiboPostList)
    KS_List = filter(lambda x: x.hasSpade and x.gender in ["m", "f"], weiboPostList)
    for subList in (MK_List, KS_List):
        for post in subList:
            if post.gender == "m":
                if subList == MK_List:
                    korsMale += 1  # Add to male counter if male, else continue the loop.
                else:
                    spadeMale += 1

    korsPctMale = korsMale / float(len(MK_List))  # Use floats to display percentages.
    spadePctMale = spadeMale / float(len(KS_List))
    overallPctMale = (korsMale + spadeMale) / float(len(MK_List) + len(KS_List))
    print
    print "MK: ", korsMale, "Males,", len(MK_List)-korsMale, "Females"
    print "KS: ", spadeMale, "Males,", len(KS_List)-spadeMale, "Females"
    print "MK % Male:", str(korsPctMale*100)+"%; % Female:", str((1-korsPctMale)*100)
    print "KS % Male:", str(spadePctMale*100)+"%; % Female:", str((1-spadePctMale)*100)
    print "Overall % Male:", str(overallPctMale*100)+"%; % Female:", str((1-overallPctMale)*100)

mainEvaluator()
