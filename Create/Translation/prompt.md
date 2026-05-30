I already have page translation engine that uses language translation keys to replace passed text with translated one;
Lets enable page translation, follow these steps:

1. Update provided HTML page file to add page translation tag on top right corner of page (or to the end of navigation if menu exists), like this:
```html
<translation languages="en,ka" />
```

> Note: If the translation tag already exists, just append requested new language abbreviation (e.g 'ru') to the languages attribute CSV list;

2. Update provided CSS file to style page translation tag if not styled already, add:
```css
translation {
  position: fixed; /* set 'position: fixed;' if page has no navigation; or set 'display: flex;' if page has navigation */
  top: 20px;
  right: 20px;
  /* Do not apply margin or padding! */
}

translation img {
  width: 40px; /* Adjustable */
  height: 40px; /* Adjustable */
  border-radius: 100px;
  transition: 0.3s ease-in-out;
  border: 2px solid #afafaf;
  object-fit: cover;
  cursor: pointer;
  /* Do not apply margin or padding! */
}

translation img:hover {
  opacity: 0.8;
}
```

3. Update provided HTML file (or files) to add attribute named 'translate' with unique (translation key) value to all HTML tags that display hardcoded text of the page, like this:
```html
<h2 translate="channels_title">Groups and Channels</h2>
```

4. Update provided JavaScript file (or files) to use App.lng(translation_key, system_text) method to display hardcoded text on page, like this:
```js
// Simply:
var hint = App.lng("youtube", "YouTube Channel");
// Or with dynamic variables in rare cases:
var hint = App.lng("introduction", "My name is {name}, I am from {country}.", {name: "John", country: "US"});
```

5. Update provided PHP file (or files) to use App::lng($translation_key, $system_text) method to display hardcoded text on page, like this:
```php
// Simply:
$hint = App::lng('share', 'Share to others');
// Or with dynamic variables in rare cases:
$hint = App::lng('introduction', 'My name is {name}, I am from {country}.', ['name' => 'John', 'country' => 'US']);
```

6. Create new JSON file "lng.__.json" that contains all used translation_keys along with translated system texts, like this:
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

# Language Request
[[MESSAGE]]
