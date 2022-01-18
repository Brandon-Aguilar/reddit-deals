import praw
from pathlib import Path
import os
from win_toaster import create_toast
import webbrowser
import time
import tkinter
import json


# TODO Add keyword files
# format file management
# implement other flair types
# copy old html files to log

def getDataDict(reddit, lastReadFile="submissionData/lastRead.txt", limit=100, subreddit=""):
    """ Retrieves posts from r/buildapcsales/new and filters for graphics cards

        All posts are then stored into the given file.
        A lastRead file is needed to retrieve posts before the last read post.
        Returns a bool value of whether a new post was seen.
        Requires a reddit instance.
    """

    graphicsList = []
    cpuList = []
    moboList = []
    monitorList = []
    memoryList = []
    preBuiltList = []

    keyWords = ["gpu", "graphics", "3090", "3080",
                        "3070", "3060", "2080", "2070", "2060",
                        "1080", "1070", "1060", "1050", "1660"]
    
    graphicsKeyWords = []
    cpuKeyWords = ["amd", "intel", "3900x", "i7", "i5", "i3", "pentium"]
    moboKeyWords = []
    monitorKeyWords = []
    memoryKeyWords = []

    directoryName = "submissionData"
    directoryPath = Path(directoryName)
    #check file for last submission read
    if not directoryPath.exists():
        os.mkdir("submissionData")

    lastRead = Path(lastReadFile)
    callParams = {
        "before": None
    }
    if lastRead.exists():
        f = open(lastRead)
        lastSubmission = f.read()
        print(lastSubmission)
        callParams = {
            "before": lastSubmission
        }
        f.close()

    foundNewCPUPost = False
    foundNewGraphicsPost = False
    foundNewMoboPost = False
    foundNewMonitorPost = False
    foundNewMemoryPost = False
    foundNewPrebuiltPost = False

    firstFlag = False
    # call to check submissions in new

    submissionList = reddit.subreddit("buildapcsales").new(limit=limit, params=callParams)
    

    for submission in submissionList:
        # saves the value of the most recent (first) submission
        if not firstFlag:
            with open(lastReadFile, 'w', encoding='utf-8') as f:
                f.write(submission.name)
                f.close()
                firstFlag = True
        # change the temporary title to lower case so we can compare easier
        title = submission.title.lower()

        # save and check if a flair is used. We discard any submissions without a flair
        flair = submission.link_flair_text
        if flair is None:
            continue

        # find the cost of the submission and discard submission if none is given or if price is irrelevant to post
        costIndex = title.find("$")
        if costIndex == -1:
            continue
        cost = title[costIndex:]

        if "$0" in cost:
            continue


        #check what the post is about and add the submission to the associated list
        if "GPU" in flair or ("Meta" in flair and submission.url != submission.permalink) and any(word in title for word in graphicsKeyWords):
            foundNewGraphicsPost = True
            graphicsList.append(submission)

        elif "CPU" in flair or ("Meta" in flair and submission.url != submission.permalink) and any(word in title for word in cpuKeyWords):
            foundNewCPUPost = True
            cpuList.append(submission)

        elif "Motherboard" in flair or ("Meta" in flair and submission.url != submission.permalink) and any(word in title for word in moboKeyWords):
            foundNewMoboPost = True
            moboList.append(submission)

        elif "Monitor" in flair or ("Meta" in flair and submission.url != submission.permalink) and any(word in title for word in monitorKeyWords):
            foundNewMonitorPost = True
            monitorList.append(submission)

        elif "RAM" in flair or ("Meta" in flair and submission.url != submission.permalink) and any(word in title for word in memoryKeyWords):
            foundNewMemoryPost = True
            memoryList.append(submission)

        elif "Prebuilt" in flair:
            foundNewPrebuiltPost = True
            preBuiltList.append(submission)

    

    submissionDictionary = {}

    # Generate a dictionary based on lists acquired
    if foundNewGraphicsPost:
        submissionDictionary["gpu"] = graphicsList

    if foundNewCPUPost:
        submissionDictionary["cpu"] = cpuList

    if foundNewMoboPost:
        submissionDictionary["mobo"] = moboList

    if foundNewMonitorPost:
        submissionDictionary["monitor"] = monitorList

    if foundNewMemoryPost:
        submissionDictionary["memory"] = memoryList

    if foundNewPrebuiltPost:
        submissionDictionary["prebuilt"] = preBuiltList

    return submissionDictionary


def open_url(page_url = ""):
    fileName = "bapcsLog.txt"
    file = Path(fileName)
    with open(file, 'a', encoding='utf-8') as f:
        try:
            webbrowser.open_new(page_url)
            f.write("\n Opening URL: " + page_url)
        except:
            print('\n Failed to open URL: ' + page_url)


