# Surveys and Additional Pages

In order to edit the information displayed on the introduction, instructions, or exit pages, the researcher must edit the HTML files from the `templates` folder. The files `welcome.html` and `instructions.html` can be edited to add text to the introduction and instructions. In order to do this, all the researcher must do is change the text in the content area. An example is provided below:

```html
{% block body %}
<div class="welcome-wrapper">
<h1 class="welcome-title">Welcome!</h1>
<div class="welcome-section">
  <h2>Introduction</h2>
  <div class="content-area"> Hi, welcome to our project! Please be aware that the displayed conversation might include concerning contents. If you feel good to proceed, please check 'I consent'. </div> <!-- Change this text!! -->
</div>
```

In order to change the intro and exit surveys. Researchers can edit the `ending.html` and `welcome.html` files. If the researcher would like to create more questions they can create them based off the example below.

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
  </div>
</div>
```

If the researcher would like to keep the same style (multiple choice), they can just edit the current template to change the question and text in the multiple choice boxes.

All three of these pages are toggleable and can be turned on and off in the `settings.json` file. Additionally, if researchers would like to keep the pages and not the surveys, these can be toggled off as well.

If researchers have generated summaries for their corpora, they can display these on the instructions page. If the researcher does not have a summary stored, the box containing the summary will automatically not be displayed. To change this, the researcher must store their summary in the meta data as `trajectory_summary` this will then be accessed in the `instructions.html` file to be displayed. If they have a summary, but do not want it displayed, this can be toggled on and off in the `settings.json` file as well.

To see what settings to turn on and off for each page and survey, check the **[Settings Configuration](settings-configuration.md)** section.
