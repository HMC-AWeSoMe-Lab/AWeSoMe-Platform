# An Open-Source Platform for Studying Conversational Interventions

## Our Mission

Designing a website tool from scratch requires valuable time, which could be spent conducting research. To lower the technical barrier, our adapter interface allows researchers to add their own conversations and interventions to our platform without touching the code that sets up the website, such as the HTML files of the pages. The platform has all the required features already completed, such as general interventions that can be customized, a user interface where participants can interact with conversations, and data collection to store participants' actions during the study locally.

![Chat Page](docs/chat.svg)

---

This platform was designed for researchers interested in studying conversational interventions. It has an abstract interface, which decreases the coding burden for researchers (more information in [**Adapter and Interface**](#adapter-and-interface)). Our website also supports three popular general interventions: a pop-up box, highlighting, and a feedback box, which can be easily implemented to fit most research needs. Any additional interventions can be added by the researcher (more information in [**Interventions**](#interventions)). All actions taken by participants during the study are recorded and stored through our data collection system, which can later be accessed by researchers (more information in [**Data Collection**](#data-collection)).

---

## How to Start

If the researchers want to test out this platform without designing their own user studies, they can directly run app.py, which uses the dummy adapter, demo adapter, or convokit adapter as examples. For detailed instructions on this, go to [**Adapter and Interface**](docs/adapter-and-interface.md).

1. First, researchers must add their own adapter file in `backend/adapters`.

   * To learn more about this, see the [**Adapter and Interface**](#adapter-and-interface) section.

2. Next, researchers can add their own custom interventions.

   * To see an example of how to do this, see the [**Interventions**](#interventions) section.

3. Finally, researchers can customize the features to design their user studies using:

   * [**Platform Structure**](#platform-structure)
   * [**Surveys and Additional Pages**](#surveys-and-additional-pages)
   * [**Data Collection**](#data-collection)
   * [**Settings Configuration**](#settings-configuration)

---

## Required Technical Skills

While the majority of the files that researchers will edit will be in Python, small amounts of HTML and CSS are required to add new interventions or edit existing ones. Additionally, to add custom information to the introduction, instructions, or exit pages, researchers will need to edit the HTML files in the templates folder. More information about this can be found in the [**Surveys and Additional Pages**](#surveys-and-additional-pages) and the [**Interventions**](#interventions). 


---
<a id="platform-structure"></a>
## Platform Structure

The platform consists of one main conversation page and three optional pages: the welcome page, instructions page, and ending page. The pages start with the welcome page which contains a survey, moves on to the instructions page which can optionally hold a conversation summary, next is the chat page, and ends with the ending page which can contain a survey. 

➡️ **Read more:** [Platform Structure](docs/platform-structure.md)

<a id="adapter-and-interface"></a>

## Adapter and Interface

The Adapter and Interface framework allows researchers to connect any type of conversation dataset to the platform without modifying the website itself. By implementing a small number of required interface functions, researchers can use Convokit corpora, JSON files, SQL databases, or other custom conversation formats.

➡️ **Read more:** [**Adapter and Interface**](docs/adapter-and-interface.md)

---

<a id="interventions"></a>

## Interventions

Our platform includes three built-in intervention types: popup boxes, highlighting, and feedback boxes. These interventions can be customized to support different research initiatives. Researchers can also create entirely new intervention types using the abstract base intervention class.

➡️ **Read more:** [Interventions](docs/interventions.md)


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


<a id="settings-configuration"></a>

## Settings Configuration

Most aspects of the platform can be configured through the settings file. Researchers can customize comment display, optional pages, surveys, reply behavior, timers, and other experiment settings without modifying the source code.

➡️ **Read more:** [Settings Configuration](docs/settings-configuration.md)
