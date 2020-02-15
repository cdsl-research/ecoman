# Kushiyaki

## How to run

```
FLASK_APP=app.py python3 -m flask run
```

## ESXi extend Annotation format

It starts with `<info>` and ends with `</info>`. The example is indicated below.

```
you comment
<info>
{
  "author": "koyama",
  "user": "cdsl",
  "password": "your_password",
  "created_at": "2020/01/01 20:03:02",
  "archivable": "2021/01/01 10:00:00", 
  "tag": [
    "foo",
    "bar"
  ]
}
</info>
your comment
```

## Screenshot

<img src="https://raw.githubusercontent.com/cdsl-research/kushiyaki/master/screenshot-list.png" width='600'>

<img src="https://raw.githubusercontent.com/cdsl-research/kushiyaki/master/screenshot-detail.png" width='600'>
