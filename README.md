# Kushiyaki

## How to run

```
FLASK_APP=main.py python3 -m flask run
```

## ESXi extend Annotation format

It starts with `<info>` and ends with `</info>`. The example is indicated below.

```
your unformated text
do you know reiwa ?
<info>
{
  "author": "koyama",
  "created_at": "2020/01/01 20:03:02",
  "tag": [
    "foo",
    "bar"
  ]
}
</info>
```
