# Additional Features

All of our additional features are optional and must be toggled on by the researcher.

Our timer is currently set to a reading speed of 1000 words per minute as participants are likely skimming the content and not deeply reading it. This can be changed in `app.py` where the researcher can change `1000` to whatever reading speed they would like.

```python
all_text = " ".join(utt.text for utt in convo.iter_utterances() if utt.text)
word_count = len(re.findall(r'\w+', all_text))
reading_seconds = max(10, (word_count / 1000) * 60)
```

We set the minimum comment length to 10 characters, but this can be changed in `settings.json`.

Our website also allows researchers to decide whether they would like participants to be able to respond to anywhere in the conversation or just the last comment.

In order for the researcher to turn on these optional features, they must turn them to `true` in the `settings.json` file.

To learn more about this check the **[Settings Configuration](settings-configuration.md)** section.
