# Surveys and Additional Pages

In order to edit the information displayed on the introduction, instructions, or ending pages, the researcher must edit the HTML files from the `templates` folder. The files `welcome.html` and `instructions.html` can be edited to add text to the introduction and instructions. In order to do this, all the researcher must do is change the text in the content area. It is important that researchers maintain the existing naming and classes, as our website requires this information for the pages to be displayed properly. When editing this page, it is easiest to just change the text. However, if researchers want to add something, make sure to keep this naming convention. An example is provided below:

```html
{% block body %}
<div class="welcome-wrapper">
<h1 class="welcome-title">Welcome!</h1>
<div class="welcome-section">
  <h2>Introduction</h2>
  <div class="content-area"> Hi, welcome to our project! Please be aware that the displayed conversation might include concerning content. If you feel good to proceed, please check 'I consent'. </div> <!-- Change this text!! -->
</div>
```

In order to change the intro and exit surveys, researchers can edit the `ending.html` and `welcome.html` files. If the researcher would like to create more questions, they can create them based on the example below.

```html
{% if entry_questionnaire_enabled %}
 <div class="welcome-section">
   <h2>Beginning Questionnaire</h2>
   <div class="content-area">
     <p class="question-text">Q1: Have you ever encountered toxic discussions online?</p>
     <div class="choices">
       <label class="choice-label">
         <input type="radio" name="q1" value="1"> Yes
       </label>
       <label class="choice-label">
         <input type="radio" name="q1" value="2"> No
       </label>
     </div>
     <p class="question-text" style="margin-top: 1.25rem;">Q2: Please briefly describe the toxic conversation you met before. If you haven't encountered any, please write N/A.</p>
     <textarea class="free-response-box" name="q2" id="q2" placeholder="Type your response here..."></textarea>
   </div>
 </div>
```

The researcher can add their own questions based on the example provided above. If the researcher would like to add more questions, it is important that they stick to the template provided, as our website requires the class information and naming conventions.

All three of these pages are toggleable and can be turned on and off in the `settings.json` file. Additionally, if researchers would like to keep the pages but not the surveys, these can be toggled off as well.

If researchers have generated summaries for their corpora, they can display these on the instructions page. If the researcher does not have a summary stored, the box containing the summary will automatically not be displayed. To do this, the researcher must store their summary in the metadata as `trajectory_summary`. This will then be accessed in the `instructions.html` file and displayed. If they have a summary but do not want it displayed, this can be toggled on and off in the `settings.json` file as well.

To see what settings to turn on and off for each page and survey, check the **[Settings Configuration](settings-configuration.md)** section.
