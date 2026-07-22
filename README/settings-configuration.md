Our settings file is split up into three categories: toggleable features, theme, and comment box. Theme and comment box do not need to be altered by the researcher. They are responsible for the aesthetic and functionality of the text and the comment box.

The toggleable features can be switched on and off using true or false. The purposes of each of them are provided in the commented text in the figure below. All of these features are optional, meaning they can be toggled off, and the website will still function as intended. 

Configure conversation display settings in `static/settings.json`:

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

  "theme": {
    "textColor": "black",
    "fontFamily": "Lato, sans-serif",
    "fontSize": "16px",
    "siteBackgroundColor": "white",
    "commentBackgroundColor": "white",
    "commentIndentation": 0.75   // Indentation is 0.75 each
  },

  "commentBox": {
    "borderColor": "gray",
    "placeholderText": "Start typing...",
    "replyInComments": true,   // Whether the participant can reply or not
    "displayScore": true,   // upvotes - downvotes, if the corpus/conversation includes such information
    "displayCancel": true,
    "submitButtonText": "Submit",
    "anon_users": "z"
  }
}
```


**For social media data**: The `"displayScore"` setting may be particularly relevant if your corpus includes engagement metrics like upvotes, likes, or scores.
