# Setting and Configuration 

Our settings file is split up into three categories: toggleable features, theme, and comment box. Theme and comment box do not need to be altered by the researcher. They are responsible for the aesthetic and functionality of the text and the comment box. All of the code below can be found in `static/settings.json`. 

## Toggleable Features 
The toggleable features can be switched on and off using `true` or `false`. The purpose of each feature is provided in the commented text in the figure below. All of these features are optional, meaning they can be toggled off and the website will still function as intended. `minCommentLength` is slightly different, as the number represents the minimum comment length. Therefore, to turn this feature off, it must be set to `0`.
```json
{
  "toggleable_features": {
    "readingTimerEnabled": true/false,   // Minimal reading time of the conversation, now set to 1000 words per minute in app.py
    "minCommentLength": 0,   // Minimal reply length of the participant in characters
    "replyToAnywhere": true/false,   // Whether the participant can reply to any utterance in the conversation or only to the last one
    "instructionPageEnabled": true/false,   // Show Instruction Page or not
    "trajectorySummaryBoxEnabled": true/false,   // Show Summary box on instruction page or not. If there's no summary, the box won't show up automatically
    "welcomePageEnabled": true/false,   // Show Welcome Page or not
    "entryQuestionnaireEnabled": true/false,   // Show entry questionnaire on welcome page or not.
    "exitPageEnabled": true/false,   // Show Exit Page or not
    "exitQuestionnaireEnabled": true/false   // Show exit questionnaire on exit page or not.
  },
```
## Theme 
The theme portion controls the visual aesthetics of the website. This includes features such as the text color, size, and font. Additionally, it controls the background color of the chat page and the color of the comment box. It also controls indents. This does not need to be edited by the researcher, but they may do so if they want to alter the physical appearance of the chat page.

```json

  "theme": {
    "textColor": "black",
    "fontFamily": "Lato, sans-serif",
    "fontSize": "16px",
    "siteBackgroundColor": "white",
    "commentBackgroundColor": "white",
    "commentIndentation": 0.75   // Indentation is 0.75 each
  },
```
## Comment Box  
The comment box section controls the appearance of the comment box. This determines attributes such as the color, what is displayed in the comment box before the user types anything, and the text on the submit button. It also controls functionality, such as whether the user is allowed to reply to the comment, whether the score (upvotes - downvotes) is displayed, and whether the usernames of the previous comments are changed to be anonymous (e.g., `Speaker 1` instead of `JoeAndFred31`).

```json
  "commentBox": {
    "borderColor": "gray",
    "placeholderText": "Start typing...",
    "replyInComments": true,   // Whether the participant can reply or not
    "displayScore": true,   // upvotes - downvotes, if the corpus/conversation includes such information
    "displayCancel": true,
    "submitButtonText": "Submit",
    "anon_users": true/false    // Turn on/off the speaker name anonymization. If true, the speakers have names like "Speaker 1"; if false, the speakers have their real names as in the corpora.
  }
}
```
**For social media data**: The `"displayScore"` setting may be particularly relevant if your corpus includes engagement metrics like upvotes, likes, or scores.
