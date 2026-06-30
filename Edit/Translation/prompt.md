I already have page translation engine that uses language translation keys to replace passed text with translated one;
Lets update page translation for specific language;

1. Update provided HTML file (or files) to update "translate" attribute value(s) based on the task, like this:
```html
<h2 translate="channels_title">Groups and Channels</h2>
```

2. Update provided JavaScript file (or files) to update App.lng(translation_key, system_text) system_text value based on the task, like this:
```js
// Simply:
var hint = App.lng("youtube", "YouTube Channel");
// Or with dynamic variables in rare cases:
var hint = App.lng("introduction", "My name is {name}, I am from {country}.", {name: "John", country: "US"});
```

3. Update provided PHP file (or files) to update App::lng($translation_key, $system_text) $system_text value based on the task, like this:
```php
// Simply:
$hint = App::lng('share', 'Share to others');
// Or with dynamic variables in rare cases:
$hint = App::lng('introduction', 'My name is {name}, I am from {country}.', ['name' => 'John', 'country' => 'US']);
```

4. Create new JSON file "lng.__.json" that contains all used translation_keys along with translated system texts, like this:
[lng.ka.json]
```json
{
  "channels_title": "ჯგუფები და არხები",
  "youtube": "YouTube არხი",
  "share": "სხვებთან გაზიარება",
  "introduction": "მე მქვია {name}, მე ვარ {country} -დან."
}
```

> Note: Use this filename format "lng.__.json" just replace "__" with abreviation of the language that I will request (e.g 'lng.ka.json' for Georgian language);

# The Task

You must uppdate the existing code files and create translation JSON file based on this task:
[[MESSAGE]]
