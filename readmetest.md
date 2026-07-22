# An Open-Source Platform for Studying Conversational Interventions

This platform was designed for researchers interested in studying conversational interventions. It has an abstract interface, which decreases the coding burden for researchers (more information in [**Adapter and Interface**](#adapter-and-interface)). Our website also supports three popular general interventions: a popup box, highlighting, and a feedback box, which can be easily implemented to fit most research needs. Any additional interventions can be added by the researcher (more information in [**Interventions**](#interventions)). All actions taken by participants during the study are recorded and stored through our data collection system, which can later be accessed by researchers (more information in [**Data Collection**](#data-collection)).

---

## Our Mission

Designing a website tool from scratch requires valuable time, which could be spent conducting research. To lower the technical barrier, our adapter interface allows researchers to add their own conversations and interventions to our platform without touching the website code. This has all the required features already completed, such as general interventions that can be customized, a user interface where participants can interact with conversations, and data collection to store participants' actions during the study locally.

---

## How to Start

1. First, researchers must add their own adapter file in `backend/adapters`.

   * To learn more about this, see the [**Adapter and Interface**](#adapter-and-interface) section.

2. Next, researchers can add their own custom interventions.

   * To see an example of how to do this, see the [**Interventions**](#interventions) section.

3. Finally, researchers can customize the features to design their user studies using:

   * [**Settings Configuration**](#settings-configuration)
   * [**Surveys and Additional Pages**](#surveys-and-additional-pages)
   * [**Data Collection**](#data-collection)

---

## Required Technical Skills

While the majority of the files that researchers will edit will be in Python, small amounts of HTML and CSS are required to power new interventions or edit existing ones. Additionally, to add custom information to the introduction, instructions, or exit pages, researchers will need to edit the HTML files in the `templates` folder. More information about this can be found in the [**Surveys and Additional Pages**](#surveys-and-additional-pages) section.

Below is a detailed diagram of the HTML for the already implemented Popup class to help people looking to add their own interventions.

```html
<div class="your-intervention"
     id="your-intervention"
     data-intervention-type="your-intervention"
     data-event-id="YOUR-INTERVENTION">

    <h2>Your header here!</h2>

    <p>Your intervention text here!</p>

    <button
        class="your-intervention-button"
        id="your-intervention-button">
        OK
    </button>
</div>
```

> **Note:** When writing HTML, things in quotes like `"popup"` or `"popup-close-button"` are names that can be defined by the researcher. However, to maintain consistent database logging, the website requires the parent wrapper of the intervention to include `data-intervention-type` along with `data-event-id` for event logging in the database.

---

<a id="adapter-and-interface"></a>

## Adapter and Interface

The Adapter and Interface framework allows researchers to connect any type of conversation dataset to the platform without modifying the website itself. By implementing a small number of required interface functions, researchers can use Convokit corpora, JSON files, SQL databases, or other custom conversation formats.

➡️ **Read more:** [Adapter and Interface](docs/adapter-and-interface.md)

---

<a id="interventions"></a>

## Interventions

Our platform includes three built-in intervention types: popup boxes, highlighting, and feedback boxes. These interventions can be customized to support different research initiatives. Researchers can also create entirely new intervention types using the abstract base intervention class.

➡️ **Read more:** [Interventions](docs/interventions.md)

---

<a id="settings-configuration"></a>

## Settings Configuration

Most aspects of the platform can be configured through the settings file. Researchers can customize comment display, optional pages, surveys, reply behavior, timers, and other experiment settings without modifying the source code.

➡️ **Read more:** [Settings Configuration](docs/settings-configuration.md)

---

<a id="surveys-and-additional-pages"></a>

## Surveys and Additional Pages

In addition to the conversation interface, the platform supports optional welcome, instructions, and exit pages. Researchers can customize these pages, edit questionnaires, and configure which pages are displayed throughout the study.

➡️ **Read more:** [Surveys and Additional Pages](docs/surveys-and-additional-pages.md)

---

<a id="data-collection"></a>

## Data Collection

The platform automatically records participant interactions throughout the study, including user actions, intervention triggers, questionnaire responses, timestamps, and experimental conditions. These data are stored locally and can later be exported for analysis.

➡️ **Read more:** [Data Collection](docs/data-collection.md)

---

<a id="additional-features"></a>

## Additional Features

The platform also includes several optional features, including reading timers, minimum comment lengths, configurable reply restrictions, and other settings that can be enabled depending on the needs of the study.

➡️ **Read more:** [Additional Features](docs/additional-features.md)