def generateNotifications(reddit, submissionDict={}):
    """Takes in a dictionary of submissions and generates notifications

    A valid reddit instance must be passed.
    The notification generated will give a link
    that leads to the reddit post.
    """
    # Open file that contains gpu info and submission fullnames

    # Get data from each file in submissionDict
    for key in submissionDict:
        for submission in submissionDict[key]:
            title = submission.title
            link = "https://reddit.com" + submission.permalink

            cost = ""
            
            # find $ sign to get cost, we keep everything till the next space
            # We ignore XX$ format.
            costIndex = submission.title.find("$")
            nextSpace = submission.title.find(" ", costIndex)
            costString = ""
            if nextSpace == -1:
                costString = submission.title[costIndex:]
            else:
                costString = submission.title[costIndex:nextSpace]

            validChars = ["0", "1", "2", "3", "4", "5",
                          "6", "7", "8", "9", ".", ",", "-", "$"]
            for i in costString:
                if i not in validChars:
                   break
                cost += i
            if len(cost) <= 1:
                cost = ""
                    
            if cost != "":
                title = cost + " " + title
            
            iconPath = Path("bapc.ico")
            icon = "bapc.ico"
            if not iconPath.exists():
                icon = None
            message = "A new part has been seen on Reddit"
            create_toast(
                title,  # title
                message,  # message
                icon_path=icon,  # 'icon_path'
                duration=None,  # for how many seconds toast should be visible; None = leave notification in Notification Center
                threaded=False,  # True = run other code in parallel; False = code execution will wait till notification disappears
                callback_on_click=lambda: open_url(link)  # click notification to run function
            )
            

    
    return

def generateFile(submissionDict, fileName="index.html"):
    file = Path(fileName)
    with open(file, 'w', encoding="utf-8") as f:
        f.write("<!DOCTYPE html> \n")
        f.write("<html> \n")
        f.write("<h1> Reddit Posts </h1> \n")
        f.write("<table>")
        f.write("<tr> \n <th> Submission Post </th> \n </tr> \n")
        for key in submissionDict:
            for submission in submissionDict[key]:
                f.write("<tr> \n <td>" + "<a href=\"https://www.reddit.com" +
                        submission.permalink + "\"> <div>")
                f.write(submission.title)
                f.write("</div> </a> </td> \n")
                f.write("</tr> \n")
        f.write("</table> \n")

        f.write("</html>")

def genAndOpenFile(submissionDict, fileName = "index.html"):
    generateFile(submissionDict, fileName)
    webbrowser.open('file:///'+os.getcwd() + '/' + fileName, new=0, autoraise=False)


def printDataDict(reddit, dataPaths={}, showPrice=False):
    """Prints every part type from a list of submissions.
    
    This function is useful for calling multiple parts
    This will shorten the amount of API calls needed to get all submission data
    by batching the submissions
    Requires a reddit instance and either a fileName or list of paths
    If both fileName and dataPaths are passed, both will be used,
    this can cause duplicated data
    """
    # Open file that contains gpu info and submission fullnames

    submissionList = []

    # Get data from each file in dataPaths
    for key in dataPaths:
        for i in dataPaths[key]:
            submissionList.append(i)

    # Turn submission fullnames into Submission objects and print info
    for submission in submissionList:
        print(submission.title)
        print("reddit.com" + submission.permalink)
        if showPrice:
            costIndex = submission.title.find("$")
            nextSpace = submission.title.find(" ", costIndex)
            costString = ""
            if nextSpace == -1:
                costString = submission.title[costIndex:]
            else:
                costString = submission.title[costIndex:nextSpace]

            newCostString = ""

            validChars = ["0", "1", "2", "3", "4", "5",
                          "6", "7", "8", "9", ".", ",", "-", "$"]
            for i in costString:
                if i == "-":
                    print()
                if i not in validChars:
                   break
                newCostString += i
            if len(newCostString) > 1:
                print(newCostString)
            else:
                print("Invalid Price Format. See title.")

        print()
    return

def main():
    # Create our instance of reddit

    reddit = praw.Reddit(
        client_id="CLIENT_ID",
        client_secret="CLIENT_SECRET",
        redirect_uri="https://mstu.io",
        user_agent="TestBot by Mushroomstew07",
    )
    

    limit = 100
    maxNotifications = 1

    submissionDictionary = getDataDict(reddit, limit=limit)
    #genAndOpenFile(submissionDictionary)
    if len(submissionDictionary) == 0:
        return
    else:
        iconPath = Path("bapc.ico")
        icon = "bapc.ico"
        if not iconPath.exists():
            icon = None
        notification = create_toast(
            "Multiple New Parts Seen on Reddit",  # title
            "A large amount of parts with your keywords were seen on reddit. \nA file with available links was generated.",  # message
            icon_path=icon,  # 'icon_path'  
            duration=50, # for how many seconds toast should be visible; None = leave notification in Notification Center
            threaded=True,  # True = run other code in parallel; False = code execution will wait till notification disappears
            callback_on_click=lambda: genAndOpenFile(submissionDictionary)
        )
        notification.display()
    print()

    


if __name__ == "__main__":
    main()


